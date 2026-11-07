"""
tests/engineering_core/test_aerodynamics.py - Aerodynamic Formulations Verification.
"""

import pytest
import math
from engineering_core.aerodynamics import (
    reynolds_number,
    mach_number,
    dynamic_pressure,
    classify_flow_regime,
    thin_airfoil_theory_cl
)
from engineering_core.fluid_properties import ISA_RHO0, ISA_MU0


def test_reynolds_number_benchmark():
    """
    Verify Reynolds number against analytical aerospace benchmarks.
    Case 1: Standard wind tunnel model
        U = 50.0 m/s, c = 0.5 m, rho = 1.225 kg/m^3, mu = 1.789e-5 Pa*s
        Re = (1.225 * 50.0 * 0.5) / 1.789e-5 = 30.625 / 1.789e-5 = 1,711,850.195...
    """
    re = reynolds_number(50.0, 0.5, ISA_RHO0, ISA_MU0)
    assert math.isclose(re, 1711850.2, rel_tol=1e-5)

    # Dimensional scaling: doubling velocity doubles Re
    re2 = reynolds_number(100.0, 0.5, ISA_RHO0, ISA_MU0)
    assert math.isclose(re2, 2.0 * re, rel_tol=1e-12)


def test_reynolds_number_invalid_inputs():
    """Verify strict physical validation for non-positive inputs."""
    with pytest.raises(ValueError, match="velocity_ms"):
        reynolds_number(0.0, 1.0)
    with pytest.raises(ValueError, match="velocity_ms"):
        reynolds_number(-10.0, 1.0)
    with pytest.raises(ValueError, match="chord_m"):
        reynolds_number(10.0, 0.0)


def test_mach_number_benchmark():
    """
    Verify Mach number calculation:
        U = 68.056 m/s, a = 340.28 m/s => Ma = 0.200
        U = 1020.84 m/s, a = 340.28 m/s => Ma = 3.000 (Supersonic)
    """
    assert math.isclose(mach_number(68.056, 340.28), 0.2, rel_tol=1e-4)
    assert math.isclose(mach_number(1020.84, 340.28), 3.0, rel_tol=1e-4)


def test_dynamic_pressure_benchmark():
    """
    Verify dynamic pressure q = 0.5 * rho * U^2:
        rho = 1.225 kg/m^3, U = 40.0 m/s
        q = 0.5 * 1.225 * 1600 = 980.0 Pa
    """
    q = dynamic_pressure(40.0, ISA_RHO0)
    assert math.isclose(q, 980.0, abs_tol=1e-6)

    # Scaling: doubling velocity quadruples dynamic pressure
    q2 = dynamic_pressure(80.0, ISA_RHO0)
    assert math.isclose(q2, 4.0 * 980.0, abs_tol=1e-6)


def test_flow_regime_classification():
    """Verify standard aerodynamic flow regime boundaries."""
    # Incompressible Turbulent (Ma < 0.3, Re > 5e5)
    r1 = classify_flow_regime(1e6, 0.15)
    assert r1["compressibility_regime"] == "Incompressible"
    assert r1["turbulence_regime"] == "Turbulent"

    # Subsonic Compressible (0.3 <= Ma < 0.8)
    r2 = classify_flow_regime(2e6, 0.55)
    assert r2["compressibility_regime"] == "Subsonic Compressible"

    # Transonic (0.8 <= Ma < 1.2)
    r3 = classify_flow_regime(5e6, 0.85)
    assert r3["compressibility_regime"] == "Transonic"

    # Supersonic (1.2 <= Ma < 5.0)
    r4 = classify_flow_regime(1e7, 2.2)
    assert r4["compressibility_regime"] == "Supersonic"

    # Hypersonic (Ma >= 5.0)
    r5 = classify_flow_regime(1e7, 6.0)
    assert r5["compressibility_regime"] == "Hypersonic"

    # Laminar / Transitional (Re < 5e5)
    r6 = classify_flow_regime(1e5, 0.1)
    assert r6["turbulence_regime"] == "Laminar / Transitional"


def test_thin_airfoil_theory_benchmarks():
    """
    Verify classical thin airfoil theory:
    dCl/dalpha = 2 * pi per radian = 2 * pi * (pi / 180) = ~0.10966 per degree.
    At alpha = 0 deg: Cl = 0.0
    At alpha = 5 deg: Cl = 5 * 0.109662 = 0.54831
    At alpha = 10 deg: Cl = 10 * 0.109662 = 1.09662
    """
    assert math.isclose(thin_airfoil_theory_cl(0.0), 0.0, abs_tol=1e-9)
    assert math.isclose(thin_airfoil_theory_cl(5.0), 5.0 * (2.0 * math.pi * math.pi / 180.0), rel_tol=1e-4)
    assert math.isclose(thin_airfoil_theory_cl(10.0), 10.0 * (2.0 * math.pi * math.pi / 180.0), rel_tol=1e-4)

