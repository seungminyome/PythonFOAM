// Copyright (C) 2021 UChicago Argonne, LLC
// SPDX-License-Identifier: (other)
// Initialize the embedded interpreter and validate the bridge API.
// NumPy's machine-limit probes deliberately overflow during import. Keep
// OpenFOAM traps enabled for PDE work, but use Python's FP semantics here.
PythonFpeOff pythonInitFpe;
Py_Initialize();
if (init_numpy() < 0)
{
    printPythonError();
    FatalErrorInFunction << "NumPy initialization failed" << exit(FatalError);
}

// Resolve python_module.py from the case even when invoked with -case; in a
// parallel run the case path is processorN/, so the undecomposed case
// directory (globalPath) is added as well. The launch folder stays on the path after them.
for (const fileName& dir : {runTime.path(), runTime.rootPath()/runTime.globalCaseName()})
{
    PyObject* casePath = PyUnicode_FromString(dir.c_str());
    if (!casePath || PyList_Insert(PySys_GetObject("path"), 0, casePath) < 0)
    {
        printPythonError();
        FatalErrorInFunction << "Cannot add case to Python path" << exit(FatalError);
    }
    Py_DECREF(casePath);
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
const label truncation = 5;
// Zero: the SVD runs at write steps. Above zero: every podSvdInterval snapshots.
const label podSvdInterval =
    runTime.controlDict().lookupOrDefault<label>("podSvdInterval", 0);
if (podSvdInterval < 0)
{
    FatalErrorInFunction << "podSvdInterval must be non-negative"
        << exit(FatalError);
}
label podSnapshotCount = 0;
label podSnapshotsSinceSvd = 0;
std::feclearexcept(FE_ALL_EXCEPT);
pythonInitFpe.restore();
Info<< "Python and NumPy initialized successfully" << endl;
