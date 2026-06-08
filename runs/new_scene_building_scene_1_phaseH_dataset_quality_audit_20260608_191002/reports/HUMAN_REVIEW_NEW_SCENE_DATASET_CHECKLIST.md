# Human Review New Scene Dataset Checklist

## Review Scope

- source_run_dir: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904
- sample_count: 200
- accepted_sample_count: 199
- warning_sample_count: 1
- rejected_sample_count: 0
- robot_platform: unitree_a1
- scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
- sensor_method: real_isaac_omniverse_rgbd
- output_contract: Go to candidate <id>.
- training_ready: false
- requires_human_review: true

## Required Manual Checks

1. BEV candidate render is clear.
2. Candidate id matches the candidate table.
3. Selected candidate is near unknown exploration space.
4. `target_language` is correct: `Go to candidate <id>.`
5. Warning/reject volume is acceptable.
6. RGB/depth/pointcloud are from real Isaac/Omniverse sensors.
7. No geometry proxy data is present.
8. A1 trajectory is continuous.
9. No collision, stuck, or falling is present.
10. Repeated viewpoints or spinning-in-place behavior are not excessive.
11. Decide whether the data can enter VLM SFT dataset preparation.

## Review Decision Template

- approve_for_sft_preparation: yes/no/unsure
- approve_for_gdpo_preparation: yes/no/unsure
- need_more_rollout_data: yes/no
- need_sensor_fix: yes/no
- need_candidate_fix: yes/no
- reviewer_notes:

## Audit Output Paths

- dataset_quality_summary: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/summary/dataset_quality_summary.json
- start_quality_summary: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/summary/start_quality_summary.csv
- failure_reason_summary: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/summary/failure_reason_summary.csv
- accepted_samples: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/quality/accepted_samples.jsonl
- warning_samples: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/quality/warning_samples.jsonl
- rejected_samples: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/quality/rejected_samples.jsonl
- plots_path: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/plots

## Guardrail

This packet does not approve training. `training_ready` remains false until a human reviewer explicitly approves a later preparation phase.
