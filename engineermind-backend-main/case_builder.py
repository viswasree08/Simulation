"""
Automated OpenFOAM Case Generator & Builder.
Creates true working 3D OpenFOAM case directories on disk and packages them as ZIP files.
Bridged with engineering_core for deterministic physical configuration.
"""

import os
import shutil
import zipfile
from typing import Dict, Any, Optional

import engineering_core
from solver_generator import (
    generate_surface_features_dict,
    generate_fv_schemes,
    generate_fv_solution
)
from openfoam_bridge import (
    generate_block_mesh_dict_v2212,
    generate_snappy_hex_mesh_dict_v2212,
    generate_control_dict_v2212,
    generate_transport_properties_v2212,
    generate_momentum_transport_v2212,
    generate_turbulence_properties_v2212,
    generate_initial_field_u_v2212,
    generate_initial_field_p_v2212,
    generate_initial_field_turbulence_v2212
)
from aerocore import compute_physics


def generate_momentum_transport_dict() -> str:
    return generate_momentum_transport_v2212()


def generate_transport_properties_dict() -> str:
    return generate_transport_properties_v2212()


def generate_initial_field_u(velocity_ms: float) -> str:
    return generate_initial_field_u_v2212(velocity_ms)


def generate_initial_field_p() -> str:
    return generate_initial_field_p_v2212()


def build_case_directory(
    case_id: int,
    base_dir: str,
    chord_m: float = 1.0,
    velocity_ms: float = 40.0,
    target_y_plus: float = 1.0,
    regime: str = "external_aerodynamics",
    stl_filename: str = "wing.stl",
    stl_bytes: Optional[bytes] = None
) -> Dict[str, Any]:
    """
    Builds a complete, valid OpenFOAM case directory on disk under openfoam_cases/case_{id}/.
    Creates 0/, constant/, and system/ directories and all necessary dictionaries.
    Also produces a ZIP archive for one-click downloading.
    """
    case_dir_name = f"case_{case_id}"
    case_path = os.path.join(base_dir, case_dir_name)

    # Subdirectories
    dir_0 = os.path.join(case_path, "0")
    dir_constant = os.path.join(case_path, "constant")
    dir_trisurface = os.path.join(dir_constant, "triSurface")
    dir_system = os.path.join(case_path, "system")

    os.makedirs(dir_0, exist_ok=True)
    os.makedirs(dir_constant, exist_ok=True)
    os.makedirs(dir_trisurface, exist_ok=True)
    os.makedirs(dir_system, exist_ok=True)

    # 1. Deterministic Scientific Metrics via engineering_core
    physics = compute_physics(velocity=velocity_ms, chord_length=chord_m, target_y_plus=target_y_plus, regime=regime)
    first_cell_m = physics["first_cell_height_m"]
    layers = physics["recommended_prism_layers"]
    growth_rate = physics["recommended_growth_rate"]

    # Turbulence boundary derivations
    turb_inflow = engineering_core.turbulence_inlet_boundary_conditions(velocity_ms=velocity_ms, turbulent_intensity_percent=1.0)
    wall_eval = engineering_core.assess_wall_treatment(target_y_plus=target_y_plus)

    # 2. system/ files
    block_mesh = generate_block_mesh_dict_v2212(chord_m=chord_m)
    surf_features = generate_surface_features_dict(stl_filename=stl_filename)
    snappy_hex = generate_snappy_hex_mesh_dict_v2212(
        stl_filename=stl_filename,
        first_cell_m=first_cell_m,
        num_layers=layers,
        expansion_ratio=growth_rate
    )
    control_dict = generate_control_dict_v2212(velocity_ms=velocity_ms, chord_m=chord_m, span_m=chord_m * 2.0)
    fv_schemes = generate_fv_schemes()
    fv_solution = generate_fv_solution()

    with open(os.path.join(dir_system, "blockMeshDict"), "w", encoding="utf-8") as f:
        f.write(block_mesh)
    # surfaceFeatureExtractDict is required for OpenCFD v2212 surfaceFeatureExtract
    with open(os.path.join(dir_system, "surfaceFeatureExtractDict"), "w", encoding="utf-8") as f:
        f.write(surf_features)
    # Also write legacy surfaceFeaturesDict symlink/copy for backward compatibility
    with open(os.path.join(dir_system, "surfaceFeaturesDict"), "w", encoding="utf-8") as f:
        f.write(surf_features)
    with open(os.path.join(dir_system, "snappyHexMeshDict"), "w", encoding="utf-8") as f:
        f.write(snappy_hex)
    with open(os.path.join(dir_system, "controlDict"), "w", encoding="utf-8") as f:
        f.write(control_dict)
    with open(os.path.join(dir_system, "fvSchemes"), "w", encoding="utf-8") as f:
        f.write(fv_schemes)
    with open(os.path.join(dir_system, "fvSolution"), "w", encoding="utf-8") as f:
        f.write(fv_solution)

    # 3. constant/ files
    mom_transport = generate_momentum_transport_v2212(turbulence_model="kOmegaSST")
    trans_props = generate_transport_properties_v2212(kinematic_viscosity=1.46e-05)
    turb_props = generate_turbulence_properties_v2212(turbulence_model="kOmegaSST")

    with open(os.path.join(dir_constant, "momentumTransport"), "w", encoding="utf-8") as f:
        f.write(mom_transport)
    with open(os.path.join(dir_constant, "turbulenceProperties"), "w", encoding="utf-8") as f:
        f.write(turb_props)
    with open(os.path.join(dir_constant, "transportProperties"), "w", encoding="utf-8") as f:
        f.write(trans_props)

    # Write STL geometry if provided
    target_stl_path = os.path.join(dir_trisurface, stl_filename)
    if stl_bytes:
        with open(target_stl_path, "wb") as f:
            f.write(stl_bytes)
    elif not os.path.exists(target_stl_path):
        with open(target_stl_path, "w", encoding="utf-8") as f:
            f.write(f"solid {stl_filename}\nfacet normal 0 0 1\nouter loop\nvertex 0 0 0\nvertex {chord_m} 0 0\nvertex 0.5 0.1 0\nendloop\nendfacet\nendsolid {stl_filename}\n")

    # 4. 0/ initial field files
    with open(os.path.join(dir_0, "U"), "w", encoding="utf-8") as f:
        f.write(generate_initial_field_u_v2212(velocity_ms=velocity_ms))
    with open(os.path.join(dir_0, "p"), "w", encoding="utf-8") as f:
        f.write(generate_initial_field_p_v2212())

    turb_fields = generate_initial_field_turbulence_v2212(
        k_val=turb_inflow["k_m2_s2"],
        omega_val=turb_inflow["omega_per_s"],
        nut_val=turb_inflow["eddy_viscosity_nut_m2_s"],
        wall_treatment=wall_eval
    )
    with open(os.path.join(dir_0, "k"), "w", encoding="utf-8") as f:
        f.write(turb_fields["k"])
    with open(os.path.join(dir_0, "omega"), "w", encoding="utf-8") as f:
        f.write(turb_fields["omega"])
    with open(os.path.join(dir_0, "nut"), "w", encoding="utf-8") as f:
        f.write(turb_fields["nut"])

    # Create ZIP archive
    zip_filename = f"{case_dir_name}.zip"
    zip_path = os.path.join(base_dir, zip_filename)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(case_path):
            for file in files:
                abs_file = os.path.join(root, file)
                rel_path = os.path.relpath(abs_file, base_dir)
                zipf.write(abs_file, rel_path)

    return {
        "case_id": case_id,
        "case_directory": case_path,
        "zip_archive_path": zip_path,
        "generated_files": [
            "system/blockMeshDict",
            "system/surfaceFeatureExtractDict",
            "system/surfaceFeaturesDict",
            "system/snappyHexMeshDict",
            "system/controlDict",
            "system/fvSchemes",
            "system/fvSolution",
            "constant/momentumTransport",
            "constant/turbulenceProperties",
            "constant/transportProperties",
            f"constant/triSurface/{stl_filename}",
            "0/U",
            "0/p",
            "0/k",
            "0/omega",
            "0/nut"
        ],
        "physics_metrics": physics
    }
