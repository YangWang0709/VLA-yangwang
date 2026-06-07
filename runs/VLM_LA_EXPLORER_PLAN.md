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
base_frame: /World/A1/base
```

The USD scene's real robot is `/World/A1`. Do not claim the USD contains a verified Go2 robot unless a real Go2 asset is provided or substituted later.

## Current Progress

- Phase 1 placed the primary USD scene bundle and kept it ignored by Git.
- Phase 2 opened the scene and identified the articulated `/World/A1` hierarchy.
- Phase 3 A1 sensor smoke passed using the existing USD A1 prim.
- Phase 4 A1 primary-scene mapping smoke passed using a BEV occupancy grid.
- Phase 5 A1 candidate viewpoint + information gain smoke passed with classical candidate scoring.
- Previous temporary Go2 proxy smoke results are superseded for formal A1 pipeline data.

## Phase 5 A1 Candidate Summary

```yaml
run_dir: /home/ubuntu22/VLA/runs/phase5_a1_candidate_gain_smoke_20260607_195140
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
candidate_sampling_method: radial_24_candidates_3_radii_8_angles_around_a1_base
path_cost_method: euclidean_plus_obstacle_penalty
information_gain_method: bev_unknown_visibility_proxy
step_count: 6
total_candidate_rows: 144
selected_candidate_valid_rate: 1.0
selected_is_top_score_rate: 1.0
safe_to_continue_phase6: true
```

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

## Current Gate

Phase 5 A1 candidate viewpoint + information gain smoke passed. The next formal route is Phase 6 VLM-LA interface smoke. Do not enter Phase 6 until explicitly requested.

## Negative Scope

Do not train VLM, RL, map_predict, PI/openpi action heads, or A1 locomotion policies in the current stage. Do not let the VLM output free coordinates, base velocities, or joint actions. Do not commit scene bundles, meshes, textures, raw sensor dumps, checkpoints, core dumps, tokens, keys, or private configs.
