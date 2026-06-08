# WEBGPT Brief

## Current Phase

New Scene Phase F short closed-loop smoke

## Context

current_scene_id: building_scene_1_scene_20260608_171052
current_scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
original_user_usd_path: /home/ubuntu22/VLA/building_scene(1).usd
current_scene_phase: New Scene Phase F short closed-loop smoke
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
next_phase: New Scene Phase G long rollout data collection

negative_scope:
- training: false
- RL: false
- SFT: false
- GDPO: false
- map_predict: false
- long_rollout: false
- real_VLM_inference: false
- PI_action_finetuning: false
- A1_locomotion_training: false


## Completed

- Opened the repaired new scene and used existing `/World/A1`.
- Captured real Isaac/Omniverse RGB-D observations and depth_backprojection pointclouds.
- Updated a BEV map online before and after movement.
- Generated online candidate viewpoints and scored them with classical information gain.
- Emitted pseudo VLM commands using `Go to candidate <id>.`.
- Parsed, validated, looked up target pose, and moved A1 with a kinematic wrapper.
- Did not run long rollout, real VLM inference, training, SFT, GDPO, or USD save.

## Metrics

action_count: 5
successful_action_count: 5
parse_success_rate: 1.0
validation_success_rate: 1.0
target_pose_lookup_success_rate: 1.0
movement_success_rate: 1.0
fallback_count: 0
initial_known_ratio: 0.0
final_known_ratio: 0.236667
total_known_ratio_gain: 0.236667
known_ratio_monotonic_non_decreasing: true
average_candidate_count: 24.0
average_valid_candidate_count: 21.4
collision_count: 0
stuck_count: 0
falling_count: 0
failure_count: 0
safe_to_long_rollout: true


## Next Action

New Scene Phase G long rollout data collection
