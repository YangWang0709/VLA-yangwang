# WEBGPT Brief

## Current Phase

Phase 4 Go2 primary-scene mapping smoke

## Workspace

/home/ubuntu22/VLA

## Main Goal

Go2-VLM-LA Explorer for 3D Active Exploration

## Output Contract

Go to candidate <id>.

## Robot Platform Target

Unitree Go2

## Robot Source

temporary_go2_proxy

## Completed

- Loaded the primary scene with Isaac headless.
- Used a temporary Go2-shaped kinematic proxy, not `/World/A1` and not a verified Go2 asset.
- Built a simplified BEV occupancy grid using pointcloud/depth proxy observations.
- Recorded known_free, occupied, unknown, observed_count, and robot pose trace.
- Generated lightweight BEV and curve plots in the Phase 4 run directory.
- Did not train, run Phase 5, generate candidates, run VLM inference, run rollout, or save the original USD.

## Key Metrics

- scene_path: `/home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd`
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
- collision_count: 0
- stuck_count: 0
- falling_count: 0
- safe_to_continue_phase5: true

## Artifacts

- runs/GO2_MAPPING_SMOKE_REPORT.md
- scripts/phase4_go2_mapping_smoke.py
- /home/ubuntu22/VLA/runs/phase4_go2_mapping_smoke_20260607_191104
- /home/ubuntu22/VLA/runs/phase4_go2_mapping_smoke_20260607_191104/summary/mapping_steps.csv
- /home/ubuntu22/VLA/runs/phase4_go2_mapping_smoke_20260607_191104/summary/mapping_summary.json
- /home/ubuntu22/VLA/runs/phase4_go2_mapping_smoke_20260607_191104/plots

## Negative Scope

- training: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- Go2_locomotion_training: false
- primary_rollout: false
- candidate_generation: false
- VLM_inference_or_finetuning: false
- free_coordinate_output: false

## Caveat

Phase 4 uses simplified BEV mapping smoke from geometry/depth/pointcloud proxy observations. The temporary proxy is not a final Go2 asset, and `/World/A1` is not treated as Go2.

## Next Phase

Phase 5 Go2 candidate viewpoint + information gain smoke.
