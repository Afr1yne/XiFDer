#!/usr/bin/env python3
"""Extract downstream wall-shear zero crossings for a backward-facing step."""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("wall_data")
    parser.add_argument("--step-height", type=float, default=0.0127)
    args = parser.parse_args()

    samples: list[tuple[float, float]] = []
    with open(args.wall_data, encoding="utf-8") as stream:
        for line in stream:
            values = line.split()
            if len(values) < 2:
                continue
            samples.append((float(values[0]), float(values[1])))

    crossings: list[float] = []
    for (x0, tau0), (x1, tau1) in zip(samples, samples[1:]):
        if x0 < 0 or tau0 * tau1 > 0 or tau1 == tau0:
            continue
        x_crossing = x0 - tau0 * (x1 - x0) / (tau1 - tau0)
        crossings.append(x_crossing / args.step_height)

    tau_values = [tau for _, tau in samples]
    print("points", len(samples))
    print("tau_x_min", min(tau_values))
    print("tau_x_max", max(tau_values))
    print("zero_crossings_x_over_h", " ".join(f"{value:.6f}" for value in crossings))


if __name__ == "__main__":
    main()
