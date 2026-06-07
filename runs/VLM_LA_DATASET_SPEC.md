# VLM-LA Dataset Spec

## Project Route

A1-VLM-LA Explorer for 3D Active Exploration

## Formal A1 Metadata

Formal A1 data must use:

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
```

Old proxy smoke data must use:

```yaml
robot_platform: temporary_quadruped_proxy
robot_source: temporary_go2_proxy
not_final_robot_asset: true
```

## Status

Phase 5 A1 candidate viewpoint + information gain smoke passed. No training is allowed at this stage.

## Phase 5 A1 Candidate Provenance

```yaml
run_dir: /home/ubuntu22/VLA/runs/phase5_a1_candidate_gain_smoke_20260607_195140
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
sensor_method: geometry_proxy_pointcloud_from_a1_base_pose
map_type: BEV occupancy grid
mapping_method: raycast_bev_proxy_mapping
candidate_sampling_method: radial_24_candidates_3_radii_8_angles_around_a1_base
path_cost_method: euclidean_plus_obstacle_penalty
information_gain_method: bev_unknown_visibility_proxy
safe_to_continue_phase6: true
```

## Sample Purpose

Each sample teaches a model to choose a candidate viewpoint through constrained language, not free-form coordinates or low-level robot commands.

## Required Fields For Formal A1 Samples

```json
{
  "sample_id": "home_like_scene_v1_a1_step000_candidate007",
  "robot_platform": "unitree_a1",
  "robot_source": "existing_usd_prim",
  "a1_root_prim": "/World/A1",
  "base_frame": "/World/A1/base",
  "scene_path": "/home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd",
  "bev_image": "relative/path/to/bev_candidates.png",
  "candidate_summary": "relative/path/to/candidate_summary.csv",
  "candidate_steps": "relative/path/to/candidate_steps.jsonl",
  "robot_pose": {
    "x": 0.0,
    "y": 0.0,
    "z": 0.0,
    "yaw": 0.0
  },
  "candidates": [],
  "prompt": "Select the best next viewpoint for active exploration.",
  "target_language": "Go to candidate 7.",
  "selected_candidate_id": 7,
  "label_source": "classical_information_gain_minus_path_cost",
  "training": false
}
```

## Label Contract

`target_language` must contain a parseable candidate ID:

```text
Go to candidate <id>.
```

## Current Gate

Phase 6 VLM-LA interface smoke is next. Do not prepare training, rollout, or final evaluation until interface parsing, validation, and fallback behavior are smoke-tested.

## Large Artifact Safety

Raw sensor data, large BEV/RGB/depth images, `.npz`, `.hdf5`, checkpoints, meshes, textures, and USD scene bundles must not be committed to Git.
