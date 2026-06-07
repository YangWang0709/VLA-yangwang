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
- Phase 7 passed a short closed-loop smoke.
- Phase 8 passed A1 primary-scene VLM-LA long rollout data collection.

## Phase 8 Rollout Route

```yaml
status: passed
run_dir: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536
script: /home/ubuntu22/VLA/scripts/phase8_a1_vlm_la_long_rollout.py
report: /home/ubuntu22/VLA/runs/A1_VLM_LA_LONG_ROLLOUT_REPORT.md
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
real_rgb_sensor_available: true
real_depth_sensor_available: true
real_camera_pointcloud_available: true
real_rgb_sensor_valid_rate: 0.987
real_depth_sensor_valid_rate: 1.0
real_camera_pointcloud_valid_rate: 1.0
geometry_proxy_used: false
mounted_geometry_proxy_used: false
movement_mode: kinematic_existing_a1_root
real_a1_locomotion_controller: false
real_vlm_inference: false
vlm_output_mode: pseudo_from_classical_selector
output_contract: Go to candidate <id>.
start_count: 10
completed_start_count: 10
max_actions_per_start: 8
total_action_count: 77
candidate_rows: 1848
vlm_la_sample_count: 77
average_final_known_ratio: 0.305375
average_known_ratio_gain: 0.305375
parse_success_rate: 1.0
validation_success_rate: 1.0
movement_success_rate: 1.0
starts_with_failures: 1
rgb_invalid_step_count: 1
collision_count: 0
stuck_count: 0
falling_count: 0
safe_to_continue_phase9: true
```

## Core Pipeline

1. Open primary USD read-only.
2. Use existing `/World/A1` and `/World/A1/base`.
3. Capture real Isaac/Omniverse RGB-D.
4. Backproject depth to pointcloud using camera intrinsics.
5. Update BEV explored map.
6. Generate and score candidate viewpoints.
7. Emit pseudo VLM label: `Go to candidate <id>.`
8. Parse and validate candidate ID.
9. Lookup target pose and move A1 with the kinematic wrapper.
10. Write review-only VLM-LA samples.

## Next Phase

Phase 9 human review packet.

Training remains out of scope until the review packet is complete and explicitly approved.
