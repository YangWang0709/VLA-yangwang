# Active Task Board

current_phase: Phase 2 Isaac headless scene open + Go2 stage inspection smoke
workspace: /home/ubuntu22/VLA
main_goal: Go2-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.
robot_platform: Unitree Go2
robot_source: temporary_proxy_required

## Phase 2 Tasks

- [x] Verify local Git state and Phase 1 sync.
- [x] Create Phase 2 run directory.
- [x] Create `scripts/probe_isaac_open_stage.py`.
- [x] Create `scripts/inspect_usd_go2_stage.py`.
- [x] Run Isaac headless scene-open smoke.
- [x] Confirm stage is available and prim_count > 0.
- [x] Confirm no core dump.
- [x] Run Go2 stage inspection.
- [x] Generate `runs/SCENE_OPEN_SMOKE_REPORT.md`.
- [x] Generate `runs/GO2_STAGE_INSPECTION_REPORT.md`.

## Key Results

- open_stage_result: true
- stage_available: true
- prim_count: 1324
- core_dump_found: false
- go2_in_usd_found: false
- go2_root_prim: null
- temporary_go2_proxy_required: true
- safe_to_continue_phase3: true

## Negative Scope

- training: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- Go2_locomotion_training: false
- primary_rollout: false
- USD_stage_modified: false

## Next Phase

Phase 3 Unitree Go2 sensor smoke.
