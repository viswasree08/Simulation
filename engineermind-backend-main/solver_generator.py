import os
import math

def generate_block_mesh_dict(chord_m: float = 1.0) -> str:
    """
    3D Farfield bounding hex domain:
    X: [-15*c, 25*c]
    Y: [-15*c, 15*c]
    Z: [-5*c, 5*c]
    Patches:
    - inlet: type patch
    - outlet: type patch
    - topBottomFrontBack: type symmetry (3D farfield, NO empty patches)
    """
    x_min = -15.0 * chord_m
    x_max = 25.0 * chord_m
    y_min = -15.0 * chord_m
    y_max = 15.0 * chord_m
    z_min = -5.0 * chord_m
    z_max = 5.0 * chord_m

    # Suggested cell counts based on bounding dimensions
    nx = 60
    ny = 40
    nz = 20

    return f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2212                                 |
|   \\\\  /    A nd           | Case:     3D Aerodynamics BlockMesh             |
|    \\\\/     M anipulation  | Boundary: 3D Farfield Symmetry                  |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}}

scale   1;

vertices
(
    ({x_min} {y_min} {z_min}) // 0
    ({x_max} {y_min} {z_min}) // 1
    ({x_max} {y_max} {z_min}) // 2
    ({x_min} {y_max} {z_min}) // 3
    ({x_min} {y_min} {z_max}) // 4
    ({x_max} {y_min} {z_max}) // 5
    ({x_max} {y_max} {z_max}) // 6
    ({x_min} {y_max} {z_max}) // 7
);

blocks
(
    hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz}) simpleGrading (1 1 1)
);

edges
(
);

boundary
(
    inlet
    {{
        type patch;
        faces
        (
            (0 4 7 3)
        );
    }}
    outlet
    {{
        type patch;
        faces
        (
            (1 2 6 5)
        );
    }}
    topBottomFrontBack
    {{
        type symmetry;
        faces
        (
            (3 7 6 2) // top
            (0 1 5 4) // bottom
            (0 3 2 1) // back (z_min)
            (4 5 6 7) // front (z_max)
        );
    }}
);

mergePatchPairs
(
);
"""

def generate_surface_features_dict(stl_filename: str = "wing.stl") -> str:
    """
    Generate system/surfaceFeatureExtractDict for OpenFOAM v2212 (OpenCFD/ESI).
    Extracts feature lines from closed manifold STL surfaces into .eMesh files.
    """
    return f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2212                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  | Case:     surfaceFeatureExtractDict             |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      surfaceFeatureExtractDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

{stl_filename}
{{
    extractionMethod    extractFromSurface;
    includedAngle       150;
    geometricTestOnly   yes;
    intersectionMethod  none;
    writeObj            yes;
}}

// ************************************************************************* //
"""

def generate_snappy_hex_mesh_dict(stl_filename: str = "wing.stl", layers: int = 28, first_cell_mm: float = 0.0084) -> str:
    first_cell_m = first_cell_mm / 1000.0
    return f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2212                                 |
|   \\\\  /    A nd           | Case:     snappyHexMeshDict                     |
|    \\\\/     M anipulation  | Geometry: constant/triSurface/{stl_filename}   |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      snappyHexMeshDict;
}}

castellatedMesh true;
snap            true;
addLayers       true;

geometry
{{
    {stl_filename}
    {{
        type triSurfaceMesh;
        name wing;
    }}
}};

castellatedMeshControls
{{
    maxLocalCells 2000000;
    maxGlobalCells 5000000;
    minRefinementCells 10;
    maxLoadUnbalance 0.10;
    nCellsBetweenLevels 3;

    features
    (
        {{
            file "{os.path.splitext(stl_filename)[0]}.eMesh";
            level 4;
        }}
    );

    refinementSurfaces
    {{
        wing
        {{
            level (3 4);
            patchInfo
            {{
                type wall;
            }}
        }}
    }}

    resolveFeatureAngle 30;

    refinementRegions
    {{
    }}

    locationInMesh (0.5 0.5 0.5);
    allowFreeStandingZoneFaces true;
}}

snapControls
{{
    nSmoothPatch 3;
    tolerance 2.0;
    nSolveIter 30;
    nRelaxIter 5;
}}

addLayersControls
{{
    relativeSizes false;
    layers
    {{
        "wing.*"
        {{
            nSurfaceLayers {layers};
        }}
    }}
    expansionRatio 1.15;
    finalLayerThickness {first_cell_m * 5.0:.8f};
    minThickness {first_cell_m * 0.5:.8f};
    nGrow 0;
    featureAngle 110;
    nSmoothSurfaceNormals 1;
    nSmoothNormals 3;
    nSmoothThickness 10;
    maxFaceThicknessRatio 0.5;
    maxThicknessToMedialRatio 0.3;
    minMedianAxisAngle 90;
    nBufferCellsNoExtrude 0;
    nLayerIter 50;
}}

meshQualityControls
{{
    maxNonOrtho 65;
    maxBoundarySkewness 20;
    maxInternalSkewness 4;
    maxConcave 80;
    minVol 1e-13;
    minTetQuality 1e-30;
    minArea -1;
    minTwist 0.02;
    minDeterminant 0.001;
    minFaceWeight 0.02;
    minVolRatio 0.01;
    minTriangleTwist -1;
    nSmoothScale 4;
    errorReduction 0.75;
}}

writeFlags
(
    scalarLevels
    layerSets
    layerFields
);

mergeTolerance 1e-6;
"""

def generate_control_dict(velocity_ms: float = 40.0, chord_m: float = 1.0, span_m: float = 2.0) -> str:
    # Aref = chord * span
    aref = chord_m * span_m
    return f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2212                                 |
|   \\\\  /    A nd           | Case:     controlDict with Forces Monitor       |
|    \\\\/     M anipulation  | Target:   simpleFoam                            |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      controlDict;
}}

application     simpleFoam;

startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         500;
deltaT          1;
writeControl    timeStep;
writeInterval   50;
purgeWrite      2;
writeFormat     ascii;
writePrecision  8;
writeCompression off;
timeFormat      general;
timePrecision   6;
runTimeModifiable true;

functions
{{
    forces
    {{
        type            forceCoeffs;
        libs            ("libforces.so");
        writeControl    timeStep;
        writeInterval   1;

        patches         ("wing.*");
        rho             rhoInf;
        rhoInf          1.225;
        liftDir         (0 1 0);
        dragDir         (1 0 0);
        pitchAxis       (0 0 1);
        magUInf         {velocity_ms};
        lRef            {chord_m};
        Aref            {aref};
        CofR            ({chord_m * 0.25} 0 0);
    }}
}}
"""

def generate_fv_schemes() -> str:
    """
    Generate system/fvSchemes for OpenFOAM v2212.
    Includes mandatory wallDist calculation required for SST k-omega turbulence modeling.
    """
    return """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2212                                 |
|   \\\\  /    A nd           | Case:     fvSchemes                             |
|    \\\\/     M anipulation  | Schemes:  Second-Order Upwind (linearUpwind)    |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      fvSchemes;
}

ddtSchemes
{
    default         steadyState;
}

gradSchemes
{
    default         Gauss linear;
    grad(U)         cellLimited Gauss linear 1;
}

divSchemes
{
    default         none;
    div(phi,U)      bounded Gauss linearUpwind grad(U);
    turbulence      bounded Gauss upwind;
    div(phi,k)      $turbulence;
    div(phi,omega)  $turbulence;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
}

laplacianSchemes
{
    default         Gauss linear corrected;
}

interpolationSchemes
{
    default         linear;
}

snGradSchemes
{
    default         corrected;
}

wallDist
{
    method          meshWave;
}

// ************************************************************************* //
"""

def generate_fv_solution() -> str:
    """
    Generate system/fvSolution for OpenFOAM v2212 SIMPLE algorithm.
    """
    return """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2212                                 |
|   \\\\  /    A nd           | Case:     fvSolution                            |
|    \\\\/     M anipulation  | Solver:   SIMPLE                                |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      fvSolution;
}

solvers
{
    p
    {
        solver          GAMG;
        tolerance       1e-06;
        relTol          0.01;
        smoother        GaussSeidel;
    }

    "(U|k|omega)"
    {
        solver          smoothSolver;
        smoother        GaussSeidel;
        tolerance       1e-06;
        relTol          0.1;
    }
}

SIMPLE
{
    nNonOrthogonalCorrectors 0;
    consistent      yes;
    residualControl
    {
        p               1e-5;
        U               1e-5;
        "(k|omega)"     1e-5;
    }
}

relaxationFactors
{
    equations
    {
        U               0.7;
        k               0.7;
        omega           0.7;
    }
    fields
    {
        p               0.3;
    }
}

// ************************************************************************* //
"""

