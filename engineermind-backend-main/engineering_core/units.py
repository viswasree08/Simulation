"""
units.py - Physical Dimensions, Conversions, and Validation for Engineering Calculations.

Provides deterministic conversion factors, dimensional validation, and standardized unit checks
for aerospace CFD workflows.
"""

from typing import Union, Tuple

# Standard SI Unit Conversion Constants
INCH_TO_METER = 0.0254
FOOT_TO_METER = 0.3048
MM_TO_METER = 0.001
KMH_TO_MS = 1.0 / 3.6
KNOT_TO_MS = 0.5144444444444445
PSI_TO_PA = 6894.757293168
BAR_TO_PA = 100000.0
ATM_TO_PA = 101325.0
RANKINE_TO_KELVIN = 5.0 / 9.0


def validate_positive(value: float, name: str, strictly_positive: bool = True) -> float:
    """
    Validate that a numerical value is positive (or non-negative).
    
    Args:
        value: Numerical quantity to check.
        name: Name of the variable for descriptive error messages.
        strictly_positive: If True, value must be > 0. If False, value >= 0.
        
    Returns:
        float: The validated float value.
        
    Raises:
        TypeError: If value is not a float or int.
        ValueError: If value violates positivity constraint.
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"'{name}' must be a numerical float or int, got {type(value).__name__}.")
    
    val = float(value)
    if strictly_positive:
        if val <= 0.0:
            raise ValueError(f"'{name}' must be strictly positive (> 0), got {val}.")
    else:
        if val < 0.0:
            raise ValueError(f"'{name}' must be non-negative (>= 0), got {val}.")
            
    return val


def validate_in_range(value: float, name: str, min_val: float, max_val: float) -> float:
    """
    Validate that a numerical value lies within [min_val, max_val].
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"'{name}' must be a numerical float or int, got {type(value).__name__}.")
    val = float(value)
    if not (min_val <= val <= max_val):
        raise ValueError(f"'{name}' must be between {min_val} and {max_val}, got {val}.")
    return val


def to_si_length(value: float, unit: str = "m") -> float:
    """Convert length to meters [m]."""
    validate_positive(value, "length", strictly_positive=False)
    u = unit.strip().lower()
    if u in ("m", "meter", "meters"):
        return float(value)
    elif u in ("mm", "millimeter", "millimeters"):
        return float(value) * MM_TO_METER
    elif u in ("in", "inch", "inches"):
        return float(value) * INCH_TO_METER
    elif u in ("ft", "foot", "feet"):
        return float(value) * FOOT_TO_METER
    else:
        raise ValueError(f"Unsupported length unit: '{unit}'. Supported: m, mm, in, ft.")


def to_si_velocity(value: float, unit: str = "m/s") -> float:
    """Convert velocity to meters per second [m/s]."""
    validate_positive(value, "velocity", strictly_positive=False)
    u = unit.strip().lower()
    if u in ("m/s", "ms", "mps"):
        return float(value)
    elif u in ("km/h", "kmh"):
        return float(value) * KMH_TO_MS
    elif u in ("kt", "knot", "knots"):
        return float(value) * KNOT_TO_MS
    elif u in ("ft/s", "fps"):
        return float(value) * FOOT_TO_METER
    else:
        raise ValueError(f"Unsupported velocity unit: '{unit}'. Supported: m/s, km/h, kt, ft/s.")


def to_si_pressure(value: float, unit: str = "pa") -> float:
    """Convert pressure to Pascals [Pa]."""
    validate_positive(value, "pressure", strictly_positive=False)
    u = unit.strip().lower()
    if u in ("pa", "pascal", "pascals"):
        return float(value)
    elif u in ("kpa", "kilopascal"):
        return float(value) * 1000.0
    elif u in ("bar", "bars"):
        return float(value) * BAR_TO_PA
    elif u in ("atm", "atmosphere"):
        return float(value) * ATM_TO_PA
    elif u in ("psi",):
        return float(value) * PSI_TO_PA
    else:
        raise ValueError(f"Unsupported pressure unit: '{unit}'. Supported: pa, kpa, bar, atm, psi.")


def to_kelvin(value: float, unit: str = "k") -> float:
    """Convert temperature to Kelvin [K]."""
    u = unit.strip().lower()
    if u in ("k", "kelvin"):
        val = float(value)
    elif u in ("c", "celsius"):
        val = float(value) + 273.15
    elif u in ("f", "fahrenheit"):
        val = (float(value) - 32.0) * (5.0 / 9.0) + 273.15
    elif u in ("r", "rankine"):
        val = float(value) * RANKINE_TO_KELVIN
    else:
        raise ValueError(f"Unsupported temperature unit: '{unit}'. Supported: K, C, F, R.")
    
    validate_positive(val, "temperature_kelvin", strictly_positive=False)
    return val

