"""
tests/engineering_core/test_turbulence.py - Turbulence Model and Boundary Condition Verification.
"""

import pytest
import math
from engineering_core.turbulence import (
    turbulence_inlet_boundary_conditions,
    assess_wall_treatment,
    SST_C_MU,
    SST_BETA_STAR
)


def test_turbulence_inlet_conditions_benchmark():
    """
    Verify inflow turbulence boundary conditions (Menter / Wilcox):
    Parameters:
        U = 50.0 m/s, I = 1.0% (0.01), l = 0.01 m
    Analytical Solutions:
        k = 1.5 * (50.0 * 0.01)^2 = 1.5 * (0.5)^2 = 1.5 * 0.25 = 0.375 m^2/s^2
        omega = sqrt(k) / (C_mu^0.25 * l)
              = sqrt(0.375) / (0.09^0.25 * 0.01)
              = 0.6123724 / (0.5477225 * 0.01)
              = 0.6123724 / 0.0054772 = 111.803398... s^-1
        epsilon = C_mu * k^1.5 / l = 0.09 * (0.375)^1.5 / 0.01 = 2.06746... m^2/s^3
        nu_t = k / omega = 0.375 / 111.8034 = 0.003354... m^2/s
    """
    res = turbulence_inlet_boundary_conditions(
        velocity_ms=50.0,
        turbulent_intensity_percent=1.0,
        turbulent_length_scale_m=0.01
    )

    assert math.isclose(res["k_m2_s2"], 0.375, rel_tol=1e-5)
    assert math.isclose(res["omega_per_s"], 111.8034, rel_tol=1e-4)
    # Exact analytical: epsilon = 0.09 * (0.375)^1.5 / 0.01 = 0.09 * 0.22963966 / 0.01 = 2.06675697...
    assert math.isclose(res["epsilon_m2_s3"], 2.066757, rel_tol=1e-4)
    assert math.isclose(res["eddy_viscosity_nut_m2_s"], 0.375 / 111.8034, rel_tol=1e-4)


def test_turbulence_inlet_viscosity_ratio_option():
    """
    Verify alternative viscosity-ratio inlet condition:
        U = 50.0 m/s, I = 1.0%, nu_t / nu = 10.0, nu = 1.5e-5 m^2/s
        k = 0.375 m^2/s^2
        omega = k / (nu * 10) = 0.375 / 1.5e-4 = 2500.0 s^-1
    """
    res = turbulence_inlet_boundary_conditions(
        velocity_ms=50.0,
        turbulent_intensity_percent=1.0,
        viscosity_ratio=10.0,
        nu_m2_s=1.5e-5
    )
    assert math.isclose(res["k_m2_s2"], 0.375, rel_tol=1e-5)
    assert math.isclose(res["omega_per_s"], 2500.0, rel_tol=1e-5)
    assert math.isclose(res["eddy_viscosity_nut_m2_s"], 1.5e-4, rel_tol=1e-5)


def test_turbulence_inlet_invalid_inputs():
    """Verify exceptions on unphysical parameters."""
    with pytest.raises(ValueError, match="velocity_ms"):
        turbulence_inlet_boundary_conditions(0.0)

    with pytest.raises(ValueError, match="turbulent_intensity_percent"):
        turbulence_inlet_boundary_conditions(50.0, turbulent_intensity_percent=-1.0)


def test_assess_wall_treatment_regimes():
    """Verify physics regimes and boundary condition assignment across y+ spectrum."""
    # Viscous sublayer: y+ = 0.8
    r_sub = assess_wall_treatment(0.8)
    assert r_sub["is_physically_recommended"] is True
    assert "Viscous Sublayer" in r_sub["regime"]
    assert r_sub["openfoam_boundary_conditions"]["k"] == "kLowReWallFunction"

    # Buffer layer: y+ = 15.0 (UNRESOLVED / INVALID)
    r_buf = assess_wall_treatment(15.0)
    assert r_buf["is_physically_recommended"] is False
    assert "Buffer Layer" in r_buf["regime"]
    assert r_buf["warning"] is not None

    # Log-law: y+ = 50.0
    r_log = assess_wall_treatment(50.0)
    assert r_log["is_physically_recommended"] is True
    assert "Log-Law" in r_log["regime"]
    assert r_log["openfoam_boundary_conditions"]["k"] == "kqRWallFunction"

    # Excessive coarseness: y+ = 500.0
    r_coarse = assess_wall_treatment(500.0)
    assert r_coarse["is_physically_recommended"] is False
    assert "Excessively Coarse" in r_coarse["regime"]
