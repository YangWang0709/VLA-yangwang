# VLM-LA Explorer Plan

## Corrected Method Name

A1-VLM-LA Explorer

Full route name:

A1-VLM-LA Explorer for 3D Active Exploration

## Workspace

`/home/ubuntu22/VLA`

## Corrected Robot Platform

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
```

The USD scene's real robot is `/World/A1`. Do not claim the USD contains a verified Go2 robot unless a real Go2 asset is provided or substituted later.

## Legacy Proxy Results

Previous Phase 3 and Phase 4 smoke results used a temporary proxy and must be labeled as:

```yaml
robot_platform: temporary_quadruped_proxy
robot_source: temporary_go2_proxy
not_final_robot_asset: true
```

Those results are valid only as proxy pipeline smoke and are not final A1 data.

## Core Pipeline

```text
USD scene with /World/A1
-> A1 pose / robot state
-> RGB-D / depth / pointcloud / LiDAR or proxy observation
-> explored_map / partial map
-> candidate viewpoints
-> BEV render with candidate IDs
-> VLM output: Go to candidate <id>.
-> LA parser: selected_candidate_id = <id>
-> candidate table lookup: candidate id -> target viewpoint pose
-> planner / A1 movement wrapper
-> A1 moves and updates map
```

## Output Contract

```text
Go to candidate <id>.
```

Only the candidate ID may drive control. Explanation text may be logged but must not control motion.

## Explicit map_predict Position

1. Explicit map_predict is not part of the main pipeline.
2. The VLM is expected to learn implicit exploration priors from RGB-D / explored_map / candidate viewpoints.
3. map_predict may be added later only as ablation or optional auxiliary prior.
4. Do not implement map_predict before primary-scene VLM-LA data collection and review.

## Current Correction Gate

Phase 6 is paused. Rerun Phase 3 through Phase 5 using explicit `/World/A1`, or explicitly continue as proxy-only, before moving forward.

## Negative Scope

Do not train VLM, RL, map_predict, PI/openpi action heads, or locomotion policies in the current stage. Do not let the VLM output free coordinates, base velocities, or joint actions. Do not commit scene bundles, meshes, textures, raw sensor dumps, checkpoints, core dumps, tokens, keys, or private configs.
