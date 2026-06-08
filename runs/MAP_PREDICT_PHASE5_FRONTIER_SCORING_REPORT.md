# MapPredict Phase 5 Frontier Scoring Report

- phase: MapPredict Phase 5
- source model: Phase 3 3D U-Net baseline
- source uncertainty: Phase 4 probability_entropy
- source BEV projection method: occupancy max_z, uncertainty max_z
- workspace: /home/ubuntu22/VLA
- run_dir: /home/ubuntu22/VLA/runs/map_predict_phase5_frontier_scoring_baseline_20260609_004919
- source_phase4_run_dir: /home/ubuntu22/VLA/runs/map_predict_phase4_uncertainty_bev_projection_20260609_004045
- scoring_config: /home/ubuntu22/VLA/configs/map_predict/frontier_scoring_baseline.yaml
- frontier feature extraction method: BEV connected components from frontier masks, enriched with Phase 4 prediction/uncertainty, robot pose, and frontier centroid
- score formula: alpha*predicted_free_volume + beta*uncertainty_volume - gamma*occupied_risk - delta*path_cost
- scoring weights: alpha 1.0, beta 0.5, gamma 1.0, delta 0.2
- path_cost_method: euclidean_proxy
- reachability_method: bev_validity_proxy
- risk_method: mean_predicted_occupied_probability
- frontier_row_count: 92
- sample_count: 29
- scored_frontier_count: 92
- selected_frontier_count: 29
- selected_frontier_valid_rate: 1.0
- selected_is_top_score_rate: 1.0
- sample_selection_rate: 1.0
- nan_feature_count: 0
- nan_score_count: 0
- score_min: 17.050577681196515
- score_mean: 2124.6047089229237
- score_max: 14033.50144315086
- selected_score_mean: 6555.24371143861
- agreement_with_classical_selector: null
- score_regret_proxy: null
- frontier_feature_scored_table: /home/ubuntu22/VLA/runs/map_predict_phase5_frontier_scoring_baseline_20260609_004919/frontier_features/frontier_feature_scored_table.csv
- summary_json: /home/ubuntu22/VLA/runs/map_predict_phase5_frontier_scoring_baseline_20260609_004919/summary/frontier_scoring_summary.json
- plots:
  - /home/ubuntu22/VLA/runs/map_predict_phase5_frontier_scoring_baseline_20260609_004919/plots/score_distribution.png
  - /home/ubuntu22/VLA/runs/map_predict_phase5_frontier_scoring_baseline_20260609_004919/plots/selected_frontier_score_distribution.png
  - /home/ubuntu22/VLA/runs/map_predict_phase5_frontier_scoring_baseline_20260609_004919/plots/predicted_free_volume_vs_score.png
  - /home/ubuntu22/VLA/runs/map_predict_phase5_frontier_scoring_baseline_20260609_004919/plots/uncertainty_volume_vs_score.png
  - /home/ubuntu22/VLA/runs/map_predict_phase5_frontier_scoring_baseline_20260609_004919/plots/occupied_risk_vs_score.png
  - /home/ubuntu22/VLA/runs/map_predict_phase5_frontier_scoring_baseline_20260609_004919/plots/path_cost_vs_score.png
  - /home/ubuntu22/VLA/runs/map_predict_phase5_frontier_scoring_baseline_20260609_004919/plots/selected_frontier_overlay_examples.png
- training_started: false
- map_predict_training_started_this_phase: false
- diffusion_training_started: false
- VLA_training_started: false
- SFT_started: false
- GDPO_started: false
- RL_started: false
- rollout_started: false
- original_USD_modified: false
- checkpoint_committed_to_git: false
- dataset_npz_committed_to_git: false
- safe_to_integrate_with_exploration_selector: true
- safe_to_prepare_vla_features: true
- next_phase: MapPredict Phase 6 integrate map_predict features into frontier selector / VLA dataset builder

## Limitations

This is a handcrafted scoring baseline on a small validation/test subset. It is
sufficient for pipeline validation and feature-interface design, but it is not a
final training result or paper-level conclusion. The path cost is an Euclidean
proxy from robot pose to frontier centroid, not A*. The reachability signal is a
BEV validity proxy, not a planner feasibility proof. There is no strict
classical selector label in this Phase 4 table, so agreement_with_classical_selector
and score_regret_proxy are recorded as null.
