# Critic Report

## Current Phase

Phase 5.5 A1 mounted sensor smoke

## Corrected Fact

The USD scene's real robot is `/World/A1`, not Go2.

## Phase 5.5 Mounted Sensor Review

status: passed
run_dir: /home/ubuntu22/VLA/runs/phase55_a1_mounted_sensor_smoke_20260607_200210
script: /home/ubuntu22/VLA/scripts/phase55_a1_mounted_sensor_smoke.py
report: /home/ubuntu22/VLA/runs/A1_MOUNTED_SENSOR_SMOKE_REPORT.md

## Evidence

- primary scene opened successfully.
- `/World/A1` exists.
- base_frame: `/World/A1/base`.
- runtime sensor_mount_parent: `/World/A1/base`.
- runtime sensor_frame_path: `/World/A1/base/Sensors/a1_front_sensor`.
- sensor_mount_xyz: `[0.3, 0.0, 0.28]`.
- sensor_mount_rpy: `[0.0, -0.261799, 0.0]`.
- mounted_geometry_proxy_used: true.
- step_count: 6.
- successful_steps: 6.
- depth_valid_steps: 6.
- pointcloud_valid_steps: 6.
- sensor_follows_base_rate: 1.0.
- average_depth_valid_ratio: 1.0.
- average_pointcloud_count: 432.0.
- collision_count: 0.
- stuck_count: 0.
- falling_count: 0.
- core_dump_found: false.
- safe_to_rerun_phase4_with_mounted_sensor: true.
- safe_to_rerun_phase5_with_mounted_sensor: true.

## Residual Risks And Caveats

- Real RGB-D sensor capture was not available or not used; RGB valid steps are 0.
- Runtime camera prims are mounted frame markers, not proof of real rendered RGB-D output.
- Depth and pointcloud are mounted geometry proxy data, not final real-sensor data.
- Phase 4 and Phase 5 should be rerun with the mounted sensor route before Phase 6.

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

Phase 5.5 passes as an A1-mounted geometry proxy sensor smoke. The next phase is to rerun Phase 4 A1 mapping smoke with mounted sensor, not Phase 6.
