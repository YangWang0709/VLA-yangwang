# New Scene Real Sensor Mapping Report

phase: New Scene Phase C
workspace: /home/ubuntu22/VLA
project_name: A1-VLM-LA Explorer
current_scene_id: building_scene_1_scene_20260608_171052
scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
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
valid_lidar_steps: 0
initial_known_ratio: 0.059506
final_known_ratio: 0.076173
final_occupied_cells: 149
final_known_free_cells: 468
final_unknown_cells: 7483
total_new_known_cells: 617
known_ratio_monotonic_non_decreasing: true
map_update_behavior: pass
plots path: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseC_real_sensor_mapping_20260608_181325/plots
summary path: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseC_real_sensor_mapping_20260608_181325/summary/mapping_summary.json
safe_to_candidate_gain: true
core_dump_found: false
new_kit_core_dump_found: false
training: false
RL: false
map_predict: false
PI_finetuning: false
A1_locomotion_training: false
rollout_started: false

## Caveats
- RTX LiDAR is optional telemetry and is not used for mapping pass/fail.
- BEV map update source is depth-backprojected real RGB-D pointcloud only.
- Runtime sensors and light are in-memory; the repaired USD is not saved.
- This is a mapping smoke only; candidate generation, VLM-LA interface, rollout, and training are not run.

## Artifacts
- run_dir: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseC_real_sensor_mapping_20260608_181325
- mapping_steps_csv: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseC_real_sensor_mapping_20260608_181325/summary/mapping_steps.csv
- mapping_summary_json: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseC_real_sensor_mapping_20260608_181325/summary/mapping_summary.json
- maps_path: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseC_real_sensor_mapping_20260608_181325/maps
- plots_path: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseC_real_sensor_mapping_20260608_181325/plots

## Negative Scope
- No candidate generation.
- No VLM-LA interface.
- No rollout.
- No training, RL, map_predict, checkpoint, or USD save.
- No geometry proxy or mounted geometry proxy mapping source.
