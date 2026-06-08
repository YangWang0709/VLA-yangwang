"""Export Phase 5 frontier features for selector and VLA preview consumers."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

from exploration.frontier_feature_schema import MapPredictFrontierFeature
from exploration.map_predict_frontier_selector import select_frontiers_by_sample


WORKSPACE = Path("/home/ubuntu22/VLA")
PHASE5_REPORT = WORKSPACE / "runs/MAP_PREDICT_PHASE5_FRONTIER_SCORING_REPORT.md"


def resolve_phase5_table(path: str | Path | None = None) -> Path:
    if path is not None:
        candidate = Path(path)
        if candidate.exists():
            return candidate
    if PHASE5_REPORT.exists():
        text = PHASE5_REPORT.read_text(encoding="utf-8")
        match = re.search(r"frontier_feature_scored_table:\s*(\S+)", text)
        if match:
            candidate = Path(match.group(1))
            if candidate.exists():
                return candidate
    candidates = sorted(WORKSPACE.glob("runs/map_predict_phase5_frontier_scoring_baseline_*/frontier_features/frontier_feature_scored_table.csv"))
    if not candidates:
        raise FileNotFoundError("could not resolve Phase 5 frontier_feature_scored_table.csv")
    return candidates[-1]


def read_frontier_table(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def group_frontier_features(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        feature = MapPredictFrontierFeature.from_row(row).to_vla_feature()
        feature["selected_by_map_predict_score"] = str(row.get("selected_by_map_predict_score", "")).lower() == "true"
        feature["expected_information_gain_proxy"] = float(row.get("expected_information_gain_proxy", 0.0))
        feature["frontier_bev_cell_count"] = int(float(row.get("frontier_bev_cell_count", 0.0)))
        feature["reachability_proxy"] = str(row.get("reachability_proxy", "")).lower() == "true"
        grouped.setdefault(str(row.get("sample_id", "")), []).append(feature)
    return grouped


def export_frontier_features(table_path: str | Path | None = None) -> dict[str, Any]:
    resolved = resolve_phase5_table(table_path)
    rows = read_frontier_table(resolved)
    selections = select_frontiers_by_sample(rows)
    grouped_features = group_frontier_features(rows)
    return {
        "source_table": str(resolved),
        "frontier_rows": rows,
        "features_by_sample": grouped_features,
        "selections_by_sample": selections,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frontier-table", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = export_frontier_features(args.frontier_table)
    compact = {
        "source_table": payload["source_table"],
        "sample_count": len(payload["features_by_sample"]),
        "frontier_row_count": len(payload["frontier_rows"]),
        "selections_by_sample": payload["selections_by_sample"],
    }
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(compact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(compact, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
