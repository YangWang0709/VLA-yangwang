# WEBGPT Brief

## Current Phase

New Scene Phase E VLM-LA interface smoke

## Context


current_scene_id: building_scene_1_scene_20260608_171052
current_scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
original_user_usd_path: /home/ubuntu22/VLA/building_scene(1).usd
current_scene_phase: New Scene Phase E VLM-LA interface smoke
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
map_update_source: depth_backprojection_pointcloud
candidate_data_source: new_scene_phaseD_real_sensor
output_contract: Go to candidate <id>.
training_ready: false
requires_human_review: true
next_phase: New Scene Phase F short closed-loop smoke


negative_scope:
- training: false
- RL: false
- SFT: false
- GDPO: false
- map_predict: false
- rollout: false
- real_VLM_inference: false
- closed_loop: false
- A1_movement: false
- mapping: false
- candidate_generation: false
- PI_action_finetuning: false
- A1_locomotion_training: false


## Completed

- Read New Scene Phase D real-sensor candidate artifacts.
- Generated pseudo VLM commands using the contract `Go to candidate <id>.`.
- Parsed supported text and JSON command forms.
- Rejected coordinate, velocity, joint-action, malformed, missing-ID, out-of-range, textual-number, invalid, and unreachable outputs.
- Validated candidate existence, validity, reachability, collision risk, and target pose lookup.
- Fell back to the Phase D classical selected candidate for invalid outputs.
- Did not run real VLM inference, move A1, map, generate candidates, rollout, or train.

## Metrics


phaseD_candidate_data_used: true
legal_command_count: 24
legal_parse_success_rate: 1.0
legal_validation_success_rate: 1.0
target_pose_lookup_success_rate: 1.0
illegal_test_count: 59
illegal_reject_or_fallback_rate: 1.0
fallback_behavior: pass
invalid_candidate_fallback_passed: true
unreachable_candidate_fallback_passed: true
free_coordinate_output_allowed: false
velocity_output_allowed: false
joint_action_output_allowed: false
malformed_output_rejected: true
final_interface_output_contract_ok: true
safe_to_closed_loop: true


## Next Action

New Scene Phase F short closed-loop smoke
