"""Convert this case's forces output to coefficients and time-window statistics."""
import argparse
import json

import numpy as np

rho = 1.0
u_ref = 0.15
area_ref = 0.02 * 0.005
force_scale = 0.5 * rho * u_ref**2 * area_ref


def read_coefficients(path):
    data = np.loadtxt(path, comments="#", ndmin=2)
    if data.shape[0] < 2 or data.shape[1] != 10:
        raise ValueError("Expected the 10-column force.dat used by this case")
    if not np.isfinite(data).all() or not np.all(np.diff(data[:, 0]) > 0):
        raise ValueError("Force records must be finite and strictly time ordered")
    if not np.allclose(data[:, 1:4], data[:, 4:7] + data[:, 7:10], rtol=1e-5, atol=1e-12):
        raise ValueError("Total force does not match pressure plus viscous force")
    time = data[:, 0]
    cd = data[:, 1] / force_scale
    cl = data[:, 2] / force_scale
    return time, cd, cl


def window_statistics(time, cd, cl, start=1.0, end=2.0):
    if not time[0] <= start < end <= time[-1]:
        raise ValueError("The requested window must lie within the saved records")
    interior = (time > start) & (time < end)
    sample_time = np.r_[start, time[interior], end]
    cd_window = np.interp(sample_time, time, cd)
    cl_window = np.interp(sample_time, time, cl)
    cd_mean = np.trapezoid(cd_window, sample_time) / (end - start)
    return {
        "Cd_mean": float(cd_mean),
        "Cd_range": [float(cd_window.min()), float(cd_window.max())],
        "Cl_range": [float(cl_window.min()), float(cl_window.max())],
        "Cl_half_peak_to_peak": float(np.ptp(cl_window) / 2),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("force_files", nargs="+")
    parser.add_argument("--start", type=float, default=1.0)
    parser.add_argument("--end", type=float, default=2.0)
    args = parser.parse_args()
    results = {}
    for path in args.force_files:
        time, cd, cl = read_coefficients(path)
        results[path] = window_statistics(time, cd, cl, args.start, args.end)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
