# VLM-LA Interface Spec

## Corrected Project Route

A1-VLM-LA Explorer for 3D Active Exploration

## Corrected Robot Platform

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
```

Legacy proxy smoke data must be labeled with:

```yaml
robot_platform: temporary_quadruped_proxy
robot_source: temporary_go2_proxy
not_final_robot_asset: true
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

## Invalid Main Outputs

These are invalid as primary control outputs:

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

## Current Correction Gate

Phase 6 is paused until Phase 3 through Phase 5 are either rerun with explicit `/World/A1` or the user explicitly chooses proxy-only continuation.
