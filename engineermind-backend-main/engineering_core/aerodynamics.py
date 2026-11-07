"""
aerodynamics.py - Aerodynamic Non-Dimensional Numbers and Operating Conditions.

References:
- Anderson, J. D., "Fundamentals of Aerodynamics", 6th Edition (McGraw-Hill, 2016).
- Abbott, I. H., and von Doenhoff, A. E., "Theory of Wing Sections" (Dover, 1959).
"""

import math
from typing import Dict, Any
from engineering_core.units import validate_positive
from engineering_core.fluid_properties import ISA_RHO0, ISA_MU0


def reynolds_number(velocity_ms: float, chord_m: float, rho_kg_m3: float = ISA_RHO0, mu_pa_s: float = ISA_MU0) -> float:
    """
    Calculate chord-based Reynolds number:
        Re = (rho * U * c) / mu = (U * c) / nu
        
    Args:
        velocity_ms: Freestream flow speed U_inf [m/s].
        chord_m: Aerodynamic reference chord length c [m].
        rho_kg_m3: Fluid density [kg/m^3] (default: 1.225 kg/m^3).
        mu_pa_s: Dynamic viscosity [Pa*s] (default: 1.789e-5 Pa*s).
        
    Returns:
        float: Dimensionless Reynolds number Re.
    """
    u = validate_positive(velocity_ms, "velocity_ms", strictly_positive=True)
    c = validate_positive(chord_m, "chord_m", strictly_positive=True)
    rho = validate_positive(rho_kg_m3, "rho_kg_m3", strictly_positive=True)
    mu = validate_positive(mu_pa_s, "mu_pa_s", strictly_positive=True)
    
    return float((rho * u * c) / mu)


def mach_number(velocity_ms: float, speed_of_sound_ms: float = 340.28) -> float:
    """
    Calculate flow Mach number:
        Ma = U / a
        
    Args:
        velocity_ms: Freestream velocity U [m/s].
        speed_of_sound_ms: Local acoustic speed a [m/s] (default: 340.28 m/s for ISA sea-level).
        
    Returns:
        float: Dimensionless Mach number Ma.
    """
    u = validate_positive(velocity_ms, "velocity_ms", strictly_positive=True)
    a = validate_positive(speed_of_sound_ms, "speed_of_sound_ms", strictly_positive=True)
    return float(u / a)


def dynamic_pressure(velocity_ms: float, rho_kg_m3: float = ISA_RHO0) -> float:
    """
    Calculate freestream dynamic pressure:
        q_inf = 0.5 * rho * U^2
        
    Args:
        velocity_ms: Freestream velocity [m/s].
        rho_kg_m3: Fluid density [kg/m^3] (default: 1.225 kg/m^3).
        
    Returns:
        float: Dynamic pressure in Pascals [Pa].
    """
    u = validate_positive(velocity_ms, "velocity_ms", strictly_positive=True)
    rho = validate_positive(rho_kg_m3, "rho_kg_m3", strictly_positive=True)
    return float(0.5 * rho * (u ** 2))


def classify_flow_regime(re: float, ma: float) -> Dict[str, str]:
    """
    Classify flow regime based on Reynolds and Mach numbers according to standard aerodynamic criteria.
    
    Args:
        re: Reynolds number [-].
        ma: Mach number [-].
        
    Returns:
        Dict containing regime labels and solver compatibility recommendation.
    """
    validate_positive(re, "Reynolds number", strictly_positive=True)
    validate_positive(ma, "Mach number", strictly_positive=True)
    
    # Compressibility classification
    if ma < 0.3:
        comp_regime = "Incompressible"
        comp_note = "Density variation < 5%. Incompressible Navier-Stokes / SIMPLE algorithm valid."
    elif ma < 0.8:
        comp_regime = "Subsonic Compressible"
        comp_note = "Compressibility effects significant. Density-based or compressible PIMPLE required."
    elif ma < 1.2:
        comp_regime = "Transonic"
        comp_note = "Mixed subsonic/supersonic regions and shocks present. Shock-capturing schemes required."
    elif ma < 5.0:
        comp_regime = "Supersonic"
        comp_note = "Supersonic flow. Compressible shock-capturing solver required."
    else:
        comp_regime = "Hypersonic"
        comp_note = "Severe aerothermal heating and high-temperature gas dynamics present."

    # Viscous / boundary layer regime
    if re < 5e5:
        turb_regime = "Laminar / Transitional"
    else:
        turb_regime = "Turbulent"
        
    full_label = f"{comp_regime} {turb_regime} Flow"
    return {
        "flow_regime": full_label,
        "compressibility_regime": comp_regime,
        "turbulence_regime": turb_regime,
        "notes": comp_note
    }


def thin_airfoil_theory_cl(alpha_deg: float) -> float:
    """
    Compute theoretical sectional lift coefficient for an ideal thin airfoil (symmetric) in inviscid flow:
        Cl = 2 * pi * alpha (in radians) = 0.1097 * alpha (in degrees)
        
    Args:
        alpha_deg: Angle of attack in degrees [deg].
        
    Returns:
        float: Theoretical lift coefficient Cl.
        
    Assumptions:
        Classical thin airfoil theory (Abbott & von Doenhoff, 1959).
        Inviscid, incompressible, small angle of attack (< 12 deg), linear pre-stall regime.
    """
    alpha_rad = math.radians(float(alpha_deg))
    return float(2.0 * math.pi * alpha_rad)

