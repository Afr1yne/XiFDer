#!/usr/bin/env python3
"""Collect GEKO source-term DOE runs into JSON and CSV datasets."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path


def uniform_value(path: Path) -> float:
    if not path.exists():
        return 0.0
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"internalField\s+uniform\s+([-+0-9.eE]+)\s*;",
        text,
    )
    if not match:
        raise ValueError(f"Cannot find a uniform internalField in {path}")
    return float(match.group(1))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("evaluator", type=Path)
    args = parser.parse_args()

    records: list[dict[str, object]] = []
    candidates = sorted(
        path
        for path in args.project.iterdir()
        if path.is_dir()
        and (path.name == "baseline_GEKO" or path.name.startswith("doe_"))
        and (path / "wall_data.dat").exists()
        and (path / "wall_cp.dat").exists()
    )

    for case_dir in candidates:
        completed = subprocess.run(
            [
                sys.executable,
                str(args.evaluator),
                str(case_dir),
                str(args.reference),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads(completed.stdout)
        result["Ck"] = uniform_value(case_dir / "0" / "Ck")
        result["Comega"] = uniform_value(case_dir / "0" / "Comega")
        records.append(result)

    json_path = args.project / "training_data.json"
    csv_path = args.project / "training_data.csv"
    json_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    columns = [
        "case",
        "Ck",
        "Comega",
        "training_loss",
        "cf_rmse",
        "cp_rmse",
        "u_rmse_train_x1_x4_x6",
        "u_rmse_holdout_x10",
        "reattachment_x_over_h",
        "reattachment_abs_error",
        "downward_crossing_count",
        "max_abs_u_over_uref",
        "physically_screened",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for record in records:
            writer.writerow({key: record[key] for key in columns})

    print(json_path)
    print(csv_path)
    print(f"records {len(records)}")


if __name__ == "__main__":
    main()
