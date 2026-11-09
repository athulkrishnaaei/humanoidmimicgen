#!/usr/bin/env bash
set -euo pipefail

if ! command -v python3.10 >/dev/null; then
  printf 'Python 3.10 is required. Install it before running this script.\n' >&2
  exit 2
fi
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install \
  'datasets==3.6.0' 'gymnasium==0.29.1' 'h5py==3.14.0' \
  'loguru' 'onnxruntime==1.22.1' 'pin>=2.7,<3' 'PyYAML==6.0.3' \
  'scipy==1.15.3' 'tqdm==4.67.1'
python -m pip install --upgrade \
  'lerobot @ git+https://github.com/huggingface/lerobot.git@8fff0fde7c79f23a93d845d1a50e985de01f8b8a'
python -m pip install --upgrade \
  --index-url https://download.pytorch.org/whl/cu128 \
  'torch==2.10.0' 'torchvision==0.25.0'
python -m pip install --upgrade \
  'numpy==1.26.4' 'opencv-python-headless==4.11.0.86'
python -m pip check
