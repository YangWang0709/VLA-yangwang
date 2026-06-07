# A1 Real Sensor Suite Smoke Report

phase: Phase 5.6
workspace: /home/ubuntu22/VLA
project_name: A1-VLM-LA Explorer
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
previous_sensor_method: mounted_geometry_proxy_pointcloud_from_a1_front_sensor
new_sensor_method: real_isaac_omniverse_sensor_suite
camera_prim_path: /World/RuntimeSensors/a1_front_rgbd_camera
sensor_mount_parent: /World/A1/base (runtime camera synced under /World/RuntimeSensors)
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
imu_available: false
joint_state_available: false
geometry_proxy_used: false
mounted_geometry_proxy_used: false
step_count: 6
successful_steps: 6
rgb_valid_steps: 6
depth_valid_steps: 6
camera_pointcloud_valid_steps: 6
lidar_valid_steps: 2
camera_follows_base_rate: 1.0
average_rgb_nonzero_ratio: 0.8384
average_depth_valid_ratio: 0.8349
average_camera_pointcloud_count: 992.83
average_lidar_point_count: 55170.17
debug_frame_paths: ['/home/ubuntu22/VLA/runs/phase56_a1_real_sensor_suite_smoke_20260607_202405/debug_frames/first_rgb.png', '/home/ubuntu22/VLA/runs/phase56_a1_real_sensor_suite_smoke_20260607_202405/debug_frames/last_rgb.png', '/home/ubuntu22/VLA/runs/phase56_a1_real_sensor_suite_smoke_20260607_202405/debug_frames/first_depth_vis.png', '/home/ubuntu22/VLA/runs/phase56_a1_real_sensor_suite_smoke_20260607_202405/debug_frames/last_depth_vis.png']
safe_to_rerun_phase4_with_real_sensors: true
safe_to_rerun_phase5_with_real_sensors: true
caveats: ['RTX LiDAR success is optional for this phase; RGB-D plus depth-derived pointcloud is the hard gate.', 'Runtime light, camera, LiDAR, and marker prims are created in memory only; the primary USD is not saved.', 'Camera pointcloud is compact depth backprojection metadata, not a raw full-resolution pointcloud dump.']
training: false
RL: false
map_predict: false
PI_finetuning: false
A1_locomotion_training: false
rollout_started: false

## Evidence

- run_dir: /home/ubuntu22/VLA/runs/phase56_a1_real_sensor_suite_smoke_20260607_202405
- steps_csv: /home/ubuntu22/VLA/runs/phase56_a1_real_sensor_suite_smoke_20260607_202405/summary/a1_real_sensor_suite_steps.csv
- summary_json: /home/ubuntu22/VLA/runs/phase56_a1_real_sensor_suite_smoke_20260607_202405/summary/a1_real_sensor_suite_summary.json
- RGB and depth are captured through Replicator render product annotators.
- Camera pointcloud is derived from real depth and camera intrinsics; no geometry proxy is used.
- Runtime camera is synced to the A1 base pose each step; the original USD file is not saved.

## Caveats

- RTX LiDAR success is optional for this phase; RGB-D plus depth-derived pointcloud is the hard gate.
- Runtime light, camera, LiDAR, and marker prims are created in memory only; the primary USD is not saved.
- Camera pointcloud is compact depth backprojection metadata, not a raw full-resolution pointcloud dump.

## Negative Scope

- No Phase 6.
- No candidate generation.
- No training, RL, map_predict, checkpoint, or rollout.
- No raw RGB-D or full pointcloud dumps were saved.
- Original USD scene was opened and edited only in memory; it was not saved or overwritten.
