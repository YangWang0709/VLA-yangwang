# Critic Report

## Current Phase

Phase 4R-real A1 real-sensor mapping smoke

## Corrected Fact

The USD scene's real robot is `/World/A1`, not Go2.

## Phase 4R-real Review

status: passed
run_dir: /home/ubuntu22/VLA/runs/phase4r_a1_real_sensor_mapping_smoke_20260607_203607
script: /home/ubuntu22/VLA/scripts/phase4r_a1_real_sensor_mapping_smoke.py
report: /home/ubuntu22/VLA/runs/A1_REAL_SENSOR_MAPPING_SMOKE_REPORT.md

## Evidence

status: passed
run_dir: /home/ubuntu22/VLA/runs/phase4r_a1_real_sensor_mapping_smoke_20260607_203607
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
camera_prim_path: /World/RuntimeSensors/a1_front_rgbd_camera
real_rgb_sensor_available: true
real_depth_sensor_available: true
camera_params_available: true
camera_intrinsics_available: true
real_camera_pointcloud_available: true
camera_pointcloud_source: depth_backprojection
semantic_segmentation_available: true
instance_segmentation_available: true
rtx_lidar_available: true
lidar_used_for_mapping: false
lidar_is_required_for_pass: false
geometry_proxy_used: false
mounted_geometry_proxy_used: false
camera_follows_base_rate: 1.0
mapping_method: raycast_real_sensor_bev_mapping
map_update_source: depth_backprojection_pointcloud
step_count: 10
successful_steps: 10
valid_rgb_steps: 10
valid_depth_steps: 10
valid_camera_pointcloud_steps: 10
valid_lidar_steps: 1
initial_known_ratio: 0.055802
final_known_ratio: 0.069383
final_occupied_cells: 136
final_known_free_cells: 426
final_unknown_cells: 7538
total_new_known_cells: 562
known_ratio_monotonic_non_decreasing: true
map_update_behavior: pass
core_dump_found: false
safe_to_rerun_phase5_with_real_sensors: true
safe_to_continue_phase6: false


## Residual Risks And Caveats

- This validates real-sensor BEV map plumbing, not full exploration behavior.
- RTX LiDAR is optional and not required for pass/fail.
- Candidate gain still needs to be rerun with real sensor maps before Phase 6.

## Prohibited Work Check

- VLM training performed: false
- VLM inference performed: false
- Phase 6 performed: false
- candidate generation performed: false
- RL training performed: false
- map_predict training performed: false
- PI/openpi fine-tuning performed: false
- A1 locomotion training performed: false
- rollout performed: false
- original USD saved or overwritten: false
- raw RGB-D dump saved: false
- large files committed: false

## Decision

Phase 4R-real passed. The next phase is `Rerun Phase 5 A1 candidate viewpoint + information gain smoke with real sensors`, not Phase 6.
