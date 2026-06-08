# MapPredict Phase 6 Feature Integration Report

- phase: MapPredict Phase 6
- source: Phase 5 frontier scoring baseline
- workspace: /home/ubuntu22/VLA
- run_dir: /home/ubuntu22/VLA/runs/map_predict_phase6_feature_integration_20260609_005844
- source_frontier_table: /home/ubuntu22/VLA/runs/map_predict_phase5_frontier_scoring_baseline_20260609_004919/frontier_features/frontier_feature_scored_table.csv
- selector API: select_frontier_with_map_predict(frontier_table, weights) -> selected_frontier
- selector output: selected_frontier_id, score, reason, failure_reason
- VLA enhanced sample schema: robot metadata, images, candidate_table, map_predict_frontier_features, prompt, action_type, target_action, selected_candidate_id, training
- preview sample path: /home/ubuntu22/VLA/runs/map_predict_phase6_feature_integration_20260609_005844/samples/enhanced_vla_samples_preview.jsonl
- summary path: /home/ubuntu22/VLA/runs/map_predict_phase6_feature_integration_20260609_005844/summary/map_predict_feature_integration_summary.json
- frontier_rows: 92
- sample_count: 29
- enhanced_vla_preview_count: 20
- selector_smoke_passed: true
- invalid_selected_count: 0
- nan_score_count: 0
- json_parse_count: 20
- target_action_format_valid_rate: 1.0
- map_predict_feature_field_rate: 1.0
- action_type: high_level_candidate_action
- output_contract: Go to candidate <id>.
- safe_to_prepare_full_enhanced_vla_dataset: true
- safe_to_integrate_online_selector: true
- training_started: false
- map_predict_training_started: false
- VLA_training_started: false
- SFT_started: false
- GDPO_started: false
- RL_started: false
- diffusion_training_started: false
- rollout_started: false
- recommended_next_step: Add more USD scenes and scale map_predict + VLA data before formal diffusion/VLA training.

## Interfaces

The exploration selector lives at:

- /home/ubuntu22/VLA/exploration/frontier_feature_schema.py
- /home/ubuntu22/VLA/exploration/map_predict_frontier_selector.py

The VLA preview/export path lives at:

- /home/ubuntu22/VLA/map_predict/export_frontier_features.py
- /home/ubuntu22/VLA/vla/build_map_predict_enhanced_dataset.py

The selector rejects unreachable frontiers, invalid frontiers, and non-finite
scores. If no valid frontier exists, it returns selected_frontier_id = null with
a failure_reason. Preview VLA samples keep the output contract as a high-level
candidate action, not ordinary chat text:

```text
Go to candidate <id>.
```

## Limitations

Current data is sufficient for pipeline validation but not enough for final
diffusion or VLA training. This phase did not run rollout, did not train any
model, and did not modify original USDs. The preview JSONL is a small schema and
interface check, not a full training dataset.
