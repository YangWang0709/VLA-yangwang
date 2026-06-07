# Critic Report

## Current Phase

Phase 3 Unitree A1 sensor smoke

## Corrected Fact

The USD scene's real robot is `/World/A1`, not Go2.

## Phase 3 A1 Smoke Review

status: passed
run_dir: /home/ubuntu22/VLA/runs/phase3_a1_sensor_smoke_20260607_193054
script: /home/ubuntu22/VLA/scripts/phase3_a1_sensor_smoke.py
report: /home/ubuntu22/VLA/runs/A1_SENSOR_SMOKE_REPORT.md

## Evidence

- primary scene opened successfully.
- `/World/A1` exists.
- `/World/A1` has articulation root API.
- base_frame: `/World/A1/base`.
- initial_root_pose_xyz: `[0.0, -2.2, 0.6]`.
- initial_base_pose_xyz: `[-0.0, -2.199414, 0.59675]`.
- movement_mode: `kinematic_existing_a1_root`.
- step_count: 8.
- successful_steps: 8.
- sensor_valid_rate: 1.0.
- min_pointcloud_count: 161.
- collision_count: 0.
- stuck_count: 0.
- falling_count: 0.
- core_dump_found: false.
- safe_to_continue_phase4: true.

## Residual Risks And Caveats

- Existing USD cameras are only Omniverse default cameras, not A1-mounted sensors.
- The sensor smoke uses geometry/depth/pointcloud proxy observations.
- The A1 movement is an in-memory kinematic root update, not a trained or existing A1 locomotion controller.
- This phase does not validate mapping, candidates, VLM parsing, or Phase 6 behavior.

## Platform Correction

Formal data must use:

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
```

Legacy proxy data must stay labeled as:

```yaml
robot_platform: temporary_quadruped_proxy
robot_source: temporary_go2_proxy
not_final_robot_asset: true
```

## Prohibited Work Check

- VLM training performed: false
- RL training performed: false
- map_predict training performed: false
- PI/openpi fine-tuning performed: false
- A1 locomotion training performed: false
- Phase 4 mapping performed in this step: false
- candidate generation performed: false
- Phase 6 performed: false
- rollout performed: false
- historical CSV/JSONL rows modified: false
- original USD saved or overwritten: false
- temporary Go2 proxy created: false
- large files committed: false

## Decision

Phase 3 A1 sensor smoke is sufficient to proceed to Phase 4 A1 primary-scene mapping smoke when requested. Do not enter Phase 6 yet.
