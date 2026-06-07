# Active Task Board

## Current Phase

Phase 1: USD scene bundle placement and Git ignore.

## Workspace

`/home/ubuntu22/VLA`

## Main Goal

Go2-VLM-LA Explorer for 3D Active Exploration.

## Output Contract

`Go to candidate <id>.`

## Phase 1 Tasks

- [x] Activate `env_isaaclab` in `/home/ubuntu22/VLA`.
- [x] Check whether the target USD already exists.
- [x] Copy the full scene bundle from `/home/ubuntu22/pi/scenes/primary_building_scene_repaired/` because the target USD was missing.
- [x] Confirm target USD exists at `/home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd`.
- [x] Confirm `dependencies/` exists.
- [x] Confirm scene bundle is ignored by Git.
- [x] Confirm Git is not tracking files larger than 50MB.
- [x] Generate `runs/SCENE_BUNDLE_PLACEMENT_REPORT.md`.

## Safety Status

- training: false
- RL: false
- map_predict: false
- PI/openpi fine-tuning: false
- Go2 locomotion training: false
- rollout: false
- scene bundle committed: false

## Next Phase

Phase 2: Isaac headless scene open + Go2 stage inspection smoke.
