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

The parser extracts the integer candidate ID from a valid command. It must validate that:

- The command contains a candidate ID.
- The ID exists in the current candidate table.
- The candidate is valid.
- The candidate is reachable.

Only `selected_candidate_id` may drive control. Explanation text must be logged but ignored for motion decisions.

## Sensor Route Gate

Phase 5.5 introduced an A1-mounted sensor frame. Phase 4 and Phase 5 should be rerun with mounted sensor observations before Phase 6 interface smoke.

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

Do not enter Phase 6 yet. Next phase is rerunning Phase 4 A1 mapping smoke with mounted sensor.
