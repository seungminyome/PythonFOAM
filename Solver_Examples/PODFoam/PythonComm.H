// Copyright (C) 2021 UChicago Argonne, LLC
// SPDX-License-Identifier: (other)
// An owning array prevents saved Python views from aliasing the next timestep.
{
Foam::sigFpe::ignore pythonCallFpe;
if (mesh.nCells() != num_cells)
{
    FatalErrorInFunction << "POD requires a fixed cell count" << exit(FatalError);
}
npy_intp dims[] = {num_cells, 3};
PyObject* snapshot = PyArray_SimpleNew(2, dims, NPY_DOUBLE);
if (!snapshot)
{
    PyErr_Print();
    FatalErrorInFunction << "Cannot allocate snapshot" << exit(FatalError);
}
double* data = static_cast<double*>
(
    PyArray_DATA(reinterpret_cast<PyArrayObject*>(snapshot))
);
forAll(U, celli)
{
    for (direction cmpt = 0; cmpt < 3; ++cmpt)
    {
        const double value = U[celli][cmpt];
        if (!std::isfinite(value) || !std::isfinite(p[celli]))
        {
            FatalErrorInFunction << "Non-finite U/p at cell " << celli
                << " time " << runTime.timeName() << exit(FatalError);
        }
        data[3*celli + cmpt] = value;
    }
}
PyObject* snapshotResult = PyObject_CallFunction(snapshot_func, "Oi", snapshot, rank);
Py_DECREF(snapshot);
if (!snapshotResult)
{
    PyErr_Print();
    FatalErrorInFunction << "Python snapshot_func failed" << exit(FatalError);
}
Py_DECREF(snapshotResult);
++podSnapshotCount;
Info<< "POD snapshot accepted: " << podSnapshotCount
    << " time=" << runTime.timeName() << " cells=" << num_cells << endl;

const bool computeSvd = podSvdInterval
    ? (podSnapshotCount % podSvdInterval == 0)
    : runTime.outputTime();
if (computeSvd)
{
    PyObject* result = PyObject_CallFunction(svd_func, "i", rank);
    if (!result)
    {
        PyErr_Print();
        FatalErrorInFunction << "Python svd_func failed" << exit(FatalError);
    }
    // Insist on a float64 ndarray instead of converting lists or lower precision.
    if (!PyArray_Check(result)
     || PyArray_TYPE(reinterpret_cast<PyArrayObject*>(result)) != NPY_DOUBLE
     || !PyArray_ISNOTSWAPPED(reinterpret_cast<PyArrayObject*>(result)))
    {
        Py_DECREF(result);
        FatalErrorInFunction << "SVD result must be a native float64 ndarray"
            << exit(FatalError);
    }
    PyArrayObject* modes = reinterpret_cast<PyArrayObject*>
    (
        PyArray_FROM_OTF(result, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY)
    );
    Py_DECREF(result);
    if (!modes)
    {
        PyErr_Print();
        FatalErrorInFunction << "SVD result must be a real numeric array"
            << exit(FatalError);
    }
    if (PyArray_NDIM(modes) != 2 || PyArray_DIM(modes, 0) != 3*num_cells
     || PyArray_DIM(modes, 1) != min(truncation, podSnapshotCount))
    {
        FatalErrorInFunction << "Expected SVD shape (3*cells, min(truncation,snapshots))"
            << exit(FatalError);
    }
    const label nModes = PyArray_DIM(modes, 1);
    const double* values = static_cast<const double*>(PyArray_DATA(modes));
    for (npy_intp i = 0; i < PyArray_SIZE(modes); ++i)
    {
        if (!std::isfinite(values[i]))
        {
            FatalErrorInFunction << "Non-finite SVD result" << exit(FatalError);
        }
    }
    const char* prefixes[] = {"upod_", "vpod_", "wpod_"};
    for (label mode = 0; mode < nModes; ++mode)
    {
        for (direction cmpt = 0; cmpt < 3; ++cmpt)
        {
            volScalarField podField
            (
                IOobject
                (
                    word(prefixes[cmpt]) + Foam::name(mode),
                    runTime.timeName(), mesh,
                    IOobject::NO_READ, IOobject::NO_WRITE, false
                ),
                mesh, dimensionedScalar("zero", dimless, 0),
                "zeroGradient"
            );
            forAll(podField, celli)
            {
                podField[celli] = values[(cmpt*num_cells + celli)*nModes + mode];
            }
            podField.correctBoundaryConditions();
            if (!podField.write())
            {
                FatalErrorInFunction << "Cannot write POD field" << exit(FatalError);
            }
        }
    }
    Py_DECREF(modes);
    Info<< "POD SVD returned to OpenFOAM: rows=" << 3*num_cells
        << " modes=" << nModes << " finite=true time="
        << runTime.timeName() << endl;
}
// The callback's return value is not used.
#include "PythonAnalysis.H"
std::feclearexcept(FE_ALL_EXCEPT);
} // Restore OpenFOAM floating-point traps before the next PDE step.
