# New Scene Real Sensor Smoke Report

phase: New Scene Phase B
workspace: /home/ubuntu22/VLA
project_name: A1-VLM-LA Explorer
current_scene_id: building_scene_1_scene_20260608_171052
scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
original_user_usd_path: /home/ubuntu22/VLA/building_scene(1).usd
scene_open_result: true
stage_available: true
stage_open_method: omni.usd.context.open_stage after repaired bundle dependency localization
stage_open_elapsed_sec: 0.21
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
base_pose_readable: true
sensor_method: real_isaac_omniverse_sensor_suite
camera_prim_path: /World/RuntimeSensors/a1_front_rgbd_camera
sensor_mount_parent: /World/A1/base equivalent runtime synced sensor path
sensor_mount_xyz: [0.3, 0.0, 0.28]
sensor_mount_rpy: [0.0, -0.261799, 0.0]
real_rgb_sensor_available: true
real_depth_sensor_available: true
camera_params_available: true
camera_intrinsics_available: true
real_camera_pointcloud_available: true
camera_pointcloud_source: depth_backprojection
rtx_lidar_attempted: true
rtx_lidar_available: true
lidar_pointcloud_available: true
lidar_scan_available: false
lidar_failure_reason: 
semantic_segmentation_available: true
instance_segmentation_available: true
geometry_proxy_used: false
mounted_geometry_proxy_used: false
step_count: 6
successful_steps: 6
rgb_valid_steps: 6
depth_valid_steps: 6
camera_pointcloud_valid_steps: 6
lidar_valid_steps: 1
camera_follows_base_rate: 1.0
average_rgb_nonzero_ratio: 0.8474
average_depth_valid_ratio: 0.8441
average_camera_pointcloud_count: 1002.5
average_lidar_point_count: 10136.17
active_remote_refs_remaining: 0
bundle_dependency_count: 58
debug_frame_paths: ['/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseB_real_sensor_smoke_20260608_180523/debug_frames/first_rgb.png', '/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseB_real_sensor_smoke_20260608_180523/debug_frames/last_rgb.png', '/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseB_real_sensor_smoke_20260608_180523/debug_frames/first_depth_vis.png', '/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseB_real_sensor_smoke_20260608_180523/debug_frames/last_depth_vis.png']
core_dump_found: false
new_kit_core_dump_found: false
safe_to_mapping: true
next_phase: New Scene Phase C real-sensor mapping smoke
training: false
RL: false
map_predict: false
PI_finetuning: false
A1_locomotion_training: false
rollout_started: false

## Caveats
- The original user USD was not modified; runtime prims are created in memory only and the stage is not saved.
- The ignored repaired bundle was preflight-localized so remaining remote prop USD references resolve from local dependencies.
- RTX LiDAR success is optional for this phase; RGB-D plus depth-derived or Isaac pointcloud is the hard gate.
- No raw RGB-D frame stream, raw pointcloud dump, npz, hdf5, checkpoint, mapping, candidate generation, rollout, or training was produced.

## Artifacts
run_dir: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseB_real_sensor_smoke_20260608_180523
steps_csv: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseB_real_sensor_smoke_20260608_180523/summary/new_scene_real_sensor_steps.csv
summary_json: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseB_real_sensor_smoke_20260608_180523/summary/new_scene_real_sensor_summary.json
