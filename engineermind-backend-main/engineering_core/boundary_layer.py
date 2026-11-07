"""
boundary_layer.py - Boundary Layer Metrics, Wall Shear, and Prism Layer Inflation.

References:
- Schlichting, H., and Gersten, K., "Boundary-Layer Theory", 9th Edition (Springer, 2017).
- White, F. M., "Viscous Fluid Flow", 3rd Edition (McGraw-Hill, 2006).
- NASA Langley Research Center Turbulence Modeling Resource (TMR): https://turbmodels.larc.nasa.gov
"""

import math
from typing import Dict, Any, List
from engineering_core.units import validate_positive, validate_in_range
from engineering_core.fluid_properties import ISA_RHO0, ISA_MU0
from engineering_core.aerodynamics import reynolds_number, dynamic_pressure


def skin_friction_coefficient_flat_plate(re_x: float, method: str = "schlichting") -> float:
    """
    Estimate skin friction coefficient Cf for a turbulent boundary layer on a smooth flat plate.
    
    Supported Methods:
        - 'schlichting' (default):
            Cf = (2 * log10(Re_x) - 0.65)^(-2.3)
            Valid for Re_x from 10^6 to 10^9 (Schlichting & Gersten, 2017).
        - 'prandtl_1_7':
            Cf = 0.0592 / (Re_x ^ 0.2)
            Standard 1/7th power law approximation (White, 2006).
            
    Args:
        re_x: Length-based Reynolds number Re_x [-]. Must be >= 1e4.
        method: Correlation name ('schlichting' or 'prandtl_1_7').
        
    Returns:
        float: Skin friction coefficient Cf [-].
    """
    re = validate_positive(re_x, "re_x", strictly_positive=True)
    if re < 1e4:
        raise ValueError(f"Turbulent flat plate correlation invalid for Re_x = {re} < 10,000.")
        
    m = method.strip().lower()
    if m == "schlichting":
        cf = (2.0 * math.log10(re) - 0.65) ** (-2.3)
    elif m in ("prandtl", "prandtl_1_7", "power_law"):
        cf = 0.0592 / (re ** 0.2)
    else:
        raise ValueError(f"Unknown Cf method: '{method}'. Supported: 'schlichting', 'prandtl_1_7'.")
        
    return float(cf)


def wall_shear_stress(cf: float, q_inf: float) -> float:
    """
    Compute wall shear stress tau_w:
        tau_w = Cf * q_inf = 0.5 * Cf * rho * U_inf^2
        
    Args:
        cf: Dimensionless skin friction coefficient [-].
        q_inf: Dynamic pressure [Pa].
        
    Returns:
        float: Wall shear stress tau_w in Pascals [Pa].
    """
    c = validate_positive(cf, "cf", strictly_positive=True)
    q = validate_positive(q_inf, "q_inf", strictly_positive=True)
    return float(c * q)


def friction_velocity(tau_w: float, rho: float = ISA_RHO0) -> float:
    """
    Compute friction velocity u_tau:
        u_tau = sqrt(tau_w / rho)
        
    Args:
        tau_w: Wall shear stress [Pa].
        rho: Fluid density [kg/m^3].
        
    Returns:
        float: Friction velocity u_tau [m/s].
    """
    t = validate_positive(tau_w, "tau_w", strictly_positive=True)
    r = validate_positive(rho, "rho", strictly_positive=True)
    return float(math.sqrt(t / r))


def first_cell_height(target_y_plus: float, u_tau: float, nu: float) -> float:
    """
    Compute required first cell wall-normal spacing delta_s (or y_1):
        delta_s = (y_plus * nu) / u_tau
        
    Args:
        target_y_plus: Target non-dimensional wall distance y+ [-].
        u_tau: Friction velocity [m/s].
        nu: Kinematic viscosity nu = mu / rho [m^2/s].
        
    Returns:
        float: First cell height delta_s in meters [m].
    """
    yp = validate_positive(target_y_plus, "target_y_plus", strictly_positive=True)
    ut = validate_positive(u_tau, "u_tau", strictly_positive=True)
    v = validate_positive(nu, "nu", strictly_positive=True)
    return float((yp * v) / ut)


def boundary_layer_thickness_flat_plate(x_m: float, re_x: float) -> float:
    """
    Estimate 99% boundary layer thickness delta_99 for a turbulent boundary layer:
        delta_99 = 0.37 * x / (Re_x ^ 0.2)
        
    Args:
        x_m: Distance from leading edge in meters [m].
        re_x: Reynolds number based on length x [-].
        
    Returns:
        float: Boundary layer thickness delta_99 in meters [m].
    """
    x = validate_positive(x_m, "x_m", strictly_positive=True)
    re = validate_positive(re_x, "re_x", strictly_positive=True)
    return float(0.37 * x / (re ** 0.2))


def generate_geometric_layer_stack(
    first_cell_m: float,
    growth_rate: float = 1.15,
    num_layers: int = 28
) -> Dict[str, Any]:
    """
    Compute deterministic geometric progression for inflation prism layers:
        h_i = h_1 * r^(i-1)
        total_thickness = sum_{i=1}^N h_i = h_1 * (r^N - 1) / (r - 1)
        
    Args:
        first_cell_m: Height of the first cell at the wall [m].
        growth_rate: Expansion ratio r [-] (typically 1.10 - 1.25).
        num_layers: Total count of prism layers N [-].
        
    Returns:
        Dict containing:
            first_layer_thickness_m: h_1 [m]
            final_layer_thickness_m: h_N [m]
            total_prism_thickness_m: sum(h_i) [m]
            growth_rate: r
            num_layers: N
            layer_heights: list of layer heights [m]
            layer_cumulative_y: cumulative distances from wall [m]
    """
    h1 = validate_positive(first_cell_m, "first_cell_m", strictly_positive=True)
    r = validate_in_range(growth_rate, "growth_rate", 1.01, 1.50)
    if not isinstance(num_layers, int) or num_layers < 1:
        raise ValueError(f"num_layers must be a positive integer >= 1, got {num_layers}.")
        
    heights = [h1 * (r ** i) for i in range(num_layers)]
    cumulative = []
    current_y = 0.0
    for h in heights:
        current_y += h
        cumulative.append(current_y)
        
    total_thickness = cumulative[-1]
    final_thickness = heights[-1]
    
    return {
        "first_layer_thickness_m": float(h1),
        "final_layer_thickness_m": float(final_thickness),
        "total_prism_thickness_m": float(total_thickness),
        "growth_rate": float(r),
        "num_layers": int(num_layers),
        "layer_heights_m": heights,
        "layer_cumulative_y_m": cumulative
    }

