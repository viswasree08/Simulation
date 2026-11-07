"""
tests/engineering_core/test_boundary_layer.py - Boundary Layer and Prism Inflation Verification.
"""

import pytest
import math
from engineering_core.boundary_layer import (
    skin_friction_coefficient_flat_plate,
    wall_shear_stress,
    friction_velocity,
    first_cell_height,
    boundary_layer_thickness_flat_plate,
    generate_geometric_layer_stack
)
from engineering_core.fluid_properties import ISA_RHO0, ISA_MU0


def test_skin_friction_schlichting_benchmarks():
    """
    Verify Schlichting flat-plate skin friction formula:
        Cf = (2 * log10(Re_x) - 0.65)^(-2.3)
    Published references (Schlichting & Gersten, 2017):
    - Re_x = 10^6:
        log10(1e6) = 6.0
        denom = (2 * 6 - 0.65) = 11.35
        Cf = 11.35^(-2.3) = 0.003738...
    - Re_x = 10^7:
        log10(1e7) = 7.0
        denom = (2 * 7 - 0.65) = 13.35
        Cf = 13.35^(-2.3) = 0.002636...
    - Re_x = 10^8:
        denom = 15.35
        Cf = 15.35^(-2.3) = 0.001944...
    """
    # Analytical evaluation of (2 * log10(Re_x) - 0.65)^(-2.3):
    # Re_x = 10^6: (2 * 6 - 0.65)^(-2.3) = 11.35^(-2.3) = 0.0037455...
    # Re_x = 10^7: (2 * 7 - 0.65)^(-2.3) = 13.35^(-2.3) = 0.0025786...
    # Re_x = 10^8: (2 * 8 - 0.65)^(-2.3) = 15.35^(-2.3) = 0.0018705...
    cf_1e6 = skin_friction_coefficient_flat_plate(1e6, method="schlichting")
    assert math.isclose(cf_1e6, 0.0037455, rel_tol=1e-4)

    cf_1e7 = skin_friction_coefficient_flat_plate(1e7, method="schlichting")
    assert math.isclose(cf_1e7, 0.0025786, rel_tol=1e-4)

    cf_1e8 = skin_friction_coefficient_flat_plate(1e8, method="schlichting")
    assert math.isclose(cf_1e8, 0.0018705, rel_tol=1e-4)


def test_skin_friction_prandtl_benchmarks():
    """
    Verify Prandtl 1/7th power law:
        Cf = 0.0592 / (Re_x ^ 0.2)
    - Re_x = 10^6: Cf = 0.0592 / 15.8489 = 0.003735...
    - Re_x = 10^7: Cf = 0.0592 / 25.1188 = 0.002356...
    """
    cf_p_1e6 = skin_friction_coefficient_flat_plate(1e6, method="prandtl_1_7")
    assert math.isclose(cf_p_1e6, 0.003735, rel_tol=1e-3)


def test_boundary_layer_invalid_reynolds():
    """Verify exception on sub-turbulent Reynolds numbers (Re < 10,000)."""
    with pytest.raises(ValueError, match="invalid for Re_x"):
        skin_friction_coefficient_flat_plate(5000.0)


def test_first_cell_height_dimensional_scaling():
    """
    Verify first cell height calculation:
        delta_s = (y+ * nu) / u_tau
    At y+ = 1.0, u_tau = 1.551 m/s, nu = 1.789e-5 / 1.225 = 1.4604e-5 m^2/s:
        delta_s = 1.4604e-5 / 1.551 = 9.4158e-6 m (0.009416 mm)
    """
    rho = 1.225
    mu = 1.789e-5
    nu = mu / rho
    u_tau = 1.551

    ds = first_cell_height(1.0, u_tau, nu)
    assert math.isclose(ds, 9.4158e-6, rel_tol=1e-3)

    # Linearity: doubling y+ doubles first cell height
    ds_y2 = first_cell_height(2.0, u_tau, nu)
    assert math.isclose(ds_y2, 2.0 * ds, rel_tol=1e-12)


def test_boundary_layer_thickness_benchmarks():
    """
    Verify 99% boundary layer thickness delta_99 = 0.37 * x / (Re_x^0.2):
    At x = 1.0 m, Re_x = 10^6:
        delta_99 = 0.37 * 1.0 / (1e6^0.2) = 0.37 / 15.84893 = 0.023345 m (23.35 mm)
    """
    delta = boundary_layer_thickness_flat_plate(1.0, 1e6)
    assert math.isclose(delta, 0.023345, rel_tol=1e-3)


def test_geometric_layer_stack_progression():
    """
    Verify geometric series progression for prism inflation:
        h_i = h_1 * r^(i-1)
        Total = h_1 * (r^N - 1) / (r - 1)
    Parameters: h_1 = 1e-5 m, r = 1.15, N = 28 layers.
        h_28 = 1e-5 * 1.15^27 = 1e-5 * 43.7438 = 4.37438e-4 m
        Total = 1e-5 * (1.15^28 - 1) / 0.15 = 1e-5 * 49.3054 / 0.15 = 3.2870e-3 m (3.287 mm)
    """
    h1 = 1e-5
    r = 1.15
    N = 28
    stack = generate_geometric_layer_stack(first_cell_m=h1, growth_rate=r, num_layers=N)

    assert stack["num_layers"] == N
    assert len(stack["layer_heights_m"]) == N
    assert len(stack["layer_cumulative_y_m"]) == N

    # Verify analytical sum formula
    expected_total = h1 * ((r ** N) - 1.0) / (r - 1.0)
    assert math.isclose(stack["total_prism_thickness_m"], expected_total, rel_tol=1e-6)

    # Verify final layer thickness
    expected_final = h1 * (r ** (N - 1))
    assert math.isclose(stack["final_layer_thickness_m"], expected_final, rel_tol=1e-6)
