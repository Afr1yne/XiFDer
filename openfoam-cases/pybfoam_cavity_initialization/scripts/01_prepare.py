from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from pybFoam import Time, argList, dictionary, fvMesh, volVectorField, write
from pybFoam.meshing import generate_blockmesh


def main() -> None:
    case = Path(sys.argv[1]).resolve()
    run_time = Time(argList([str(case), "-case", str(case)]))
    generate_blockmesh(
        run_time,
        dictionary.read(str(case / "system" / "blockMeshDict")),
    )
    mesh = fvMesh(run_time)

    U = volVectorField.read_field(mesh, "U")
    U_view = np.asarray(U["internalField"])
    centres = np.asarray(mesh.C()["internalField"])

    length = 0.1
    x = centres[:, 0]
    y = centres[:, 1]
    U_view[:, 0] = np.sin(np.pi * x / length) * np.cos(np.pi * y / length)
    U_view[:, 1] = -np.cos(np.pi * x / length) * np.sin(np.pi * y / length)
    U_view[:, 2] = 0.0

    U.correctBoundaryConditions()
    write(U)

    speed = np.linalg.norm(U_view, axis=1)
    print(f"case={case}")
    print(f"nCells={mesh.nCells()}")
    print(f"U shape={U_view.shape}")
    print(f"min(|U|)={speed.min():.8f} m/s")
    print(f"mean(|U|)={speed.mean():.8f} m/s")
    print(f"max(|U|)={speed.max():.8f} m/s")
    print(f"field written={case / '0' / 'U'}")


if __name__ == "__main__":
    main()
