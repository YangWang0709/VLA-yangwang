# MapPredict Plan

phase: MapPredict Phase 0
project_name: A1-VLM-LA Explorer
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
module_name: map_predict
module_role: SceneSense-style feature provider
planner: false
VLA: false
training_started: false
rollout_started: false
GDPO_started: false

## Objective

Implement a map_predict module that consumes partial 3D occupancy and returns
predicted occupancy plus uncertainty. The output is intended to enrich frontier
and candidate features for later planners or VLM-LA interfaces. It does not
select actions by itself.

## Phase 0 Scope

* Audit whether current real-sensor rollout data can produce map_predict samples.
* Define the canonical sample schema.
* Create engineering skeleton files under `map_predict/`.
* Create draft configs under `configs/map_predict/`.
* Document the interface between occupancy completion and downstream frontier features.

## Planned Phases

1. Phase 0: data audit and format design.
2. Phase 1: generate full occupancy GT by dense scan or USD voxelization.
3. Phase 2: build offline map_predict dataset shards.
4. Phase 3: train a small 3D occupancy completion baseline only after approval.
5. Phase 4: expose uncertainty BEV and candidate-level feature enrichment.
6. Phase 5: evaluate closed-loop impact without changing the VLM output contract.

## Non-Goals

* No VLM training.
* No SFT or GDPO.
* No rollout.
* No planner implementation.
* No mutation of Phase 8, Phase G, Phase 9, Phase H, or Phase 10 source data.
