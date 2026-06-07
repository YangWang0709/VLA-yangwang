# WEBGPT Brief

## Current Phase

Phase 1: USD scene bundle placement and Git ignore

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

- Activated `env_isaaclab` in the VLA workspace.
- Copied the complete primary scene bundle from `/home/ubuntu22/pi/scenes/primary_building_scene_repaired/` to `/home/ubuntu22/VLA/scenes/primary_building_scene_repaired/`.
- Confirmed the target USD exists and is `USD ASCII, version 1.0`.
- Confirmed `dependencies/` exists.
- Confirmed the scene bundle and dependencies are ignored by Git.
- Confirmed no files larger than 50MB are tracked by Git.

## Key Metrics

- scene_path: `/home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd`
- scene_exists: true
- copied_from_pi: true
- bundle_size: 490M
- dependencies_present: true
- git_ignore_scene_bundle: true
- files_over_50MB_tracked_by_git: none
- safe_to_continue_phase2: true

## Artifacts

- runs/SCENE_BUNDLE_PLACEMENT_REPORT.md
- runs/ACTIVE_TASK_BOARD.md
- runs/WEBGPT_BRIEF.md
- runs/CRITIC_REPORT.md

## Negative Scope

- training: false
- RL: false
- Go2 locomotion training: false
- PI action fine-tuning: false
- openpi action fine-tuning: false
- explicit map_predict mainline: false
- free coordinate output: false
- rollout: false

## Next Step

Phase 2: Isaac headless scene open + Go2 stage inspection smoke.
