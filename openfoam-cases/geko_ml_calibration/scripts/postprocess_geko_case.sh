#!/usr/bin/env bash
set -euo pipefail

case_dir=${1:?Usage: postprocess_geko_case.sh CASE_DIR}
extractor=${2:?Usage: postprocess_geko_case.sh CASE_DIR EXTRACTOR}

cd "$case_dir"

if [[ -d processor0 ]]; then
    reconstructPar -latestTime > log.reconstructPar
fi

latest_time=$(foamListTimes -latestTime)
if [[ -z "$latest_time" ]]; then
    echo "No reconstructed time found in $case_dir" >&2
    exit 4
fi

foamDictionary \
    -entry boundaryField/lowerWall/value \
    -value "$latest_time/Cx" |
    sed -n '/(/,/)/p' |
    sed -e 's/[()]//g;/^[[:space:]]*$/d' > wall_x.dat

foamDictionary \
    -entry boundaryField/lowerWall/value \
    -value "$latest_time/wallShearStress" |
    sed -n '/(/,/)/p' |
    sed -e 's/[()]//g;/^[[:space:]]*$/d' > wall_tau.dat

paste -d ' ' wall_x.dat wall_tau.dat > wall_data.dat

foamDictionary \
    -entry boundaryField/lowerWall/value \
    -value "$latest_time/cp" |
    sed -n '/(/,/)/p' |
    sed -e 's/[()]//g;/^[[:space:]]*$/d' > wall_cp_values.dat

paste -d ' ' wall_x.dat wall_cp_values.dat > wall_cp.dat

echo "case $(basename "$case_dir")"
echo "latest_time $latest_time"
if [[ -f log.time ]]; then
    awk '/^(real|user|sys) / {print}' log.time
fi
python3 "$extractor" wall_data.dat
