# Combined VLM SFT Dataset Preparation Report

phase: Phase 10
phase_detail: Phase 10 combined SFT dataset preparation only
project_name: A1-VLM-LA Explorer
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.

## Source Scenes

* old_scene: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
* new_scene: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda

## Source Review Decision

* source_review_decision: /home/ubuntu22/VLA/runs/COMBINED_DATASET_REVIEW_DECISION.md
* approve_for_sft_preparation: yes
* approve_for_direct_training: no
* approve_for_gdpo_preparation: no

## Samples Used

* old_scene_accepted_samples: 74
* new_scene_accepted_samples: 199
* accepted_samples_used: 273
* warning_samples_excluded: 4
* rejected_samples_excluded: 0
* geometry_proxy_used_in_sft: false
* all_data_real_sensor: true

## Dataset Artifacts

* sft_samples path: /home/ubuntu22/VLA/runs/phase10_combined_sft_dataset_preparation_20260608_193108/dataset/sft_samples.jsonl
* optional_review_pool path: /home/ubuntu22/VLA/runs/phase10_combined_sft_dataset_preparation_20260608_193108/dataset/optional_review_pool.jsonl
* rejected_samples_excluded path: /home/ubuntu22/VLA/runs/phase10_combined_sft_dataset_preparation_20260608_193108/dataset/rejected_samples_excluded.jsonl
* train split path: /home/ubuntu22/VLA/runs/phase10_combined_sft_dataset_preparation_20260608_193108/splits/train.jsonl
* val split path: /home/ubuntu22/VLA/runs/phase10_combined_sft_dataset_preparation_20260608_193108/splits/val.jsonl
* test split path: /home/ubuntu22/VLA/runs/phase10_combined_sft_dataset_preparation_20260608_193108/splits/test.jsonl
* split_summary path: /home/ubuntu22/VLA/runs/phase10_combined_sft_dataset_preparation_20260608_193108/splits/split_summary.json
* prompt template path: /home/ubuntu22/VLA/runs/COMBINED_VLM_SFT_PROMPT_TEMPLATE.md
* training config draft path: /home/ubuntu22/VLA/runs/COMBINED_VLM_SFT_TRAINING_CONFIG_DRAFT.md
* evaluation protocol path: /home/ubuntu22/VLA/runs/COMBINED_VLM_SFT_EVALUATION_PROTOCOL.md
* summary path: /home/ubuntu22/VLA/runs/phase10_combined_sft_dataset_preparation_20260608_193108/summary/combined_sft_dataset_summary.json

## Split Summary

* split_by: scene_id_and_start_id
* train_sample_count: 161
* val_sample_count: 56
* test_sample_count: 56
* train_scene_ids: building_scene_1_scene_20260608_171052, old_home_like_scene_v1
* val_scene_ids: building_scene_1_scene_20260608_171052, old_home_like_scene_v1
* test_scene_ids: building_scene_1_scene_20260608_171052, old_home_like_scene_v1

## Safety

* training_started: false
* SFT_started: false
* GDPO_started: false
* RL_started: false
* checkpoint_created: false
* requires_user_approval_before_training: true

## Recommended Next Phase

user approval for SFT training or collect more rollout data
