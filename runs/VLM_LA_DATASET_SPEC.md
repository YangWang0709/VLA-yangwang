<!-- map_predict_phase6_vla_dataset_status:start -->
## MapPredict Phase 6 VLA Dataset Preview Status

current_phase: MapPredict Phase 6 feature integration with frontier selector and VLA dataset preview
project_name: A1-VLM-LA Explorer
dataset_route: VLA high-level candidate action
VLA_output_contract: Go to candidate <id>.
action_type: high_level_candidate_action
source_phase: MapPredict Phase 5 frontier scoring baseline
preview_sample_path: /home/ubuntu22/VLA/runs/map_predict_phase6_feature_integration_20260609_005844/samples/enhanced_vla_samples_preview.jsonl
enhanced_vla_preview_count: 20
map_predict_frontier_features_present: true
target_action_format_valid_rate: 1.0
safe_to_prepare_full_enhanced_vla_dataset: true
training_started: false
VLA_training_started: false
SFT_started: false
GDPO_started: false
RL_started: false
diffusion_training_started: false
data_volume_warning: current dataset is sufficient for pipeline validation but not enough for final diffusion or VLA training
recommended_next_step: Add more USD scenes and scale map_predict + VLA data before formal diffusion/VLA training.
<!-- map_predict_phase6_vla_dataset_status:end -->

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
