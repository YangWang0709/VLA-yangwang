# Context Compact

## Workspace

`/home/ubuntu22/VLA` is the new primary workspace. Do not use `/home/ubuntu22/pi` as the primary workspace. It may only be used as a source for copying the full primary scene bundle in Phase 1 if needed.

## Goal

Go2-VLM-LA Explorer for 3D Active Exploration.

## Pipeline

```text
USD scene with existing Unitree Go2
-> Go2 pose / robot state
-> RGB-D / depth / pointcloud / LiDAR or proxy observation
-> explored_map / partial map
-> candidate viewpoints
-> BEV render with candidate IDs
-> VLM output: Go to candidate <id>.
-> LA parser extracts candidate id
-> candidate table maps id to target pose
-> planner / Go2 movement wrapper executes navigation target
```

## Hard Contract

The main VLM output must be `Go to candidate <id>.` Optional explanation may exist, but only the candidate ID may control motion.

## Hard Negative Scope

No VLM training, RL, map_predict training, PI/openpi action fine-tuning, Go2 locomotion training, free coordinate output, velocity output, joint action output, or scene bundle commit before human review and explicit approval.

## Current Phase

Phase 0 completed the initialization baseline. Next is Phase 1 scene bundle placement and Git ignore verification.
