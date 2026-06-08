# VLM-LA Dataset Spec

## Project Route

A1-VLM-LA Explorer for 3D Active Exploration

## Current New Scene Dataset Status

```yaml
current_scene_id: building_scene_1_scene_20260608_171052
current_scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
original_user_usd_path: /home/ubuntu22/VLA/building_scene(1).usd
current_scene_phase: New Scene Phase G long rollout data collection
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
map_update_source: depth_backprojection_pointcloud
candidate_data_source: online_new_scene_real_sensor_candidate_generation
vlm_output_mode: pseudo_from_classical_selector
output_contract: Go to candidate <id>.
training_ready: false
requires_human_review: true
safe_to_human_review: true
next_phase: New Scene Phase H dataset quality audit / human review packet
dataset_name: new_scene_building_scene_1_a1_vlm_la_real_sensor_rollout_v0
sample_format: vlm_la_jsonl
sample_file: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/samples/vlm_la_samples.jsonl
dataset_manifest: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/samples/dataset_manifest.json
phaseG_status: passed
```

## Phase G Sample Metadata

Each sample records real RGB-D metadata, depth_backprojection pointcloud stats,
BEV map and candidate image references, candidate table data, selected candidate
ID, target language, parser and validator results, target pose lookup, movement
result, map statistics, and failure reason if present.

## Training Gate

training_ready: false
requires_human_review: true

Do not use new-scene data for SFT, GDPO, RL, or any training until a later
explicit human review approves preparation.
