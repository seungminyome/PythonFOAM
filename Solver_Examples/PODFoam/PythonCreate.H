// Copyright (C) 2021 UChicago Argonne, LLC
// Copyright (C) 2026 Seungmin Yome
// SPDX-License-Identifier: (other)
//
// Python-OpenFOAM integration
//
// Initialize the interpreter, import python_module and check its functions.
// NumPy's machine-limit probes overflow on purpose during import, so the
// floating-point traps are off until the end of this file.

PythonFpeOff pythonInitFpe;
Py_Initialize();
if (init_numpy() < 0)
{
    printPythonError();
    FatalErrorInFunction << "NumPy initialization failed" << exit(FatalError);
}

// sys.path: the case folder first, so that -case finds the case's module. In a
// parallel run the case path is processorN/, so the undecomposed case folder
// goes in front of it; in a serial run the two are the same folder and it is
// inserted once. The launch folder follows them.
{
    const fileName casePath = runTime.path();
    const fileName globalPath = runTime.rootPath()/runTime.globalCaseName();
    const auto insertPath = [](const fileName& dir)
    {
        PyObject* text = PyUnicode_DecodeFSDefault(dir.c_str());
        if (!text || PyList_Insert(PySys_GetObject("path"), 0, text) < 0)
        {
            printPythonError();
            FatalErrorInFunction << "Cannot add " << dir << " to Python path"
                << exit(FatalError);
        }
        Py_DECREF(text);
    };
    insertPath(casePath);
    if (globalPath != casePath)
    {
        insertPath(globalPath);
    }
}
if (PyRun_SimpleString("import sys; sys.path.append('.')") < 0)
{
    FatalErrorInFunction << "Cannot add the launch folder to Python path" << exit(FatalError);
}

PyObject* pModule = PyImport_ImportModule("python_module");
if (!pModule)
{
    printPythonError();
    FatalErrorInFunction << "Cannot import python_module" << exit(FatalError);
}
PyObject* snapshot_func = PyObject_GetAttrString(pModule, "snapshot_func");
PyObject* svd_func = snapshot_func ? PyObject_GetAttrString(pModule, "svd_func") : nullptr;
if (!snapshot_func || !svd_func
 || !PyCallable_Check(snapshot_func) || !PyCallable_Check(svd_func))
{
    printPythonError();
    FatalErrorInFunction << "snapshot_func and svd_func must be callable"
        << exit(FatalError);
}
Py_DECREF(pModule);

const int rank = Pstream::myProcNo();
const label num_cells = mesh.nCells();
// The modes written per component; the shipped module returns 5.
const label truncation =
    runTime.controlDict().lookupOrDefault<label>("podTruncation", 5);
if (truncation < 1)
{
    FatalErrorInFunction << "podTruncation must be at least 1, not " << truncation
        << exit(FatalError);
}
// Zero: the SVD runs at write steps. Above zero: every podSvdInterval snapshots.
const label podSvdInterval =
    runTime.controlDict().lookupOrDefault<label>("podSvdInterval", 0);
if (podSvdInterval < 0)
{
    FatalErrorInFunction << "podSvdInterval must be 0 or positive, not " << podSvdInterval
        << exit(FatalError);
}
label podSnapshotCount = 0;
label podSnapshotsSinceSvd = 0;
bool podTruncationWarned = false;
std::feclearexcept(FE_ALL_EXCEPT);
pythonInitFpe.restore();
Info<< "Python and NumPy initialized successfully" << endl;
