# Robot Platform Correction Audit

phase: Phase 5.5 robot platform correction audit
workspace: /home/ubuntu22/VLA
current_fact: USD real robot is /World/A1
previous_label: Go2 / temporary_go2_proxy
corrected_project_name: A1-VLM-LA Explorer for 3D Active Exploration
corrected_robot_platform: unitree_a1
corrected_robot_source: existing_usd_prim
a1_root_prim: /World/A1
output_contract: Go to candidate <id>.

## Audit Scope

This audit checks Phase 3 through Phase 5 robot-source metadata without deleting results, rerunning smoke tests, modifying the original USD, or editing historical CSV/JSONL rows.

## Phase 3 Actual Robot Source

phase3_actual_robot_source: temporary_go2_proxy
phase3_root_prim: /World/TemporaryGo2Proxy
phase3_robot_platform_metadata: Unitree Go2 target label, not verified USD Go2
phase3_not_final_robot_asset: true
phase3_actual_data_type: proxy sensor smoke
phase3_evidence:
- runs/GO2_SENSOR_SMOKE_REPORT.md records `robot_source: temporary_go2_proxy`.
- runs/phase3_go2_sensor_smoke_20260607_190528/sensor_smoke/go2_sensor_smoke_summary.json records `go2_root_prim: /World/TemporaryGo2Proxy`.

## Phase 4 Actual Robot Source

phase4_actual_robot_source: temporary_go2_proxy
phase4_root_prim: /World/TemporaryGo2Proxy
phase4_robot_platform_metadata: Unitree Go2 target label, not verified USD Go2
phase4_not_final_robot_asset: true
phase4_actual_data_type: proxy mapping smoke
phase4_evidence:
- runs/GO2_MAPPING_SMOKE_REPORT.md records `robot_source: temporary_go2_proxy`.
- runs/phase4_go2_mapping_smoke_20260607_191104/summary/mapping_summary.json records `robot_source: temporary_go2_proxy`.

## Phase 5 Actual Robot Source

phase5_actual_robot_source: not_found_in_current_repo
phase5_root_prim: null
phase5_artifacts_found: false
phase5_files_checked:
- runs/GO2_CANDIDATE_GAIN_REPORT.md: missing
- phase5 run directory: missing
- candidate_summary.csv: missing
- candidate_steps.jsonl: missing

## Judgment

phase3_to_phase5_validity: incomplete_proxy_pipeline_smoke
phase3_phase4_validity: valid_as_proxy_pipeline_smoke
phase5_validity: not_available
not_valid_as_final_a1_data: true
whether_phase5_data_is_usable: false
whether_rerun_needed: true
rerun_needed_for_a1: true

The existing Phase 3 and Phase 4 results are still useful as proxy pipeline smoke tests. They are not valid as final `/World/A1` robot data. Phase 5 artifacts are not present in the current repository, so there is no Phase 5 candidate data to use or correct.

## Corrected Naming Rules

From this point forward, the formal project route is:

```text
A1-VLM-LA Explorer for 3D Active Exploration
```

Correct robot fields for formal USD robot runs:

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
```

Correct fields for old proxy results:

```yaml
robot_platform: temporary_quadruped_proxy
robot_source: temporary_go2_proxy
not_final_robot_asset: true
```

Do not claim that the USD contains a verified Go2 robot unless a real Go2 asset is provided or substituted later.

## Next Action

next_action: rerun Phase 3 through Phase 5 using explicit `/World/A1` root prim before entering Phase 6.
next_phase: rerun Phase 3-5 using /World/A1, or explicitly continue as proxy only
phase6_status: paused

## Negative Scope Confirmed

- VLM training: false
- RL training: false
- map_predict training: false
- PI/openpi fine-tuning: false
- Phase 6 execution: false
- rollout: false
- original USD overwritten: false
- Phase 3-5 results deleted: false
- historical CSV/JSONL rows modified: false
- large files committed: false
