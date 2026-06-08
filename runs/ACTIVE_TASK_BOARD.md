# Active Task Board

current_phase: New Scene Phase D candidate viewpoint + information gain smoke
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
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

## New Scene Phase D Result

status: passed
run_dir: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseD_candidate_gain_20260608_182127
script: /home/ubuntu22/VLA/scripts/new_scene_phaseD_candidate_gain_smoke.py
report: /home/ubuntu22/VLA/runs/NEW_SCENE_CANDIDATE_GAIN_REPORT.md
summary_json: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseD_candidate_gain_20260608_182127/summary/candidate_summary.json
candidate_summary_csv: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseD_candidate_gain_20260608_182127/summary/candidate_summary.csv
candidate_steps_jsonl: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseD_candidate_gain_20260608_182127/summary/candidate_steps.jsonl

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

## Scope

No VLM-LA interface, rollout, training, RL, SFT, GDPO, map_predict, PI/openpi fine-tuning, A1 locomotion training, checkpoint creation, geometry proxy, or USD save was run.
