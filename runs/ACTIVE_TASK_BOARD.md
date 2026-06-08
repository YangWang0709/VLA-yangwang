# Active Task Board

current_phase: New Scene Phase H dataset quality audit / human review packet
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
current_scene_id: building_scene_1_scene_20260608_171052
current_scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
current_scene_phase: New Scene Phase H dataset quality audit / human review packet
source_dataset: New Scene Phase G rollout
source_run_dir: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
vlm_output_mode: pseudo_from_classical_selector
output_contract: Go to candidate <id>.
training_ready: false
requires_human_review: true
next_phase: Manual review result required before SFT preparation

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


## New Scene Phase H Result

status: completed
run_dir: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002
script: /home/ubuntu22/VLA/scripts/new_scene_phaseH_dataset_quality_audit.py
quality_report: /home/ubuntu22/VLA/runs/NEW_SCENE_DATASET_QUALITY_REPORT.md
human_review_checklist: /home/ubuntu22/VLA/runs/HUMAN_REVIEW_NEW_SCENE_DATASET_CHECKLIST.md
dataset_quality_summary: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/summary/dataset_quality_summary.json
start_quality_summary: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/summary/start_quality_summary.csv
failure_reason_summary: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/summary/failure_reason_summary.csv

total_samples: 200
accepted_sample_count: 199
warning_sample_count: 1
rejected_sample_count: 0
acceptance_rate: 0.995
warning_rate: 0.005
rejection_rate: 0.0
parse_success_rate: 1.0
validation_success_rate: 1.0
movement_success_rate: 1.0
real_sensor_sample_rate: 1.0
average_final_known_ratio: 0.408687


## Scope

Phase H only audited New Scene Phase G rollout data and generated a human review
packet. It did not train, run real VLM inference, modify Phase G source rows,
save USD files, or mark the data training-ready.
