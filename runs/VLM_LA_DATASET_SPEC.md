# VLM-LA Dataset Spec

## Status

Specification only. No training is allowed in Phase 0.

## Sample Purpose

Each sample teaches a model to choose a candidate viewpoint through constrained language, not free-form coordinates or low-level robot commands.

## Required Fields

```json
{
  "sample_id": "home_like_scene_v1_go2_start000_step000",
  "robot_platform": "unitree_go2",
  "robot_source": "existing_usd_prim",
  "go2_root_prim": "/World/...",
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
  "robot_state": {
    "base_frame": "base_link",
    "locomotion_mode": "kinematic_proxy_or_existing_controller"
  },
  "candidates": [
    {
      "id": 0,
      "x": 1.5,
      "y": 0.0,
      "z": 0.0,
      "yaw": 0.0,
      "is_valid": true,
      "is_reachable": true,
      "path_cost": 1.5,
      "information_gain": 120.0,
      "score": 87.0
    }
  ],
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

## Data Collection Gate

Long rollout data collection belongs to Phase 8. Human review belongs to Phase 9. Training preparation belongs to Phase 10. Actual training requires explicit approval after review.

## Large Artifact Safety

Raw sensor data, BEV images, RGB/depth images, `.npz`, `.hdf5`, checkpoints, meshes, textures, and USD scene bundles must not be committed to Git.
