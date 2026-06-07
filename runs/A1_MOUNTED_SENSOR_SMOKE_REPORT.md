# A1 Mounted Sensor Smoke Report

phase: Phase 5.5
workspace: /home/ubuntu22/VLA
project_name: A1-VLM-LA Explorer
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
previous_sensor_method: geometry_proxy_pointcloud_from_a1_base_pose
new_sensor_mount_parent: /World/A1/base
new_sensor_frame: a1_front_sensor
sensor_mount_xyz: [0.3, 0.0, 0.28]
sensor_mount_rpy: [0.0, -0.261799, 0.0]
real_rgb_sensor_available: false
real_depth_sensor_available: false
real_pointcloud_available: false
mounted_geometry_proxy_used: true
step_count: 6
successful_steps: 6
rgb_valid_steps: 0
depth_valid_steps: 6
pointcloud_valid_steps: 6
sensor_follows_base_rate: 1.0
average_depth_valid_ratio: 1.0
average_pointcloud_count: 432.0
debug_frame_paths: ['/home/ubuntu22/VLA/runs/phase55_a1_mounted_sensor_smoke_20260607_200210/debug_frames/mounted_depth_proxy_step_000.png', '/home/ubuntu22/VLA/runs/phase55_a1_mounted_sensor_smoke_20260607_200210/debug_frames/mounted_depth_proxy_step_001.png', '/home/ubuntu22/VLA/runs/phase55_a1_mounted_sensor_smoke_20260607_200210/debug_frames/mounted_depth_proxy_step_002.png']
safe_to_rerun_phase4_with_mounted_sensor: true
safe_to_rerun_phase5_with_mounted_sensor: true
training: false
RL: false
map_predict: false
PI_finetuning: false
A1_locomotion_training: false
rollout_started: false

## Caveats

- Real Isaac RGB-D capture API was not used in this smoke; runtime camera prims are created only as mounted frame markers.
- Depth and pointcloud are A1-mounted geometry proxy observations from /World/A1/base/Sensors/a1_front_sensor.
- This validates mounted sensor frame behavior and lightweight stats, not final real-sensor RGB-D data.

## Negative Scope

- No Phase 6.
- No candidate generation.
- No training, RL, map_predict, checkpoint, or rollout.
- No raw RGB-D or full pointcloud dumps were saved.
- Original USD scene was opened and edited only in memory; it was not saved or overwritten.
