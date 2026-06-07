# WEBGPT Brief

## Current Phase

Phase 3 Unitree A1 sensor smoke

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

## Completed

- Created `scripts/phase3_a1_sensor_smoke.py`.
- Opened the primary USD scene without saving or overwriting it.
- Verified `/World/A1` exists and has articulation root API.
- Selected `/World/A1/base` as the base frame.
- Ran 8 short in-memory kinematic A1 root steps.
- Generated lightweight geometry/depth/pointcloud proxy observations.
- Wrote `runs/A1_SENSOR_SMOKE_REPORT.md`.

## Phase 3 Metrics

run_dir: /home/ubuntu22/VLA/runs/phase3_a1_sensor_smoke_20260607_193054
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
step_count: 8
successful_steps: 8
sensor_valid_steps: 8
sensor_valid_rate: 1.0
pointcloud_point_count_per_valid_step: 161
collision_count: 0
stuck_count: 0
falling_count: 0
core_dump_found: false
safe_to_continue_phase4: true

## Key Caveats

- No A1-bound USD camera/sensor prim was found; only Omniverse default cameras exist.
- Sensor data is a geometry proxy, not RTX rendering or raw sensor data.
- Movement is `kinematic_existing_a1_root`, not real A1 locomotion control.
- Previous Go2 proxy results remain proxy-only smoke and are superseded for formal A1 pipeline data.

## Negative Scope

- training: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- A1_locomotion_training: false
- candidate_generation: false
- primary_rollout: false
- Phase_6: false

## Next Step

Phase 4 A1 primary-scene mapping smoke. Do not run candidate generation, rollout, or Phase 6 in this phase.
