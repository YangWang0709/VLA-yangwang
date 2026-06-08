# Active Task Board

current_phase: New Scene Phase F short closed-loop smoke
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
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


## New Scene Phase F Result

status: passed
run_dir: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseF_closed_loop_smoke_20260608_184342
script: /home/ubuntu22/VLA/scripts/new_scene_phaseF_closed_loop_smoke.py
report: /home/ubuntu22/VLA/runs/NEW_SCENE_CLOSED_LOOP_SMOKE_REPORT.md
summary_json: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseF_closed_loop_smoke_20260608_184342/summary/closed_loop_summary.json
closed_loop_steps_csv: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseF_closed_loop_smoke_20260608_184342/summary/closed_loop_steps.csv
command_log_jsonl: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseF_closed_loop_smoke_20260608_184342/commands/command_log.jsonl
parse_log_jsonl: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseF_closed_loop_smoke_20260608_184342/parsing/parse_log.jsonl

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


## Scope

Phase F ran only a short closed-loop smoke. It used real Isaac/Omniverse RGB-D
observations, depth_backprojection pointclouds, online candidate generation,
pseudo VLM commands, parser/validator checks, and kinematic A1 root movement.
It did not run long rollout, real VLM inference, training, RL, SFT, GDPO,
map_predict, PI/openpi fine-tuning, A1 locomotion training, checkpoint creation,
geometry proxy, or USD save.
