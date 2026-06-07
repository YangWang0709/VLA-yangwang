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

## Phase 5R-real Candidate Gain Route

```yaml
status: passed
run_dir: /home/ubuntu22/VLA/runs/phase5r_a1_real_sensor_candidate_gain_smoke_20260607_204631
script: /home/ubuntu22/VLA/scripts/phase5r_a1_real_sensor_candidate_gain_smoke.py
report: /home/ubuntu22/VLA/runs/A1_REAL_SENSOR_CANDIDATE_GAIN_REPORT.md
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
real_rgb_sensor_available: true
real_depth_sensor_available: true
camera_params_available: true
camera_intrinsics_available: true
real_camera_pointcloud_available: true
camera_pointcloud_source: depth_backprojection
semantic_segmentation_available: true
instance_segmentation_available: true
rtx_lidar_available: true
lidar_used_for_candidate_gain: false
lidar_is_required_for_pass: false
geometry_proxy_used: false
mounted_geometry_proxy_used: false
map_type: BEV occupancy grid
mapping_method: raycast_real_sensor_bev_mapping
map_update_source: depth_backprojection_pointcloud
candidate_sampling_method: radial_24_candidates_3_radii_8_angles_around_a1_base
path_cost_method: astar_bev_grid_unknown_penalty
information_gain_method: real_sensor_bev_unknown_visibility
score_formula: score = information_gain - 0.2 * path_cost - 1.0 * collision_penalty - 200.0 * invalid_penalty
step_count: 6
successful_steps: 6
candidate_count_per_step: 24
total_candidate_rows: 144
valid_candidate_ratio: 0.8958
positive_gain_candidate_ratio: 0.8819
selected_candidate_valid_rate: 1.0
selected_is_top_score_rate: 1.0
path_cost_constant: false
min_path_cost: 1.0243
max_path_cost: 6.4742
min_information_gain: 0
max_information_gain: 749
failure_count: 0
safe_to_continue_phase6: true
```

## Core Pipeline

```text
USD scene with /World/A1
-> A1-synced real Isaac/Omniverse RGB-D sensor route
-> depth_backprojected_pointcloud
-> BEV explored_map / partial map
-> candidate viewpoints
-> information gain + path cost + classical score
-> constrained VLM-LA contract: Go to candidate <id>.
```

## Next Phase Gate

next_phase: Phase 6 VLM-LA interface smoke

Phase 6 should only test the constrained interface. It must not train, fine-tune, run RL, run map_predict training, run A1 locomotion training, or let the VLM output free-form coordinates.
