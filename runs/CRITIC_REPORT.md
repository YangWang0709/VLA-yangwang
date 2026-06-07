# Critic Report

## Current Phase

Phase 5.6 A1-mounted real Isaac/Omniverse sensor suite smoke

## Corrected Fact

The USD scene's real robot is `/World/A1`, not Go2.

## Phase 5.6 Real Sensor Suite Review

status: passed
run_dir: /home/ubuntu22/VLA/runs/phase56_a1_real_sensor_suite_smoke_20260607_202405
script: /home/ubuntu22/VLA/scripts/phase56_a1_real_sensor_suite_smoke.py
report: /home/ubuntu22/VLA/runs/A1_REAL_SENSOR_SUITE_SMOKE_REPORT.md

## Evidence

- primary scene opened successfully: true.
- `/World/A1` exists: true.
- base_frame: `/World/A1/base`.
- camera_prim_path: `/World/RuntimeSensors/a1_front_rgbd_camera`.
- sensor_mount_parent: `/World/A1/base (runtime camera synced under /World/RuntimeSensors)`.
- real_rgb_sensor_available: true.
- real_depth_sensor_available: true.
- camera_params_available: true.
- camera_intrinsics_available: true.
- real_camera_pointcloud_available: true.
- camera_pointcloud_source: `depth_backprojection`.
- rtx_lidar_attempted: true.
- rtx_lidar_available: true.
- lidar_pointcloud_available: true.
- semantic_segmentation_available: true.
- instance_segmentation_available: true.
- geometry_proxy_used: false.
- mounted_geometry_proxy_used: false.
- step_count: 6.
- successful_steps: 6.
- rgb_valid_steps: 6.
- depth_valid_steps: 6.
- camera_pointcloud_valid_steps: 6.
- camera_follows_base_rate: 1.0.
- core_dump_found: false.
- safe_to_rerun_phase4_with_real_sensors: true.
- safe_to_rerun_phase5_with_real_sensors: true.

## Residual Risks And Caveats

- This validates sensor availability and data plumbing only; it does not validate full exploration behavior.
- RTX LiDAR is recorded as available, but RGB-D plus depth-backprojection remains the dependable hard-gated route.
- Mapping and candidate gain still need to be rerun using real sensor outputs before Phase 6.

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

Phase 5.6 passed. The next phase is `Rerun Phase 4 A1 mapping smoke with real Isaac/Omniverse sensors`, not Phase 6.
