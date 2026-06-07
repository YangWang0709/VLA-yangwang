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

## Purpose

Define a constrained language-action interface for candidate viewpoint selection. The interface does not expose coordinates, velocities, or joint actions to the VLM.

## Primary Output

```text
Go to candidate <id>.
```

## Parser Contract

The parser extracts the integer candidate ID from a valid command. It accepts:

- `Go to candidate 7.`
- `go to candidate 7`
- `Go to candidate 7 because it faces unknown space.`
- `{"command": "go_to_candidate", "selected_candidate_id": 7}`

It rejects free coordinate, velocity, joint action, malformed JSON, missing-ID, out-of-range, invalid-candidate, and unreachable-candidate outputs as main control commands.

## Validator Contract

The validator checks:

- candidate ID exists in the current Phase 5R candidate table.
- candidate is valid.
- candidate is reachable.
- candidate collision risk is acceptable.

Invalid outputs fallback to the Phase 5R classical selected candidate for the same step.

## Phase 6 Gate

```yaml
candidate_data_source: phase5r_real_sensor
legal_parse_success_rate: 1.0
legal_validation_success_rate: 1.0
target_pose_lookup_success_rate: 1.0
illegal_reject_or_fallback_rate: 1.0
fallback_test_passed: true
free_coordinate_output_allowed: false
velocity_output_allowed: false
joint_action_output_allowed: false
safe_to_continue_phase7: true
```

## Invalid Main Outputs

```text
Go to the left room.
```

```json
{
  "x": 1.2,
  "y": 3.4,
  "yaw": 1.57
}
```

```text
forward, turn left, forward
```

```text
v, omega
```

```text
robot joint actions
```
