# VLM-LA Explorer Plan

## Method Name

A1-VLM-LA Explorer

Full route name:

A1-VLM-LA Explorer for 3D Active Exploration

## Workspace

`/home/ubuntu22/VLA`

## Robot Platform

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
```

The USD scene's real robot is `/World/A1`. Do not claim the USD contains a verified Go2 robot unless a real Go2 asset is provided or substituted later.

## Current Progress

- Phase 1 placed the primary USD scene bundle and kept it ignored by Git.
- Phase 2 opened the scene and identified the articulated `/World/A1` hierarchy.
- Old proxy Phase 3 through Phase 5 outputs remain proxy-only and are not final A1 real-sensor data.
- Phase 5.6 validated real Isaac/Omniverse RGB-D sensing and depth-backprojected pointclouds.
- Phase 4R-real, Phase 5R-real, Phase 6, and Phase 7 passed the real-sensor A1 pipeline gates.
- Phase 8 collected A1 real-sensor VLM-LA rollout samples.
- Phase 9 prepared the human review packet and dataset quality audit.

## Phase 9 Audit Route

```yaml
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
```

## Next Phase

Manual review result required before SFT preparation.

Training remains out of scope until explicit human approval.
