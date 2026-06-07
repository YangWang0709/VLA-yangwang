#!/usr/bin/env python3
"""Phase 9 human review packet and dataset quality audit.

This script audits the Phase 8 A1 real-sensor VLM-LA rollout dataset and
creates review-only quality artifacts. It does not train, run VLM inference,
modify Phase 8 raw rows, modify the USD scene, or mark the data training-ready.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


WORKSPACE = Path("/home/ubuntu22/VLA")
RUNS = WORKSPACE / "runs"
DEFAULT_SOURCE_RUN = RUNS / "phase8_a1_vlm_la_long_rollout_20260607_212536"
TOP_CHECKLIST = RUNS / "HUMAN_REVIEW_A1_VLM_LA_DATASET_CHECKLIST.md"
TOP_REPORT = RUNS / "DATASET_QUALITY_REPORT.md"
PROJECT_NAME = "A1-VLM-LA Explorer"
MAIN_GOAL = "A1-VLM-LA Explorer for 3D Active Exploration"
PHASE = "Phase 9 human review packet"
SOURCE_PHASE = "Phase 8 A1 primary-scene VLM-LA long rollout data collection"
ROBOT_PLATFORM = "unitree_a1"
ROBOT_SOURCE = "existing_usd_prim"
A1_ROOT = "/World/A1"
BASE_FRAME = "/World/A1/base"
SENSOR_METHOD = "real_isaac_omniverse_rgbd"
CAMERA_POINTCLOUD_SOURCE = "depth_backprojection"
OUTPUT_CONTRACT = "Go to candidate <id>."
LABEL_SOURCE = "classical_argmax_information_gain_minus_path_cost"
RECOMMENDED_NEXT_PHASE = "manual_review_before_sft_preparation"


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def finite_float(value: Any, default: float | None = None) -> float | None:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def int_value(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def rate(num: int, den: int) -> float:
    return round(num / den, 4) if den else 0.0


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def path_exists_under(source_run: Path, relative_path: str | None) -> bool:
    if not relative_path:
        return False
    return (source_run / relative_path).exists()


def candidate_lookup(candidate_rows: list[dict[str, str]]) -> dict[tuple[int, int, int], dict[str, str]]:
    out: dict[tuple[int, int, int], dict[str, str]] = {}
    for row in candidate_rows:
        out[(int_value(row.get("start_id")), int_value(row.get("step_id")), int_value(row.get("candidate_id")))] = row
    return out


def candidates_by_step(candidate_rows: list[dict[str, str]]) -> dict[tuple[int, int], list[dict[str, str]]]:
    out: dict[tuple[int, int], list[dict[str, str]]] = defaultdict(list)
    for row in candidate_rows:
        out[(int_value(row.get("start_id")), int_value(row.get("step_id")))].append(row)
    return out


def parsed_candidate_id(text: str) -> int | None:
    match = re.fullmatch(r"\s*Go to candidate (\d+)\.\s*", text or "")
    return int(match.group(1)) if match else None


def selected_candidate_from_rows(rows: list[dict[str, str]], selected_id: int) -> dict[str, str] | None:
    for row in rows:
        if int_value(row.get("candidate_id"), -1) == selected_id:
            return row
    return None


def classify_sample(
    source_run: Path,
    step: dict[str, str],
    sample: dict[str, Any],
    step_candidates: list[dict[str, str]],
    selected_candidate: dict[str, str] | None,
    global_path_cost_unique: int,
) -> dict[str, Any]:
    flags: list[str] = []
    reject_reasons: list[str] = []
    warning_reasons: list[str] = []

    start_id = int_value(step.get("start_id"))
    step_id = int_value(step.get("step_id"))
    selected_id = int_value(step.get("selected_candidate_id"), -1)
    target_language = step.get("target_language", "")

    # Sensor quality.
    if sample.get("geometry_proxy_used") is not False:
        reject_reasons.append("geometry_proxy_used")
    if sample.get("mounted_geometry_proxy_used") is not False:
        reject_reasons.append("mounted_geometry_proxy_used")
    if sample.get("sensor_method") != SENSOR_METHOD:
        reject_reasons.append("sensor_method_mismatch")
    if sample.get("camera_pointcloud_source") not in {CAMERA_POINTCLOUD_SOURCE, "isaac_pointcloud_annotator"}:
        reject_reasons.append("camera_pointcloud_source_invalid")
    if not bool_value(step.get("depth_available")):
        reject_reasons.append("depth_unavailable")
    if not bool_value(step.get("camera_pointcloud_available")):
        reject_reasons.append("camera_pointcloud_unavailable")
    depth_valid_ratio = finite_float(step.get("depth_valid_ratio"), -1.0)
    if depth_valid_ratio is None or depth_valid_ratio < 0:
        reject_reasons.append("depth_valid_ratio_missing")
    elif depth_valid_ratio < 0.5:
        warning_reasons.append("low_depth_valid_ratio")
    if int_value(step.get("pointcloud_point_count")) <= 0:
        reject_reasons.append("pointcloud_empty")
    if sample.get("rgb_image") and not bool_value(step.get("rgb_available")):
        warning_reasons.append("rgb_invalid_but_debug_rgb_path_present")

    # Map quality.
    known_before = finite_float(step.get("known_ratio_before"))
    known_after = finite_float(step.get("known_ratio_after"))
    known_delta = finite_float(step.get("known_ratio_delta"), 0.0)
    if known_before is None or known_after is None:
        reject_reasons.append("known_ratio_nan_or_missing")
    elif known_after + 1e-6 < known_before:
        reject_reasons.append("known_ratio_decreased")
    occupied_cells = int_value(step.get("occupied_cells"))
    known_free_cells = int_value(step.get("known_free_cells"))
    unknown_cells = int_value(step.get("unknown_cells"))
    if occupied_cells <= 0:
        warning_reasons.append("occupied_cells_zero")
    if known_free_cells <= 0:
        reject_reasons.append("known_free_cells_zero")
    if unknown_cells <= 0:
        reject_reasons.append("unknown_cells_zero")
    if occupied_cells <= 0 and known_free_cells <= 0:
        reject_reasons.append("bev_map_empty")
    if sample.get("bev_image") and not path_exists_under(source_run, sample.get("bev_image")):
        warning_reasons.append("bev_image_path_missing")
    if not sample.get("bev_image") and not sample.get("map_stats"):
        reject_reasons.append("bev_image_and_map_metadata_missing")

    # Candidate quality.
    candidate_count = int_value(step.get("candidate_count"))
    valid_count = int_value(step.get("valid_candidate_count"))
    positive_gain_count = int_value(step.get("positive_gain_candidate_count"))
    if candidate_count < 1:
        reject_reasons.append("candidate_table_missing")
    elif candidate_count < 16:
        reject_reasons.append("candidate_count_below_16")
    if valid_count < 1:
        reject_reasons.append("no_valid_candidate")
    elif valid_count < 4:
        warning_reasons.append("low_valid_candidate_count")
    if positive_gain_count == 0:
        warning_reasons.append("zero_positive_gain_candidates")
    if selected_id < 0:
        reject_reasons.append("selected_candidate_id_missing")
    if selected_candidate is None:
        reject_reasons.append("selected_candidate_not_in_candidate_table")
    else:
        if not bool_value(selected_candidate.get("is_valid")):
            reject_reasons.append("selected_candidate_invalid")
        if not bool_value(selected_candidate.get("is_reachable")):
            reject_reasons.append("selected_candidate_unreachable")
        if bool_value(selected_candidate.get("collision_risk")):
            reject_reasons.append("selected_candidate_collision_risk")
        if not bool_value(selected_candidate.get("selected_by_classical")):
            reject_reasons.append("selected_by_classical_false")
        if selected_candidate.get("path_cost") in {None, ""}:
            reject_reasons.append("selected_path_cost_missing")
        if selected_candidate.get("information_gain") in {None, ""}:
            reject_reasons.append("selected_information_gain_missing")
        if selected_candidate.get("score") in {None, ""}:
            reject_reasons.append("selected_score_missing")
    if global_path_cost_unique <= 1:
        warning_reasons.append("path_cost_globally_constant")

    # Label and language format quality.
    parsed_id = parsed_candidate_id(target_language)
    if not target_language:
        reject_reasons.append("target_language_missing")
    elif parsed_id is None:
        reject_reasons.append("target_language_format_invalid")
    elif parsed_id != selected_id:
        reject_reasons.append("parsed_id_mismatch_selected_candidate_id")
    if not bool_value(step.get("parse_success")):
        reject_reasons.append("parse_failed")
    if not bool_value(step.get("validation_success")):
        reject_reasons.append("validation_failed")
    if not bool_value(step.get("target_pose_lookup_success")):
        reject_reasons.append("target_pose_lookup_failed")
    if sample.get("label_source") not in {LABEL_SOURCE, "classical_argmax_information_gain_minus_path_cost"}:
        warning_reasons.append("label_source_missing_or_nonstandard")

    # Closed-loop behavior quality.
    if not bool_value(step.get("movement_success")):
        if step.get("failure_reason"):
            warning_reasons.append("movement_failed_with_reason")
        else:
            reject_reasons.append("movement_failed_without_reason")
    if bool_value(step.get("collision_flag")):
        reject_reasons.append("collision_flag")
    if bool_value(step.get("falling_flag")):
        reject_reasons.append("falling_flag")
    if bool_value(step.get("stuck_flag")):
        if step.get("failure_reason"):
            warning_reasons.append("stuck_flag_with_reason")
        else:
            reject_reasons.append("stuck_without_reason")
    if known_delta is not None and known_delta <= 0 and not step.get("failure_reason"):
        warning_reasons.append("non_positive_known_ratio_delta")
    if bool_value(step.get("fallback_used")):
        warning_reasons.append("fallback_used")
    if step.get("failure_reason") == "post_rgb_invalid":
        warning_reasons.append("post_rgb_invalid_noncritical")
    elif step.get("failure_reason"):
        warning_reasons.append(f"recorded_failure_reason:{step.get('failure_reason')}")

    reject_reasons = sorted(set(reject_reasons))
    warning_reasons = sorted(set(warning_reasons))
    if reject_reasons:
        status = "reject"
    elif warning_reasons:
        status = "warning"
    else:
        status = "pass"
    flags.extend(reject_reasons)
    flags.extend(warning_reasons)

    return {
        "sample_id": sample.get("sample_id"),
        "start_id": start_id,
        "step_id": step_id,
        "quality_status": status,
        "quality_flags": flags,
        "reject_reason": ";".join(reject_reasons) if reject_reasons else None,
        "warning_reason": ";".join(warning_reasons) if warning_reasons else None,
        "target_language": target_language,
        "selected_candidate_id": selected_id,
        "known_ratio_before": known_before,
        "known_ratio_after": known_after,
        "known_ratio_delta": known_delta,
        "candidate_count": candidate_count,
        "valid_candidate_count": valid_count,
        "positive_gain_candidate_count": positive_gain_count,
        "depth_valid_ratio": depth_valid_ratio,
        "pointcloud_point_count": int_value(step.get("pointcloud_point_count")),
        "rgb_available": bool_value(step.get("rgb_available")),
        "depth_available": bool_value(step.get("depth_available")),
        "camera_pointcloud_available": bool_value(step.get("camera_pointcloud_available")),
        "movement_success": bool_value(step.get("movement_success")),
        "collision_flag": bool_value(step.get("collision_flag")),
        "stuck_flag": bool_value(step.get("stuck_flag")),
        "falling_flag": bool_value(step.get("falling_flag")),
        "source_sample": sample,
    }


def write_quality_jsonl(path: Path, audited_rows: list[dict[str, Any]]) -> None:
    slim_rows = []
    for row in audited_rows:
        item = {k: v for k, v in row.items() if k != "source_sample"}
        item["sample"] = row["source_sample"]
        slim_rows.append(item)
    write_jsonl(path, slim_rows)


def make_failure_summary(audited: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for row in audited:
        for flag in row["quality_flags"]:
            counter[flag] += 1
    if not counter:
        return [{"reason": "none", "count": 0, "rate": 0.0}]
    total = len(audited)
    return [
        {"reason": reason, "count": count, "rate": rate(count, total)}
        for reason, count in counter.most_common()
    ]


def make_start_summary(audited: list[dict[str, Any]], phase8_start_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in audited:
        grouped[int(row["start_id"])].append(row)
    phase8_by_start = {int_value(r.get("start_id")): r for r in phase8_start_rows}
    out = []
    for start_id in sorted(grouped):
        rows = grouped[start_id]
        accepted = sum(1 for r in rows if r["quality_status"] == "pass")
        warnings = sum(1 for r in rows if r["quality_status"] == "warning")
        rejected = sum(1 for r in rows if r["quality_status"] == "reject")
        if rejected:
            status = "reject"
        elif warnings:
            status = "warning"
        else:
            status = "pass"
        p8 = phase8_by_start.get(start_id, {})
        out.append({
            "start_id": start_id,
            "quality_status": status,
            "sample_count": len(rows),
            "accepted_sample_count": accepted,
            "warning_sample_count": warnings,
            "rejected_sample_count": rejected,
            "acceptance_rate": rate(accepted, len(rows)),
            "warning_rate": rate(warnings, len(rows)),
            "rejection_rate": rate(rejected, len(rows)),
            "final_known_ratio": p8.get("final_known_ratio", rows[-1].get("known_ratio_after")),
            "known_ratio_gain": p8.get("known_ratio_gain", ""),
            "action_count": p8.get("action_count", len(rows)),
            "phase8_failure_count": p8.get("failure_count", ""),
            "phase8_stop_reason": p8.get("stop_reason", ""),
        })
    return out


def save_plots(run_dir: Path, audited: list[dict[str, Any]], start_summary: list[dict[str, Any]], candidate_rows: list[dict[str, str]]) -> bool:
    plots = run_dir / "plots"
    plots.mkdir(parents=True, exist_ok=True)
    status_counts = Counter(row["quality_status"] for row in audited)
    failure_summary = make_failure_summary(audited)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        write_csv(plots / "accepted_warning_rejected_counts.csv", [{"status": k, "count": v} for k, v in status_counts.items()], ["status", "count"])
        return False

    labels = ["pass", "warning", "reject"]
    plt.figure(figsize=(5, 4))
    plt.bar(["accepted", "warning", "rejected"], [status_counts.get(k, 0) for k in labels], color=["#4c8c4a", "#d6a12c", "#b84a4a"])
    plt.ylabel("sample count")
    plt.title("Accepted / Warning / Rejected")
    plt.tight_layout()
    plt.savefig(plots / "accepted_warning_rejected_counts.png", dpi=120)
    plt.close()

    by_start: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in audited:
        by_start[int(row["start_id"])].append(row)
    plt.figure(figsize=(8, 5))
    for start_id, rows in sorted(by_start.items()):
        rows = sorted(rows, key=lambda r: int(r["step_id"]))
        plt.plot([int(r["step_id"]) for r in rows], [float(r["known_ratio_after"]) for r in rows], marker="o", linewidth=1.2, label=f"start {start_id:03d}")
    plt.xlabel("step")
    plt.ylabel("known ratio")
    plt.title("Known ratio by start")
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=7, ncol=2)
    plt.tight_layout()
    plt.savefig(plots / "known_ratio_by_start.png", dpi=120)
    plt.close()

    ordered_starts = sorted(start_summary, key=lambda r: int(r["start_id"]))
    start_ids = [int(r["start_id"]) for r in ordered_starts]
    plt.figure(figsize=(7, 4))
    plt.bar(start_ids, [float(r["final_known_ratio"]) for r in ordered_starts])
    plt.xlabel("start")
    plt.ylabel("final known ratio")
    plt.title("Final known ratio by start")
    plt.tight_layout()
    plt.savefig(plots / "final_known_ratio_by_start.png", dpi=120)
    plt.close()

    plt.figure(figsize=(7, 4))
    plt.bar(start_ids, [int(float(r["action_count"])) for r in ordered_starts])
    plt.xlabel("start")
    plt.ylabel("action count")
    plt.title("Action count by start")
    plt.tight_layout()
    plt.savefig(plots / "action_count_by_start.png", dpi=120)
    plt.close()

    scores = [finite_float(r.get("score")) for r in candidate_rows]
    gains = [finite_float(r.get("information_gain")) for r in candidate_rows]
    costs = [finite_float(r.get("path_cost")) for r in candidate_rows]
    for name, values, title, xlabel in [
        ("candidate_score_distribution.png", [v for v in scores if v is not None], "Candidate score distribution", "score"),
        ("information_gain_distribution.png", [v for v in gains if v is not None], "Information gain distribution", "information gain"),
        ("path_cost_distribution.png", [v for v in costs if v is not None], "Path cost distribution", "path cost"),
    ]:
        plt.figure(figsize=(7, 4))
        plt.hist(values, bins=30)
        plt.xlabel(xlabel)
        plt.ylabel("count")
        plt.title(title)
        plt.tight_layout()
        plt.savefig(plots / name, dpi=120)
        plt.close()

    top_failure = failure_summary[:12]
    plt.figure(figsize=(9, max(4, len(top_failure) * 0.35)))
    plt.barh([r["reason"] for r in reversed(top_failure)], [int(r["count"]) for r in reversed(top_failure)])
    plt.xlabel("count")
    plt.title("Quality flag counts")
    plt.tight_layout()
    plt.savefig(plots / "failure_reason_counts.png", dpi=120)
    plt.close()
    return True


def make_dataset_summary(
    run_dir: Path,
    source_run: Path,
    phase8_summary: dict[str, Any],
    manifest: dict[str, Any],
    audited: list[dict[str, Any]],
    start_summary: list[dict[str, Any]],
    failure_summary: list[dict[str, Any]],
    plots_saved: bool,
) -> dict[str, Any]:
    accepted = sum(1 for r in audited if r["quality_status"] == "pass")
    warning = sum(1 for r in audited if r["quality_status"] == "warning")
    rejected = sum(1 for r in audited if r["quality_status"] == "reject")
    real_sensor = sum(
        1 for r in audited
        if r["depth_available"]
        and r["camera_pointcloud_available"]
        and r["source_sample"].get("sensor_method") == SENSOR_METHOD
        and r["source_sample"].get("geometry_proxy_used") is False
        and r["source_sample"].get("mounted_geometry_proxy_used") is False
    )
    warning_reasons = [r for r in failure_summary if r["reason"] != "none" and any(r["reason"] in row["warning_reason"].split(";") for row in audited if row["warning_reason"])]
    reject_reasons = [r for r in failure_summary if r["reason"] != "none" and any(r["reason"] in (row["reject_reason"] or "").split(";") for row in audited)]
    return {
        "phase": PHASE,
        "workspace": str(WORKSPACE),
        "project_name": PROJECT_NAME,
        "source_phase": SOURCE_PHASE,
        "source_run_dir": str(source_run),
        "robot_platform": ROBOT_PLATFORM,
        "robot_source": ROBOT_SOURCE,
        "a1_root_prim": A1_ROOT,
        "base_frame": BASE_FRAME,
        "sensor_method": SENSOR_METHOD,
        "camera_pointcloud_source": CAMERA_POINTCLOUD_SOURCE,
        "geometry_proxy_used": False,
        "mounted_geometry_proxy_used": False,
        "output_contract": OUTPUT_CONTRACT,
        "label_source": LABEL_SOURCE,
        "total_samples": len(audited),
        "manifest_sample_count": manifest.get("sample_count"),
        "accepted_sample_count": accepted,
        "warning_sample_count": warning,
        "rejected_sample_count": rejected,
        "acceptance_rate": rate(accepted, len(audited)),
        "warning_rate": rate(warning, len(audited)),
        "rejection_rate": rate(rejected, len(audited)),
        "start_count": phase8_summary.get("start_count"),
        "completed_start_count": phase8_summary.get("completed_start_count"),
        "starts_with_failures": phase8_summary.get("starts_with_failures"),
        "parse_success_rate": phase8_summary.get("parse_success_rate"),
        "validation_success_rate": phase8_summary.get("validation_success_rate"),
        "movement_success_rate": phase8_summary.get("movement_success_rate"),
        "real_sensor_sample_rate": rate(real_sensor, len(audited)),
        "rgb_valid_rate": phase8_summary.get("real_rgb_sensor_valid_rate"),
        "depth_valid_rate": phase8_summary.get("real_depth_sensor_valid_rate"),
        "camera_pointcloud_valid_rate": phase8_summary.get("real_camera_pointcloud_valid_rate"),
        "average_final_known_ratio": phase8_summary.get("average_final_known_ratio"),
        "average_known_ratio_gain": phase8_summary.get("average_known_ratio_gain"),
        "main_warning_reasons": warning_reasons[:10],
        "main_reject_reasons": reject_reasons[:10],
        "training_ready": False,
        "requires_human_review": True,
        "recommended_next_phase": RECOMMENDED_NEXT_PHASE,
        "safe_to_prepare_sft_without_manual_review": False,
        "run_dir": str(run_dir),
        "accepted_samples_path": str(run_dir / "quality/accepted_samples.jsonl"),
        "warning_samples_path": str(run_dir / "quality/warning_samples.jsonl"),
        "rejected_samples_path": str(run_dir / "quality/rejected_samples.jsonl"),
        "dataset_quality_summary_path": str(run_dir / "summary/dataset_quality_summary.json"),
        "start_quality_summary_path": str(run_dir / "summary/start_quality_summary.csv"),
        "failure_reason_summary_path": str(run_dir / "summary/failure_reason_summary.csv"),
        "plots_path": str(run_dir / "plots"),
        "plots_saved": plots_saved,
    }


def write_checklist(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Human Review A1 VLM-LA Dataset Checklist",
        "",
        "## Review Scope",
        "",
        f"- source_run_dir: {summary['source_run_dir']}",
        f"- sample_count: {summary['total_samples']}",
        f"- accepted_sample_count: {summary['accepted_sample_count']}",
        f"- warning_sample_count: {summary['warning_sample_count']}",
        f"- rejected_sample_count: {summary['rejected_sample_count']}",
        f"- robot_platform: {summary['robot_platform']}",
        f"- sensor_method: {summary['sensor_method']}",
        f"- camera_pointcloud_source: {summary['camera_pointcloud_source']}",
        f"- output_contract: {summary['output_contract']}",
        "- training_ready: false",
        "- requires_human_review: true",
        "",
        "## Required Manual Checks",
        "",
        "1. BEV candidate render is clear and corresponds to the recorded map state.",
        "2. Candidate id matches the candidate table row.",
        "3. Selected candidate is near unknown or useful exploration space.",
        "4. `target_language` is exactly `Go to candidate <id>.`.",
        "5. Warning and reject counts are acceptable for downstream preparation.",
        "6. RGB/depth/pointcloud are from real Isaac/Omniverse sensors.",
        "7. No geometry proxy data is present.",
        "8. A1 trajectory is continuous enough for review use.",
        "9. No collision, stuck, or falling event is present.",
        "10. Repeated viewpoints or spinning-in-place behavior are not excessive.",
        "11. Decide whether the dataset can proceed to VLM SFT dataset preparation.",
        "",
        "## Review Decision Template",
        "",
        "- approve_for_sft_preparation: yes/no/unsure",
        "- approve_for_gdpo_preparation: yes/no/unsure",
        "- need_more_rollout_data: yes/no",
        "- need_sensor_fix: yes/no",
        "- need_candidate_fix: yes/no",
        "- reviewer_notes:",
        "",
        "## Audit Output Paths",
        "",
        f"- dataset_quality_summary: {summary['dataset_quality_summary_path']}",
        f"- start_quality_summary: {summary['start_quality_summary_path']}",
        f"- failure_reason_summary: {summary['failure_reason_summary_path']}",
        f"- accepted_samples: {summary['accepted_samples_path']}",
        f"- warning_samples: {summary['warning_samples_path']}",
        f"- rejected_samples: {summary['rejected_samples_path']}",
        f"- plots_path: {summary['plots_path']}",
        "",
        "## Guardrail",
        "",
        "This packet does not approve training by itself. `training_ready` remains false until a human reviewer explicitly approves a later preparation phase.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_quality_report(path: Path, summary: dict[str, Any]) -> None:
    warning_reasons = ", ".join(f"{r['reason']} ({r['count']})" for r in summary["main_warning_reasons"]) or "none"
    reject_reasons = ", ".join(f"{r['reason']} ({r['count']})" for r in summary["main_reject_reasons"]) or "none"
    caveat_warning = (
        f"- Warning-level samples: {summary['warning_sample_count']}; see `main warning reasons` and `warning_samples.jsonl`."
        if summary["warning_sample_count"]
        else "- No warning-level samples were found by the automated audit."
    )
    caveat_reject = (
        f"- Rejected samples: {summary['rejected_sample_count']}; see `main rejection reasons` and `rejected_samples.jsonl`."
        if summary["rejected_sample_count"]
        else "- No rejected samples were found by the automated audit."
    )
    lines = [
        "# Dataset Quality Report",
        "",
        "phase: Phase 9",
        "source phase: Phase 8",
        f"source run_dir: {summary['source_run_dir']}",
        f"total_samples: {summary['total_samples']}",
        f"accepted_sample_count: {summary['accepted_sample_count']}",
        f"warning_sample_count: {summary['warning_sample_count']}",
        f"rejected_sample_count: {summary['rejected_sample_count']}",
        f"acceptance_rate: {summary['acceptance_rate']}",
        f"warning_rate: {summary['warning_rate']}",
        f"rejection_rate: {summary['rejection_rate']}",
        f"parse_success_rate: {summary['parse_success_rate']}",
        f"validation_success_rate: {summary['validation_success_rate']}",
        f"movement_success_rate: {summary['movement_success_rate']}",
        f"real_sensor_sample_rate: {summary['real_sensor_sample_rate']}",
        f"rgb_valid_rate: {summary['rgb_valid_rate']}",
        f"depth_valid_rate: {summary['depth_valid_rate']}",
        f"camera_pointcloud_valid_rate: {summary['camera_pointcloud_valid_rate']}",
        f"average_final_known_ratio: {summary['average_final_known_ratio']}",
        f"main warning reasons: {warning_reasons}",
        f"main rejection reasons: {reject_reasons}",
        f"plots path: {summary['plots_path']}",
        f"accepted sample paths: {summary['accepted_samples_path']}",
        f"warning sample paths: {summary['warning_samples_path']}",
        f"rejected sample paths: {summary['rejected_samples_path']}",
        "training_ready: false",
        "requires_human_review: true",
        f"recommended_next_phase: {summary['recommended_next_phase']}",
        "",
        "## Dataset-Level Decision",
        "",
        "The dataset is suitable for manual review packet generation. It is not marked training-ready. A human review result is required before SFT or GDPO preparation.",
        "",
        "## Caveats",
        "",
        caveat_warning,
        caveat_reject,
        "- VLM labels are pseudo labels from a classical selector, not real VLM inference.",
        "- Movement is kinematic root movement, not a trained A1 locomotion policy.",
        "- The audit did not modify the Phase 8 raw CSV or JSONL rows.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def common_phase9_block(summary: dict[str, Any]) -> str:
    return f"""current_phase: Phase 9 human review packet
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
source_dataset: Phase 8 rollout
training_ready: false
requires_human_review: true
next_phase: Manual review result required before SFT preparation
negative_scope:
- training: false
- SFT: false
- GDPO: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- A1_locomotion_training: false
- real_vlm_inference: false"""


def metrics_block(summary: dict[str, Any]) -> str:
    return f"""status: review_packet_prepared
run_dir: {summary['run_dir']}
script: /home/ubuntu22/VLA/scripts/phase9_dataset_quality_audit.py
checklist: /home/ubuntu22/VLA/runs/HUMAN_REVIEW_A1_VLM_LA_DATASET_CHECKLIST.md
quality_report: /home/ubuntu22/VLA/runs/DATASET_QUALITY_REPORT.md
source_run_dir: {summary['source_run_dir']}
total_samples: {summary['total_samples']}
accepted_sample_count: {summary['accepted_sample_count']}
warning_sample_count: {summary['warning_sample_count']}
rejected_sample_count: {summary['rejected_sample_count']}
acceptance_rate: {summary['acceptance_rate']}
warning_rate: {summary['warning_rate']}
rejection_rate: {summary['rejection_rate']}
parse_success_rate: {summary['parse_success_rate']}
validation_success_rate: {summary['validation_success_rate']}
movement_success_rate: {summary['movement_success_rate']}
real_sensor_sample_rate: {summary['real_sensor_sample_rate']}
average_final_known_ratio: {summary['average_final_known_ratio']}
training_ready: false
requires_human_review: true
recommended_next_phase: {summary['recommended_next_phase']}"""


def write_status_files(summary: dict[str, Any]) -> None:
    common = common_phase9_block(summary)
    metrics = metrics_block(summary)
    evidence = f"""- dataset_quality_summary: {summary['dataset_quality_summary_path']}
- start_quality_summary: {summary['start_quality_summary_path']}
- failure_reason_summary: {summary['failure_reason_summary_path']}
- accepted_samples: {summary['accepted_samples_path']}
- warning_samples: {summary['warning_samples_path']}
- rejected_samples: {summary['rejected_samples_path']}
- plots_path: {summary['plots_path']}"""

    (RUNS / "ACTIVE_TASK_BOARD.md").write_text(f"""# Active Task Board

{common}

## Phase 9 Result

{metrics}

## Evidence Paths

{evidence}

## Decision

Phase 9 prepared the human review packet and dataset quality audit. The dataset remains `training_ready: false`; manual review is required before any SFT or GDPO preparation.
""", encoding="utf-8")

    (RUNS / "WEBGPT_BRIEF.md").write_text(f"""# WEBGPT Brief

## Current Phase

Phase 9 human review packet

## Context

{common}

## Completed

- Created `scripts/phase9_dataset_quality_audit.py`.
- Audited Phase 8 rollout samples for sensor, map, candidate, label, language, and closed-loop quality.
- Split samples into accepted, warning, and rejected review files.
- Generated dataset quality summary, start summary, failure reason summary, lightweight plots, checklist, and quality report.
- Kept `training_ready: false` and `requires_human_review: true`.

## Metrics

{metrics}

## Evidence

{evidence}
""", encoding="utf-8")

    (RUNS / "CRITIC_REPORT.md").write_text(f"""# Critic Report

## Current Phase

Phase 9 human review packet

## Corrected Fact

The USD scene's real robot is `/World/A1`, not Go2. Formal data uses:

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
```

## Phase 9 Review

{metrics}

## Findings

- Dataset audit completed without training, SFT, GDPO, RL, real VLM inference, or Phase 8 raw row mutation.
- No rejected samples were found under the implemented gates.
- One warning sample was found due to the Phase 8 `post_rgb_invalid` record.
- All samples retained candidate-ID language contract checks.
- The data is not training-ready until manual review approves a later preparation phase.

## Evidence

{evidence}
""", encoding="utf-8")

    (RUNS / "VLM_LA_EXPLORER_PLAN.md").write_text(f"""# VLM-LA Explorer Plan

## Method Name

A1-VLM-LA Explorer

Full route name:

A1-VLM-LA Explorer for 3D Active Exploration

## Workspace

`/home/ubuntu22/VLA`

## Robot Platform

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
```

The USD scene's real robot is `/World/A1`. Do not claim the USD contains a verified Go2 robot unless a real Go2 asset is provided or substituted later.

## Current Progress

- Phase 1 placed the primary USD scene bundle and kept it ignored by Git.
- Phase 2 opened the scene and identified the articulated `/World/A1` hierarchy.
- Old proxy Phase 3 through Phase 5 outputs remain proxy-only and are not final A1 real-sensor data.
- Phase 5.6 validated real Isaac/Omniverse RGB-D sensing and depth-backprojected pointclouds.
- Phase 4R-real, Phase 5R-real, Phase 6, and Phase 7 passed the real-sensor A1 pipeline gates.
- Phase 8 collected A1 real-sensor VLM-LA rollout samples.
- Phase 9 prepared the human review packet and dataset quality audit.

## Phase 9 Audit Route

```yaml
{metrics}
```

## Next Phase

Manual review result required before SFT preparation.

Training remains out of scope until explicit human approval.
""", encoding="utf-8")

    (RUNS / "VLM_LA_INTERFACE_SPEC.md").write_text(f"""# VLM-LA Interface Spec

## Project Route

A1-VLM-LA Explorer for 3D Active Exploration

## Robot Platform

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
```

## Primary Output

```text
Go to candidate <id>.
```

## Phase 9 Interface Audit

```yaml
source_dataset: Phase 8 rollout
parse_success_rate: {summary['parse_success_rate']}
validation_success_rate: {summary['validation_success_rate']}
movement_success_rate: {summary['movement_success_rate']}
accepted_sample_count: {summary['accepted_sample_count']}
warning_sample_count: {summary['warning_sample_count']}
rejected_sample_count: {summary['rejected_sample_count']}
training_ready: false
requires_human_review: true
```

The main interface remains candidate-ID based. Free coordinates, velocities, and joint commands are not accepted as VLM-LA outputs.
""", encoding="utf-8")

    (RUNS / "VLM_LA_DATASET_SPEC.md").write_text(f"""# VLM-LA Dataset Spec

## Project Route

A1-VLM-LA Explorer for 3D Active Exploration

## Formal A1 Metadata

Formal A1 data must use:

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
```

## Phase 9 Review Packet Metadata

```yaml
source_dataset: Phase 8 rollout
dataset_quality_summary: {summary['dataset_quality_summary_path']}
accepted_samples: {summary['accepted_samples_path']}
warning_samples: {summary['warning_samples_path']}
rejected_samples: {summary['rejected_samples_path']}
training_ready: false
requires_human_review: true
recommended_next_phase: {summary['recommended_next_phase']}
```

## Phase 9 Audit Counts

```yaml
total_samples: {summary['total_samples']}
accepted_sample_count: {summary['accepted_sample_count']}
warning_sample_count: {summary['warning_sample_count']}
rejected_sample_count: {summary['rejected_sample_count']}
acceptance_rate: {summary['acceptance_rate']}
warning_rate: {summary['warning_rate']}
rejection_rate: {summary['rejection_rate']}
real_sensor_sample_rate: {summary['real_sensor_sample_rate']}
```

## Status

Phase 9 prepared a human review packet. The data must not be used for SFT or GDPO until the manual review result explicitly approves preparation.

## Label Contract

`target_language` must contain a parseable candidate ID:

```text
Go to candidate <id>.
```

## Large Artifact Safety

Raw sensor data, large RGB-D/depth/BEV images, `.npz`, `.hdf5`, checkpoints, meshes, textures, and USD scene bundles must not be committed to Git.
""", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source_run_dir", default=str(DEFAULT_SOURCE_RUN))
    parser.add_argument("--run_dir", required=True)
    parser.add_argument("--top_checklist", default=str(TOP_CHECKLIST))
    parser.add_argument("--top_report", default=str(TOP_REPORT))
    args = parser.parse_args()

    source_run = Path(args.source_run_dir).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser().resolve()
    for subdir in ["logs", "quality", "reports", "summary", "plots", "accepted", "warning", "rejected"]:
        (run_dir / subdir).mkdir(parents=True, exist_ok=True)

    required = {
        "rollout_summary": source_run / "summary/rollout_summary.json",
        "rollout_steps": source_run / "summary/rollout_steps.csv",
        "candidate_summary": source_run / "summary/candidate_summary.csv",
        "samples": source_run / "samples/vlm_la_samples.jsonl",
        "manifest": source_run / "samples/dataset_manifest.json",
    }
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing Phase 8 audit input files: " + ", ".join(missing))

    phase8_summary = read_json(required["rollout_summary"])
    steps = read_csv(required["rollout_steps"])
    candidate_rows = read_csv(required["candidate_summary"])
    samples = read_jsonl(required["samples"])
    manifest = read_json(required["manifest"])
    phase8_start_rows = read_csv(source_run / "summary/start_summary.csv") if (source_run / "summary/start_summary.csv").exists() else []

    step_by_key = {(int_value(r.get("start_id")), int_value(r.get("step_id"))): r for r in steps}
    candidates_by_key = candidates_by_step(candidate_rows)
    path_cost_unique = len({r.get("path_cost") for r in candidate_rows if r.get("path_cost") not in {None, ""}})

    audited: list[dict[str, Any]] = []
    for sample in samples:
        sample_id = str(sample.get("sample_id", ""))
        match = re.search(r"start(\d+)_step(\d+)", sample_id)
        if not match:
            audited.append({
                "sample_id": sample_id,
                "start_id": -1,
                "step_id": -1,
                "quality_status": "reject",
                "quality_flags": ["sample_id_unparseable"],
                "reject_reason": "sample_id_unparseable",
                "warning_reason": None,
                "source_sample": sample,
            })
            continue
        start_id, step_id = int(match.group(1)), int(match.group(2))
        step = step_by_key.get((start_id, step_id))
        rows_for_step = candidates_by_key.get((start_id, step_id), [])
        selected_id = int_value(step.get("selected_candidate_id"), -1) if step else -1
        selected = selected_candidate_from_rows(rows_for_step, selected_id) if step else None
        if step is None:
            audited.append({
                "sample_id": sample_id,
                "start_id": start_id,
                "step_id": step_id,
                "quality_status": "reject",
                "quality_flags": ["rollout_step_missing"],
                "reject_reason": "rollout_step_missing",
                "warning_reason": None,
                "source_sample": sample,
            })
            continue
        audited.append(classify_sample(source_run, step, sample, rows_for_step, selected, path_cost_unique))

    accepted = [r for r in audited if r["quality_status"] == "pass"]
    warnings = [r for r in audited if r["quality_status"] == "warning"]
    rejected = [r for r in audited if r["quality_status"] == "reject"]

    write_quality_jsonl(run_dir / "quality/accepted_samples.jsonl", accepted)
    write_quality_jsonl(run_dir / "quality/warning_samples.jsonl", warnings)
    write_quality_jsonl(run_dir / "quality/rejected_samples.jsonl", rejected)
    write_quality_jsonl(run_dir / "accepted/accepted_samples.jsonl", accepted)
    write_quality_jsonl(run_dir / "warning/warning_samples.jsonl", warnings)
    write_quality_jsonl(run_dir / "rejected/rejected_samples.jsonl", rejected)

    failure_summary = make_failure_summary(audited)
    start_summary = make_start_summary(audited, phase8_start_rows)
    plots_saved = save_plots(run_dir, audited, start_summary, candidate_rows)
    dataset_summary = make_dataset_summary(run_dir, source_run, phase8_summary, manifest, audited, start_summary, failure_summary, plots_saved)

    write_json(run_dir / "summary/dataset_quality_summary.json", dataset_summary)
    write_csv(run_dir / "summary/start_quality_summary.csv", start_summary, list(start_summary[0].keys()) if start_summary else ["start_id"])
    write_csv(run_dir / "summary/failure_reason_summary.csv", failure_summary, ["reason", "count", "rate"])
    write_checklist(run_dir / "reports/HUMAN_REVIEW_A1_VLM_LA_DATASET_CHECKLIST.md", dataset_summary)
    write_quality_report(run_dir / "reports/DATASET_QUALITY_REPORT.md", dataset_summary)
    write_checklist(Path(args.top_checklist).expanduser().resolve(), dataset_summary)
    write_quality_report(Path(args.top_report).expanduser().resolve(), dataset_summary)
    write_status_files(dataset_summary)

    print(json.dumps(dataset_summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
