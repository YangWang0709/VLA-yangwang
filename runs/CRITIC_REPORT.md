# Critic Report

## Current Phase

New Scene Phase C real-sensor mapping smoke

## Finding

status: passed

The new-scene BEV map was updated from real Isaac/Omniverse RGB-D observations using depth_backprojection pointclouds. Geometry proxy and old proxy map outputs were not used.

## Evidence

- scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
- a1_root_prim: /World/A1
- base_frame: /World/A1/base
- sensor_method: real_isaac_omniverse_rgbd
- map_update_source: depth_backprojection_pointcloud
- camera_pointcloud_source: depth_backprojection
- valid_rgb_steps: 10
- valid_depth_steps: 10
- valid_camera_pointcloud_steps: 10
- final_known_ratio: 0.076173
- final_occupied_cells: 149
- final_known_free_cells: 468
- final_unknown_cells: 7483
- map_update_behavior: pass
- safe_to_candidate_gain: true

## Risks / Gates

- Phase C is a mapping smoke, not final dataset generation.
- RTX LiDAR is optional telemetry and is not used for mapping pass/fail.
- Do not start Phase D unless `safe_to_candidate_gain` is true.

training: false
RL: false
SFT: false
GDPO: false
rollout: false
USD_modified_or_saved: false
