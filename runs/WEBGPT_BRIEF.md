# WEBGPT Brief

## Current Phase

Phase 9 human review packet

## Context

current_phase: Phase 9 human review packet
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
source_dataset: Phase 8 rollout
training_ready: false
requires_human_review: true
next_phase: Manual review result required before SFT preparation
negative_scope:
- training: false
- SFT: false
- GDPO: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- A1_locomotion_training: false
- real_vlm_inference: false

## Completed

- Created `scripts/phase9_dataset_quality_audit.py`.
- Audited Phase 8 rollout samples for sensor, map, candidate, label, language, and closed-loop quality.
- Split samples into accepted, warning, and rejected review files.
- Generated dataset quality summary, start summary, failure reason summary, lightweight plots, checklist, and quality report.
- Kept `training_ready: false` and `requires_human_review: true`.

## Metrics

status: review_packet_prepared
run_dir: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732
script: /home/ubuntu22/VLA/scripts/phase9_dataset_quality_audit.py
checklist: /home/ubuntu22/VLA/runs/HUMAN_REVIEW_A1_VLM_LA_DATASET_CHECKLIST.md
quality_report: /home/ubuntu22/VLA/runs/DATASET_QUALITY_REPORT.md
source_run_dir: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536
total_samples: 77
accepted_sample_count: 74
warning_sample_count: 3
rejected_sample_count: 0
acceptance_rate: 0.961
warning_rate: 0.039
rejection_rate: 0.0
parse_success_rate: 1.0
validation_success_rate: 1.0
movement_success_rate: 1.0
real_sensor_sample_rate: 1.0
average_final_known_ratio: 0.305375
training_ready: false
requires_human_review: true
recommended_next_phase: manual_review_before_sft_preparation

## Evidence

- dataset_quality_summary: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/summary/dataset_quality_summary.json
- start_quality_summary: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/summary/start_quality_summary.csv
- failure_reason_summary: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/summary/failure_reason_summary.csv
- accepted_samples: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/quality/accepted_samples.jsonl
- warning_samples: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/quality/warning_samples.jsonl
- rejected_samples: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/quality/rejected_samples.jsonl
- plots_path: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/plots
