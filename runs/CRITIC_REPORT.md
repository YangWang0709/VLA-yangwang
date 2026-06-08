# Critic Report

## Current Phase

New Scene Phase G long rollout data collection

## Finding

status: passed

New Scene Phase G used the repaired new scene, existing `/World/A1`, real
Isaac/Omniverse RGB-D observations, depth_backprojection pointclouds, online
candidate generation, pseudo VLM command labels, parser/validator checks, and
kinematic A1 root movement. It did not use geometry proxy, mounted proxy, old
scene data, Go2 labels, real VLM inference, or any training route.

## Evidence

- scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
- run_dir: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904
- dataset_manifest: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/samples/dataset_manifest.json
- vlm_la_samples: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/samples/vlm_la_samples.jsonl
- safe_to_human_review: true
- start_count: 10
- completed_start_count: 10
- max_actions_per_start: 20
- total_action_count: 200
- candidate_rows: 4800
- vlm_la_sample_count: 200
- average_final_known_ratio: 0.408687
- average_known_ratio_gain: 0.408687
- parse_success_rate: 1.0
- validation_success_rate: 1.0
- movement_success_rate: 1.0
- starts_with_failures: 0
- collision_count: 0
- stuck_count: 0
- falling_count: 0
- real_rgb_sensor_valid_rate: 1.0
- real_depth_sensor_valid_rate: 1.0
- real_camera_pointcloud_valid_rate: 1.0


## Risks / Gates

- Samples are not training-ready and require Phase H human review.
- VLM commands are pseudo labels from a classical selector; no real VLM inference was run.
- Movement uses a kinematic root wrapper, not an A1 locomotion controller.

training: false
RL: false
SFT: false
GDPO: false
map_predict: false
real_VLM_inference: false
USD_modified_or_saved: false
