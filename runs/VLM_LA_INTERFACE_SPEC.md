# VLM-LA Interface Spec

## Project Route

A1-VLM-LA Explorer for 3D Active Exploration

## Robot Platform

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
```

## Primary Output

```text
Go to candidate <id>.
```

## Phase 9 Interface Audit

```yaml
source_dataset: Phase 8 rollout
parse_success_rate: 1.0
validation_success_rate: 1.0
movement_success_rate: 1.0
accepted_sample_count: 74
warning_sample_count: 3
rejected_sample_count: 0
training_ready: false
requires_human_review: true
```

The main interface remains candidate-ID based. Free coordinates, velocities, and joint commands are not accepted as VLM-LA outputs.
