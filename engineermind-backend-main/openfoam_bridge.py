"""
openfoam_bridge.py - Unified Engineering-to-OpenFOAM v2212 Bridge.

Translates validated scientific computations from `engineering_core` into fully compliant
OpenFOAM v2212 (OpenCFD/ESI) directory structures and dictionaries.

Key Responsibilities:
1. Sizing farfield hexahedral domains via AIAA DPW standards without 2D empty patches.
2. Generating geometrically consistent snappyHexMesh boundary layer prism controls.
3. Mapping thermophysical properties (nu = mu/rho) to constant/transportProperties.
4. Setting up modern constant/momentumTransport (v2212 RAS kOmegaSST).
5. Configuring 0/ initial and boundary fields for U, p, k, omega, and nut.
6. Configuring system/controlDict runtime force monitors (forceCoeffs) using exact U_inf and chord.
"""

import os
import math
from typing import Dict, Any, Optional

import engineering_core


def generate_v2212_header(class_type: str, object_name: str, location: Optional[str] = None) -> str:
    """Standard OpenFOAM v2212 ASCII dictionary header."""
    loc_entry = f'\n    location    "{location}";' if location else ""
    return f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2212                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  | Engineering Core Bridge                         |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       {class_type};{loc_entry}
    object      {object_name};
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
"""


def generate_block_mesh_dict_v2212(
    chord_m: float,
    inlet_factor: float = 15.0,
    outlet_factor: float = 25.0,
    lateral_factor: float = 15.0,
    span_m: Optional[float] = None
) -> str:
    """
    Generate 3D blockMeshDict using validated AIAA DPW domain cushions.
    Replaces duplicated logic and ensures pure 3D symmetry patches without 2D 'empty'.
    """
    span = span_m if span_m is not None else (chord_m * 2.0)
    domain = engineering_core.calculate_external_aero_domain_bounds(
        chord_m=chord_m,
        inlet_factor=inlet_factor,
        outlet_factor=outlet_factor,
        lateral_factor=lateral_factor,
        span_m=span
    )

    b = domain["bounds"]
    x_min, x_max = b["min_x"], b["max_x"]
    y_min, y_max = b["min_y"], b["max_y"]
    z_min, z_max = b["min_z"], b["max_z"]

    # Suggested cell counts based on aspect ratio
    nx = max(40, int(domain["dimensions"]["length_x_m"] / (chord_m * 0.5)))
    ny = max(30, int(domain["dimensions"]["height_y_m"] / (chord_m * 0.5)))
    nz = max(10, int(domain["dimensions"]["width_z_m"] / (chord_m * 0.1)))

    header = generate_v2212_header("dictionary", "blockMeshDict", "system")
    return f"""{header}
scale   1;

vertices
(
    ({x_min:.4f} {y_min:.4f} {z_min:.4f}) // 0
    ({x_max:.4f} {y_min:.4f} {z_min:.4f}) // 1
    ({x_max:.4f} {y_max:.4f} {z_min:.4f}) // 2
    ({x_min:.4f} {y_max:.4f} {z_min:.4f}) // 3
    ({x_min:.4f} {y_min:.4f} {z_max:.4f}) // 4
    ({x_max:.4f} {y_min:.4f} {z_max:.4f}) // 5
    ({x_max:.4f} {y_max:.4f} {z_max:.4f}) // 6
    ({x_min:.4f} {y_max:.4f} {z_max:.4f}) // 7
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
            (0 3 2 1) // back
            (4 5 6 7) // front
        );
    }}
);

mergePatchPairs
(
);

// ************************************************************************* //
"""


def generate_snappy_hex_mesh_dict_v2212(
    stl_filename: str,
    first_cell_m: float,
    num_layers: int = 28,
    expansion_ratio: float = 1.15
) -> str:
    """
    Generate mathematically consistent snappyHexMeshDict for OpenFOAM v2212.
    Eliminates historical 9x finalLayerThickness conflict by using exact geometric progression.
    """
    layer_cfg = engineering_core.calculate_snappy_hex_mesh_layers(
        first_cell_m=first_cell_m,
        num_layers=num_layers,
        expansion_ratio=expansion_ratio
    )

    final_thickness = layer_cfg["finalLayerThickness"]
    min_thickness = layer_cfg["minThickness"]

    # Determine base name without extension for .eMesh feature file
    base_surf_name = os.path.splitext(stl_filename)[0]

    header = generate_v2212_header("dictionary", "snappyHexMeshDict", "system")
    return f"""{header}
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
    maxLocalCells 1000000;
    maxGlobalCells 2000000;
    minRefinementCells 10;
    maxLoadUnbalance 0.10;
    nCellsBetweenLevels 3;

    features
    (
        {{
            file "{base_surf_name}.eMesh";
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
            nSurfaceLayers {num_layers};
        }}
    }}
    expansionRatio {expansion_ratio:.4f};
    finalLayerThickness {final_thickness:.9f};
    minThickness {min_thickness:.9f};
    nGrow 0;
    featureAngle 110;
    nSmoothSurfaceNormals 1;
    nSmoothNormals 3;
    nSmoothThickness 10;
    maxFaceThicknessRatio 0.5;
    maxThicknessToMedialRatio 0.3;
    minMedialAxisAngle 90;
    minMedianAxisAngle 90;
    slipFeatureAngle 30;
    nRelaxIter 5;
    nBufferCellsNoExtrude 0;
    nLayerIter 50;
    nRelaxedIter 20;
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

// Optional write flags
// writeFlags
// (
//     scalarLevels
//     layerSets
//     layerFields
// );

// Merge tolerance. Fraction of overall bounding box of initial mesh.
mergeTolerance 1e-6;

// ************************************************************************* //
"""


def generate_control_dict_v2212(
    velocity_ms: float,
    chord_m: float,
    span_m: Optional[float] = None,
    solver_name: str = "simpleFoam",
    end_time: int = 1000,
    write_interval: int = 100
) -> str:
    """
    Generate system/controlDict with runtime forceCoeffs function object.
    Includes mandatory CofR (quarter-chord aerodynamic center) for moment computation in OpenFOAM v2212.
    """
    span = span_m if span_m is not None else (chord_m * 2.0)
    ref_area = chord_m * span
    c_quarter = chord_m * 0.25

    header = generate_v2212_header("dictionary", "controlDict", "system")
    return f"""{header}
application     {solver_name};

startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         {end_time};
deltaT          1;
writeControl    timeStep;
writeInterval   {write_interval};
purgeWrite      2;
writeFormat     ascii;
writePrecision  7;
writeCompression off;
timeFormat      general;
timePrecision   6;
runTimeModifiable true;

functions
{{
    forceCoeffs
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
        CofR            ({c_quarter:.4f} 0 0);
        magUInf         {velocity_ms:.4f};
        lRef            {chord_m:.4f};
        Aref            {ref_area:.4f};
    }}
}}

// ************************************************************************* //
"""


def generate_transport_properties_v2212(kinematic_viscosity: float = 1.46e-5) -> str:
    """Generate constant/transportProperties for incompressible Newtonian fluid."""
    header = generate_v2212_header("dictionary", "transportProperties", "constant")
    return f"""{header}
transportModel  Newtonian;
nu              [0 2 -1 0 0 0 0] {kinematic_viscosity:.8e};

// ************************************************************************* //
"""


def generate_turbulence_properties_v2212(turbulence_model: str = "kOmegaSST") -> str:
    """
    Generate constant/turbulenceProperties required by OpenFOAM v2212 simpleFoam.
    """
    header = generate_v2212_header("dictionary", "turbulenceProperties", "constant")
    return f"""{header}
simulationType  RAS;

RAS
{{
    RASModel        {turbulence_model};
    turbulence      on;
    printCoeffs     on;
}}

// ************************************************************************* //
"""


def generate_momentum_transport_v2212(turbulence_model: str = "kOmegaSST") -> str:
    """Generate constant/momentumTransport (standard in OpenFOAM v20+ and v2212+ compressible/multiphase)."""
    header = generate_v2212_header("dictionary", "momentumTransport", "constant")
    return f"""{header}
simulationType  RAS;

RAS
{{
    model           {turbulence_model};
    turbulence      on;
    printCoeffs     on;
}}

// ************************************************************************* //
"""


def generate_initial_field_u_v2212(velocity_ms: float) -> str:
    """Generate 0/U with freestream vector and no-slip wall."""
    header = generate_v2212_header("volVectorField", "U", "0")
    return f"""{header}
dimensions      [0 1 -1 0 0 0 0];
internalField   uniform ({velocity_ms:.4f} 0 0);

boundaryField
{{
    inlet
    {{
        type            fixedValue;
        value           uniform ({velocity_ms:.4f} 0 0);
    }}
    outlet
    {{
        type            zeroGradient;
    }}
    topBottomFrontBack
    {{
        type            symmetry;
    }}
    wing
    {{
        type            noSlip;
    }}
}}

// ************************************************************************* //
"""


def generate_initial_field_p_v2212() -> str:
    """Generate 0/p (kinematic pressure p/rho [m^2/s^2])."""
    header = generate_v2212_header("volScalarField", "p", "0")
    return f"""{header}
dimensions      [0 2 -2 0 0 0 0];
internalField   uniform 0;

boundaryField
{{
    inlet
    {{
        type            zeroGradient;
    }}
    outlet
    {{
        type            fixedValue;
        value           uniform 0;
    }}
    topBottomFrontBack
    {{
        type            symmetry;
    }}
    wing
    {{
        type            zeroGradient;
    }}
}}

// ************************************************************************* //
"""


def generate_initial_field_turbulence_v2212(
    k_val: float,
    omega_val: float,
    nut_val: float,
    wall_treatment: Dict[str, Any]
) -> Dict[str, str]:
    """
    Generate 0/k, 0/omega, and 0/nut fields mapped from deterministic turbulence calculations.
    """
    bc = wall_treatment.get("openfoam_boundary_conditions", {})
    nut_bc = bc.get("nut", "nutkWallFunction")
    k_bc = bc.get("k", "kLowReWallFunction")
    omega_bc = bc.get("omega", "omegaWallFunction")

    # 0/k
    header_k = generate_v2212_header("volScalarField", "k", "0")
    field_k = f"""{header_k}
dimensions      [0 2 -2 0 0 0 0];
internalField   uniform {k_val:.6e};

boundaryField
{{
    inlet
    {{
        type            fixedValue;
        value           uniform {k_val:.6e};
    }}
    outlet
    {{
        type            zeroGradient;
    }}
    topBottomFrontBack
    {{
        type            symmetry;
    }}
    wing
    {{
        type            {k_bc};
        value           uniform {k_val:.6e};
    }}
}}

// ************************************************************************* //
"""

    # 0/omega
    header_omega = generate_v2212_header("volScalarField", "omega", "0")
    field_omega = f"""{header_omega}
dimensions      [0 0 -1 0 0 0 0];
internalField   uniform {omega_val:.6e};

boundaryField
{{
    inlet
    {{
        type            fixedValue;
        value           uniform {omega_val:.6e};
    }}
    outlet
    {{
        type            zeroGradient;
    }}
    topBottomFrontBack
    {{
        type            symmetry;
    }}
    wing
    {{
        type            {omega_bc};
        value           uniform {omega_val:.6e};
    }}
}}

// ************************************************************************* //
"""

    # 0/nut
    header_nut = generate_v2212_header("volScalarField", "nut", "0")
    field_nut = f"""{header_nut}
dimensions      [0 2 -1 0 0 0 0];
internalField   uniform {nut_val:.6e};

boundaryField
{{
    inlet
    {{
        type            calculated;
        value           uniform {nut_val:.6e};
    }}
    outlet
    {{
        type            calculated;
        value           uniform {nut_val:.6e};
    }}
    topBottomFrontBack
    {{
        type            symmetry;
    }}
    wing
    {{
        type            {nut_bc};
        value           uniform 0;
    }}
}}

// ************************************************************************* //
"""

    return {"k": field_k, "omega": field_omega, "nut": field_nut}

