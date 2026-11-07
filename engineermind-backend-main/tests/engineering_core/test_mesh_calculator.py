"""
tests/engineering_core/test_mesh_calculator.py - CFD Domain and Snappy Hex Mesh Verification.
"""

import pytest
import math
from engineering_core.mesh_calculator import (
    calculate_external_aero_domain_bounds,
    calculate_snappy_hex_mesh_layers
)


def test_domain_bounds_sizing():
    """
    Verify 3D aerodynamic wind tunnel domain extents:
    c = 2.0 m, span = 0.5 m, inlet = 15c, outlet = 25c, lateral = 15c.
    Upstream inlet = 15 * 2 = 30 m => min_x = -30.0
    Downstream outlet = 25 * 2 = 50 m => max_x = 2.0 + 50.0 = 52.0
    Lateral = 15 * 2 = 30 m => min_y = -30.0, max_y = 30.0
    Spanwise = 0.5 m => min_z = -0.25, max_z = 0.25
    """
    res = calculate_external_aero_domain_bounds(
        chord_m=2.0,
        inlet_factor=15.0,
        outlet_factor=25.0,
        lateral_factor=15.0,
        span_m=0.5
    )

    b = res["bounds"]
    assert b["min_x"] == -30.0
    assert b["max_x"] == 52.0
    assert b["min_y"] == -30.0
    assert b["max_y"] == 30.0
    assert b["min_z"] == -0.25
    assert b["max_z"] == 0.25

    dims = res["dimensions"]
    assert dims["length_x_m"] == 82.0
    assert dims["height_y_m"] == 60.0
    assert dims["width_z_m"] == 0.5


def test_domain_bounds_invalid_inputs():
    """Verify exceptions on zero or negative geometric parameters."""
    with pytest.raises(ValueError, match="chord_m"):
        calculate_external_aero_domain_bounds(0.0)
    with pytest.raises(ValueError, match="inlet_factor"):
        calculate_external_aero_domain_bounds(1.0, inlet_factor=-5.0)


def test_snappy_hex_mesh_layer_consistency():
    """
    Verify mathematical consistency of snappyHexMesh controls:
    h1 = 1e-5 m, r = 1.15, N = 28.
    Ensures finalLayerThickness = h1 * 1.15^27 (~4.374e-4 m) is consistent with the progression.
    """
    layers = calculate_snappy_hex_mesh_layers(first_cell_m=1e-5, num_layers=28, expansion_ratio=1.15)

    assert layers["relativeSizes"] is False
    assert layers["nSurfaceLayers"] == 28
    assert layers["expansionRatio"] == 1.15
    assert layers["firstLayerThickness"] == 1e-5

    # Consistency check
    assert layers["math_consistency_check"]["is_geometrically_consistent"] is True
    assert math.isclose(
        layers["finalLayerThickness"],
        1e-5 * (1.15 ** 27),
        rel_tol=1e-5
    )
    # minThickness check
    assert layers["minThickness"] == 1e-5 * 0.25

