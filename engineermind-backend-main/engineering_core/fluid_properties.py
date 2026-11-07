"""
fluid_properties.py - Thermophysical Properties of Fluids and Standard Atmospheres.

References:
- U.S. Standard Atmosphere (1976), NOAA/NASA/USAF.
- Sutherland, W. (1893), "The viscosity of gases and molecular force", Phil. Mag.
- Frank M. White, "Fluid Mechanics", 8th Edition (McGraw-Hill, 2016).
"""

import math
from typing import Dict, Any
from engineering_core.units import validate_positive, validate_in_range

# ISA Sea-Level Baseline Constants
ISA_P0 = 101325.0       # Sea level pressure [Pa]
ISA_T0 = 288.15         # Sea level temperature [K] (15 deg C)
ISA_RHO0 = 1.225        # Sea level air density [kg/m^3]
ISA_LAPSE_RATE = 0.0065 # Troposphere temperature lapse rate [K/m]
R_SPECIFIC_AIR = 287.058 # Specific gas constant for dry air [J/(kg*K)]
GAMMA_AIR = 1.4         # Ratio of specific heats for dry air [-]
EARTH_G = 9.80665       # Standard gravitational acceleration [m/s^2]

# Sutherland's Law Constants for Dry Air
SUTHERLAND_S = 110.4    # Sutherland temperature [K]
SUTHERLAND_T_REF = 273.15 # Reference temperature [K]
SUTHERLAND_MU_REF = 1.716e-5 # Reference dynamic viscosity [Pa*s]
ISA_MU0 = 1.789e-5      # Dynamic viscosity at 288.15 K [Pa*s] (Standard OpenFOAM default)


def sutherland_viscosity(temperature_k: float) -> float:
    """
    Calculate dynamic viscosity of dry air using Sutherland's law (Sutherland, 1893).
    
    Formula:
        mu(T) = mu_ref * (T / T_ref)^(3/2) * (T_ref + S) / (T + S)
        
    Args:
        temperature_k: Absolute temperature in Kelvin [K].
        
    Returns:
        float: Dynamic viscosity mu in [Pa*s] (or [kg/(m*s)]).
        
    Assumptions:
        Ideal gas behavior, dry air, valid for 100 K < T < 1900 K.
    """
    T = validate_in_range(temperature_k, "temperature_k", 100.0, 1900.0)
    mu = SUTHERLAND_MU_REF * ((T / SUTHERLAND_T_REF) ** 1.5) * ((SUTHERLAND_T_REF + SUTHERLAND_S) / (T + SUTHERLAND_S))
    return float(mu)


def standard_atmosphere_isa(altitude_m: float = 0.0) -> Dict[str, Any]:
    """
    Compute atmospheric conditions up to 11,000 m (Troposphere) using ISA 1976 equations.
    
    Equations:
        T(h) = T0 - L * h
        p(h) = p0 * (1 - L*h/T0)^(g / (R*L))
        rho(h) = p(h) / (R * T(h))
        a(h) = sqrt(gamma * R * T(h))
        
    Args:
        altitude_m: Geometric geopotential altitude above mean sea level in meters [m].
                    Valid for 0 <= altitude_m <= 11000 m.
                    
    Returns:
        Dict containing:
            temperature_k: Ambient temperature [K]
            pressure_pa: Ambient static pressure [Pa]
            density_kg_m3: Mass density [kg/m^3]
            speed_of_sound_ms: Speed of sound [m/s]
            dynamic_viscosity_pa_s: Dynamic viscosity [Pa*s]
            kinematic_viscosity_m2_s: Kinematic viscosity nu [m^2/s]
            method: Reference documentation
            assumptions: Stated physical assumptions
    """
    h = validate_in_range(altitude_m, "altitude_m", -500.0, 11000.0)
    
    T = ISA_T0 - ISA_LAPSE_RATE * h
    exponent = EARTH_G / (R_SPECIFIC_AIR * ISA_LAPSE_RATE) # ~ 5.25588
    p = ISA_P0 * ((1.0 - (ISA_LAPSE_RATE * h) / ISA_T0) ** exponent)
    rho = p / (R_SPECIFIC_AIR * T)
    a = math.sqrt(GAMMA_AIR * R_SPECIFIC_AIR * T)
    mu = sutherland_viscosity(T)
    nu = mu / rho
    
    return {
        "altitude_m": float(h),
        "temperature_k": round(float(T), 3),
        "pressure_pa": round(float(p), 2),
        "density_kg_m3": round(float(rho), 5),
        "speed_of_sound_ms": round(float(a), 2),
        "dynamic_viscosity_pa_s": float(mu),
        "kinematic_viscosity_m2_s": float(nu),
        "method": "U.S. Standard Atmosphere (1976) / Sutherland Viscosity",
        "assumptions": "Troposphere linear lapse rate (L=0.0065 K/m), dry ideal air, hydrostatic balance."
    }


def get_fluid_properties(fluid: str = "air_sea_level") -> Dict[str, Any]:
    """
    Retrieve standardized fluid physical properties.
    
    Supported fluids:
        - 'air_sea_level': Standard ISA Sea Level Dry Air (rho=1.225 kg/m^3, mu=1.789e-5 Pa*s)
        - 'water_20c': Liquid water at 20 deg C (rho=998.2 kg/m^3, mu=1.002e-3 Pa*s)
    """
    f = fluid.strip().lower()
    if f in ("air", "air_sea_level", "standard_air"):
        rho = ISA_RHO0
        mu = ISA_MU0
        return {
            "fluid": "air_sea_level",
            "density_kg_m3": rho,
            "dynamic_viscosity_pa_s": mu,
            "kinematic_viscosity_m2_s": mu / rho,
            "speed_of_sound_ms": 340.28,
            "specific_heat_ratio": GAMMA_AIR,
            "gas_constant_j_kg_k": R_SPECIFIC_AIR,
            "source": "ISA Standard Sea-Level Baseline"
        }
    elif f in ("water", "water_20c"):
        rho = 998.2
        mu = 1.002e-3
        return {
            "fluid": "water_20c",
            "density_kg_m3": rho,
            "dynamic_viscosity_pa_s": mu,
            "kinematic_viscosity_m2_s": mu / rho,
            "speed_of_sound_ms": 1482.0,
            "specific_heat_ratio": 1.0,
            "gas_constant_j_kg_k": None,
            "source": "Standard Water at 20 deg C"
        }
    else:
        raise ValueError(f"Fluid '{fluid}' not supported. Supported: 'air_sea_level', 'water_20c'.")

