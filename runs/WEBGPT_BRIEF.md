# WEBGPT Brief

## Current Phase

New Scene Phase C real-sensor mapping smoke

## Context

current_scene_id: building_scene_1_scene_20260608_171052
current_scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
original_user_usd_path: /home/ubuntu22/VLA/building_scene(1).usd
current_scene_phase: New Scene Phase C real-sensor mapping smoke
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
map_update_source: depth_backprojection_pointcloud
output_contract: Go to candidate <id>.
training_ready: false
requires_human_review: true
next_phase: New Scene Phase D candidate viewpoint + information gain smoke

negative_scope:
- training: false
- RL: false
- SFT: false
- GDPO: false
- map_predict: false
- rollout: false
- candidate_generation: false
- VLM_LA_interface: false
- PI_action_finetuning: false
- A1_locomotion_training: false

## Completed

- Used the repaired new scene and existing `/World/A1`.
- Reused the real Isaac/Omniverse RGB-D route validated in Phase B.
- Converted real depth plus camera intrinsics into depth_backprojection pointclouds.
- Updated a BEV occupancy grid from depth-backprojected pointcloud observations.
- Generated lightweight map summaries and plots without saving raw RGB-D streams.
- Did not use geometry proxy and did not start candidate generation, VLM-LA interface, rollout, or training.

## Metrics

step_count: 10
successful_steps: 10
real_rgb_sensor_available: true
real_depth_sensor_available: true
real_camera_pointcloud_available: true
camera_pointcloud_source: depth_backprojection
geometry_proxy_used: false
mounted_geometry_proxy_used: false
mapping_method: raycast_real_sensor_bev_mapping
map_update_source: depth_backprojection_pointcloud
initial_known_ratio: 0.059506
final_known_ratio: 0.076173
final_occupied_cells: 149
final_known_free_cells: 468
final_unknown_cells: 7483
total_new_known_cells: 617
map_update_behavior: pass
safe_to_candidate_gain: true

## Next Action

New Scene Phase D candidate viewpoint + information gain smoke
