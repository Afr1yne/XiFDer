#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 5 ]]; then
    echo "Usage: $0 TEMPLATE DEST CK COMEGA NPROCS" >&2
    exit 2
fi

template=$1
dest=$2
ck_value=$3
comega_value=$4
nprocs=$5

if [[ -e "$dest" ]]; then
    echo "Destination already exists: $dest" >&2
    exit 3
fi

cp -a "$template" "$dest"
cd "$dest"

foamListTimes -rm >/dev/null 2>&1 || true
rm -rf postProcessing
find . -maxdepth 1 -type d -name 'processor*' -exec rm -rf -- {} +
rm -rf 0
cp -a 0.orig 0

foamDictionary constant/turbulenceProperties \
    -entry RAS/RASModel -set GEKO
foamDictionary constant/turbulenceProperties \
    -entry RAS/GEKOCoeffs -add \
    "{ machineLearning true; writeCalibrationFields true; }"

for field in Ck Comega; do
    cp 0/k "0/$field"
    foamDictionary "0/$field" -entry FoamFile/object -set "$field"
    foamDictionary "0/$field" -entry dimensions -set "[0 0 0 0 0 0 0]"
done

foamDictionary 0/Ck -entry internalField -set "uniform $ck_value"
foamDictionary 0/Comega -entry internalField -set "uniform $comega_value"

set_boundaries()
{
    local field=$1
    local value=$2
    local boundary_dict="{
        inlet
        {
            type fixedValue;
            value uniform $value;
        }
        outlet
        {
            type zeroGradient;
        }
        \"(lowerWallStartup|upperWallStartup)\"
        {
            type symmetryPlane;
        }
        \"(upperWall|lowerWall)\"
        {
            type zeroGradient;
        }
        \"(front|back)\"
        {
            type empty;
        }
    }"
    foamDictionary "0/$field" -entry boundaryField -set "$boundary_dict"
}

set_boundaries Ck "$ck_value"
set_boundaries Comega "$comega_value"

cp \
    ${FOAM_TUTORIALS:?}/incompressible/simpleFoam/airFoil2D/system/decomposeParDict \
    system/decomposeParDict
foamDictionary system/decomposeParDict \
    -entry numberOfSubdomains -set "$nprocs"
foamDictionary system/decomposeParDict -entry method -set scotch

decomposePar -force > log.decomposePar
