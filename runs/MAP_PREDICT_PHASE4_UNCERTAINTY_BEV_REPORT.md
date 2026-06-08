# MapPredict Phase 4 Uncertainty + BEV Projection Report

- phase: MapPredict Phase 4
- source model: 3D U-Net baseline
- workspace: /home/ubuntu22/VLA
- run_dir: /home/ubuntu22/VLA/runs/map_predict_phase4_uncertainty_bev_projection_20260609_004045
- checkpoint path: /home/ubuntu22/VLA/runs/map_predict_phase3_3d_unet_baseline_20260609_002658/checkpoints/best_3d_unet.pt
- checkpoint_committed_to_git: false
- dataset: local_voxel_v2_aligned_real_partial_3d
- dataset_root: /home/ubuntu22/VLA/data/map_predict/local_voxel_dataset/local_voxel_v2_aligned_real_partial_3d
- samples evaluated: 29
- splits evaluated: val 20, test 9
- uncertainty methods:
  - probability_entropy: true
  - mc_dropout_available: false
  - mc_dropout_used: false
- observed_space_preserved: true
- observed_consistency_error_after_projection: 0.0
- BEV projection method:
  - bev_occ_projection: max
  - bev_uncertainty_projection: max
- unknown_region_iou: 0.24285150260276642
- unknown_region_bce: 0.1688627752784241
- uncertainty_mean_unknown: 0.11295758059312558
- uncertainty_mean_observed: 0.0
- uncertainty_observed_gap: 0.11295758059312558
- entropy_calibration_basic: 0.46823029528404103
- frontier feature table path: /home/ubuntu22/VLA/runs/map_predict_phase4_uncertainty_bev_projection_20260609_004045/frontier_features/frontier_feature_table.csv
- frontier_feature_row_count: 92
- frontier_feature_nan_count: 0
- frontier_rows_per_sample_mean: 3.1724137931034484
- frontier_mean_uncertainty_mean: 0.08729826610373415
- frontier_max_uncertainty_mean: 0.6964031741347002
- frontier_predicted_occupied_risk_mean: 0.0587764099523749
- visualization paths:
  - /home/ubuntu22/VLA/runs/map_predict_phase4_uncertainty_bev_projection_20260609_004045/plots/bev_pred_occ_examples.png
  - /home/ubuntu22/VLA/runs/map_predict_phase4_uncertainty_bev_projection_20260609_004045/plots/bev_uncertainty_examples.png
  - /home/ubuntu22/VLA/runs/map_predict_phase4_uncertainty_bev_projection_20260609_004045/plots/uncertainty_histogram.png
  - /home/ubuntu22/VLA/runs/map_predict_phase4_uncertainty_bev_projection_20260609_004045/plots/frontier_feature_distributions.png
- pred_occ_prob_outputs: /home/ubuntu22/VLA/runs/map_predict_phase4_uncertainty_bev_projection_20260609_004045/inference/*.npz
- voxel_uncertainty_outputs: /home/ubuntu22/VLA/runs/map_predict_phase4_uncertainty_bev_projection_20260609_004045/inference/*.npz
- bev_outputs: /home/ubuntu22/VLA/runs/map_predict_phase4_uncertainty_bev_projection_20260609_004045/inference/*.npz
- map_predict_training_started_this_phase: false
- diffusion_training_started: false
- VLA_training_started: false
- SFT_started: false
- GDPO_started: false
- RL_started: false
- rollout_started: false
- original_USD_modified: false
- dense_scan_pseudo_gt_is_perfect_ground_truth: false
- checkpoint_committed_to_git: false
- large_outputs_committed_to_git: false
- safe_to_build_frontier_scoring_baseline: true
- next_phase: MapPredict Phase 5 frontier feature extraction and scoring baseline

## Validation Notes

Phase 4 loads the Phase 3 3D U-Net checkpoint and runs offline inference only.
It does not train diffusion, VLA, SFT, GDPO, RL, or any new model. The first
uncertainty baseline is normalized probability entropy. The Phase 3 model does
not contain dropout layers, so MC dropout is recorded as unavailable rather
than reported as an uncertainty method.

Observed-space preservation is enforced after inference:

```text
pred_occ_prob[observed_free == 1] = 0.0
pred_occ_prob[observed_occupied == 1] = 1.0
uncertainty[observed_free == 1] = 0.0
uncertainty[observed_occupied == 1] = 0.0
```

This yields observed_consistency_error_after_projection = 0.0. Unknown-region
uncertainty is greater than observed-region uncertainty, as expected after
preservation.
