# A1 Real Sensor Mapping Smoke Report

phase: Phase 4R-real
workspace: /home/ubuntu22/VLA
project_name: A1-VLM-LA Explorer
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
previous_sensor_method: mounted_geometry_proxy_pointcloud_from_a1_front_sensor
sensor_method: real_isaac_omniverse_rgbd
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
movement_mode: kinematic_existing_a1_root
real_a1_locomotion_controller: false
map_type: BEV occupancy grid
mapping_method: raycast_real_sensor_bev_mapping
map_update_source: depth_backprojection_pointcloud
map_resolution_m: 0.1
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
plots_path: /home/ubuntu22/VLA/runs/phase4r_a1_real_sensor_mapping_smoke_20260607_203607/plots
summary_path: /home/ubuntu22/VLA/runs/phase4r_a1_real_sensor_mapping_smoke_20260607_203607/summary/mapping_summary.json
safe_to_rerun_phase5_with_real_sensors: true
safe_to_continue_phase6: false
caveats: ['RTX LiDAR is optional telemetry and not used for mapping pass/fail.', 'Mapping update source is depth-backprojected real RGB-D pointcloud only.', 'Runtime sensors and light are in-memory; the primary USD is not saved.']
training: false
RL: false
map_predict: false
PI_finetuning: false
A1_locomotion_training: false
rollout_started: false

## Evidence

- run_dir: /home/ubuntu22/VLA/runs/phase4r_a1_real_sensor_mapping_smoke_20260607_203607
- mapping_steps_csv: /home/ubuntu22/VLA/runs/phase4r_a1_real_sensor_mapping_smoke_20260607_203607/summary/mapping_steps.csv
- mapping_summary_json: /home/ubuntu22/VLA/runs/phase4r_a1_real_sensor_mapping_smoke_20260607_203607/summary/mapping_summary.json
- BEV map was updated from depth-backprojected real camera pointclouds.
- RTX LiDAR was recorded as optional telemetry and was not used for map pass/fail.
- The original USD scene was not saved or overwritten.

## Negative Scope

- No Phase 5 was auto-started.
- No Phase 6.
- No candidate generation.
- No training, RL, map_predict, checkpoint, or rollout.
- No geometry proxy or mounted geometry proxy mapping source.
