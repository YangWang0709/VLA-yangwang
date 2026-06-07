# Phase Plan

## Phase 0: VLA workspace initialization

Create `/home/ubuntu22/VLA`, audit the environment, create the directory structure, create project specs, and commit the safety baseline.

## Phase 1: USD scene bundle placement and Git ignore

Place the full primary scene bundle under `scenes/primary_building_scene_repaired/` if needed. Keep the bundle ignored by Git.

## Phase 2: Isaac headless scene open and Go2 stage inspection smoke

Open the primary USD scene headlessly and inspect the stage for an existing Unitree Go2 hierarchy.

## Phase 3: Unitree Go2 sensor smoke

Use the existing USD Go2 when available. Validate base pose, sensor/proxy observation, and short safe actions.

## Phase 4: Go2 primary-scene mapping smoke

Build a partial BEV occupancy/explored map from pose plus depth/pointcloud/proxy observations.

## Phase 5: Candidate viewpoint and information gain smoke

Generate candidate viewpoints, stable IDs, path costs, information gain, scores, and BEV overlays.

## Phase 6: VLM-LA interface smoke

Validate language output and parser only. No VLM training.

## Phase 7: Go2 VLM-LA closed-loop smoke

Run a short loop using pseudo VLM output from the classical selected candidate.

## Phase 8: Primary-scene VLM-LA long rollout data collection

Collect data prototypes only. No training.

## Phase 9: Human review packet

Prepare review artifacts and quality summaries.

## Phase 10: VLM fine-tuning preparation only

Prepare training configuration only after human review approval. Do not train unless explicitly approved.
