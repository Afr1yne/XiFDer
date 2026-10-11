"""Analyze this case's forceCoeffs record using the published FFT method."""
import argparse
import json
from pathlib import Path

import numpy as np


def analyze(source, start, end):
    data = np.loadtxt(source, comments="#", ndmin=2)
    if data.shape[1] < 5 or not np.isfinite(data).all():
        raise ValueError("Expected finite forceCoeffs data with at least five columns")
    selected = (data[:, 0] >= start) & (data[:, 0] <= end)
    time = data[selected, 0]
    drag = data[selected, 1]
    lift = data[selected, 4]
    if len(time) < 4:
        raise ValueError("Analysis window contains fewer than four samples")
    steps = np.diff(time)
    dt = float(np.median(steps))
    if dt <= 0 or not np.allclose(steps, dt, rtol=1e-6, atol=1e-10):
        raise ValueError("FFT requires strictly increasing, uniformly sampled times")
    window = np.hanning(len(lift))
    signal = lift - lift.mean()
    frequencies = np.fft.rfftfreq(len(signal), dt)
    amplitudes = 2 * np.abs(np.fft.rfft(signal * window)) / window.sum()
    amplitudes[0] /= 2
    if len(signal) % 2 == 0:
        amplitudes[-1] /= 2
    peak = int(np.argmax(amplitudes[1:]) + 1)
    summary = {
        "start_s": float(time[0]),
        "end_s": float(time[-1]),
        "samples": len(time),
        "dt_s": dt,
        "Cd_mean": float(drag.mean()),
        "Cl_range": [float(lift.min()), float(lift.max())],
        "frequency_resolution_Hz": float(frequencies[1]),
        "peak_Hz": float(frequencies[peak]),
        "St": float(frequencies[peak] * 0.1 / 1.0),
    }
    return summary, np.column_stack((frequencies, amplitudes))


def main():
    case = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path,
                        default=case / "postProcessing/forces/0/coefficient.dat")
    parser.add_argument("--start", type=float, default=10.0)
    parser.add_argument("--end", type=float, default=30.0)
    parser.add_argument("--output", type=Path, default=case / "analysis")
    args = parser.parse_args()
    summary, spectrum = analyze(args.input, args.start, args.end)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    np.savetxt(args.output / "lift_spectrum.csv", spectrum, delimiter=",",
               header="frequency_Hz,Cl_amplitude", comments="")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
