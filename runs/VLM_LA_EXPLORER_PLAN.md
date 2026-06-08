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
phaseG_status: passed
```

## New Scene Route

1. Phase A: scene open and robot inspection. Status: passed.
2. Phase B: real Isaac/Omniverse sensor suite smoke. Status: passed.
3. Phase C: real-sensor mapping smoke. Status: passed.
4. Phase D: candidate viewpoint + information gain smoke. Status: passed.
5. Phase E: VLM-LA interface smoke. Status: passed.
6. Phase F: short closed-loop smoke. Status: passed.
7. Phase G: long rollout data collection. Status: passed.
8. Phase H: dataset quality audit and human review packet.

## Phase G Gate

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


## Negative Scope

training: false
RL: false
SFT: false
GDPO: false
map_predict: false
PI_finetuning: false
A1_locomotion_training: false
real_VLM_inference: false
training_ready: false
