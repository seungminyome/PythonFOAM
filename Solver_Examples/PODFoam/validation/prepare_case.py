"""Stage the three cases from Run_Case without touching it."""
from pathlib import Path
import os
import re
import shutil
import sys

source, output = map(Path, sys.argv[1:])
for name in ('baseline-pimple', 'fixed-pimple', 'fixed-pod'):
    case = output / name
    for directory in ('0', 'constant', 'system'):
        shutil.copytree(source / 'Run_Case' / directory, case / directory)
    # Remove restart metadata only from the newly staged copies.
    (case / '0/uniform/time').unlink(missing_ok=True)
    # openfoam.org reads momentumTransport, openfoam.com turbulenceProperties.
    transport = case / 'constant/momentumTransport'
    turbulence = transport.read_text()
    turbulence = re.sub(r'(LES\s*\{)', r'\1\n    LESModel Smagorinsky;', turbulence)
    if name != 'baseline-pimple':
        turbulence = re.sub(r'simulationType\s+LES;', 'simulationType laminar;', turbulence)
        u = case / '0/U'
        u.write_text(u.read_text().replace('uniform (1e-8 0 0)', 'uniform (32.2 0 0)'))
        schemes = case / 'system/fvSchemes'
        schemes.write_text(schemes.read_text()
            .replace('default         backward;', 'default         Euler;')
            .replace('div(phi,U)      Gauss linear;', 'div(phi,U)      Gauss upwind;')
            .replace('Gauss linear corrected', 'Gauss linear limited 0.5')
            .replace('default         corrected;', 'default         limited 0.5;'))
        solution = case / 'system/fvSolution'
        solution.write_text(solution.read_text()
            .replace('nNonOrthogonalCorrectors 0;', 'nNonOrthogonalCorrectors 2;')
            .replace('smoother        GaussSeidel;', 'smoother        DICGaussSeidel;'))
    transport.write_text(turbulence)
    (case / 'constant/turbulenceProperties').unlink(missing_ok=True)
    (case / 'constant/turbulenceProperties').write_text(
        turbulence.replace('object      momentumTransport;', 'object      turbulenceProperties;'))
    dt, end = ('1e-5', '1e-4') if name == 'baseline-pimple' else ('1e-7', '1e-6')
    control = '''FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    object controlDict;
}
application SOLVER;
startFrom startTime;
startTime 0;
stopAt endTime;
endTime END;
deltaT DT;
writeControl timeStep;
writeInterval 1;
purgeWrite 0;
writeFormat ascii;
writePrecision 12;
writeCompression off;
timeFormat general;
timePrecision 10;
runTimeModifiable false;
adjustTimeStep no;
maxCo 1;
podSvdInterval 10;
functions {}
libs ("libincompressibleTurbulenceModels.so");
'''
    if not os.environ.get('WM_PROJECT_VERSION', 'v').startswith('v'):
        control = control.replace('libs ("libincompressibleTurbulenceModels.so");\n', '')
    (case / 'system/controlDict').write_text(control.replace('SOLVER', 'PODFoam' if name == 'fixed-pod' else 'pimpleFoam').replace('END', end).replace('DT', dt))
    if name == 'fixed-pod':
        shutil.copy2(source / 'validation/python_module.py', case / 'python_module.py')
