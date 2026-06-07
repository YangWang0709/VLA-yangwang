# WEBGPT Brief

## Current Phase

Phase 0: VLA workspace initialization.

## Workspace

/home/ubuntu22/VLA

## Main Goal

Go2-VLM-LA Explorer for 3D Active Exploration

## Robot Platform

Unitree Go2

## Robot Source

Working premise: existing Go2 prim inside the USD scene. Phase 2 must inspect and verify the actual prim path. A temporary proxy is allowed only if no Go2-like hierarchy is found in the USD.

## Output Contract

VLM output: Go to candidate <id>.

## Completed

- Created the VLA workspace structure.
- Audited conda, Python, Isaac-related modules, GPU, and Git.
- Created Phase 0 planning, interface, dataset, Go2 sensor mount, critic, and context docs.
- Added Git ignore rules for large USD/scene/mesh/texture/data/checkpoint artifacts.

## Key Metrics

- Conda env: env_isaaclab activation succeeds.
- Python: 3.11.15 in env_isaaclab.
- Isaac module discovery: isaacsim true, isaaclab true.
- GPU: NVIDIA GeForce RTX 5080 detected through nvidia-smi.
- Git: available.
- Training: false.

## Artifacts

- runs/ENVIRONMENT_AUDIT.md
- runs/VLM_LA_EXPLORER_PLAN.md
- runs/VLM_LA_INTERFACE_SPEC.md
- runs/VLM_LA_DATASET_SPEC.md
- runs/GO2_SENSOR_MOUNT_SPEC.md
- runs/GO2_STAGE_INSPECTION_REPORT.md
- runs/ACTIVE_TASK_BOARD.md
- runs/CRITIC_REPORT.md
- runs/CONTEXT_COMPACT.md
- runs/FAILURE_DIAGNOSIS.md

## Negative Scope

- training: false
- RL: false
- Go2 locomotion training: false
- PI action fine-tuning: false
- openpi action fine-tuning: false
- explicit map_predict mainline: false
- free coordinate output: false

## Next Step

Phase 1: locate or copy the full primary USD scene bundle into `/home/ubuntu22/VLA/scenes/primary_building_scene_repaired/`, then verify it is ignored by Git.
