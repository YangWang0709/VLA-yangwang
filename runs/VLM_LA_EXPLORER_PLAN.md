# VLM-LA Explorer Plan

## Method Name

Go2-VLM-LA Explorer

Alternative descriptive name:

Unitree-Go2 VLM-guided Candidate Viewpoint Selection for 3D Active Exploration

## Workspace

`/home/ubuntu22/VLA`

## Core Pipeline

```text
Unitree Go2 RGB-D / depth / pointcloud / pose
+
explored_map / partial map
+
candidate viewpoints
-> BEV render with candidate IDs
-> VLM output: Go to candidate <id>.
-> LA parser: selected_candidate_id = <id>
-> candidate table lookup: candidate id -> target viewpoint pose
-> planner / Go2 movement wrapper
-> Go2 moves and updates map
```

## Robot Platform

Unitree Go2.

Current role: Unitree Go2 sensor carrier for VLM-LA active exploration.

The system must prefer the existing Unitree Go2 prim inside the USD scene. Only if Phase 2 cannot find a Go2-like hierarchy may a temporary Go2-shaped proxy be created, and that proxy must be reported as non-final.

## Output Contract

Primary language output:

```text
Go to candidate <id>.
```

Allowed example:

```text
Go to candidate 7.
```

Machine-readable fallback form:

```json
{
  "command": "go_to_candidate",
  "selected_candidate_id": 7
}
```

The execution layer must parse only the candidate ID. Any natural-language reason may be logged as explanation but must not be used as control evidence.

## Explicit map_predict Position

1. Explicit map_predict is not part of the main pipeline.
2. The VLM is expected to learn implicit exploration priors from RGB-D / explored_map / candidate viewpoints.
3. map_predict may be added later only as ablation or optional auxiliary prior.
4. Do not implement map_predict before primary-scene VLM-LA data collection and review.

## Negative Scope

Do not train VLM, RL, map_predict, PI/openpi action heads, or Unitree Go2 locomotion policies in the current stage. Do not let the VLM output free coordinates, base velocities, or Go2 joint actions. Do not commit scene bundles, meshes, textures, raw sensor dumps, checkpoints, core dumps, tokens, keys, or private configs.

## Phase Gates

- Phase 0: initialize workspace and docs.
- Phase 1: place full primary scene bundle and verify Git safety.
- Phase 2: open scene headlessly and inspect USD for existing Go2.
- Phase 3: Go2 pose and sensor smoke.
- Phase 4: primary-scene mapping smoke.
- Phase 5: candidate viewpoint and information gain smoke.
- Phase 6: VLM-LA interface smoke without training.
- Phase 7: short closed-loop smoke with pseudo VLM output.
- Phase 8: long rollout data collection without training.
- Phase 9: human review packet.
- Phase 10: fine-tuning preparation only after review approval.
