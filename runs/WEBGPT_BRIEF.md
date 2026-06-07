# WEBGPT Brief

## Current Phase

Phase 2 Isaac headless scene open + Go2 stage inspection smoke

## Workspace

/home/ubuntu22/VLA

## Main Goal

Go2-VLM-LA Explorer for 3D Active Exploration

## Output Contract

Go to candidate <id>.

## Robot Platform

Unitree Go2

## Robot Source

temporary_proxy_required

## Completed

- Verified Phase 1 commit and origin/main sync.
- Opened the primary USD with Isaac headless SimulationApp.
- Confirmed the stage is available and has 1324 prims.
- Confirmed no core dump was detected.
- Ran read-only stage inspection for Go2/Unitree/robot/base/sensor candidates.
- Wrote Phase 2 reports.

## Key Metrics

- scene_path: `/home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd`
- scene_bundle_size: 490M
- dependencies_present: true
- git_ignore_scene_bundle: true
- isaac_headless_open_exit_code: 0
- open_stage_result: true
- stage_available: true
- prim_count: 1324
- mesh_count: 127
- cube_count: 279
- material_count: 124
- camera_count: 4
- go2_in_usd_found: false
- go2_root_prim: null
- temporary_go2_proxy_required: true
- safe_to_continue_phase3: true

## Artifacts

- runs/SCENE_OPEN_SMOKE_REPORT.md
- runs/GO2_STAGE_INSPECTION_REPORT.md
- scripts/probe_isaac_open_stage.py
- scripts/inspect_usd_go2_stage.py
- /home/ubuntu22/VLA/runs/phase2_scene_open_go2_inspection_20260607_181505

## Negative Scope

- training: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- Go2_locomotion_training: false
- primary_rollout: false
- free_coordinate_output: false

## Caveat

Inspection found an articulated `/World/A1` hierarchy but did not find an explicit verified Go2 prim. Phase 3 must use the temporary proxy route unless a verified Go2 prim is provided or identified.

## Next Phase

Phase 3 Unitree Go2 sensor smoke.
