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

# VLM-LA Dataset Spec

## Project Route

A1-VLM-LA Explorer for 3D Active Exploration

## Current New Scene Dataset Status

```yaml
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
dataset_quality_summary: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/summary/dataset_quality_summary.json
human_review_checklist: /home/ubuntu22/VLA/runs/HUMAN_REVIEW_NEW_SCENE_DATASET_CHECKLIST.md
phaseH_status: completed
```

## Phase H Audit Outputs

- accepted_samples: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/quality/accepted_samples.jsonl
- warning_samples: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/quality/warning_samples.jsonl
- rejected_samples: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/quality/rejected_samples.jsonl
- start_quality_summary: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/summary/start_quality_summary.csv
- failure_reason_summary: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/summary/failure_reason_summary.csv

## Quality Metrics

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


## Training Gate

training_ready: false
requires_human_review: true

Do not use new-scene data for SFT, GDPO, RL, or any training until a later
explicit human review approves preparation.
