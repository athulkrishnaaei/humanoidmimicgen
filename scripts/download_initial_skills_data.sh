#!/usr/bin/env bash
set -euo pipefail

# Run where Hugging Face access is permitted. Transfer the resulting directory
# to AWS through an approved company storage channel.
destination="${1:?Usage: $0 DESTINATION_DIRECTORY [task_slug]}"
task="${2:-all}"
case "$task" in
  all) tasks=(04_push_shelf_forward 07_box_table_to_shelf) ;;
  04_push_shelf_forward|07_box_table_to_shelf) tasks=("$task") ;;
  *) printf 'Unknown skill: %s\n' "$task" >&2; exit 2 ;;
esac

for skill in "${tasks[@]}"; do
  hf download linkenv/humanoidmimicgen-g1-benchmark \
    --repo-type dataset \
    --revision acf6b53853dd0199bf852286ca68067cc37472ff \
    --include "datasets/$skill/shard_*/meta/**" \
    --include "datasets/$skill/shard_*/data/**" \
    --include "datasets/$skill/shard_*/videos/**/observation.images.ego_view/**" \
    --local-dir "$destination"
  python3 scripts/verify_initial_skills_data.py "$destination" --task "$skill"
done
