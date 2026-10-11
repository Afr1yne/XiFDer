#!/usr/bin/env bash
set -euo pipefail

project=${1:?Usage: run_geko_cases_sequential.sh PROJECT CASE...}
shift

for name in "$@"; do
    echo "running $name"
    (
        cd "$project/$name"
        /usr/bin/time -p mpirun -np 8 simpleFoam -parallel \
            > log.simpleFoam 2> log.time
    )
done
