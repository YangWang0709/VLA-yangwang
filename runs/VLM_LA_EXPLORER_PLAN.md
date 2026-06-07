# VLM-LA Explorer Plan

## Method Name

A1-VLM-LA Explorer

Full route name:

A1-VLM-LA Explorer for 3D Active Exploration

## Workspace

`/home/ubuntu22/VLA`

## Robot Platform

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
```

The USD scene's real robot is `/World/A1`. Do not claim the USD contains a verified Go2 robot unless a real Go2 asset is provided or substituted later.

## Current Progress

- Phase 1 placed the primary USD scene bundle and kept it ignored by Git.
- Phase 2 opened the scene and identified the articulated `/World/A1` hierarchy.
- Old proxy Phase 3 through Phase 5 outputs remain proxy-only and are not final A1 real-sensor data.
- Phase 5.6 validated real Isaac/Omniverse RGB-D sensing and depth-backprojected pointclouds.
- Phase 4R-real passed BEV mapping from real depth-backprojected pointclouds.
- Phase 5R-real passed candidate viewpoint generation and information gain scoring on the real-sensor BEV route.
- Phase 6 passed the constrained VLM-LA command parser, validator, target pose lookup, and fallback smoke.

## Phase 6 Interface Route

```yaml
status: passed
run_dir: /home/ubuntu22/VLA/runs/phase6_vlm_la_interface_smoke_20260607_205612
script: /home/ubuntu22/VLA/scripts/phase6_vlm_la_interface_smoke.py
report: /home/ubuntu22/VLA/runs/VLM_LA_INTERFACE_SMOKE_REPORT.md
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
candidate_data_source: phase5r_real_sensor
output_contract: Go to candidate <id>.
phase5r_candidate_data_used: true
phase5r_run_dir: /home/ubuntu22/VLA/runs/phase5r_a1_real_sensor_candidate_gain_smoke_20260607_204631
legal_command_count: 24
legal_parse_success_rate: 1.0
legal_validation_success_rate: 1.0
target_pose_lookup_success_rate: 1.0
illegal_test_count: 47
illegal_reject_or_fallback_rate: 1.0
fallback_test_passed: true
invalid_candidate_fallback_tested: true
unreachable_candidate_fallback_tested: true
free_coordinate_output_allowed: false
velocity_output_allowed: false
joint_action_output_allowed: false
malformed_output_rejected: true
A1_moved: false
mapping_started: false
candidate_generation_started: false
real_vlm_inference_started: false
safe_to_continue_phase7: true
```

## Core Pipeline

```text
USD scene with /World/A1
-> A1-synced real Isaac/Omniverse RGB-D sensor route
-> depth_backprojected_pointcloud
-> BEV explored_map / partial map
-> candidate viewpoints
-> information gain + path cost + classical score
-> constrained command: Go to candidate <id>.
-> parser + validator + target pose lookup + fallback
```

## Next Phase Gate

next_phase: Phase 7 A1 VLM-LA closed-loop smoke

Phase 7 may only run a closed-loop smoke when explicitly requested. It must not train, fine-tune, run RL, run map_predict training, run A1 locomotion training, or let the VLM output free-form coordinates.
