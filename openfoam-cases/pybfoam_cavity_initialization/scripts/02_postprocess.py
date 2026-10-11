from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from pybFoam import Time, argList, fvc, fvMesh, selectTimes, volVectorField, write


def main() -> None:
    case = Path(sys.argv[1]).resolve()
    output = case / "pythonResults"
    output.mkdir(exist_ok=True)

    run_time = Time(argList([str(case), "-case", str(case)]))
    mesh = fvMesh(run_time)
    instants = list(selectTimes(run_time, ["postProcess"]))
    positive = [instant for instant in instants if float(str(instant)) > 0.0]
    if not positive:
        raise RuntimeError("No solved time directories were found")

    chosen = positive[-1]
    run_time.setTime(chosen, len(positive))
    U = volVectorField.read_field(mesh, "U")
    values = np.asarray(U["internalField"])
    centres = np.asarray(mesh.C()["internalField"])
    speed = np.linalg.norm(values, axis=1)

    grad_U = fvc.grad(U)()
    write(grad_U)
    grad_values = np.asarray(grad_U["internalField"])
    vorticity_z = grad_values[:, 1] - grad_values[:, 3]

    x = centres[:, 0]
    y = centres[:, 1]
    np.savetxt(
        output / "vorticity_z.csv",
        np.column_stack([centres, vorticity_z]),
        delimiter=",",
        header="x_m,y_m,z_m,omega_z_per_s",
        comments="",
    )

    x_line = np.unique(x)[np.argmin(np.abs(np.unique(x) - 0.05))]
    mask = np.isclose(x, x_line)
    order = np.argsort(y[mask])
    y_line = y[mask][order]
    ux_line = values[mask, 0][order]

    np.savetxt(
        output / "vertical_midline_Ux.csv",
        np.column_stack([y_line, ux_line]),
        delimiter=",",
        header="y_m,Ux_m_per_s",
        comments="",
    )

    print(f"latestTime={chosen}")
    print(f"nCells={mesh.nCells()}")
    print(f"min(|U|)={speed.min():.8f} m/s")
    print(f"mean(|U|)={speed.mean():.8f} m/s")
    print(f"max(|U|)={speed.max():.8f} m/s")
    print(f"midlineX={x_line:.8f} m")
    print(f"midlinePoints={len(y_line)}")
    print(f"gradUField={case / str(chosen) / 'grad(U)'}")
    print(f"results={output}")


if __name__ == "__main__":
    main()
