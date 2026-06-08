# Critic Report

## Current Phase

New Scene Phase D candidate viewpoint + information gain smoke

## Finding

status: passed

Candidate viewpoint generation and classical information gain scoring used the new-scene real RGB-D/depth_backprojection BEV map. No Go2 label, old scene data, proxy map, or geometry proxy was used.

## Evidence

- scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
- a1_root_prim: /World/A1
- sensor_method: real_isaac_omniverse_rgbd
- map_update_source: depth_backprojection_pointcloud
- candidate_sampling_method: radial_24_candidates_3_radii_8_angles_around_a1_base
- path_cost_method: astar_bev_grid_unknown_penalty
- information_gain_method: real_sensor_bev_unknown_visibility
- candidate_count_per_step: 24
- valid_candidate_ratio: 0.8819
- positive_gain_candidate_ratio: 0.8819
- selected_is_top_score_rate: 1.0
- safe_to_interface: true

## Risks / Gates

- This is classical candidate-gain smoke, not VLM inference.
- Phase E may consume the candidate id contract but should not train or roll out.
- Do not start Phase E unless `safe_to_interface` is true.

training: false
RL: false
SFT: false
GDPO: false
rollout: false
USD_modified_or_saved: false
