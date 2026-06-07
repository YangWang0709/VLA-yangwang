# Go2 Mapping Smoke Report

phase: Phase 4
workspace: /home/ubuntu22/VLA
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
robot_platform_target: Unitree Go2
go2_in_usd_found: false
robot_source: temporary_go2_proxy
temporary_go2_proxy_used: true
not_final_robot_asset: true
movement_mode: kinematic_proxy
map_type: BEV occupancy grid
map_resolution_m: 0.1
step_count: 10
successful_steps: 10
valid_observation_steps: 10
initial_known_ratio: 0.052969
final_known_ratio: 0.105625
final_occupied_cells: 423
final_known_free_cells: 253
final_unknown_cells: 5724
total_new_known_cells: 676
known_ratio_monotonic_non_decreasing: true
map_update_behavior: pass
plots path: /home/ubuntu22/VLA/runs/phase4_go2_mapping_smoke_20260607_191104/plots
summary path: /home/ubuntu22/VLA/runs/phase4_go2_mapping_smoke_20260607_191104/summary
safe_to_continue_phase5: true
training: false
RL: false
map_predict: false
PI_finetuning: false
Go2_locomotion_training: false
rollout_started: false

## Caveats

- Phase 4 uses a temporary Go2-shaped proxy because Phase 2 did not verify an existing Go2 prim.
- Mapping uses simplified BEV smoke logic from geometry/depth/pointcloud proxy observations, not map_predict.
- The temporary proxy is not a final robot asset and `/World/A1` is not treated as Go2.

## Artifacts

- mapping_steps.csv: `/home/ubuntu22/VLA/runs/phase4_go2_mapping_smoke_20260607_191104/summary/mapping_steps.csv`
- mapping_summary.json: `/home/ubuntu22/VLA/runs/phase4_go2_mapping_smoke_20260607_191104/summary/mapping_summary.json`
- final_bev_ascii.txt: `/home/ubuntu22/VLA/runs/phase4_go2_mapping_smoke_20260607_191104/maps/final_bev_ascii.txt`
- final_map_snapshot.npz: `/home/ubuntu22/VLA/runs/phase4_go2_mapping_smoke_20260607_191104/maps/final_map_snapshot.npz`

## Negative Scope

- No Phase 5 candidate generation.
- No VLM-LA interface or VLM inference.
- No rollout.
- No training, RL, map_predict, PI/openpi fine-tuning, or Go2 locomotion training.
- Original USD scene was not saved or overwritten.
- `/World/A1` was not treated as Go2.
