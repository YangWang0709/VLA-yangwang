# WEBGPT Brief

## Current Phase

Phase 5.5 A1 mounted sensor smoke

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

Phase 3 through Phase 5 passed with `geometry_proxy_pointcloud_from_a1_base_pose`, but final VLM-LA data should use an A1-mounted sensor route. Phase 5.5 validates the mounted sensor frame before rerunning mapping and candidate gain.

## Completed

- Created `scripts/phase55_a1_mounted_sensor_smoke.py`.
- Opened the primary USD scene without saving or overwriting it.
- Created runtime sensor frame `/World/A1/base/Sensors/a1_front_sensor` in memory.
- Created runtime RGB/depth camera marker prims under that sensor frame.
- Validated A1-mounted depth/pointcloud proxy observations over 6 short steps.
- Saved only lightweight metadata and 3 small debug depth PNGs in the ignored run directory.
- Wrote `runs/A1_MOUNTED_SENSOR_SMOKE_REPORT.md`.

## Phase 5.5 Metrics

run_dir: /home/ubuntu22/VLA/runs/phase55_a1_mounted_sensor_smoke_20260607_200210
real_rgb_sensor_available: false
real_depth_sensor_available: false
real_pointcloud_available: false
mounted_geometry_proxy_used: true
step_count: 6
successful_steps: 6
depth_valid_steps: 6
pointcloud_valid_steps: 6
sensor_follows_base_rate: 1.0
average_depth_valid_ratio: 1.0
average_pointcloud_count: 432.0
core_dump_found: false
safe_to_rerun_phase4_with_mounted_sensor: true
safe_to_rerun_phase5_with_mounted_sensor: true

## Key Caveats

- This is mounted geometry proxy sensor smoke, not final real RGB-D data.
- Real Isaac RGB-D capture was not used in this pass.
- The next step must be rerunning Phase 4 with the mounted sensor, not Phase 6.

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

Rerun Phase 4 A1 mapping smoke with mounted sensor.
