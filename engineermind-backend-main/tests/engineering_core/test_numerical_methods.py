"""
tests/engineering_core/test_numerical_methods.py - Numerical Methods and Post-Processing Verification.
"""

import pytest
import math
import numpy as np
from engineering_core.numerical_methods import (
    pressure_coefficient,
    compute_rolling_standard_deviation,
    courant_number_1d
)
from engineering_core.fluid_properties import ISA_RHO0


def test_pressure_coefficient_kinematic():
    """
    Verify incompressible OpenFOAM kinematic pressure:
        p_OF = p / rho [m^2/s^2]
        Cp = p_OF / (0.5 * U_inf^2)
    Case: Stagnation point where p_tot - p_inf = 0.5 * rho * U^2 => p_OF = 0.5 * U^2
    For U = 40.0 m/s:
        p_OF_stag = 0.5 * 1600 = 800.0 m^2/s^2
        Cp = 800.0 / (0.5 * 1600) = 1.000000
    """
    cp_stag = pressure_coefficient(
        surface_pressure=800.0,
        freestream_velocity_ms=40.0,
        is_kinematic_pressure=True
    )
    assert math.isclose(cp_stag, 1.0, abs_tol=1e-7)

    # Suction peak: p_OF = -1200 m^2/s^2 => Cp = -1200 / 800 = -1.5
    cp_suction = pressure_coefficient(-1200.0, 40.0, is_kinematic_pressure=True)
    assert math.isclose(cp_suction, -1.5, abs_tol=1e-7)


def test_pressure_coefficient_static_si():
    """
    Verify standard physical gauge pressure in Pascals:
        Cp = (p - p_inf) / (0.5 * rho * U^2)
    For U = 40.0 m/s, rho = 1.225 kg/m^3:
        q_inf = 980.0 Pa
        At p = 980.0 Pa => Cp = 1.0
        At p = 0.0 Pa (freestream) => Cp = 0.0
    """
    cp_si_stag = pressure_coefficient(980.0, 40.0, rho_kg_m3=ISA_RHO0, is_kinematic_pressure=False)
    assert math.isclose(cp_si_stag, 1.0, abs_tol=1e-7)

    cp_si_free = pressure_coefficient(0.0, 40.0, rho_kg_m3=ISA_RHO0, is_kinematic_pressure=False)
    assert math.isclose(cp_si_free, 0.0, abs_tol=1e-7)


def test_pressure_coefficient_numpy_vectorization():
    """Verify NumPy array handling."""
    pressures = np.array([800.0, 400.0, 0.0, -800.0])
    cps = pressure_coefficient(pressures, 40.0, is_kinematic_pressure=True)
    expected = np.array([1.0, 0.5, 0.0, -1.0])
    np.testing.assert_allclose(cps, expected, rtol=1e-6)


def test_compute_rolling_standard_deviation_benchmark():
    """
    Verify statistical sample mean and Bessel-corrected sample standard deviation:
        values = [10.0, 12.0, 23.0, 23.0, 16.0, 23.0, 21.0, 16.0] (N = 8)
        Sum = 144, Mean = 18.0
        Sample variance s^2 = sum((x - 18)^2) / 7 = (64 + 36 + 25 + 25 + 4 + 25 + 9 + 4) / 7 = 192 / 7 = 27.42857
        s = sqrt(27.42857) = 5.237225...
    """
    vals = [10.0, 12.0, 23.0, 23.0, 16.0, 23.0, 21.0, 16.0]
    res = compute_rolling_standard_deviation(vals, window_size=8)
    assert math.isclose(res["mean"], 18.0, rel_tol=1e-5)
    assert math.isclose(res["standard_deviation"], 5.237225, rel_tol=1e-4)


def test_courant_number_1d_benchmark():
    """
    Verify 1D CFL:
        Co = U * dt / dx
        U = 100.0 m/s, dt = 1e-4 s, dx = 0.02 m => Co = 100 * 0.0001 / 0.02 = 0.500
    """
    co = courant_number_1d(velocity_ms=100.0, delta_t_s=1e-4, delta_x_m=0.02)
    assert math.isclose(co, 0.5, abs_tol=1e-7)

