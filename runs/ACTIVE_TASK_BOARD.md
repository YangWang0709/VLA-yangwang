# Active Task Board

current_phase: Phase 4 Go2 primary-scene mapping smoke
workspace: /home/ubuntu22/VLA
main_goal: Go2-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.
robot_platform_target: Unitree Go2
robot_source: temporary_go2_proxy

## Phase 4 Tasks

- [x] Verify Phase 3 commit and clean Git state.
- [x] Create Phase 4 run directory.
- [x] Create `scripts/phase4_go2_mapping_smoke.py`.
- [x] Load primary scene in Isaac headless.
- [x] Create in-memory `/World/TemporaryGo2Proxy`.
- [x] Run 10 short mapping steps.
- [x] Build simplified BEV occupancy grid from pointcloud/depth proxy observations.
- [x] Save mapping steps, summary, final map snapshot, ASCII map, and lightweight plots in the run directory.
- [x] Write `runs/GO2_MAPPING_SMOKE_REPORT.md`.

## Key Results

- robot_source: temporary_go2_proxy
- not_final_robot_asset: true
- movement_mode: kinematic_proxy
- map_type: BEV occupancy grid
- map_resolution_m: 0.1
- step_count: 10
- successful_steps: 10
- valid_observation_steps: 10
- initial_known_ratio: 0.052969
- final_known_ratio: 0.105625
- final_occupied_cells: 423
- final_known_free_cells: 253
- final_unknown_cells: 5724
- total_new_known_cells: 676
- known_ratio_monotonic_non_decreasing: true
- map_update_behavior: pass
- safe_to_continue_phase5: true

## Negative Scope

- training: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- Go2_locomotion_training: false
- primary_rollout: false
- candidate_generation: false
- VLM_inference_or_finetuning: false
- original_USD_modified: false

## Next Phase

Phase 5 Go2 candidate viewpoint + information gain smoke.
