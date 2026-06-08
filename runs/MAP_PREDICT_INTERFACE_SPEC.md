# MapPredict Interface Spec

phase: MapPredict Phase 0
module: map_predict
role: feature_provider
planner: false
VLA: false
training_started: false

## Input

The feature provider receives a voxel crop with channels:

* observed_free: [D, H, W]
* observed_occupied: [D, H, W]
* unknown_mask: [D, H, W]
* frontier_mask: [D, H, W]
* robot_pose: [x, y, z, yaw]
* crop_origin: [x, y, z]
* voxel_size: float

## Output

The feature provider returns:

* predicted_occupancy: [D, H, W]
* occupancy_probability: [D, H, W]
* uncertainty: [D, H, W]
* bev_uncertainty: [H, W]
* optional candidate_features with local uncertainty statistics

## Downstream Contract

map_predict must not emit navigation commands. It only enriches map and candidate
features. The VLM-LA output contract remains:

`Go to candidate <id>.`

## Candidate Feature Enrichment

For each candidate, later phases may attach:

* map_predict_uncertainty_mean
* map_predict_uncertainty_max
* predicted_occupied_ratio_near_candidate
* predicted_free_ratio_near_candidate
* unknown_to_predicted_free_gain

These fields are advisory features. They do not replace command validation.
