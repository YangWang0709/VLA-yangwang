# Active Task Board

current_phase: Phase 4R-real A1 real-sensor mapping smoke
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
primary_input_channels:
- RGB
- depth
- depth_backprojected_pointcloud
- camera intrinsics/extrinsics
optional_channels:
- semantic segmentation
- instance segmentation
- RTX LiDAR
next_phase: Rerun Phase 5 A1 candidate viewpoint + information gain smoke with real sensors


## Reason

Phase 5.6 validated real Isaac/Omniverse RGB-D sensing. Phase 4R-real reruns mapping so the explored_map / partial map is built from real depth-backprojected pointclouds instead of old geometry proxy data.

## Phase 4R-real Result

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


## Caveats

- RTX LiDAR was recorded as optional telemetry and was not used for mapping pass/fail.
- BEV map update source was `depth_backprojection_pointcloud`.
- Runtime sensors and runtime light are in-memory only; the primary USD scene was not saved or overwritten.
- Do not enter Phase 6 until Phase 5 is rerun with the real sensor route.

## Negative Scope

negative_scope:
- training: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- A1_locomotion_training: false
- primary_rollout: false
- candidate_generation: false
- Phase_6_executed: false


## Next Phase

Rerun Phase 5 A1 candidate viewpoint + information gain smoke with real sensors.
