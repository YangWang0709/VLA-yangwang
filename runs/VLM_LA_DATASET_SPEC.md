# VLM-LA Dataset Spec

## Corrected Project Route

A1-VLM-LA Explorer for 3D Active Exploration

## Corrected Robot Metadata

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

Specification only. No training is allowed at this correction stage.

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

## Correction Gate

Current Phase 3 and Phase 4 results are proxy pipeline smoke and are not final A1 data. Phase 5 data is not present in the current repository. Do not prepare training or Phase 6 evaluation until the user decides whether to rerun Phase 3 through Phase 5 using `/World/A1`.

## Large Artifact Safety

Raw sensor data, BEV images, RGB/depth images, `.npz`, `.hdf5`, checkpoints, meshes, textures, and USD scene bundles must not be committed to Git.
