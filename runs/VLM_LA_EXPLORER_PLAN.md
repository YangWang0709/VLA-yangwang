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
- Phase 7 passed a short closed-loop smoke with online real-sensor mapping, candidate generation, pseudo VLM command parsing, target lookup, kinematic A1 movement, and post-move map updates.

## Phase 7 Closed-Loop Route

```yaml
status: passed
run_dir: /home/ubuntu22/VLA/runs/phase7_a1_vlm_la_closed_loop_smoke_20260607_210429
script: /home/ubuntu22/VLA/scripts/phase7_a1_vlm_la_closed_loop_smoke.py
report: /home/ubuntu22/VLA/runs/A1_VLM_LA_CLOSED_LOOP_SMOKE_REPORT.md
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
geometry_proxy_used: false
mounted_geometry_proxy_used: false
movement_mode: kinematic_existing_a1_root
real_a1_locomotion_controller: false
real_vlm_inference: false
vlm_output_mode: pseudo_from_classical_selector
candidate_data_source: online_real_sensor_candidate_generation
output_contract: Go to candidate <id>.
action_count: 5
successful_action_count: 5
parse_success_rate: 1.0
validation_success_rate: 1.0
target_pose_lookup_success_rate: 1.0
movement_success_rate: 1.0
fallback_count: 0
initial_known_ratio: 0.0
final_known_ratio: 0.322222
total_known_ratio_gain: 0.322222
known_ratio_monotonic_non_decreasing: true
average_candidate_count: 24.0
average_valid_candidate_count: 21.4
collision_count: 0
stuck_count: 0
falling_count: 0
failure_count: 0
safe_to_continue_phase8: true
```

## Core Pipeline

```text
USD scene with /World/A1
-> A1-synced real Isaac/Omniverse RGB-D sensor route
-> depth_backprojected_pointcloud
-> BEV explored_map / partial map
-> online candidate viewpoints
-> information gain + path cost + classical score
-> pseudo VLM command: Go to candidate <id>.
-> parser + validator + target pose lookup
-> kinematic_existing_a1_root movement
-> post-move real-sensor map update
```

## Next Phase Gate

next_phase: Phase 8 A1 primary-scene VLM-LA long rollout data collection

Phase 8 must only start when explicitly requested. It must not train, fine-tune, run RL, run map_predict training, train A1 locomotion, or let the VLM output free-form coordinates.
