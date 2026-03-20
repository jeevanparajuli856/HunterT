# GCP Infra — DirHunterT (NVIDIA V100 Spot)

Spot V100 GPU infrastructure for training both LSTM baseline and DirHunterT transformer models.

## Scripts

| Script | Does |
|--------|------|
| `create_infra.sh` | Create Spot V100 VM (auto-tries zones until capacity found) |
| `destroy_infra.sh` | Delete VM deployment |
| `create_storage.sh` | Create GCS bucket for checkpoints & results |
| `destroy_storage.sh` | Delete GCS bucket |

VM and storage are independent — create/destroy them separately.

---

## Prerequisites

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable deploymentmanager.googleapis.com compute.googleapis.com storage.googleapis.com
sudo apt-get install -y gettext-base
```

---

## VM Defaults

| Setting | Default |
|---------|---------|
| `DEPLOYMENT_NAME` | `lstm-v100-transformer` |
| `MACHINE_TYPE` | `custom-12-46080` (12 vCPU, 45 GB RAM) |
| `GPU_TYPE` | `nvidia-tesla-v100` |
| `DISK_SIZE_GB` | `200` (SSD) |
| Image | PyTorch 2.7 / CUDA 12.8 / Ubuntu 22.04 (GCP Deep Learning VM) |

**Zone fallback order:** `us-central1-b → a → c → us-east1-c → d → europe-west4-a → b → asia-east1-a`

Override any default: `MACHINE_TYPE=n1-standard-16 ./create_infra.sh`

---

## Storage

```bash
# Create bucket (name must be globally unique)
BUCKET_NAME=dirhuntert-artifacts ./create_storage.sh

# Upload training data (one-time)
gsutil -m rsync -r ~/HunterT/LTSM_Research/datasets/LM-training-datasets \
  gs://dirhuntert-artifacts/data/LM-training-datasets

gsutil -m rsync -r ~/HunterT/LTSM_Research/chosen_wordlists \
  gs://dirhuntert-artifacts/data/wordlists

# Destroy when done
BUCKET_NAME=dirhuntert-artifacts ./destroy_storage.sh
```

---

## Create & Connect to VM

```bash
# Create — auto-tries zones until V100 Spot capacity is found
./create_infra.sh

# Script prints SSH command on success, e.g.:
#   gcloud compute ssh lstm-v100-transformer-vm --zone us-central1-b --project <PROJECT_ID>

# Destroy
./destroy_infra.sh
```

---

## First-Time VM Setup

```bash
# Pull repo and data from bucket
gsutil -m rsync -r gs://dirhuntert-artifacts/repo ~/HunterT
gsutil -m rsync -r gs://dirhuntert-artifacts/data/LM-training-datasets \
  ~/HunterT/LTSM_Research/datasets/LM-training-datasets
gsutil -m rsync -r gs://dirhuntert-artifacts/data/wordlists \
  ~/HunterT/LTSM_Research/chosen_wordlists

# Setup venv (DLVM image has driver + CUDA pre-installed, no manual install needed)
cd ~/HunterT
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Verify GPU
nvidia-smi
python3 -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

---

## Training

### LSTM Baseline

```bash
source ~/HunterT/.venv/bin/activate
cd ~/HunterT/ltsm_pipeline
tmux new -s lstm

python3 main.py train \
  --data-folder ../LTSM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models \
  --resume \
  --sync-cmd "gsutil -m rsync -r ./saved_models gs://dirhuntert-artifacts/lstm/saved_models" \
  --sync-every-n 1

# Detach: Ctrl+B then D  |  Reattach: tmux attach -t lstm
```

### DirHunterT Transformer

```bash
source ~/HunterT/.venv/bin/activate
cd ~/HunterT/transformer_pipeline
tmux new -s transformer

python3 main.py train \
  --data-folder ../LTSM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models \
  --resume \
  --sync-cmd "gsutil -m rsync -r ./saved_models gs://dirhuntert-artifacts/transformer/saved_models" \
  --sync-every-n 1

# Detach: Ctrl+B then D  |  Reattach: tmux attach -t transformer
```

---

## Evaluation

```bash
# LSTM
cd ~/HunterT/ltsm_pipeline
python3 main.py evaluate \
  --data-folder ../LTSM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models \
  --wordlist ../LTSM_Research/chosen_wordlists/big_wfuzz.txt \
  --results-folder ./results

# Transformer
cd ~/HunterT/transformer_pipeline
python3 main.py evaluate \
  --data-folder ../LTSM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models \
  --wordlist ../LTSM_Research/chosen_wordlists/big_wfuzz.txt \
  --results-folder ./results
```

---

## Spot Recovery

Spot VMs can be preempted at any time. Both pipelines support `--resume` which skips completed hyperparameter combos.

```bash
# 1. Recreate VM
./create_infra.sh

# 2. Restore checkpoints from GCS
gsutil -m rsync -r gs://dirhuntert-artifacts/transformer/saved_models \
  ~/HunterT/transformer_pipeline/saved_models

# 3. Resume training (completed combos skipped automatically)
source ~/HunterT/.venv/bin/activate
cd ~/HunterT/transformer_pipeline
tmux new -s transformer
python3 main.py train --resume \
  --data-folder ../LTSM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models \
  --sync-cmd "gsutil -m rsync -r ./saved_models gs://dirhuntert-artifacts/transformer/saved_models" \
  --sync-every-n 1
```
