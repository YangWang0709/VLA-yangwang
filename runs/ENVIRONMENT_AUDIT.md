# Environment Audit

## Workspace

`/home/ubuntu22/VLA`

## Activation Command

```bash
source /home/ubuntu22/miniconda3/etc/profile.d/conda.sh
conda activate env_isaaclab
```

## Conda Discovery

- `conda.sh`: `/home/ubuntu22/miniconda3/etc/profile.d/conda.sh`
- `env_isaaclab`: present
- Activation result: success

## Python / Isaac Probe

- Active env: `env_isaaclab`
- Python executable: `/home/ubuntu22/miniconda3/envs/env_isaaclab/bin/python`
- Python version: `Python 3.11.15`
- `isaacsim` discoverable: true
- `isaaclab` discoverable: true
- `torch` discoverable: true
- `numpy` discoverable: true
- `omni` direct simple import discovery: false
- `pxr` direct simple import discovery: false

Note: Phase 2 should use the proper Isaac headless stage-open probe. The simple import probe is not final evidence for USD stage-open capability.

## Torch / CUDA

- Torch version: `2.7.0+cu128`
- `torch.cuda.is_available()`: true

## GPU

- `nvidia-smi`: `/usr/bin/nvidia-smi`
- GPU: `NVIDIA GeForce RTX 5080`
- Driver: `580.159.03`
- Memory: `16303 MiB`

## Git

- Git executable: `/usr/bin/git`
- Git version: `2.34.1`
- Initial repo state before Phase 0 commit: not a Git repository

## Safety State

- Training performed: false
- RL performed: false
- map_predict training performed: false
- PI/openpi fine-tuning performed: false
- Go2 locomotion training performed: false
- Scene bundle copied: false
- Large files committed: false
