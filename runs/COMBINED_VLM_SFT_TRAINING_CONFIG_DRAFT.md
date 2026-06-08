# Combined VLM SFT Training Config Draft

phase: Phase 10 combined SFT dataset preparation only
draft_only: true
training_started: false
SFT_started: false
GDPO_started: false
checkpoint_created: false
requires_user_approval_before_training: true

## Model Candidates

* Qwen2.5-VL-7B-Instruct for debug
* Qwen2.5-VL-32B-Instruct as main model
* Qwen2.5-VL-72B-Instruct optional strong baseline

## Training Method

* LoRA / QLoRA
* no full fine-tune in first stage

## Input

* BEV candidate render
* optional RGB observation
* candidate table text

## Output

* Go to candidate <id>.

## Dataset Paths

* sft_samples: /home/ubuntu22/VLA/runs/phase10_combined_sft_dataset_preparation_20260608_193108/dataset/sft_samples.jsonl
* train: /home/ubuntu22/VLA/runs/phase10_combined_sft_dataset_preparation_20260608_193108/splits/train.jsonl
* val: /home/ubuntu22/VLA/runs/phase10_combined_sft_dataset_preparation_20260608_193108/splits/val.jsonl
* test: /home/ubuntu22/VLA/runs/phase10_combined_sft_dataset_preparation_20260608_193108/splits/test.jsonl

## Metrics

* exact_candidate_id_accuracy
* parse_success_rate
* valid_output_rate
* invalid_output_rate
* candidate_id_exists_rate
* score_regret
* selected_candidate_valid_rate

## Dataset Counts

* sft_sample_count: 273
* train_sample_count: 161
* val_sample_count: 56
* test_sample_count: 56
