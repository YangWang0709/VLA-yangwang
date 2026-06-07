# WEBGPT Brief

## Current Phase

Phase 5.6 A1-mounted real Isaac/Omniverse sensor suite smoke

## Workspace

/home/ubuntu22/VLA

## Main Goal

A1-VLM-LA Explorer for 3D Active Exploration

## Output Contract

Go to candidate <id>.

## Robot Platform

robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base

## Why This Phase Was Inserted

Phase 5.5 validated a mounted sensor frame but still used a mounted geometry proxy. The formal route now requires real Isaac/Omniverse sensor output: RGB, depth, camera params, and pointcloud from either an Isaac pointcloud annotator or depth backprojection.

## Completed

- Created `scripts/phase56_a1_real_sensor_suite_smoke.py`.
- Opened the primary USD scene without saving or overwriting it.
- Used the existing `/World/A1` and `/World/A1/base`.
- Created a runtime Replicator camera at `/World/RuntimeSensors/a1_front_rgbd_camera` synced to A1 base motion.
- Captured real Replicator RGB and `distance_to_image_plane` depth.
- Read camera params and computed intrinsics from focal length and aperture where OpenCV fx/fy were zero.
- Produced camera pointcloud via `depth_backprojection`.
- Attempted RTX LiDAR and recorded its availability.
- Saved lightweight metadata and debug frames only.
- Wrote `runs/A1_REAL_SENSOR_SUITE_SMOKE_REPORT.md`.

## Phase 5.6 Metrics

status: passed
run_dir: /home/ubuntu22/VLA/runs/phase56_a1_real_sensor_suite_smoke_20260607_202405
real_rgb_sensor_available: true
real_depth_sensor_available: true
camera_params_available: true
camera_intrinsics_available: true
real_camera_pointcloud_available: true
camera_pointcloud_source: depth_backprojection
rtx_lidar_attempted: true
rtx_lidar_available: true
lidar_pointcloud_available: true
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
core_dump_found: false
safe_to_rerun_phase4_with_real_sensors: true
safe_to_rerun_phase5_with_real_sensors: true

## Key Caveats

- This is a smoke test, not a rollout and not candidate generation.
- Real RGB-D data is available; geometry proxy was not used.
- The next step must be rerunning Phase 4 with real Isaac/Omniverse sensors, not Phase 6.

## Negative Scope

- training: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- A1_locomotion_training: false
- candidate_generation: false
- primary_rollout: false
- Phase_6_executed: false

## Next Step

Rerun Phase 4 A1 mapping smoke with real Isaac/Omniverse sensors.
