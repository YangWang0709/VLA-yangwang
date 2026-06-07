# Dataset Quality Report

phase: Phase 9
source phase: Phase 8
source run_dir: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536
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
rgb_valid_rate: 0.987
depth_valid_rate: 1.0
camera_pointcloud_valid_rate: 1.0
average_final_known_ratio: 0.305375
main warning reasons: occupied_cells_zero (2), post_rgb_invalid_noncritical (1), rgb_invalid_but_debug_rgb_path_present (1)
main rejection reasons: none
plots path: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/plots
accepted sample paths: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/quality/accepted_samples.jsonl
warning sample paths: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/quality/warning_samples.jsonl
rejected sample paths: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/quality/rejected_samples.jsonl
training_ready: false
requires_human_review: true
recommended_next_phase: manual_review_before_sft_preparation

## Dataset-Level Decision

The dataset is suitable for manual review packet generation. It is not marked training-ready. A human review result is required before SFT or GDPO preparation.

## Caveats

- Warning-level samples: 3; see `main warning reasons` and `warning_samples.jsonl`.
- No rejected samples were found by the automated audit.
- VLM labels are pseudo labels from a classical selector, not real VLM inference.
- Movement is kinematic root movement, not a trained A1 locomotion policy.
- The audit did not modify the Phase 8 raw CSV or JSONL rows.
