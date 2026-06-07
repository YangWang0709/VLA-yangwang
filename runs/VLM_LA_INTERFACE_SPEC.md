# VLM-LA Interface Spec

## Purpose

Define a constrained language-action interface for candidate viewpoint selection.

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

## Machine-Readable Alternative

```json
{
  "command": "go_to_candidate",
  "selected_candidate_id": 7
}
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
Go2 joint actions
```

## Fallback Policy

If parsing or candidate validation fails, the system must fall back to the classical candidate selector for that step and log the reason code.

## Phase 6 Smoke Tests

Planned tests:

- Valid commands parse with 100% success.
- Missing ID triggers fallback.
- Unknown ID triggers fallback.
- Invalid or unreachable ID triggers fallback.
- Candidate ID maps to the expected target pose.
- Free coordinate output is rejected.
