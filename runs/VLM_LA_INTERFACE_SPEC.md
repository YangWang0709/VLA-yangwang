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

Example:

```text
Go to candidate 7.
```

Optional explanation is allowed only after a valid candidate ID:

```text
Go to candidate 7 because it faces the largest unexplored region.
```

## Parser Contract

The parser extracts the integer candidate ID from a valid command. It must validate that:

- The command contains a candidate ID.
- The ID exists in the current candidate table.
- The candidate is valid.
- The candidate is reachable.

Only `selected_candidate_id` may drive control. Explanation text must be logged but ignored for motion decisions.

## Candidate Input Provenance

Phase 5 produced proxy-mapping based candidate tables and BEV overlays. They are suitable for Phase 6 interface smoke, but they are not final real-sensor data.

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

## Fallback Policy

If parsing or candidate validation fails, the system must fall back to the classical candidate selector for that step and log the reason code.

## Current Gate

Phase 5 A1 candidate viewpoint + information gain smoke passed with `safe_to_continue_phase6: true`. Phase 6 VLM-LA interface smoke is the next formal phase, but it has not been run yet.
