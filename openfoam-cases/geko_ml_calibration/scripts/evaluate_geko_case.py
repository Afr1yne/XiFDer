#!/usr/bin/env python3
"""Compare one backward-facing-step case with the TMBWG experiment."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import numpy as np


STEP_HEIGHT = 0.0127
U_REF = 44.2


def numeric_rows(path: Path) -> np.ndarray:
    rows: list[list[float]] = []
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.split():
                continue
            try:
                rows.append([float(value) for value in line.split()])
            except ValueError:
                continue
    return np.asarray(rows)


def experimental_cp(path: Path) -> np.ndarray:
    rows: list[list[float]] = []
    in_bottom_zone = False
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.startswith("zone"):
                in_bottom_zone = "bottom wall" in line
                continue
            if not in_bottom_zone:
                continue
            if not line.split():
                continue
            try:
                rows.append([float(value) for value in line.split()])
            except ValueError:
                continue
    return np.asarray(rows)


def experimental_profiles(path: Path) -> dict[float, np.ndarray]:
    profiles: dict[float, list[list[float]]] = {}
    current_x: float | None = None
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.startswith("zone"):
                match = re.search(r"x/H=([-+0-9.]+)", line)
                current_x = float(match.group(1)) if match else None
                if current_x is not None:
                    profiles[current_x] = []
                continue
            if current_x is None:
                continue
            if not line.split():
                continue
            try:
                profiles[current_x].append(
                    [float(value) for value in line.split()]
                )
            except ValueError:
                continue
    return {key: np.asarray(value) for key, value in profiles.items()}


def interpolate_unique(x: np.ndarray, y: np.ndarray, target: np.ndarray) -> np.ndarray:
    order = np.argsort(x)
    x_sorted = x[order]
    y_sorted = y[order]
    x_unique, indices = np.unique(x_sorted, return_index=True)
    y_unique = y_sorted[indices]
    return np.interp(target, x_unique, y_unique)


def reattachment_x_over_h(wall_data: np.ndarray) -> tuple[float, int]:
    xh = wall_data[:, 0] / STEP_HEIGHT
    tau = wall_data[:, 1]
    crossings: list[float] = []
    for i in range(len(xh) - 1):
        if xh[i] < 1.0 or tau[i] <= 0.0 or tau[i + 1] >= 0.0:
            continue
        fraction = tau[i] / (tau[i] - tau[i + 1])
        crossings.append(xh[i] + fraction * (xh[i + 1] - xh[i]))
    if not crossings:
        return math.nan, 0
    physical = [value for value in crossings if value < 12.0]
    return (physical[-1] if physical else crossings[-1]), len(crossings)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_dir", type=Path)
    parser.add_argument("reference_dir", type=Path)
    args = parser.parse_args()

    case_dir = args.case_dir
    reference_dir = args.reference_dir
    sample_dir = case_dir / "postProcessing" / "sample" / "2000"

    wall_data = np.loadtxt(case_dir / "wall_data.dat")
    wall_cp = np.loadtxt(case_dir / "wall_cp.dat")

    cf_exp = numeric_rows(reference_dir / "cf.exp.dat")
    cp_exp = experimental_cp(reference_dir / "cp.expnew.dat")
    profile_exp = experimental_profiles(reference_dir / "profiles.exp.dat")

    xh_wall = wall_data[:, 0] / STEP_HEIGHT
    cf_sim = -wall_data[:, 1] / (0.5 * U_REF**2)
    cf_at_exp = interpolate_unique(xh_wall, cf_sim, cf_exp[:, 0])
    cf_rmse = float(np.sqrt(np.mean((cf_at_exp - cf_exp[:, 1]) ** 2)))

    xh_cp = wall_cp[:, 0] / STEP_HEIGHT
    cp_at_exp = interpolate_unique(xh_cp, wall_cp[:, 1], cp_exp[:, 0])
    cp_rmse = float(np.sqrt(np.mean((cp_at_exp - cp_exp[:, 1]) ** 2)))

    profile_rmse: dict[str, float] = {}
    max_abs_u_ratio = 0.0
    for xh in (1.0, 4.0, 6.0, 10.0):
        label = f"x_by_h_{int(xh):02d}_p_U_turbulenceProperties:devReff.xy"
        sim = np.loadtxt(sample_dir / label)
        y_sim = sim[:, 0] / STEP_HEIGHT
        u_sim = sim[:, 2] / U_REF
        max_abs_u_ratio = max(max_abs_u_ratio, float(np.max(np.abs(u_sim))))

        exp = profile_exp[xh]
        mask = (exp[:, 1] >= y_sim.min()) & (exp[:, 1] <= y_sim.max())
        u_at_exp = interpolate_unique(y_sim, u_sim, exp[mask, 1])
        profile_rmse[str(int(xh))] = float(
            np.sqrt(np.mean((u_at_exp - exp[mask, 2]) ** 2))
        )

    train_u_rmse = float(
        np.mean([profile_rmse[key] for key in ("1", "4", "6")])
    )
    holdout_u_rmse = profile_rmse["10"]

    # Equal-weighted normalized training score. The x/H=10 profile is held out.
    training_loss = float(
        np.mean(
            [
                cf_rmse / 0.003,
                cp_rmse / 0.20,
                train_u_rmse,
            ]
        )
    )

    reattachment, crossing_count = reattachment_x_over_h(wall_data)
    result = {
        "case": case_dir.name,
        "cf_rmse": cf_rmse,
        "cp_rmse": cp_rmse,
        "u_rmse_train_x1_x4_x6": train_u_rmse,
        "u_rmse_holdout_x10": holdout_u_rmse,
        "u_rmse_by_xh": profile_rmse,
        "training_loss": training_loss,
        "reattachment_x_over_h": reattachment,
        "reattachment_abs_error": abs(reattachment - 6.26),
        "downward_crossing_count": crossing_count,
        "max_abs_u_over_uref": max_abs_u_ratio,
        "physically_screened": bool(
            max_abs_u_ratio <= 2.0 and crossing_count == 1
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
