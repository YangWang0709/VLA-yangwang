# Combined VLM SFT Evaluation Protocol

phase: Phase 10 combined SFT dataset preparation only
project_name: A1-VLM-LA Explorer
output_contract: Go to candidate <id>.
training_started: false
SFT_started: false
GDPO_started: false

## Offline Metrics

1. Parse success rate
2. Exact candidate id accuracy
3. Candidate id exists rate
4. Selected candidate validity rate
5. Score regret
6. Top-k agreement with classical selector
7. Invalid output rate
8. Coordinate / velocity / joint-action rejection rate
9. Per-scene accuracy
10. Old-scene vs new-scene generalization
11. Later closed-loop coverage evaluation

## Hard Rejection Rules

Any output that contains coordinates, velocity commands, joint actions, or any
format other than `Go to candidate <id>.` is invalid for this project contract.
