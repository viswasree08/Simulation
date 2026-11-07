"""
turbulence.py - Turbulence Model Boundary Conditions and Near-Wall Formulations.

References:
- Menter, F. R., "Two-equation eddy-viscosity turbulence models for engineering applications",
  AIAA Journal, 32(8), 1598-1605 (1994).
- Wilcox, D. C., "Turbulence Modeling for CFD", 3rd Edition, DCW Industries (2006).
- NASA Langley Turbulence Modeling Resource: SST-2003 model specifications.
"""

import math
from typing import Dict, Any
from engineering_core.units import validate_positive, validate_in_range


# Menter k-omega SST Model Constants
SST_BETA_STAR = 0.09
SST_C_MU = 0.09


def turbulence_inlet_boundary_conditions(
    velocity_ms: float,
    turbulent_intensity_percent: float = 1.0,
    turbulent_length_scale_m: float = 0.01,
    viscosity_ratio: float = None,
    nu_m2_s: float = 1.46e-5
) -> Dict[str, Any]:
    """
    Compute deterministic inflow boundary conditions for k-omega SST / k-epsilon models.
    
    Formulas:
        k = 1.5 * (U * I)^2
        omega = C_mu^(-0.25) * sqrt(k) / l
        (or omega = k / (nu * (nu_t / nu)))
        epsilon = C_mu * k^(3/2) / l
        nu_t = C_mu * k^2 / epsilon = k / omega
        
    Args:
        velocity_ms: Freestream velocity U [m/s].
        turbulent_intensity_percent: Freestream turbulence intensity I in percent [%] (e.g., 0.1% to 5%).
        turbulent_length_scale_m: Turbulent length scale l [m] (typically 0.07 * D_h or 0.01 * c).
        viscosity_ratio: Optional turbulent-to-molecular viscosity ratio (nu_t / nu) [-].
        nu_m2_s: Molecular kinematic viscosity [m^2/s].
        
    Returns:
        Dict containing turbulent kinetic energy k, specific dissipation rate omega,
        dissipation rate epsilon, and eddy viscosity nu_t.
    """
    u = validate_positive(velocity_ms, "velocity_ms", strictly_positive=True)
    ti = validate_in_range(turbulent_intensity_percent, "turbulent_intensity_percent", 0.001, 50.0)
    i_frac = ti / 100.0
    
    # Turbulent kinetic energy k [m^2/s^2]
    k = 1.5 * ((u * i_frac) ** 2)
    
    if viscosity_ratio is not None and viscosity_ratio > 0:
        mu_ratio = validate_positive(viscosity_ratio, "viscosity_ratio", strictly_positive=True)
        nu = validate_positive(nu_m2_s, "nu_m2_s", strictly_positive=True)
        # omega based on viscosity ratio
        omega = k / (nu * mu_ratio)
        epsilon = SST_BETA_STAR * k * omega
        nu_t = nu * mu_ratio
    else:
        l = validate_positive(turbulent_length_scale_m, "turbulent_length_scale_m", strictly_positive=True)
        # Standard length-scale formulation (Wilcox / Menter)
        omega = (k ** 0.5) / ((SST_C_MU ** 0.25) * l)
        epsilon = SST_C_MU * (k ** 1.5) / l
        nu_t = k / omega
        
    return {
        "k_m2_s2": float(k),
        "omega_per_s": float(omega),
        "epsilon_m2_s3": float(epsilon),
        "eddy_viscosity_nut_m2_s": float(nu_t),
        "turbulence_intensity_percent": float(ti),
        "model_reference": "Menter k-omega SST (1994) / NASA TMR Standard Inflow Boundary"
    }


def assess_wall_treatment(target_y_plus: float) -> Dict[str, Any]:
    """
    Evaluate wall treatment regime and boundary condition requirements for two-equation models.
    
    Regimes:
        - y+ <= 1.0: Wall-resolved (viscous sublayer resolved). Zero wall functions needed.
        - 1.0 < y+ < 5.0: Low-Re buffer margin. Acceptable with automatic wall treatment (e.g. omegaWallFunction).
        - 5.0 <= y+ <= 30.0: BUFFER LAYER. Numerically invalid regime! Neither pure linear law nor log-law holds.
        - 30.0 < y+ <= 300.0: High-Re log-law region. High-Re wall functions required (kLowReWallFunction / nutkWallFunction).
        - y+ > 300.0: Excessive near-wall coarseness. Unacceptable for aerodynamic separation.
        
    Args:
        target_y_plus: Target y+ value [-].
        
    Returns:
        Dict containing regime status, validity boolean, and OpenFOAM wall BC recommendations.
    """
    yp = validate_positive(target_y_plus, "target_y_plus", strictly_positive=True)
    
    if yp <= 1.0:
        regime = "Wall-Resolved (Viscous Sublayer)"
        valid = True
        warning = None
        bc_nut = "nutkWallFunction"
        bc_k = "kLowReWallFunction"
        bc_omega = "omegaWallFunction"
        rationale = "Near-wall viscous sublayer resolved directly. Pristine accuracy for SST k-omega."
    elif yp <= 5.0:
        regime = "Transitional Near-Wall (Sublayer Upper Margin)"
        valid = True
        warning = "Target y+ slightly above 1.0; ensure SST automatic wall treatment is active."
        bc_nut = "nutkWallFunction"
        bc_k = "kLowReWallFunction"
        bc_omega = "omegaWallFunction"
        rationale = "Near-wall viscous sublayer acceptable with standard blended wall functions."
    elif yp <= 30.0:
        regime = "Buffer Layer (Unresolved Zone)"
        valid = False
        warning = f"y+ = {yp} lies inside the buffer layer (5 <= y+ <= 30). Standard wall functions incur major error."
        bc_nut = "nutkWallFunction"
        bc_k = "kLowReWallFunction"
        bc_omega = "omegaWallFunction"
        rationale = "Buffer layer placement violates boundary layer law-of-the-wall physics. Refine to y+ <= 1 or coarsen to y+ >= 30."
    elif yp <= 300.0:
        regime = "Log-Law Region (High-Re Wall Functions)"
        valid = True
        warning = None
        bc_nut = "nutkWallFunction"
        bc_k = "kqRWallFunction"
        bc_omega = "omegaWallFunction"
        rationale = "Standard log-law wall function regime. Suitable for high-Reynolds attached flows."
    else:
        regime = "Excessively Coarse"
        valid = False
        warning = f"y+ = {yp} exceeds 300. Boundary layer velocity profile cannot be modeled accurately."
        bc_nut = "nutkWallFunction"
        bc_k = "kqRWallFunction"
        bc_omega = "omegaWallFunction"
        rationale = "Grid is too coarse to capture boundary layer effects."

    return {
        "target_y_plus": float(yp),
        "regime": regime,
        "is_physically_recommended": valid,
        "warning": warning,
        "rationale": rationale,
        "openfoam_boundary_conditions": {
            "nut": bc_nut,
            "k": bc_k,
            "omega": bc_omega
        }
    }

