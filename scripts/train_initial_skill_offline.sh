#!/usr/bin/env bash
set -euo pipefail

task="${SKILL_TASK:?Set SKILL_TASK to 04_push_shelf_forward or 07_box_table_to_shelf}"
case "$task" in
  04_push_shelf_forward|07_box_table_to_shelf) ;;
  *) printf 'Unknown skill: %s\n' "$task" >&2; exit 2 ;;
esac
source_dir="${SKILL_SOURCE_DIR:?Set SKILL_SOURCE_DIR to the transferred dataset snapshot root}"
data_dir="${SKILL_DATA_DIR:-$PWD/data/policy_data}"
output_dir="${SKILL_OUTPUT_DIR:-$PWD/outputs/$task}"
batch_size="${SKILL_BATCH_SIZE:-16}"
steps="${SKILL_STEPS:-20000}"
save_freq="${SKILL_SAVE_FREQ:-5000}"
workers="${SKILL_WORKERS:-4}"
seed="${SKILL_SEED:-1000}"

python3 scripts/verify_initial_skills_data.py "$source_dir" --task "$task"
export HF_HUB_OFFLINE=1
export HF_DATASETS_OFFLINE=1

args=(
  --task "$task"
  --offline-source-dir "$source_dir"
  --data-dir "$data_dir"
  --output-dir "$output_dir"
  --batch-size "$batch_size"
  --steps "$steps"
  --save-freq "$save_freq"
  --num-workers "$workers"
  --seed "$seed"
)
if [[ "${SKILL_RESUME:-0}" == "1" ]]; then
  args+=(--resume)
fi
exec python3 scripts/train_policy_example.py "${args[@]}"
