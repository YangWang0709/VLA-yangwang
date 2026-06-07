# VLM-LA Dataset Spec

## Project Route

A1-VLM-LA Explorer for 3D Active Exploration

## Formal A1 Metadata

Formal A1 data must use:

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
```

Old proxy smoke data must use:

```yaml
robot_platform: temporary_quadruped_proxy
robot_source: temporary_go2_proxy
not_final_robot_asset: true
```

## Status

Phase 3 A1 sensor smoke passed. No training is allowed at this stage.

## Phase 3 A1 Provenance

```yaml
run_dir: /home/ubuntu22/VLA/runs/phase3_a1_sensor_smoke_20260607_193054
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
base_frame: /World/A1/base
movement_mode: kinematic_existing_a1_root
real_a1_locomotion_controller: false
sensor_method: geometry_proxy_pointcloud_from_a1_base_pose
existing_sensor_reused: false
geometry_proxy_sensor_used: true
safe_to_continue_phase4: true
```

## Sample Purpose

Each sample teaches a model to choose a candidate viewpoint through constrained language, not free-form coordinates or low-level robot commands.

## Required Fields For Formal A1 Samples

```json
{
  "sample_id": "home_like_scene_v1_a1_start000_step000",
  "robot_platform": "unitree_a1",
  "robot_source": "existing_usd_prim",
  "a1_root_prim": "/World/A1",
  "scene_path": "/home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd",
  "bev_image": "relative/path/to/bev_candidates.png",
  "rgb_image": null,
  "depth_image": null,
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
  "label_source": "argmax_information_gain_minus_path_cost",
  "training": false
}
```

## Label Contract

`target_language` must contain a parseable candidate ID:

```text
Go to candidate <id>.
```

## Current Gate

Phase 4 A1 primary-scene mapping smoke is next. Do not prepare candidate generation, training, rollout, or Phase 6 evaluation until the formal A1 mapping and candidate phases exist.

## Large Artifact Safety

Raw sensor data, BEV images, RGB/depth images, `.npz`, `.hdf5`, checkpoints, meshes, textures, and USD scene bundles must not be committed to Git.
