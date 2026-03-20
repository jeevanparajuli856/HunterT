# GCP Infra (YAML-based)

This folder contains a simple Google Cloud Deployment Manager setup to create and destroy a Spot T4 VM for LSTM training and benchmarks.

## Files

- `deployment-template.yaml`: Parameterized Deployment Manager template.
- `create_infra.sh`: Renders template to `deployment.yaml` and creates infra.
- `destroy_infra.sh`: Deletes the deployment and all managed resources.
- `create_storage.sh`: Creates a GCS bucket for model/results artifacts.
- `destroy_storage.sh`: Deletes the GCS bucket and all objects.
- `deployment.yaml`: Auto-generated at create time. Do not edit manually.

## Prerequisites

- Google Cloud SDK (`gcloud`) installed and authenticated.
- Deployment Manager API enabled in your project.
- `envsubst` available (`sudo apt-get install -y gettext-base`).
- Compute Engine API enabled.

## Quick Start

1. Set project (optional if already set in gcloud):

```bash
gcloud config set project YOUR_PROJECT_ID
```

2. Create Spot instance with defaults:

```bash
cd infra
chmod +x create_infra.sh destroy_infra.sh
./create_infra.sh
```

Optional: create storage bucket (recommended for Spot interruptions):

```bash
cd infra
BUCKET_NAME=your-globally-unique-bucket ./create_storage.sh
```

Defaults used by script:

- `DEPLOYMENT_NAME=lstm-t4`
- `ZONE=us-central1-a`
- `MACHINE_TYPE=n1-standard-8`
- `DISK_SIZE_GB=200`

3. Connect to Spot VM:

```bash
gcloud compute ssh lstm-t4-vm --zone us-central1-a --project YOUR_PROJECT_ID
```

4. Setup on the Spot VM:

```bash
# Install Python and dependencies
sudo apt-get update
sudo apt-get install -y python3.10-venv python3-pip git

# Clone or copy your project
# (Use gsutil, scp, or git clone)

# Setup venv and install dependencies
cd HunterT/lstm_pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt

# Verify GPU
nvidia-smi
```

5. Run in tmux (protects against disconnection):

```bash
tmux new -s lstm
# Now run your training commands
# Detach with Ctrl+B then D
# Reattach with: tmux attach -t lstm
```

6. Destroy infra when done:

```bash
cd infra
./destroy_infra.sh
```

7. Optional: destroy storage bucket when finished with experiments:

```bash
cd infra
BUCKET_NAME=your-globally-unique-bucket ./destroy_storage.sh
```

## Custom Configuration

Override defaults via environment variables:

```bash
cd infra
PROJECT_ID=your-project-id \
DEPLOYMENT_NAME=lstm-t4 \
ZONE=us-central1-a \
MACHINE_TYPE=n1-standard-8 \
DISK_SIZE_GB=200 \
./create_infra.sh
```

Destroy a custom deployment:

```bash
cd infra
PROJECT_ID=your-project-id DEPLOYMENT_NAME=lstm-t4 ./destroy_infra.sh
```

## Running on Spot Instances

Spot VMs are ~70-80% cheaper but can be preempted. To handle this:

1. **Always use tmux** to prevent disconnection issues
2. **Enable resume mode** in training (`--resume` flag)
3. **Sync to GCS periodically** to prevent data loss
4. **Re-run same command** if preempted - completed work is automatically skipped

See `../lstm_pipeline/README.md` for full training commands.

## Cloud Storage Sync

Create bucket (one time):

```bash
cd infra
BUCKET_NAME=dirhuntert-lstm ./create_storage.sh
```

Run training with periodic sync:

```bash
cd ../lstm_pipeline
python main.py train \
	--resume \
	--progress-file ./saved_models/train_progress.json \
	--checkpoint-dir ./saved_models/checkpoints \
	--sync-cmd "gsutil -m rsync -r ./saved_models gs://dirhuntert-lstm/lstm/saved_models && gsutil -m rsync -r ./results gs://dirhuntert-lstm/lstm/results" \
	--sync-every-n 1
```

Restore artifacts on a new Spot VM after preemption:

```bash
cd ~/HunterT/lstm_pipeline
gsutil -m rsync -r gs://dirhuntert-lstm/lstm/saved_models ./saved_models
gsutil -m rsync -r gs://dirhuntert-lstm/lstm/results ./results
```

## Spot Recovery Runbook

If the Spot VM is preempted, run this exact sequence.

1. Recreate infrastructure:

```bash
cd /home/jeevan/HunterT/infra
./create_infra.sh
```

2. Connect to the new VM:

```bash
gcloud compute ssh lstm-t4-vm --zone us-central1-a --project YOUR_PROJECT_ID
```

3. Recreate Python environment:

```bash
cd ~/HunterT/lstm_pipeline
python -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt
```

4. Restore saved artifacts from GCS:

```bash
cd ~/HunterT/lstm_pipeline
gsutil -m rsync -r gs://dirhuntert-lstm/lstm/saved_models ./saved_models
gsutil -m rsync -r gs://dirhuntert-lstm/lstm/results ./results
```

5. Resume training:

```bash
cd ~/HunterT/lstm_pipeline
python main.py train \
	--resume \
	--progress-file ./saved_models/train_progress.json \
	--checkpoint-dir ./saved_models/checkpoints \
	--sync-cmd "gsutil -m rsync -r ./saved_models gs://dirhuntert-lstm/lstm/saved_models && gsutil -m rsync -r ./results gs://dirhuntert-lstm/lstm/results" \
	--sync-every-n 1
```

6. Optional: run in tmux to avoid SSH disconnect interruptions:

```bash
tmux new -s lstm
# run training command
# detach: Ctrl+B then D
# reattach: tmux attach -t lstm
```

## Notes

- VM is created as Spot (`preemptible`) with `nvidia-tesla-t4` accelerator.
- Startup script installs base tools and attempts NVIDIA driver installation.
- If Spot capacity is unavailable in your zone, switch `ZONE` and retry.
- Deployment Manager is used because you asked for YAML-based easy create/destroy flow.
- Spot instances can be preempted at any time - use resume mode and sync to GCS.




gsutil -m rsync -r ./LSTM_Research/ gs://dirhuntert-lstm/


gcloud compute ssh lstm-t4-vm --zone us-central1-a --project dirhunter-t
gcloud compute config-ssh