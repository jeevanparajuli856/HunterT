# GCP Infra — DirHunterT Transformer (NVIDIA L4)

## Scripts

| Script | Does |
|--------|------|
| `create_infra.sh` | Create Spot L4 VM |
| `destroy_infra.sh` | Delete VM |
| `create_storage.sh` | Create GCS bucket |
| `destroy_storage.sh` | Delete GCS bucket |

VM and storage are independent — create/destroy them separately.

---

## Prerequisites

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable deploymentmanager.googleapis.com compute.googleapis.com storage.googleapis.com
sudo apt-get install -y gettext-base   # for envsubst
```

---

## Storage

```bash
# Create (once)
BUCKET_NAME=dirhuntert-transformer ./create_storage.sh

# Upload training data (once)
gsutil -m rsync -r ~/HunterT/LTSM_Research/datasets/LM-training-datasets \
  gs://dirhuntert-transformer/data/LM-training-datasets

gsutil -m rsync -r ~/HunterT/LTSM_Research/chosen_wordlists \
  gs://dirhuntert-transformer/data/wordlists

# Destroy when project is done
BUCKET_NAME=dirhuntert-transformer ./destroy_storage.sh
```

---

## VM

```bash
# Create
./create_infra.sh

# SSH in (wait ~2 min for startup script)
gcloud compute ssh ltsm-l4-transformer-vm --zone us-central1-a --project dirhunter-t

# Destroy
./destroy_infra.sh
```

Defaults: `DEPLOYMENT_NAME=ltsm-l4-transformer`, `ZONE=us-central1-a`, `MACHINE_TYPE=g2-standard-4`, `DISK_SIZE_GB=200`.

If L4 Spot capacity is unavailable, try: `ZONE=us-east1-c`, `ZONE=us-east4-c`, `ZONE=europe-west4-b`.

---

## On the VM — first time setup

```bash
# Pull repo and data from bucket
gsutil -m rsync -r gs://dirhuntert-transformer/repo ~/HunterT
gsutil -m rsync -r gs://dirhuntert-transformer/data/LM-training-datasets \
  ~/HunterT/LTSM_Research/datasets/LM-training-datasets
gsutil -m rsync -r gs://dirhuntert-transformer/data/wordlists \
  ~/HunterT/LTSM_Research/chosen_wordlists

# Setup venv
cd ~/HunterT
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Verify
nvidia-smi
python3 -c "import torch; print(torch.cuda.get_device_name(0))"
```

---

## Training

```bash
source ~/HunterT/.venv/bin/activate
cd ~/HunterT/transformer_pipeline
tmux new -s transformer

python3 main.py train \
  --data-folder ../LTSM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models \
  --resume \
  --sync-cmd "gsutil -m rsync -r ./saved_models gs://dirhuntert-transformer/transformer/saved_models" \
  --sync-every-n 1
```

---

## Spot Recovery

```bash
# 1. Recreate VM
./create_infra.sh

# 2. SSH in and restore checkpoints
gsutil -m rsync -r gs://dirhuntert-transformer/transformer/saved_models \
  ~/HunterT/transformer_pipeline/saved_models

# 3. Resume — completed combos are skipped automatically
source ~/HunterT/.venv/bin/activate
cd ~/HunterT/transformer_pipeline
tmux new -s transformer
python3 main.py train --resume \
  --data-folder ../LTSM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models \
  --sync-cmd "gsutil -m rsync -r ./saved_models gs://dirhuntert-transformer/transformer/saved_models" \
  --sync-every-n 1
```
