# A1 Mapping Smoke Report

phase: Phase 4
workspace: /home/ubuntu22/VLA
project_name: A1-VLM-LA Explorer
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
previous_proxy_results_status: superseded_for_formal_a1_pipeline
movement_mode: kinematic_existing_a1_root
real_a1_locomotion_controller: false
existing_sensor_reused: false
geometry_proxy_sensor_used: true
sensor_method: geometry_proxy_pointcloud_from_a1_base_pose
map_type: BEV occupancy grid
mapping_method: raycast_bev_proxy_mapping
map_resolution_m: 0.1
step_count: 10
successful_steps: 10
valid_observation_steps: 10
initial_known_ratio: 0.052969
final_known_ratio: 0.087188
final_occupied_cells: 308
final_known_free_cells: 250
final_unknown_cells: 5842
total_new_known_cells: 558
known_ratio_monotonic_non_decreasing: true
map_update_behavior: pass
plots_path: /home/ubuntu22/VLA/runs/phase4_a1_mapping_smoke_20260607_194403/plots
summary_path: /home/ubuntu22/VLA/runs/phase4_a1_mapping_smoke_20260607_194403/summary/mapping_summary.json
safe_to_continue_phase5: true
training: false
RL: false
map_predict: false
PI_finetuning: false
A1_locomotion_training: false
rollout_started: false

## Artifacts

- run_dir: `/home/ubuntu22/VLA/runs/phase4_a1_mapping_smoke_20260607_194403`
- steps_csv: `/home/ubuntu22/VLA/runs/phase4_a1_mapping_smoke_20260607_194403/summary/mapping_steps.csv`
- final_bev_ascii: `/home/ubuntu22/VLA/runs/phase4_a1_mapping_smoke_20260607_194403/maps/final_bev_ascii.txt`
- reports_dir: `/home/ubuntu22/VLA/runs/phase4_a1_mapping_smoke_20260607_194403/reports`

## Caveats

- This is formal A1 mapping smoke based on existing USD prim /World/A1, not the old temporary Go2 proxy.
- Sensor data is geometry proxy pointcloud/depth from A1 base pose; this is not real RGB-D SLAM.
- Movement is short in-memory kinematic A1 root motion for mapping smoke, not real A1 locomotion control or a rollout.
- No A1-bound USD camera/sensor prim was found; mapping used geometry proxy observations only.

## Negative Scope

- No VLM training or inference.
- No RL training.
- No map_predict training or mainline implementation.
- No PI/openpi action-head fine-tuning.
- No A1 locomotion policy training.
- No Phase 5 candidate generation and no long rollout.
- No temporary Go2 proxy was created or used as formal data.
- Original USD scene was opened and edited only in memory; it was not saved or overwritten.
