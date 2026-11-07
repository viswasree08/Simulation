"""
AeroCore: Aerodynamics calculations, boundary layer metrics,
and ASME V&V 20 Grid Convergence Index (Roache GCI) Engine.

Refactored to delegate directly to the independent engineering_core module,
preserving exact backwards compatibility with all existing API contracts.
"""

from typing import Dict, Any
from engineering_core.aerodynamics import reynolds_number, dynamic_pressure
from engineering_core.boundary_layer import (
    wall_shear_stress,
    friction_velocity,
    first_cell_height
)
from engineering_core.verification import calculate_grid_convergence_index
from engineering_core.fluid_properties import ISA_RHO0, ISA_MU0


def compute_physics(
    velocity: float,
    chord_length: float,
    target_y_plus: float,
    regime: str = "external_aerodynamics"
) -> Dict[str, Any]:
    """
    Computes deterministic aerothermal and boundary layer metrics.
    Zero client-side math fallback. Delegates to engineering_core.
    """
    if velocity <= 0 or chord_length <= 0:
        raise ValueError("Velocity and chord length must be strictly positive.")
    if target_y_plus <= 0:
        raise ValueError("Target y+ must be strictly positive.")

    fluid_density = ISA_RHO0
    viscosity = ISA_MU0

    re_val = reynolds_number(velocity, chord_length, fluid_density, viscosity)
    mach = velocity / 340.3
    q = dynamic_pressure(velocity, fluid_density)

    if regime == "internal_nozzle":
        cf = 0.079 * (re_val ** -0.25)
        tau_w = wall_shear_stress(cf, q)
        u_tau = friction_velocity(tau_w, fluid_density)
        delta_s_m = first_cell_height(target_y_plus, u_tau, viscosity / fluid_density)
        delta_m = 0.5 * chord_length
        f_drag = 2.0 * q * chord_length * cf
        cl_slope = 0.0
        cl_4deg = 0.0
        cd0_str = f"{cf:.5f} (Internal Pipe Friction Factor)"
        inlet = chord_length * 5.0
        outlet = chord_length * 8.0
        lateral = chord_length * 2.5
        regime_desc = "Internal Compressible Flow"
    else:
        cf = 0.0583 * (re_val ** -0.2)
        tau_w = wall_shear_stress(cf, q)
        u_tau = friction_velocity(tau_w, fluid_density)
        delta_s_m = first_cell_height(target_y_plus, u_tau, viscosity / fluid_density)
        delta_m = (0.37 * chord_length) / (re_val ** 0.2)
        f_drag = 2.0 * q * chord_length * cf
        cl_slope = 0.11
        cl_4deg = cl_slope * 4.0
        cd0_str = "0.0060 - 0.0085 (Typical Aerofoil Parasite Cd0)"
        inlet = chord_length * 15.0
        outlet = chord_length * 25.0
        lateral = chord_length * 15.0
        regime_desc = "Incompressible Fully Turbulent Flow" if mach < 0.3 else "Compressible Subsonic Flow"

    delta_s_mm = delta_s_m * 1000.0
    delta_mm = delta_m * 1000.0
    layers = 28 if target_y_plus <= 1.0 else 12

    hand_calc = {
        "reynolds_number": round(re_val, 2),
        "dynamic_pressure_pa": round(q, 2),
        "skin_friction_coeff": float(f"{cf:.6f}"),
        "wall_shear_stress_pa": round(tau_w, 3),
        "friction_velocity_ms": round(u_tau, 3),
        "first_cell_height_mm": round(delta_s_mm, 5),
        "first_cell_height_m": delta_s_m,
        "boundary_layer_thickness_mm": round(delta_mm, 2),
        "estimated_friction_drag_n_per_m": round(f_drag, 2),
        "theoretical_cl_alpha_per_deg": round(cl_slope, 3),
        "theoretical_cl_at_4deg": round(cl_4deg, 3),
        "expected_cd0_range": cd0_str
    }

    rationale = (
        f"Wall-Resolved formulation (y+ = {target_y_plus:.1f}): Near-wall viscous sublayer "
        "is resolved without empirical wall functions. Required for SST k-omega."
        if target_y_plus <= 1.0 else
        f"Wall-Function formulation (y+ = {target_y_plus:.1f}): First node placed in log-law layer (30 < y+ < 300)."
    )

    return {
        "reynolds_number": round(re_val, 2),
        "mach_number": round(mach, 3),
        "flow_regime": regime_desc,
        "boundary_layer_thickness_mm": round(delta_mm, 2),
        "skin_friction_coeff": float(f"{cf:.6f}"),
        "wall_shear_stress_pa": round(tau_w, 3),
        "friction_velocity_ms": round(u_tau, 3),
        "first_cell_height_mm": round(delta_s_mm, 5),
        "first_cell_height_m": delta_s_m,
        "recommended_prism_layers": layers,
        "recommended_growth_rate": 1.15,
        "inlet_distance_m": round(inlet, 2),
        "outlet_distance_m": round(outlet, 2),
        "lateral_distance_m": round(lateral, 2),
        "recommended_turbulence_model": "kOmegaSST",
        "wall_treatment_rationale": rationale,
        "hand_calculation": hand_calc
    }


def calculate_roache_gci(f_coarse: float, f_medium: float, f_fine: float, r: float = 1.414) -> Dict[str, Any]:
    """
    ASME V&V 20 Grid Convergence Index (GCI) calculation across 3 systematically refined grids.
    Maintains exact API output dictionary for backward compatibility while using engineering_core.
    """
    if f_fine <= 0 or f_medium <= 0 or f_coarse <= 0:
        raise ValueError("Grid values must be positive non-zero numbers.")
        
    res = calculate_grid_convergence_index(f1=f_fine, f2=f_medium, f3=f_coarse, r21=r, r32=r)
    
    # Map to existing expected aerocore.py output format
    is_asymptotic = bool(res["gci_fine_percent"] < 3.0)
    verdict = "PASS" if is_asymptotic else "MESH_REFINEMENT_REQUIRED"
    recommendation = (
        "Verified: Grid convergence index satisfies ASME V&V 20 criteria (< 3.0%)."
        if is_asymptotic else
        "Notice: GCI exceeds 3.0%. Grid refinement required in high-gradient regions."
    )
    
    return {
        "apparent_order_p": res["apparent_order_p"],
        "theoretical_order": 2.0,
        "relative_error_eps21_percent": res["relative_error_eps21_percent"],
        "gci_fine_percent": res["gci_fine_percent"],
        "is_asymptotic_range": is_asymptotic,
        "verdict": verdict,
        "recommendation": recommendation
    }
