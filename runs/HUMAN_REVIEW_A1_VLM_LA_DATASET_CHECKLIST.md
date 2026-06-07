# Human Review A1 VLM-LA Dataset Checklist

## Review Scope

- source_run_dir: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536
- sample_count: 77
- accepted_sample_count: 74
- warning_sample_count: 3
- rejected_sample_count: 0
- robot_platform: unitree_a1
- sensor_method: real_isaac_omniverse_rgbd
- camera_pointcloud_source: depth_backprojection
- output_contract: Go to candidate <id>.
- training_ready: false
- requires_human_review: true

## Required Manual Checks

1. BEV candidate render is clear and corresponds to the recorded map state.
2. Candidate id matches the candidate table row.
3. Selected candidate is near unknown or useful exploration space.
4. `target_language` is exactly `Go to candidate <id>.`.
5. Warning and reject counts are acceptable for downstream preparation.
6. RGB/depth/pointcloud are from real Isaac/Omniverse sensors.
7. No geometry proxy data is present.
8. A1 trajectory is continuous enough for review use.
9. No collision, stuck, or falling event is present.
10. Repeated viewpoints or spinning-in-place behavior are not excessive.
11. Decide whether the dataset can proceed to VLM SFT dataset preparation.

## Review Decision Template

- approve_for_sft_preparation: yes/no/unsure
- approve_for_gdpo_preparation: yes/no/unsure
- need_more_rollout_data: yes/no
- need_sensor_fix: yes/no
- need_candidate_fix: yes/no
- reviewer_notes:

## Audit Output Paths

- dataset_quality_summary: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/summary/dataset_quality_summary.json
- start_quality_summary: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/summary/start_quality_summary.csv
- failure_reason_summary: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/summary/failure_reason_summary.csv
- accepted_samples: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/quality/accepted_samples.jsonl
- warning_samples: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/quality/warning_samples.jsonl
- rejected_samples: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/quality/rejected_samples.jsonl
- plots_path: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/plots

## Guardrail

This packet does not approve training by itself. `training_ready` remains false until a human reviewer explicitly approves a later preparation phase.
