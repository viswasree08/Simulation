"""
numerical_methods.py - Numerical Methods, Discretization Schemes, and Post-Processing Reductions.

References:
- Ferziger, J. H., and Peric, M., "Computational Methods for Fluid Dynamics", 3rd Edition (Springer, 2002).
- Patankar, S. V., "Numerical Heat Transfer and Fluid Flow" (Hemisphere, 1980).
- OpenFOAM v2212 fvSchemes and postProcessing utilities.
"""

import math
from typing import List, Dict, Any, Union
import numpy as np
from engineering_core.units import validate_positive
from engineering_core.fluid_properties import ISA_RHO0


def pressure_coefficient(
    surface_pressure: Union[float, np.ndarray, List[float]],
    freestream_velocity_ms: float,
    freestream_pressure_pa: float = 0.0,
    rho_kg_m3: float = ISA_RHO0,
    is_kinematic_pressure: bool = True
) -> Union[float, np.ndarray]:
    """
    Calculate aerodynamic surface pressure coefficient Cp.
    
    Formula:
        Static pressure form:
            Cp = (p - p_inf) / (0.5 * rho * U_inf^2)
        Kinematic pressure form (OpenFOAM incompressible solvers where p_OF = p / rho):
            Cp = (p_OF - p_OF_inf) / (0.5 * U_inf^2)
            
    Args:
        surface_pressure: Surface pressure (gauge or absolute, or kinematic m^2/s^2).
        freestream_velocity_ms: Freestream velocity U_inf [m/s].
        freestream_pressure_pa: Reference freestream pressure [Pa] or [m^2/s^2] (default: 0.0 gauge).
        rho_kg_m3: Fluid density [kg/m^3] (only used if is_kinematic_pressure is False).
        is_kinematic_pressure: Set True for incompressible OpenFOAM output (p / rho).
        
    Returns:
        float or np.ndarray: Dimensionless pressure coefficient Cp.
    """
    u = validate_positive(freestream_velocity_ms, "freestream_velocity_ms", strictly_positive=True)
    
    if is_kinematic_pressure:
        denominator = 0.5 * (u ** 2)
    else:
        rho = validate_positive(rho_kg_m3, "rho_kg_m3", strictly_positive=True)
        denominator = 0.5 * rho * (u ** 2)
        
    if isinstance(surface_pressure, (list, tuple)):
        p_arr = np.array(surface_pressure, dtype=float)
        return (p_arr - freestream_pressure_pa) / denominator
    elif isinstance(surface_pressure, np.ndarray):
        return (surface_pressure - freestream_pressure_pa) / denominator
    else:
        return float((float(surface_pressure) - freestream_pressure_pa) / denominator)


def compute_rolling_standard_deviation(
    values: List[float],
    window_size: int = 50
) -> Dict[str, Any]:
    """
    Compute rolling standard deviation and relative variation of an iterative CFD monitor (e.g., Cd or Cl).
    
    Used to assess asymptotic statistical convergence of force coefficients.
    
    Args:
        values: Sequence of iterations [float].
        window_size: Window size over which standard deviation is computed (default: 50).
        
    Returns:
        Dict containing mean, standard deviation, and relative coefficient of variation (sigma / |mean|).
    """
    if not values or len(values) == 0:
        raise ValueError("Cannot compute rolling standard deviation on empty list.")
    if window_size < 2:
        raise ValueError("window_size must be at least 2.")
        
    window = values[-window_size:] if len(values) >= window_size else values
    arr = np.array(window, dtype=float)
    
    mean_val = float(np.mean(arr))
    std_val = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    
    rel_variation = float(std_val / abs(mean_val)) if abs(mean_val) > 1e-12 else 0.0
    
    return {
        "sample_count": len(window),
        "mean": mean_val,
        "standard_deviation": std_val,
        "relative_variation": rel_variation,
        "is_converged_statistically": bool(rel_variation < 1e-3 and len(window) >= window_size)
    }


def courant_number_1d(velocity_ms: float, delta_t_s: float, delta_x_m: float) -> float:
    """
    Compute 1D Courant-Friedrichs-Lewy (CFL) number:
        Co = U * delta_t / delta_x
        
    Args:
        velocity_ms: Local flow speed [m/s].
        delta_t_s: Time step size [s].
        delta_x_m: Grid cell spacing [m].
        
    Returns:
        float: Dimensionless Courant number Co.
    """
    u = validate_positive(velocity_ms, "velocity_ms", strictly_positive=True)
    dt = validate_positive(delta_t_s, "delta_t_s", strictly_positive=True)
    dx = validate_positive(delta_x_m, "delta_x_m", strictly_positive=True)
    return float((u * dt) / dx)

