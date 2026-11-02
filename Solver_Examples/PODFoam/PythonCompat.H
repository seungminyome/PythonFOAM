// Copyright (C) 2026 Seungmin Yome
// SPDX-License-Identifier: (other)
// What the calls into Python need that differs between openfoam.com (OPENFOAM
// defined) and openfoam.org.
#ifndef PythonCompat_H
#define PythonCompat_H

#include <cfenv>
#ifdef OPENFOAM
    #include "sigFpe.H"
#endif

// Floating-point traps off inside a scope, as around the calls into Python
// (NumPy's machine-limit probes overflow on purpose); restore() or the end of
// the scope turns them back on. Pending exception flags are cleared before the
// traps come back, since enabling a trap with its flag set raises it at once.
#ifdef OPENFOAM
typedef Foam::sigFpe::ignore PythonFpeOff;
#else
class PythonFpeOff
{
    int saved_;

public:
    PythonFpeOff()
    :
        saved_(fedisableexcept(FE_ALL_EXCEPT))
    {}

    PythonFpeOff(const PythonFpeOff&) = delete;
    PythonFpeOff& operator=(const PythonFpeOff&) = delete;

    ~PythonFpeOff()
    {
        restore();
    }

    void restore()
    {
        if (saved_ != -1)
        {
            feclearexcept(FE_ALL_EXCEPT);
            feenableexcept(saved_);
            saved_ = -1;
        }
    }
};
#endif

#endif
