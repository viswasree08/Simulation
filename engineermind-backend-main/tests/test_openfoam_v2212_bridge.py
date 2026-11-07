"""
tests/test_openfoam_v2212_bridge.py - Verification Suite for OpenFOAM v2212 Case Bridge.

Validates that:
1. All dictionaries conform to OpenFOAM v2212 FoamFile conventions.
2. 3D farfield blocks have valid symmetry faces and zero 2D 'empty' patches.
3. snappyHexMeshDict contains mathematically consistent inflation layer heights.
4. controlDict registers forceCoeffs with exact reference U, chord, and area.
5. 0/ initial field files (U, p, k, omega, nut) carry correct physical dimensions.
"""

import os
import shutil
import pytest
from case_builder import build_case_directory
from openfoam_bridge import (
    generate_block_mesh_dict_v2212,
    generate_snappy_hex_mesh_dict_v2212,
    generate_control_dict_v2212,
    generate_transport_properties_v2212,
    generate_momentum_transport_v2212,
    generate_initial_field_u_v2212,
    generate_initial_field_p_v2212,
    generate_initial_field_turbulence_v2212
)
import engineering_core


TEST_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_cases_temp"))


@pytest.fixture(autouse=True)
def cleanup_temp_dir():
    os.makedirs(TEST_BASE_DIR, exist_ok=True)
    yield
    if os.path.exists(TEST_BASE_DIR):
        shutil.rmtree(TEST_BASE_DIR, ignore_errors=True)


def test_block_mesh_dict_syntax():
    """Verify blockMeshDict contains valid 3D symmetry and no 'empty' boundaries."""
    bm_text = generate_block_mesh_dict_v2212(chord_m=1.5)
    assert "version     2.0;" in bm_text
    assert "class       dictionary;" in bm_text
    assert "object      blockMeshDict;" in bm_text
    assert "type symmetry;" in bm_text
    assert "empty" not in bm_text.lower()
    # Check 15c and 25c cushion scaling for chord = 1.5
    # min_x = -15 * 1.5 = -22.5, max_x = 1.5 + 25 * 1.5 = 39.0
    assert "-22.5000" in bm_text
    assert "39.0000" in bm_text


def test_snappy_hex_mesh_consistent_layers():
    """Verify snappyHexMeshDict has geometrically consistent layer heights."""
    first_cell_m = 9.4e-6
    shm_text = generate_snappy_hex_mesh_dict_v2212(
        stl_filename="test_airfoil.stl",
        first_cell_m=first_cell_m,
        num_layers=28,
        expansion_ratio=1.15
    )

    assert "object      snappyHexMeshDict;" in shm_text
    assert "nSurfaceLayers 28;" in shm_text
    assert "expansionRatio 1.1500;" in shm_text
    # Expected final thickness = 9.4e-6 * 1.15^27 = ~4.11e-4 m
    expected_final = first_cell_m * (1.15 ** 27)
    assert f"{expected_final:.7f}" in shm_text


def test_control_dict_force_coeffs():
    """Verify controlDict registers forceCoeffs with exact reference area and velocity."""
    U = 45.0
    chord = 1.2
    span = 2.4
    cd_text = generate_control_dict_v2212(velocity_ms=U, chord_m=chord, span_m=span)

    assert "object      controlDict;" in cd_text
    assert "type            forceCoeffs;" in cd_text
    assert f"magUInf         {U:.4f};" in cd_text
    assert f"lRef            {chord:.4f};" in cd_text
    assert f"Aref            {chord * span:.4f};" in cd_text


def test_initial_field_dimensions():
    """Verify physical dimensions in 0/ initial field dictionaries."""
    # U: [0 1 -1 0 0 0 0] (m/s)
    u_text = generate_initial_field_u_v2212(40.0)
    assert "dimensions      [0 1 -1 0 0 0 0];" in u_text
    assert "uniform (40.0000 0 0);" in u_text

    # p: [0 2 -2 0 0 0 0] (kinematic pressure m^2/s^2)
    p_text = generate_initial_field_p_v2212()
    assert "dimensions      [0 2 -2 0 0 0 0];" in p_text

    # Turbulence k, omega, nut
    wall_eval = engineering_core.assess_wall_treatment(target_y_plus=0.8)
    turb = generate_initial_field_turbulence_v2212(k_val=0.375, omega_val=111.8, nut_val=0.00335, wall_treatment=wall_eval)
    # k: [0 2 -2 0 0 0 0] (m^2/s^2)
    assert "dimensions      [0 2 -2 0 0 0 0];" in turb["k"]
    # omega: [0 0 -1 0 0 0 0] (1/s)
    assert "dimensions      [0 0 -1 0 0 0 0];" in turb["omega"]
    # nut: [0 2 -1 0 0 0 0] (m^2/s)
    assert "dimensions      [0 2 -1 0 0 0 0];" in turb["nut"]


def test_build_case_directory_full():
    """Verify full OpenFOAM case construction and ZIP packaging."""
    res = build_case_directory(
        case_id=999,
        base_dir=TEST_BASE_DIR,
        chord_m=1.0,
        velocity_ms=40.0,
        target_y_plus=1.0,
        stl_filename="naca0012.stl"
    )

    case_dir = res["case_directory"]
    assert os.path.exists(os.path.join(case_dir, "system", "blockMeshDict"))
    assert os.path.exists(os.path.join(case_dir, "system", "snappyHexMeshDict"))
    assert os.path.exists(os.path.join(case_dir, "system", "controlDict"))
    assert os.path.exists(os.path.join(case_dir, "constant", "momentumTransport"))
    assert os.path.exists(os.path.join(case_dir, "constant", "transportProperties"))
    assert os.path.exists(os.path.join(case_dir, "constant", "triSurface", "naca0012.stl"))
    assert os.path.exists(os.path.join(case_dir, "0", "U"))
    assert os.path.exists(os.path.join(case_dir, "0", "p"))
    assert os.path.exists(os.path.join(case_dir, "0", "k"))
    assert os.path.exists(os.path.join(case_dir, "0", "omega"))
    assert os.path.exists(os.path.join(case_dir, "0", "nut"))

    # Assert ZIP archive generated
    assert os.path.exists(res["zip_archive_path"])
    assert res["zip_archive_path"].endswith(".zip")

