# WEBGPT Brief

## Current Phase

New Scene Phase G long rollout data collection

## Context

current_scene_id: building_scene_1_scene_20260608_171052
current_scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
original_user_usd_path: /home/ubuntu22/VLA/building_scene(1).usd
current_scene_phase: New Scene Phase G long rollout data collection
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
map_update_source: depth_backprojection_pointcloud
candidate_data_source: online_new_scene_real_sensor_candidate_generation
vlm_output_mode: pseudo_from_classical_selector
output_contract: Go to candidate <id>.
training_ready: false
requires_human_review: true
safe_to_human_review: true
next_phase: New Scene Phase H dataset quality audit / human review packet

negative_scope:
- training: false
- RL: false
- SFT: false
- GDPO: false
- map_predict: false
- real_VLM_inference: false
- PI_action_finetuning: false
- A1_locomotion_training: false
- checkpoint_created: false


## Completed

- Collected new-scene real Isaac/Omniverse RGB-D rollout samples.
- Used `/World/A1` and `/World/A1/base` as the existing USD robot prims.
- Updated BEV maps from depth-backprojected pointclouds.
- Generated online candidate viewpoints and pseudo VLM labels.
- Enforced the output contract `Go to candidate <id>.`.
- Kept `training_ready: false` and `requires_human_review: true`.

## Metrics

start_count: 10
completed_start_count: 10
max_actions_per_start: 20
total_action_count: 200
candidate_rows: 4800
vlm_la_sample_count: 200
average_final_known_ratio: 0.408687
average_known_ratio_gain: 0.408687
parse_success_rate: 1.0
validation_success_rate: 1.0
movement_success_rate: 1.0
starts_with_failures: 0
collision_count: 0
stuck_count: 0
falling_count: 0
real_rgb_sensor_valid_rate: 1.0
real_depth_sensor_valid_rate: 1.0
real_camera_pointcloud_valid_rate: 1.0


## Next Action

New Scene Phase H dataset quality audit / human review packet
