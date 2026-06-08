# VLM-LA Explorer Plan

## Method Name

A1-VLM-LA Explorer

Full route name:

A1-VLM-LA Explorer for 3D Active Exploration

## Output Contract

`Go to candidate <id>.`

## Current New Scene

```yaml
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
interface_phaseE_status: passed
phaseD_candidate_data_used: true
safe_to_closed_loop: true
```

## New Scene Route

1. Phase A: scene open and robot inspection. Status: passed.
2. Phase B: real Isaac/Omniverse sensor suite smoke. Status: passed.
3. Phase C: real-sensor mapping smoke. Status: passed.
4. Phase D: candidate viewpoint + information gain smoke. Status: passed.
5. Phase E: VLM-LA interface smoke. Status: passed.
6. Phase F: short closed-loop smoke. Status: next if Phase E passed.
7. Phase G: long rollout data collection.
8. Phase H: dataset quality audit and human review packet.

## Phase E Gate


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


## Negative Scope

training: false
RL: false
SFT: false
GDPO: false
map_predict: false
PI_finetuning: false
A1_locomotion_training: false
rollout: false
real_VLM_inference: false
