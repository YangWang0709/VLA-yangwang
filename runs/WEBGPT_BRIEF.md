# WEBGPT Brief

## Current Phase

Phase 5 A1 candidate viewpoint + information gain smoke

## Workspace

/home/ubuntu22/VLA

## Main Goal

A1-VLM-LA Explorer for 3D Active Exploration

## Output Contract

Go to candidate <id>.

## Robot Platform

robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base

## Completed

- Created `scripts/phase5_a1_candidate_gain_smoke.py`.
- Opened the primary USD scene without saving or overwriting it.
- Used the existing `/World/A1` prim and `/World/A1/base` frame.
- Rebuilt a proxy BEV partial map from A1 base pose observations.
- Generated 24 candidate viewpoints per step across 6 steps.
- Computed approximate validity, reachability, path cost, BEV unknown visibility, information gain, and classical score.
- Generated lightweight BEV candidate overlay renders under the Phase 5 run directory.
- Wrote `runs/A1_CANDIDATE_GAIN_REPORT.md`.

## Phase 5 Metrics

run_dir: /home/ubuntu22/VLA/runs/phase5_a1_candidate_gain_smoke_20260607_195140
step_count: 6
candidate_count_per_step: 24
total_candidate_rows: 144
valid_candidate_ratio: 0.3958
positive_gain_candidate_ratio: 0.8056
selected_candidate_valid_rate: 1.0
selected_is_top_score_rate: 1.0
path_cost_constant: false
min_path_cost: 0.9
max_path_cost: 6.98
min_information_gain: 0.0
max_information_gain: 406.0
failure_count: 0
safe_to_continue_phase6: true

## Key Caveats

- Phase 5 is proxy-mapping based candidate smoke, not final real-sensor data.
- No VLM inference or VLM-LA interface smoke was run.
- Candidate scoring is classical and uses BEV proxy information gain.

## Negative Scope

- training: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- A1_locomotion_training: false
- VLM_inference: false
- primary_rollout: false
- Phase_6_executed: false

## Next Step

Phase 6 VLM-LA interface smoke, only when explicitly requested.
