"""
tests/engineering_core/test_fluid_properties.py - Thermophysical Fluid Verification.
"""

import pytest
import math
from engineering_core.fluid_properties import (
    sutherland_viscosity,
    standard_atmosphere_isa,
    get_fluid_properties,
    ISA_P0,
    ISA_T0,
    ISA_RHO0,
    ISA_MU0
)


def test_sutherland_viscosity_known_benchmarks():
    """
    Verify Sutherland's equation against published experimental data for dry air.
    Published reference values (Frank M. White, Fluid Mechanics, Appendix A):
    - T = 273.15 K: mu = 1.716e-5 Pa*s
    - T = 300.00 K: mu ~ 1.846e-5 Pa*s
    - T = 400.00 K: mu ~ 2.286e-5 Pa*s
    """
    # At T_ref = 273.15 K, Sutherland law must evaluate exactly to mu_ref = 1.716e-5
    mu_273 = sutherland_viscosity(273.15)
    assert math.isclose(mu_273, 1.716e-5, rel_tol=1e-5)

    # At 300 K
    mu_300 = sutherland_viscosity(300.0)
    assert math.isclose(mu_300, 1.846e-5, rel_tol=1e-2)

    # At 400 K
    mu_400 = sutherland_viscosity(400.0)
    assert math.isclose(mu_400, 2.286e-5, rel_tol=1e-2)

    # Standard atmosphere sea-level T = 288.15 K
    mu_sl = sutherland_viscosity(288.15)
    assert math.isclose(mu_sl, 1.789e-5, rel_tol=1e-2)


def test_sutherland_temperature_bounds():
    """Verify temperature validity range constraints [100 K, 1900 K]."""
    with pytest.raises(ValueError, match="temperature_k"):
        sutherland_viscosity(50.0)

    with pytest.raises(ValueError, match="temperature_k"):
        sutherland_viscosity(2500.0)


def test_standard_atmosphere_isa_benchmarks():
    """
    Verify standard atmosphere against official NOAA/NASA/USAF 1976 tables:
    Sea Level (h = 0 m):
        T = 288.15 K
        p = 101325 Pa
        rho = 1.2250 kg/m^3
        a = 340.294 m/s
    h = 2000 m:
        T = 288.15 - 0.0065 * 2000 = 275.15 K
        p = 79495 Pa (+/- 5 Pa)
        rho = 1.0065 kg/m^3 (+/- 0.005)
    h = 10,000 m:
        T = 288.15 - 65 = 223.15 K
        p = 26499 Pa (+/- 20 Pa)
        rho = 0.4135 kg/m^3 (+/- 0.005)
    """
    # Sea Level
    sl = standard_atmosphere_isa(0.0)
    assert math.isclose(sl["temperature_k"], 288.15, rel_tol=1e-4)
    assert math.isclose(sl["pressure_pa"], 101325.0, rel_tol=1e-4)
    assert math.isclose(sl["density_kg_m3"], 1.2250, rel_tol=1e-3)
    assert math.isclose(sl["speed_of_sound_ms"], 340.29, rel_tol=1e-3)

    # 2000 m
    h2k = standard_atmosphere_isa(2000.0)
    assert math.isclose(h2k["temperature_k"], 275.15, rel_tol=1e-4)
    assert math.isclose(h2k["pressure_pa"], 79495.0, rel_tol=2e-3)
    assert math.isclose(h2k["density_kg_m3"], 1.0065, rel_tol=5e-3)

    # 10,000 m
    h10k = standard_atmosphere_isa(10000.0)
    assert math.isclose(h10k["temperature_k"], 223.15, rel_tol=1e-4)
    assert math.isclose(h10k["pressure_pa"], 26499.0, rel_tol=5e-3)
    assert math.isclose(h10k["density_kg_m3"], 0.4135, rel_tol=5e-3)


def test_standard_atmosphere_altitude_limits():
    """Verify troposphere altitude constraints [-500 m, 11000 m]."""
    with pytest.raises(ValueError, match="altitude_m"):
        standard_atmosphere_isa(-600.0)

    with pytest.raises(ValueError, match="altitude_m"):
        standard_atmosphere_isa(12000.0)


def test_fluid_properties_catalog():
    """Verify registered property catalog."""
    air = get_fluid_properties("air_sea_level")
    assert air["density_kg_m3"] == ISA_RHO0
    assert air["dynamic_viscosity_pa_s"] == ISA_MU0
    assert air["specific_heat_ratio"] == 1.4

    water = get_fluid_properties("water_20c")
    assert water["density_kg_m3"] == 998.2
    assert math.isclose(water["dynamic_viscosity_pa_s"], 1.002e-3, rel_tol=1e-4)

    with pytest.raises(ValueError, match="not supported"):
        get_fluid_properties("liquid_hydrogen")

