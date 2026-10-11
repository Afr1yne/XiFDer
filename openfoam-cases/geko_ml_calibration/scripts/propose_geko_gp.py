#!/usr/bin/env python3
"""Propose a GEKO Ck/Comega CFD sample with a small Gaussian process."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np


SCALES = np.asarray([0.005, 0.005])
BOUNDS = np.asarray([[-0.002, 0.010], [-0.006, 0.001]])


def rbf_kernel(
    left: np.ndarray,
    right: np.ndarray,
    length_scales: np.ndarray,
) -> np.ndarray:
    delta = (
        left[:, None, :] - right[None, :, :]
    ) / length_scales[None, None, :]
    return np.exp(-0.5 * np.sum(delta**2, axis=2))


def normal_cdf(values: np.ndarray) -> np.ndarray:
    return 0.5 * (
        1.0
        + np.asarray(
            [math.erf(value / math.sqrt(2.0)) for value in values]
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("training_csv", type=Path)
    args = parser.parse_args()

    rows: list[dict[str, str]] = []
    with args.training_csv.open(encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row["physically_screened"].lower() == "true":
                rows.append(row)

    x_physical = np.asarray(
        [[float(row["Ck"]), float(row["Comega"])] for row in rows]
    )
    y = np.asarray([float(row["training_loss"]) for row in rows])
    x = x_physical / SCALES
    y_mean = float(np.mean(y))
    y_std = float(np.std(y)) or 1.0
    y_scaled = (y - y_mean) / y_std

    best_lml = -math.inf
    best_parameters: tuple[np.ndarray, float, np.ndarray] | None = None
    for lx in (0.35, 0.6, 1.0, 1.8, 3.0):
        for ly in (0.35, 0.6, 1.0, 1.8, 3.0):
            length_scales = np.asarray([lx, ly])
            for noise in (1e-6, 1e-4, 1e-3, 1e-2):
                covariance = rbf_kernel(x, x, length_scales)
                covariance += np.eye(len(x)) * noise
                try:
                    cholesky = np.linalg.cholesky(covariance)
                except np.linalg.LinAlgError:
                    continue
                alpha = np.linalg.solve(
                    cholesky.T,
                    np.linalg.solve(cholesky, y_scaled),
                )
                lml = float(
                    -0.5 * y_scaled @ alpha
                    - np.sum(np.log(np.diag(cholesky)))
                    - 0.5 * len(x) * math.log(2.0 * math.pi)
                )
                if lml > best_lml:
                    best_lml = lml
                    best_parameters = (length_scales, noise, cholesky)

    if best_parameters is None:
        raise RuntimeError("No positive-definite GP covariance was found")

    length_scales, noise, cholesky = best_parameters
    alpha = np.linalg.solve(
        cholesky.T,
        np.linalg.solve(cholesky, y_scaled),
    )

    ck_grid = np.linspace(BOUNDS[0, 0], BOUNDS[0, 1], 121)
    comega_grid = np.linspace(BOUNDS[1, 0], BOUNDS[1, 1], 141)
    mesh_ck, mesh_comega = np.meshgrid(ck_grid, comega_grid)
    candidates_physical = np.column_stack(
        [mesh_ck.ravel(), mesh_comega.ravel()]
    )
    candidates = candidates_physical / SCALES

    cross_covariance = rbf_kernel(candidates, x, length_scales)
    mean_scaled = cross_covariance @ alpha
    solved = np.linalg.solve(cholesky, cross_covariance.T)
    variance = np.maximum(1.0 - np.sum(solved**2, axis=0), 1e-12)
    sigma = np.sqrt(variance)

    best_y_scaled = float(np.min(y_scaled))
    improvement = best_y_scaled - mean_scaled - 0.01
    z_score = improvement / sigma
    expected_improvement = (
        improvement * normal_cdf(z_score)
        + sigma
        * np.exp(-0.5 * z_score**2)
        / math.sqrt(2.0 * math.pi)
    )

    # Do not resample an existing point.
    distances = np.linalg.norm(
        candidates[:, None, :] - x[None, :, :],
        axis=2,
    )
    expected_improvement[np.min(distances, axis=1) < 0.08] = -math.inf

    selected = int(np.argmax(expected_improvement))
    predicted_mean = mean_scaled[selected] * y_std + y_mean
    predicted_std = sigma[selected] * y_std
    best_observed_index = int(np.argmin(y))

    result = {
        "Ck": float(candidates_physical[selected, 0]),
        "Comega": float(candidates_physical[selected, 1]),
        "predicted_training_loss_mean": float(predicted_mean),
        "predicted_training_loss_std": float(predicted_std),
        "expected_improvement": float(expected_improvement[selected] * y_std),
        "best_observed": {
            "case": rows[best_observed_index]["case"],
            "Ck": float(x_physical[best_observed_index, 0]),
            "Comega": float(x_physical[best_observed_index, 1]),
            "training_loss": float(y[best_observed_index]),
        },
        "gp": {
            "length_scale_Ck_scaled": float(length_scales[0]),
            "length_scale_Comega_scaled": float(length_scales[1]),
            "noise": float(noise),
            "log_marginal_likelihood": float(best_lml),
            "training_points": len(rows),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
