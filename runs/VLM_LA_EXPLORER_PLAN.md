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
- Phase 3 through Phase 5 old formal route used proxy observations and should not be treated as final real-sensor data.
- Phase 5.6 validated real Isaac/Omniverse RGB-D sensing and depth-backprojected pointclouds.
- Phase 4R-real passed by building BEV map updates from real depth-backprojected pointclouds.

## Real Sensor Mapping Route

```yaml
status: passed
run_dir: /home/ubuntu22/VLA/runs/phase4r_a1_real_sensor_mapping_smoke_20260607_203607
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
camera_prim_path: /World/RuntimeSensors/a1_front_rgbd_camera
real_rgb_sensor_available: true
real_depth_sensor_available: true
camera_params_available: true
camera_intrinsics_available: true
real_camera_pointcloud_available: true
camera_pointcloud_source: depth_backprojection
semantic_segmentation_available: true
instance_segmentation_available: true
rtx_lidar_available: true
lidar_used_for_mapping: false
lidar_is_required_for_pass: false
geometry_proxy_used: false
mounted_geometry_proxy_used: false
camera_follows_base_rate: 1.0
mapping_method: raycast_real_sensor_bev_mapping
map_update_source: depth_backprojection_pointcloud
step_count: 10
successful_steps: 10
valid_rgb_steps: 10
valid_depth_steps: 10
valid_camera_pointcloud_steps: 10
valid_lidar_steps: 1
initial_known_ratio: 0.055802
final_known_ratio: 0.069383
final_occupied_cells: 136
final_known_free_cells: 426
final_unknown_cells: 7538
total_new_known_cells: 562
known_ratio_monotonic_non_decreasing: true
map_update_behavior: pass
core_dump_found: false
safe_to_rerun_phase5_with_real_sensors: true
safe_to_continue_phase6: false
```

## Core Pipeline

```text
USD scene with /World/A1
-> A1-synced real Isaac/Omniverse RGB-D sensor route
-> real depth-derived pointcloud and optional segmentation / RTX LiDAR telemetry
-> explored_map / partial map
-> candidate viewpoints
-> BEV render with candidate IDs
-> VLM output: Go to candidate <id>.
-> LA parser: selected_candidate_id = <id>
-> candidate table lookup: candidate id -> target viewpoint pose
-> planner / A1 movement wrapper
```

## Output Contract

```text
Go to candidate <id>.
```

Only the candidate ID may drive control. Explanation text may be logged but must not control motion.

## Current Gate

Phase 4R-real passed. The next formal route is `Rerun Phase 5 A1 candidate viewpoint + information gain smoke with real sensors`. Do not enter Phase 6 yet.

## Negative Scope

Do not train VLM, RL, map_predict, PI/openpi action heads, or A1 locomotion policies in the current stage. Do not let the VLM output free coordinates, base velocities, or joint actions. Do not commit scene bundles, meshes, textures, raw sensor dumps, checkpoints, core dumps, tokens, keys, or private configs.
