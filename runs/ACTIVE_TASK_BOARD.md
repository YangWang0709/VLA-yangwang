# Active Task Board

current_phase: New Scene Phase C real-sensor mapping smoke
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
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

## New Scene Phase C Result

status: passed
run_dir: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseC_real_sensor_mapping_20260608_181325
script: /home/ubuntu22/VLA/scripts/new_scene_phaseC_real_sensor_mapping_smoke.py
report: /home/ubuntu22/VLA/runs/NEW_SCENE_REAL_SENSOR_MAPPING_REPORT.md
summary_json: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseC_real_sensor_mapping_20260608_181325/summary/mapping_summary.json
mapping_steps_csv: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseC_real_sensor_mapping_20260608_181325/summary/mapping_steps.csv

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

## Scope

No candidate generation, VLM-LA interface, rollout, training, RL, SFT, GDPO, map_predict, PI/openpi fine-tuning, A1 locomotion training, checkpoint creation, geometry proxy mapping, or USD save was run.
