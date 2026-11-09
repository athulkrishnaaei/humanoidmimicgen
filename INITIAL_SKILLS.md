# Two initial HumanoidMimicGen skills

This fork trains separate Diffusion Policies for two Unitree G1 MuJoCo tasks:

| Skill | Task ID | Objective |
| --- | --- | --- |
| Push Shelf Forward | `04_push_shelf_forward` | Push a shelving cart into a marked target zone. |
| Box Table to Shelf | `07_box_table_to_shelf` | Transfer a box from a table into a shelf. |

The upstream [HumanoidMimicGen repository](https://github.com/NVlabs/humanoidmimicgen)
contains the MuJoCo scenes, robot model, whole-body controller integration, and
training code. It does **not** contain the training demonstrations or a released
checkpoint for either task. The [benchmark dataset](https://huggingface.co/datasets/linkenv/humanoidmimicgen-g1-benchmark)
is hosted separately. Do not commit datasets, checkpoints, or company data to GitHub.

## Compute and storage

The published training example was reproduced on an RTX 5090 with Python 3.10,
CUDA 12.8, PyTorch 2.10, 20,000 updates, and batch size 16. For a full AWS
run, start with [`g6e.2xlarge`](https://aws.amazon.com/ec2/instance-types/accelerated-computing/):
one NVIDIA L40S GPU with 48 GB VRAM, 8 vCPUs, and 64 GiB system RAM. This is
a capacity recommendation, not a verified performance result for this exact
job. Check VRAM and throughput during a short run. A cheaper 24 GB G5 GPU may
work, but its memory fit at batch size 16 is unverified.
The RTX 4060 8 GB can be tried at batch size 1 or 2, but that is not the same
training exposure as 20,000 updates at batch size 16. Out-of-memory is possible.

Plan for at least 200 GB of persistent working storage when preparing both task
datasets, conversions, checkpoints, and logs; actual use should be measured.
The benchmark repository is about 100 GB across all nine tasks. This workflow
downloads only the selected task directories. The local `manim` filesystem had
only 18 GB free when this setup was created, so the datasets were not downloaded
there. AWS instance charges and storage charges depend on your account and region.

## Get the dataset to AWS without Hugging Face access there

You can use the [Google Colab download notebook](https://colab.research.google.com/github/athulkrishnaaei/humanoidmimicgen/blob/main/notebooks/download_initial_skills_colab.ipynb)
to save verified task archives to Google Drive, then transfer those archives
through a company-approved route. The notebook includes extraction and
checksum commands for AWS.

On a machine where downloading from Hugging Face is allowed and enough disk is
available, clone this fork and run:

```bash
git clone https://github.com/athulkrishnaaei/humanoidmimicgen.git
cd humanoidmimicgen
bash scripts/download_initial_skills_data.sh /data/hmg-initial-skills
```

To fetch just one task first, append its task ID:

```bash
bash scripts/download_initial_skills_data.sh /data/hmg-initial-skills 07_box_table_to_shelf
```

The downloader pins the benchmark dataset revision and verifies all eight
shards, their metadata, per-episode Parquet files, and ego-camera videos.
Transfer `/data/hmg-initial-skills` through a company-approved storage route,
such as an S3 bucket your organization permits. For example:

```bash
aws s3 sync /data/hmg-initial-skills/ s3://YOUR_APPROVED_BUCKET/hmg-initial-skills/
```

On AWS, download from that bucket and verify before training:

```bash
aws s3 sync s3://YOUR_APPROVED_BUCKET/hmg-initial-skills/ /data/hmg-initial-skills/
python3 scripts/verify_initial_skills_data.py /data/hmg-initial-skills \
  --task 04_push_shelf_forward --task 07_box_table_to_shelf
```

If your company's rules prohibit importing this dataset altogether, do not use
the transfer route. The GitHub repository alone cannot train these policies;
you would need an approved dataset or to generate demonstrations in MuJoCo.

## Set up the AWS training environment

Use a GPU-enabled Linux image with a driver compatible with CUDA 12.8. The
setup script follows the exact upstream LeRobot and PyTorch revisions:

```bash
git clone https://github.com/athulkrishnaaei/humanoidmimicgen.git
cd humanoidmimicgen
bash scripts/setup_training_env.sh
source .venv/bin/activate
nvidia-smi
```

The setup needs GitHub, PyPI, and the PyTorch wheel index, but the **training
run** uses a local dataset and sets Hugging Face offline mode. If AWS also
blocks those package sources, mirror the dependencies through your approved
package repository first.

## Train each skill

Run from the repository root. The source directory must contain `datasets/`.
The trainer converts each task's eight shards into the pinned model-facing
43D state, ego image, and 35D WBC-goal action schema. Keep data and output
directories on persistent storage.

```bash
export SKILL_SOURCE_DIR=/data/hmg-initial-skills
export SKILL_DATA_DIR=/data/hmg-policy-data
export SKILL_TASK=07_box_table_to_shelf
bash scripts/train_initial_skill_offline.sh
```

Then train the other skill independently:

```bash
export SKILL_TASK=04_push_shelf_forward
bash scripts/train_initial_skill_offline.sh
```

Defaults are batch size 16, 20,000 updates, a checkpoint every 5,000 updates,
four workers, and seed 1000. Output is under `outputs/<task>` unless
`SKILL_OUTPUT_DIR` is set. For an 8 GB **feasibility run** with a separate
output directory:

```bash
export SKILL_TASK=07_box_table_to_shelf
export SKILL_BATCH_SIZE=1
export SKILL_STEPS=100
export SKILL_SAVE_FREQ=100
export SKILL_WORKERS=2
export SKILL_OUTPUT_DIR=/data/outputs/box_shelf_8gb_smoke
time bash scripts/train_initial_skill_offline.sh
nvidia-smi
```

This 100-update run checks setup and memory only. It is not a trained policy.
For a full run, unset those overrides or choose a separate full-run output.
Estimate training duration from the measured seconds per update. At 1, 3, or
5 seconds per update, 20,000 updates take roughly 5.6, 16.7, or 27.8 hours,
respectively, plus preparation and evaluation. No measured duration for these
specific two tasks is published in the upstream instructions.

To resume an interrupted run, keep the same output directory and all original
training parameters, then run with `SKILL_RESUME=1`.

## Evaluate

The whole-body controller weights are distinct from the task policy. Their
downloader fetches two checksum-pinned files from GitHub under the NVIDIA Open
Model License; download them once, then evaluate each skill separately:

```bash
python -m humanoidmimicgen.download_wbc_policies \
  --output-dir /data/hmg-wbc-policies
python scripts/evaluate_policy_example.py \
  --checkpoint-dir outputs/07_box_table_to_shelf/checkpoints/020000 \
  --task 07_box_table_to_shelf --num-episodes 20 --seed 0 \
  --wbc-policy-dir /data/hmg-wbc-policies \
  --output outputs/07_box_table_to_shelf/eval_020000_20ep.json
python scripts/evaluate_policy_example.py \
  --checkpoint-dir outputs/04_push_shelf_forward/checkpoints/020000 \
  --task 04_push_shelf_forward --num-episodes 20 --seed 0 \
  --wbc-policy-dir /data/hmg-wbc-policies \
  --output outputs/04_push_shelf_forward/eval_020000_20ep.json
```

These commands establish task-policy baselines. Safety Brain interruption and
replanning are separate experiments and are not implemented by this fork yet.
