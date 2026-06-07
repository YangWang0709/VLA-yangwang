# WEBGPT Brief

## Current Phase

Phase 3 Unitree Go2 sensor smoke

## Workspace

/home/ubuntu22/VLA

## Main Goal

Go2-VLM-LA Explorer for 3D Active Exploration

## Output Contract

Go to candidate <id>.

## Robot Platform Target

Unitree Go2

## Robot Source

temporary_go2_proxy

## Completed

- Loaded the primary scene in Isaac headless.
- Created `/World/TemporaryGo2Proxy` as an in-memory temporary Go2-shaped sensor carrier.
- Confirmed the proxy is not a final robot asset and is not the existing USD Go2.
- Ran 8 short kinematic proxy action steps.
- Recorded pose, depth proxy, pointcloud proxy, and failure flags for each step.
- Confirmed no training, no RL, no rollout, no mapping, no candidate generation, and no USD save.

## Key Metrics

- scene_path: `/home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd`
- go2_in_usd_found: false
- robot_source: temporary_go2_proxy
- temporary_go2_proxy_used: true
- not_final_robot_asset: true
- movement_mode: kinematic_proxy
- step_count: 8
- successful_steps: 8
- sensor_valid_rate: 1.0
- min_pointcloud_count: 161
- average_pointcloud_count: 161
- collision_count: 0
- stuck_count: 0
- falling_count: 0
- core_dump_found: false
- safe_to_continue_phase4: true

## Artifacts

- runs/GO2_SENSOR_SMOKE_REPORT.md
- scripts/phase3_go2_sensor_smoke.py
- /home/ubuntu22/VLA/runs/phase3_go2_sensor_smoke_20260607_190528
- /home/ubuntu22/VLA/runs/phase3_go2_sensor_smoke_20260607_190528/sensor_smoke/go2_sensor_smoke_steps.csv
- /home/ubuntu22/VLA/runs/phase3_go2_sensor_smoke_20260607_190528/sensor_smoke/go2_sensor_smoke_summary.json

## Negative Scope

- training: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- Go2_locomotion_training: false
- primary_rollout: false
- free_coordinate_output: false
- candidate_generation: false
- VLM_inference_or_finetuning: false

## Caveat

Phase 3 used a temporary Go2-shaped proxy because Phase 2 did not verify an existing Go2 prim. `/World/A1` is not reported as Go2.

## Next Phase

Phase 4 Go2 primary-scene mapping smoke.
