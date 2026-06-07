# VLM-LA Explorer Plan

## Method Name

A1-VLM-LA Explorer

Full route name:

A1-VLM-LA Explorer for 3D Active Exploration

## Workspace

`/home/ubuntu22/VLA`

## Robot Platform

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
```

The USD scene's real robot is `/World/A1`. Do not claim the USD contains a verified Go2 robot unless a real Go2 asset is provided or substituted later.

## Current Progress

- Phase 1 placed the primary USD scene bundle and kept it ignored by Git.
- Phase 2 opened the scene and identified the articulated `/World/A1` hierarchy.
- Phase 3 A1 sensor smoke passed using the existing USD A1 prim.
- Previous temporary Go2 proxy smoke results are superseded for formal A1 pipeline data.

## Phase 3 A1 Smoke Summary

```yaml
run_dir: /home/ubuntu22/VLA/runs/phase3_a1_sensor_smoke_20260607_193054
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
base_frame: /World/A1/base
movement_mode: kinematic_existing_a1_root
real_a1_locomotion_controller: false
existing_sensor_reused: false
geometry_proxy_sensor_used: true
sensor_valid_rate: 1.0
safe_to_continue_phase4: true
```

## Legacy Proxy Results

Previous proxy smoke results must be labeled as:

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

## Current Gate

Phase 3 A1 sensor smoke passed. The next formal route is Phase 4 A1 primary-scene mapping smoke. Do not enter Phase 6 yet.

## Negative Scope

Do not train VLM, RL, map_predict, PI/openpi action heads, or A1 locomotion policies in the current stage. Do not let the VLM output free coordinates, base velocities, or joint actions. Do not commit scene bundles, meshes, textures, raw sensor dumps, checkpoints, core dumps, tokens, keys, or private configs.
