<!-- phase10_combined_sft_status:start -->
## Phase 10 Combined SFT Dataset Preparation Status

current_phase: Phase 10 combined SFT dataset preparation only
project_name: A1-VLM-LA Explorer
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.
source_review_decision: /home/ubuntu22/VLA/runs/COMBINED_DATASET_REVIEW_DECISION.md
phase10_run_dir: /home/ubuntu22/VLA/runs/phase10_combined_sft_dataset_preparation_20260608_193108
sft_sample_count: 273
train_sample_count: 161
val_sample_count: 56
test_sample_count: 56
robot_platform: unitree_a1
sensor_method: real_isaac_omniverse_rgbd
geometry_proxy_used_in_sft: false
training_started: false
SFT_started: false
GDPO_started: false
RL_started: false
checkpoint_created: false
requires_user_approval_before_training: true
next_phase: User approval required before SFT training
<!-- phase10_combined_sft_status:end -->

# Active Task Board

current_phase: Combined manual review decision before SFT preparation
workspace: /home/ubuntu22/VLA
project_name: A1-VLM-LA Explorer
output_contract: Go to candidate <id>.
old_scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
new_scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
old_quality_audit_completed: true
new_quality_audit_completed: true
total_samples_all: 277
accepted_samples_all: 273
warning_samples_all: 4
rejected_samples_all: 0
combined_acceptance_rate: 0.9856
whether_data_is_multi_scene: true
whether_all_data_real_sensor: true
whether_geometry_proxy_in_training_candidates: false
approve_for_sft_preparation: yes
approve_for_direct_training: no
approve_for_gdpo_preparation: no
training_started: false
SFT_started: false
GDPO_started: false
RL_started: false
rollout_started: false
next_phase: Phase 10 combined SFT dataset preparation, only if approved

negative_scope:
- training: false
- SFT: false
- GDPO: false
- RL: false
- rollout: false
- resampling: false
- real_VLM_inference: false
- raw_data_modified: false
- training_ready_changed: false


## Combined Review Decision

status: completed
decision_report: /home/ubuntu22/VLA/runs/COMBINED_DATASET_REVIEW_DECISION.md
phase_status_audit: /home/ubuntu22/VLA/runs/VLA_PHASE_STATUS_AUDIT.md

The combined old and new scene datasets are approved for SFT dataset preparation
only. Direct training and GDPO preparation remain not approved.
