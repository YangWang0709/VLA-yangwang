# MapPredict Phase 3 3D U-Net Baseline Report

- phase: MapPredict Phase 3
- model: 3D U-Net occupancy completion baseline
- workspace: /home/ubuntu22/VLA
- run_dir: /home/ubuntu22/VLA/runs/map_predict_phase3_3d_unet_baseline_20260609_002658
- dataset: local_voxel_v2_aligned_real_partial_3d
- dataset_root: /home/ubuntu22/VLA/data/map_predict/local_voxel_dataset/local_voxel_v2_aligned_real_partial_3d
- gt_type: dense_scan_pseudo_gt
- dense_scan_pseudo_gt_is_perfect_ground_truth: false
- sample_count: 97
- train/val/test split: 68 / 20 / 9
- skipped_non_pass: train 2, val 0, test 1
- input channels: observed_free, observed_occupied, unknown_mask, frontier_mask, robot_position_gaussian, height_channel
- output: occupancy_logits [B,1,D,H,W]
- forward_shape: [2, 1, 24, 64, 64]
- loss formula: BCEWithLogits(unknown_mask, dense_scan_pseudo_gt) + lambda_obs * BCEWithLogits(observed_free|observed_occupied)
- lambda_obs: 0.1
- unknown_pos_weight: 47.98977745679803
- optimizer: AdamW
- lr: 0.001
- weight_decay: 0.0001
- epochs: 30
- batch_size: 2
- base_channels: 16
- parameter_count: 341729
- smoke_train_epochs: 3
- smoke_train_passed: true
- train_loss_start: 0.8290747281383065
- train_loss_end: 0.2337177886682398
- train_loss_decreased: true
- best_epoch: 24
- best val unknown IoU: 0.24434269921427498
- best val unknown BCE: 0.16702158148546034
- val unknown precision: 0.25717927321378525
- val unknown recall: 0.8344187093700681
- val observed_consistency_error: 0.0
- val full_crop_iou: 0.25315474739097216
- val naive_all_free_iou: 0.0
- val naive_all_occupied_iou: 0.0250804214740958
- val naive_all_free_bce: 0.34649980259363045
- val naive_all_occupied_bce: 13.469011755343104
- test unknown IoU: 0.2395377323549695
- test unknown BCE: 0.1729543162925098
- test unknown precision: 0.2492830514665268
- test unknown recall: 0.8537496276087023
- test observed_consistency_error: 0.0
- test full_crop_iou: 0.24878077177539076
- checkpoint path: /home/ubuntu22/VLA/runs/map_predict_phase3_3d_unet_baseline_20260609_002658/checkpoints/best_3d_unet.pt
- checkpoint_committed_to_git: false
- training_started: true
- map_predict_training_started: true
- diffusion_training_started: false
- VLA_training_started: false
- SFT_started: false
- GDPO_started: false
- RL_started: false
- rollout_started: false
- original_USD_modified: false
- source_VLA_data_modified: false
- dataset_npz_committed_to_git: false
- checkpoint_committed_to_git: false
- observed_consistency_enforced_after_inference: true
- safe_to_build_uncertainty_baseline: true
- next_phase: MapPredict Phase 4 uncertainty baseline via MC dropout / ensemble or lightweight diffusion sampling

## Offline Validation

The baseline passed the required loader, forward-shape, 3 epoch smoke train, 30
epoch baseline train, loss-decrease, naive baseline comparison, and observed
consistency checks. The validation unknown-region BCE is below the all-free
naive BCE, and validation unknown-region IoU is above both all-free and
all-occupied naive IoU baselines. Observed free and observed occupied voxels are
clamped after inference, yielding observed_consistency_error = 0.0.

## Local-Only Outputs

- summary/train_metrics.csv
- summary/val_metrics.csv
- summary/test_metrics.json
- summary/model_summary.json
- plots/loss_curve.png
- plots/val_unknown_iou_curve.png
- debug_predictions/sample_*_bev_pred.png
- debug_predictions/sample_*_z_slices.png
- checkpoints/best_3d_unet.pt

The Phase 3 run directory is local-only and excluded from Git. The checkpoint is
small but is still not committed, per project safety rules.
