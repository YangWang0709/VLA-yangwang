# Critic Report

## Current Phase

Phase 5.5 robot platform correction audit

## Corrected Fact

The USD scene's real robot is `/World/A1`, not Go2.

## Mainline Correction

- corrected_project_name: A1-VLM-LA Explorer for 3D Active Exploration
- corrected_robot_platform: unitree_a1
- corrected_robot_source: existing_usd_prim
- a1_root_prim: /World/A1
- output_contract: Go to candidate <id>.

## Audit Findings

- Phase 3 actual robot source: temporary_go2_proxy
- Phase 4 actual robot source: temporary_go2_proxy
- Phase 5 actual robot source: not_found_in_current_repo
- Phase 3/4 validity: valid_as_proxy_pipeline_smoke
- Phase 5 data usable: false
- Valid as final A1 data: false
- Rerun needed for A1: true

## Risk Correction

The previous Go2 label is now considered a target/platform label used during proxy smoke, not evidence of a verified Go2 asset in the USD. Future formal data must use `/World/A1` with:

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
```

Old proxy data must stay labeled as:

```yaml
robot_platform: temporary_quadruped_proxy
robot_source: temporary_go2_proxy
not_final_robot_asset: true
```

## Prohibited Work Check

- VLM training performed: false
- RL training performed: false
- map_predict training performed: false
- PI/openpi fine-tuning performed: false
- Phase 6 performed: false
- rollout performed: false
- historical CSV/JSONL rows modified: false
- Phase 3/4 run results deleted: false
- original USD saved or overwritten: false
- large files committed: false

## Decision

Do not enter Phase 6 yet. Rerun Phase 3 through Phase 5 using explicit `/World/A1`, unless the user explicitly chooses to continue with proxy-only data.
