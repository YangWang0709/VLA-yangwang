# VLM-LA Dataset Spec

## Project Route

A1-VLM-LA Explorer for 3D Active Exploration

## Formal A1 Metadata

Formal A1 data must use:

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
```

## Phase 9 Review Packet Metadata

```yaml
source_dataset: Phase 8 rollout
dataset_quality_summary: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/summary/dataset_quality_summary.json
accepted_samples: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/quality/accepted_samples.jsonl
warning_samples: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/quality/warning_samples.jsonl
rejected_samples: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/quality/rejected_samples.jsonl
training_ready: false
requires_human_review: true
recommended_next_phase: manual_review_before_sft_preparation
```

## Phase 9 Audit Counts

```yaml
total_samples: 77
accepted_sample_count: 74
warning_sample_count: 3
rejected_sample_count: 0
acceptance_rate: 0.961
warning_rate: 0.039
rejection_rate: 0.0
real_sensor_sample_rate: 1.0
```

## Status

Phase 9 prepared a human review packet. The data must not be used for SFT or GDPO until the manual review result explicitly approves preparation.

## Label Contract

`target_language` must contain a parseable candidate ID:

```text
Go to candidate <id>.
```

## Large Artifact Safety

Raw sensor data, large RGB-D/depth/BEV images, `.npz`, `.hdf5`, checkpoints, meshes, textures, and USD scene bundles must not be committed to Git.
