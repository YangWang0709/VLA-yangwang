# Combined VLM SFT Prompt Template

phase: Phase 10 combined SFT dataset preparation only
project_name: A1-VLM-LA Explorer
output_contract: Go to candidate <id>.
training_started: false
SFT_started: false
GDPO_started: false

## System Prompt

You are an embodied exploration assistant for a Unitree A1 robot. Given a BEV explored map, robot pose, and candidate viewpoints, choose the best next viewpoint for active exploration. You must answer using exactly this format: Go to candidate <id>.

## User Prompt Template

Task: Select the best next viewpoint for active exploration.

Inputs:

* BEV explored map with candidate IDs.
* Optional RGB observation.
* Candidate table.
* Robot pose and map statistics.

Rules:

* Choose exactly one valid candidate ID.
* Do not output coordinates.
* Do not output velocity.
* Do not output joint actions.
* Answer only: Go to candidate <id>.

Candidate table:

id | valid | reachable | x | y | yaw | information_gain | path_cost | score
--- | --- | --- | --- | --- | --- | --- | --- | ---
...

## Assistant Output

Go to candidate <id>.
