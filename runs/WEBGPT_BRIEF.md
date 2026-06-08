# WEBGPT Brief

## Current Phase

New Scene Phase D candidate viewpoint + information gain smoke

## Context

current_scene_id: building_scene_1_scene_20260608_171052
current_scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
original_user_usd_path: /home/ubuntu22/VLA/building_scene(1).usd
current_scene_phase: New Scene Phase D candidate viewpoint + information gain smoke
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
map_update_source: depth_backprojection_pointcloud
output_contract: Go to candidate <id>.
training_ready: false
requires_human_review: true
next_phase: New Scene Phase E VLM-LA interface smoke

negative_scope:
- training: false
- RL: false
- SFT: false
- GDPO: false
- map_predict: false
- rollout: false
- VLM_LA_interface: false
- PI_action_finetuning: false
- A1_locomotion_training: false

## Completed

- Used the repaired new scene and existing `/World/A1`.
- Reused the real Isaac/Omniverse RGB-D route and Phase C BEV mapping logic.
- Generated radial candidate viewpoints at each decision step.
- Scored candidates with A* BEV path cost, real-sensor BEV unknown visibility, and a classical score formula.
- Wrote candidate tables, per-step JSONL, and BEV candidate overlays.
- Did not run VLM inference, VLM-LA interface, rollout, or training.

## Metrics

step_count: 6
candidate_count_per_step: 24
total_candidate_rows: 144
valid_candidate_ratio: 0.8819
positive_gain_candidate_ratio: 0.8819
selected_candidate_valid_rate: 1.0
selected_is_top_score_rate: 1.0
path_cost_constant: false
min_path_cost: 1.0071
max_path_cost: 6.4599
min_information_gain: 0
max_information_gain: 749
failure_count: 0
safe_to_interface: true

## Next Action

New Scene Phase E VLM-LA interface smoke
