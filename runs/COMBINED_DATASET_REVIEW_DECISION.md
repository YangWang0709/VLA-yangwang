# Combined Dataset Review Decision

## Project Status

- project_name: A1-VLM-LA Explorer
- output_contract: Go to candidate <id>.
- training_started: false
- SFT_started: false
- GDPO_started: false
- RL_started: false
- rollout_started: false
- raw_data_modified: false
- training_ready_changed: false

## Old Scene Summary

- scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
- rollout_completed: true
- quality_audit_completed: true
- total_samples: 77
- accepted_samples: 74
- warning_samples: 3
- rejected_samples: 0
- acceptance_rate: 0.961
- parse_success_rate: 1.0
- validation_success_rate: 1.0
- movement_success_rate: 1.0
- real_sensor_sample_rate: 1.0
- geometry_proxy_used: false
- mounted_geometry_proxy_used: false
- main_warning_reasons: occupied_cells_zero (2), post_rgb_invalid_noncritical (1), rgb_invalid_but_debug_rgb_path_present (1)
- main_reject_reasons: none

## New Scene Summary

- scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
- rollout_completed: true
- quality_audit_completed: true
- total_samples: 200
- accepted_samples: 199
- warning_samples: 1
- rejected_samples: 0
- acceptance_rate: 0.995
- parse_success_rate: 1.0
- validation_success_rate: 1.0
- movement_success_rate: 1.0
- real_sensor_sample_rate: 1.0
- geometry_proxy_used: false
- mounted_geometry_proxy_used: false
- main_warning_reasons: occupied_cells_zero (1)
- main_reject_reasons: none

## Combined Dataset Summary

- total_samples_all: 277
- accepted_samples_all: 273
- warning_samples_all: 4
- rejected_samples_all: 0
- combined_acceptance_rate: 0.9856
- scenes_count: 2
- whether_data_is_multi_scene: true
- whether_all_data_real_sensor: true
- whether_geometry_proxy_in_training_candidates: false
- whether_all_quality_audits_completed: true
- whether_all_parser_validator_rates_are_1_0: true

## Review Decision

- approve_for_sft_preparation: yes
- approve_for_direct_training: no
- approve_for_gdpo_preparation: no
- need_more_rollout_data: optional
- need_sensor_fix: no
- need_candidate_fix: no
- recommended_next_phase: Phase 10 combined SFT dataset preparation

## Decision Rationale

- Both scene datasets have completed long rollout and dataset quality audit / human review packet stages.
- Both datasets report `real_sensor_sample_rate: 1.0` and no geometry proxy usage in training candidates.
- Both datasets have `parse_success_rate: 1.0` and `validation_success_rate: 1.0`.
- Combined rejected sample count is 0.
- Warning reasons are non-blocking audit warnings: old scene has occupied-cell/RGB noncritical warnings, new scene has one occupied-cells-zero warning.
- This decision approves SFT dataset preparation only. It does not approve direct training, GDPO preparation, RL, or any model update.

## Guardrails

- Do not train in this review decision step.
- Do not start SFT, GDPO, RL, map_predict, or real VLM inference here.
- Do not modify Phase 8 or Phase G source data.
- Do not set any existing dataset manifest `training_ready` field to true.
- Phase 10 should prepare combined SFT dataset artifacts for review; model training remains a later explicitly approved step.

## Source Reports

- old_quality_report: /home/ubuntu22/VLA/runs/DATASET_QUALITY_REPORT.md
- old_human_review_checklist: /home/ubuntu22/VLA/runs/HUMAN_REVIEW_A1_VLM_LA_DATASET_CHECKLIST.md
- new_quality_report: /home/ubuntu22/VLA/runs/NEW_SCENE_DATASET_QUALITY_REPORT.md
- new_human_review_checklist: /home/ubuntu22/VLA/runs/HUMAN_REVIEW_NEW_SCENE_DATASET_CHECKLIST.md
- phase_status_audit: /home/ubuntu22/VLA/runs/VLA_PHASE_STATUS_AUDIT.md
