"""
tests/engineering_core/test_units.py - Unit and Dimensional Validation Verification.
"""

import pytest
import math
from engineering_core.units import (
    validate_positive,
    validate_in_range,
    to_si_length,
    to_si_velocity,
    to_si_pressure,
    to_kelvin,
    INCH_TO_METER,
    FOOT_TO_METER,
    MM_TO_METER,
    KMH_TO_MS,
    KNOT_TO_MS,
    PSI_TO_PA,
    BAR_TO_PA,
    ATM_TO_PA
)


def test_validate_positive_strict():
    """Verify strict positivity enforcement with TypeError and ValueError."""
    assert validate_positive(1.0, "x", strictly_positive=True) == 1.0
    assert validate_positive(1e-12, "x", strictly_positive=True) == 1e-12

    with pytest.raises(ValueError, match="strictly positive"):
        validate_positive(0.0, "x", strictly_positive=True)

    with pytest.raises(ValueError, match="strictly positive"):
        validate_positive(-0.001, "x", strictly_positive=True)

    with pytest.raises(TypeError, match="must be a numerical float or int"):
        validate_positive("10", "x")

    with pytest.raises(TypeError, match="must be a numerical float or int"):
        validate_positive(None, "x")


def test_validate_positive_non_strict():
    """Verify non-negative enforcement allows zero."""
    assert validate_positive(0.0, "x", strictly_positive=False) == 0.0
    assert validate_positive(5.0, "x", strictly_positive=False) == 5.0

    with pytest.raises(ValueError, match="non-negative"):
        validate_positive(-1e-6, "x", strictly_positive=False)


def test_validate_in_range():
    """Verify bounded interval enforcement."""
    assert validate_in_range(0.5, "mach", 0.0, 1.0) == 0.5
    assert validate_in_range(0.0, "mach", 0.0, 1.0) == 0.0
    assert validate_in_range(1.0, "mach", 0.0, 1.0) == 1.0

    with pytest.raises(ValueError, match="must be between"):
        validate_in_range(-0.1, "mach", 0.0, 1.0)

    with pytest.raises(ValueError, match="must be between"):
        validate_in_range(1.01, "mach", 0.0, 1.0)


def test_exact_conversion_constants():
    """Verify exact international legal standards for unit conversions."""
    # 1 inch = exactly 25.4 mm = 0.0254 m (ISO 31-1 / NIST SP 811)
    assert INCH_TO_METER == 0.0254
    # 1 foot = exactly 12 inches = 0.3048 m
    assert FOOT_TO_METER == 0.3048
    # 1 nautical mile = 1852 m => 1 knot = 1852 m / 3600 s = 0.514444... m/s
    assert math.isclose(KNOT_TO_MS, 1852.0 / 3600.0, rel_tol=1e-12)
    # Standard atmosphere NIST definition = exactly 101325 Pa
    assert ATM_TO_PA == 101325.0
    # 1 bar = exactly 10^5 Pa
    assert BAR_TO_PA == 100000.0
    # 1 psi = 6894.757... Pa
    assert math.isclose(PSI_TO_PA, 6894.757293168, rel_tol=1e-6)


def test_unit_conversion_functions():
    """Verify conversion routines against independent benchmarks."""
    # Lengths
    assert math.isclose(to_si_length(100.0, "mm"), 0.1, abs_tol=1e-9)
    assert math.isclose(to_si_length(12.0, "in"), 0.3048, abs_tol=1e-9)
    assert math.isclose(to_si_length(1.0, "ft"), 0.3048, abs_tol=1e-9)
    assert math.isclose(to_si_length(2.5, "m"), 2.5, abs_tol=1e-9)

    # Velocities
    # 100 km/h = 27.777777... m/s
    assert math.isclose(to_si_velocity(100.0, "km/h"), 27.777777778, rel_tol=1e-6)
    # 250 knots = 128.61111... m/s
    assert math.isclose(to_si_velocity(250.0, "knot"), 250.0 * (1852.0 / 3600.0), rel_tol=1e-6)

    # Pressures
    assert math.isclose(to_si_pressure(1.0, "atm"), 101325.0, abs_tol=1e-6)
    assert math.isclose(to_si_pressure(14.69595, "psi"), 101325.0, rel_tol=1e-4)

    # Temperature
    # Absolute zero
    assert math.isclose(to_kelvin(-273.15, "C"), 0.0, abs_tol=1e-6)
    # Boiling point of water at 1 atm = 100 C = 373.15 K
    assert math.isclose(to_kelvin(100.0, "C"), 373.15, abs_tol=1e-6)
    # Fahrenheit freezing point 32 F = 273.15 K
    assert math.isclose(to_kelvin(32.0, "F"), 273.15, abs_tol=1e-6)
    # Fahrenheit boiling point 212 F = 373.15 K
    assert math.isclose(to_kelvin(212.0, "F"), 373.15, abs_tol=1e-6)


def test_invalid_units_raise_error():
    """Verify unsupported unit labels raise ValueError."""
    with pytest.raises(ValueError, match="Unsupported length unit"):
        to_si_length(10.0, "lightyears")

    with pytest.raises(ValueError, match="Unsupported velocity unit"):
        to_si_velocity(10.0, "mach")

    with pytest.raises(ValueError, match="Unsupported pressure unit"):
        to_si_pressure(10.0, "torr")

    with pytest.raises(ValueError, match="Unsupported temperature unit"):
        to_kelvin(100.0, "kelvins_invalid")

