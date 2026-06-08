# New Scene Dataset Quality Report

phase: New Scene Phase H
source phase: New Scene Phase G
source run_dir: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904
scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
robot_platform: unitree_a1
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
geometry_proxy_used: false
mounted_geometry_proxy_used: false
total_samples: 200
accepted_sample_count: 199
warning_sample_count: 1
rejected_sample_count: 0
acceptance_rate: 0.995
warning_rate: 0.005
rejection_rate: 0.0
parse_success_rate: 1.0
validation_success_rate: 1.0
movement_success_rate: 1.0
real_sensor_sample_rate: 1.0
average_final_known_ratio: 0.408687
main warning reasons: occupied_cells_zero (1)
main rejection reasons: none
plots path: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/plots
accepted samples path: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/quality/accepted_samples.jsonl
warning samples path: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/quality/warning_samples.jsonl
rejected samples path: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/quality/rejected_samples.jsonl
training_ready: false
requires_human_review: true
recommended_next_phase: manual_review_before_sft_preparation

## Interpretation

- Automated audit completed without modifying Phase G source rows.
- Accepted samples pass all automated quality gates.
- Warning samples require manual attention but are not automatically rejected.
- Rejected samples must not enter SFT/GDPO preparation unless manually repaired and re-audited.
- This report keeps `training_ready: false`; a human review decision is required before SFT preparation.

## Negative Scope

- No training, SFT, GDPO, RL, map_predict, real VLM inference, checkpoint creation, or USD save.
- No repaired USD bundle, dependencies, mesh, texture, raw RGB-D, npz/hdf5, checkpoint, or core dump is included.
