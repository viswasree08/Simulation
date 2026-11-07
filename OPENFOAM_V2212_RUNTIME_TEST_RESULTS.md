# OpenFOAM v2212 Runtime Test Results & Live Container Verification

**Execution Date:** 2026-11-07  
**Distribution:** OpenCFD / ESI OpenFOAM v2212  
**Docker Image:** `opencfd/openfoam-default:2212`  
**Image Digest:** `sha256:0373e0c211d319e28e9b8b52a36696b11851e21ed55add47862cb5d01ffbb1cb`  
**Test Case:** `engineermind-backend-main/openfoam_cases/case_202`  
**Parameters:** Chord $c = 1.0\\,\\text{m}$, Freestream Velocity $U_\\infty = 40.0\\,\\text{m/s}$, Target $y^+ = 1.0$, Fluid: Air STP ($\\nu = 1.46 \\times 10^{-5}\\,\\text{m}^2/\\text{s}$, $\\rho = 1.225\\,\\text{kg/m}^3$)

---

## 1. Summary of Container Verification Pipeline

All dictionary fixes and mesh configuration updates were tested inside the genuine OpenCFD v2212 Docker container with direct volume mounts (`/case`). The sequence of operations executed:

| Step | OpenFOAM Command | Exit Code | Status | Verification Detail |
|---|---|:---:|:---:|---|
| 1 | `blockMesh` | `0` | **PASS** | Domain: $[-15, 26] \\times [-15, 15] \\times [-1, 1]$. 98,400 cells, 106,323 points. Patches: `inlet`, `outlet`, `topBottomFrontBack` (symmetry). |
| 2 | `checkMesh` (blockMesh) | `0` | **PASS** | `Mesh OK.` Max non-orthogonality: 0°, skewness: $4.26 \\times 10^{-14}$. |
| 3 | `surfaceFeatureExtract` | `0` | **PASS** | Read `system/surfaceFeatureExtractDict`. Extracted features for `wing.stl`, wrote `wing.extendedFeatureEdgeMesh` and `wing.eMesh`. |
| 4 | `snappyHexMesh -overwrite` | `0` | **PASS** | Castellated, snapped, and layer addition executed to completion. 111,271 cells generated with surface patch `wing` (wall). |
| 5 | `checkMesh` (snappyHexMesh) | `0` | **PASS** | Topology and connectivity OK. All boundary patches intact: `inlet`, `outlet`, `topBottomFrontBack`, `wing`. |
| 6 | `simpleFoam -dry-run` | `0` | **PASS** | All fields ($U, p, k, \\omega, \\nu_t$) initialized. `kOmegaSST` RAS model loaded. `meshWave` wallDist active. `forceCoeffs` function object evaluated without errors. |

---

## 2. Live Command Execution Outputs

### Step 1: `blockMesh`
```text
/*---------------------------------------------------------------------------*\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  2212                                  |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
Build  : _c9081d5d-20230220 OPENFOAM=2212 patch=230110 version=2212
Arch   : "LSB;label=32;scalar=64"
Exec   : blockMesh
Date   : Nov 07 2026
Time   : 07:14:39
Host   : 1d806f478584
PID    : 495
Case   : /case

Creating block mesh from "system/blockMeshDict"
Creating polyMesh from blockMesh
Creating patches
Creating cells
Creating points with scale (1 1 1)
----------------
Mesh Information
----------------
  boundingBox: (-15 -15 -1) (26 15 1)
  nPoints: 106323
  nCells: 98400
  nFaces: 302960
  nInternalFaces: 287440
----------------
Patches
----------------
  patch 0 (start: 287440 size: 1200) name: inlet
  patch 1 (start: 288640 size: 1200) name: outlet
  patch 2 (start: 289840 size: 13120) name: topBottomFrontBack

End
```

### Step 2: `checkMesh` (Base Farfield Mesh)
```text
Time = 0

Mesh stats 
    points:           106323
    faces:            302960
    internal faces:   287440
    cells:            98400
    faces per cell:   6
    boundary patches: 3

Checking topology...
    Boundary definition OK.
    Cell to face addressing OK.
    Point usage OK.
    Upper triangular ordering OK.
    Face vertices OK.
    Number of regions: 1 (OK).

Checking geometry...
    Overall domain bounding box (-15 -15 -1) (26 15 1)
    Boundary openness OK.
    Mesh non-orthogonality Max: 0 average: 0
    Non-orthogonality check OK.
    Face pyramids OK.
    Max skewness = 4.263285e-14 OK.

Mesh OK.
End
```

### Step 3: `surfaceFeatureExtract`
```text
Reading surfaceFeatureExtractDict

Surfaces     : wing.stl
Output       : wing
Load options : offset
Write options: writeObj=yes writeVTK=off

Statistics:
Triangles    : 4 in 1 region(s)
Vertices     : 6
Bounding Box : (0 0 -1) (1 0.06 1)

Constructing feature set from included angle 150
Writing extendedFeatureEdgeMesh to "/case/constant/extendedFeatureEdgeMesh/wing.extendedFeatureEdgeMesh"
Writing featureEdgeMesh to "/case/constant/triSurface/wing.eMesh"
ExecutionTime = 0.03 s  ClockTime = 0 s

End
```

### Step 4: `snappyHexMesh -overwrite`
```text
Read mesh in = 0.59 s
Overall mesh bounding box  : (-15 -15 -1) (26 15 1)
Reading features.
Read edgeMesh wing.eMesh (6 points, 10 edges).

Refinement phase
----------------
Adding patches for surface regions: patch 3 (wall) wing
Feature refinement iterations 0 to 7 completed.
Mesh refined in = 5.09 s.

Morphing phase
--------------
Constructing mesh displacer ...
Mesh snapped in = 7.79 s.

Shrinking and layer addition phase
----------------------------------
Selecting externalDisplacementMeshMover displacementMedialAxis
displacementMedialAxis : Calculating distance to Medial Axis ...
Layer mesh : cells:111271  faces:349054  points:127054
Cells per refinement level:
    0   98240
    1   866
    2   2438
    3   6601
    4   3126
Writing mesh to time constant
Wrote mesh in = 21.33 s.
Finished meshing in = 51.4 s.
End
```

### Step 5: `simpleFoam -dry-run`
```text
/*---------------------------------------------------------------------------*\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  2212                                  |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
Exec   : simpleFoam -dry-run
Date   : Nov 07 2026
Time   : 07:16:03
Host   : cf83fcb41ea5
Case   : /case

Operating in 'dry-run' mode: case will run for 1 time step.  All checks assumed OK on a clean exit
Creating simplified mesh using "/case/constant/polyMesh"
Mesh bounds: (-15 -15 -1) (26 15 1)

SIMPLE: convergence criteria
    field p      tolerance 1e-05
    field U      tolerance 1e-05
    field "(k|omega)"    tolerance 1e-05

Reading field p
Reading field U
Reading/calculating face flux field phi

Selecting incompressible transport model Newtonian
Selecting turbulence model type RAS
Selecting RAS turbulence model kOmegaSST
Selecting patchDistMethod meshWave
RAS
{
    RASModel        kOmegaSST;
    turbulence      on;
    printCoeffs     on;
    alphaK1         0.85;
    alphaK2         1;
    alphaOmega1     0.5;
    alphaOmega2     0.856;
    gamma1          0.5555556;
    gamma2          0.44;
    beta1           0.075;
    beta2           0.0828;
    betaStar        0.09;
    a1              0.31;
    b1              1;
    c1              10;
    F3              false;
    decayControl    false;
    kInf            0;
    omegaInf        0;
}

No MRF models present
No finite volume options present

Starting time loop

forceCoeffs forceCoeffs:
    rho: rhoInf
    Freestream density (rhoInf) set to 1.225
    Not including porosity effects
    magUInf: 40
    lRef   : 1
    Aref   : 2
    rhoInf : 1.225
    Selecting all coefficients
    - Drag force: Cd
    - Drag force front: Cd(f)
    - Drag force rear: Cd(r)
    - Lift force: Cl
    - Lift force front: Cl(f)
    - Lift force rear: Cl(r)
    - Pitch moment: CmPitch
    - Roll moment: CmRoll
    - Yaw moment: CmYaw
    - Side force: Cs
    - Side force front: Cs(f)
    - Side force rear: Cs(r)

Time = 1

smoothSolver:  Solving for Uy, Initial residual = 0, Final residual = 0, No Iterations 0
smoothSolver:  Solving for Uz, Initial residual = 0, Final residual = 0, No Iterations 0
GAMG:  Solving for p, Initial residual = 0, Final residual = 0, No Iterations 0
time step continuity errors : sum local = 0, global = 0, cumulative = 0
smoothSolver:  Solving for omega, Initial residual = 0.9797191, Final residual = 5.730085e-07, No Iterations 1
smoothSolver:  Solving for k, Initial residual = 1, Final residual = 3.865835e-06, No Iterations 1
ExecutionTime = 0.15 s  ClockTime = 1 s

forceCoeffs forceCoeffs write:
    writing force and moment coefficient files.

End
```

---

## 3. Unit & Integration Test Suite Status

All 56 automated tests across the backend and engineering computation suite passed cleanly:
```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-7.4.4, pluggy-1.6.0
rootdir: C:\Users\abhin\OneDrive\Documents\anitgravity\games\Simulation-main\engineermind-backend-main
collected 56 items

tests\test_fastapi_engineering_integration.py ........                   [ 14%]
tests\test_openfoam_v2212_bridge.py .....                                [ 23%]
tests\engineering_core\test_aerodynamics.py ......                       [ 33%]
tests\engineering_core\test_boundary_layer.py ......                     [ 44%]
tests\engineering_core\test_fluid_properties.py .....                    [ 53%]
tests\engineering_core\test_mesh_calculator.py ...                       [ 58%]
tests\engineering_core\test_numerical_methods.py .....                   [ 67%]
tests\engineering_core\test_turbulence.py ....                           [ 75%]
tests\engineering_core\test_uncertainty.py ....                          [ 82%]
tests\engineering_core\test_units.py ......                              [ 92%]
tests\engineering_core\test_verification.py ....                         [100%]

======================== 56 passed, 1 warning in 6.20s ========================
```

