"""
verification.py - Numerical Verification, Grid Convergence Index (GCI), and Code Verification.

References:
- ASME V&V 20-2009: "Standard for Verification and Validation in Computational Fluid Dynamics and Heat Transfer".
- Roache, P. J., "Verification and Validation in Computational Science and Engineering", Hermosa Publishers (1998).
- Celik, I. B., et al., "Procedure for Estimation and Reporting of Uncertainty Due to Discretization in CFD Applications",
  ASME Journal of Fluids Engineering, Vol. 130, 2008.
"""

import math
from typing import Dict, Any, Optional
from engineering_core.units import validate_positive, validate_in_range


def calculate_grid_convergence_index(
    f1: float,
    f2: float,
    f3: float,
    r21: float = 1.3,
    r32: Optional[float] = None,
    order_p_theoretical: float = 2.0,
    safety_factor: Optional[float] = None
) -> Dict[str, Any]:
    """
    Perform rigorous Grid Convergence Index (GCI) analysis based on ASME V&V 20 and Celik et al. (2008).
    
    Grid Definitions:
        f1: Solution on the finest grid (h1)
        f2: Solution on the medium grid (h2)
        f3: Solution on the coarse grid (h3)
        r21 = h2 / h1 > 1.0 (Refinement ratio between medium and fine)
        r32 = h3 / h2 > 1.0 (Refinement ratio between coarse and medium)
        
    Equations:
        eps21 = (f2 - f1) / f1
        eps32 = (f3 - f2) / f2
        
        Apparent order p:
            For r21 == r32 = r:
                p = ln((f3 - f2) / (f2 - f1)) / ln(r)
            For general r21, r32:
                Fixed point iteration of:
                p = (1 / ln(r21)) * |ln|(f3 - f2)/(f2 - f1)| + q(p)|
                
        Extrapolated value (Richardson Extrapolation):
            f_ext21 = (r21^p * f1 - f2) / (r21^p - 1)
            
        Fine Grid Convergence Index:
            GCI_fine = Fs * |eps21| / (r21^p - 1)
            
    Args:
        f1: Fine grid solution value.
        f2: Medium grid solution value.
        f3: Coarse grid solution value.
        r21: Refinement ratio h2 / h1 (must be > 1.0, typically >= 1.3).
        r32: Refinement ratio h3 / h2 (default matches r21 if None).
        order_p_theoretical: Theoretical formal order of accuracy (typically 2.0).
        safety_factor: Factor of safety Fs (typically 1.25 for 3 grids, 3.0 for 2 grids).
        
    Returns:
        Dict with apparent order, GCI percentages, asymptotic check, and ASME compliance verdict.
    """
    if r32 is None:
        r32 = r21
        
    r21 = validate_positive(r21, "r21", strictly_positive=True)
    r32 = validate_positive(r32, "r32", strictly_positive=True)
    if r21 <= 1.0 or r32 <= 1.0:
        raise ValueError("Grid refinement ratios r21 and r32 must be strictly greater than 1.0.")
        
    eps21_abs = f2 - f1
    eps32_abs = f3 - f2
    
    # Check for monotonic convergence vs oscillatory vs divergence
    if abs(eps21_abs) < 1e-15:
        return {
            "apparent_order_p": float(order_p_theoretical),
            "theoretical_order": float(order_p_theoretical),
            "relative_error_eps21_percent": 0.0,
            "gci_fine_percent": 0.0,
            "is_asymptotic_range": True,
            "convergence_type": "Identical fine solutions",
            "verdict": "GRID_INDEPENDENT",
            "recommendation": "Fine and medium solutions match within machine precision."
        }
        
    s = eps32_abs / eps21_abs
    if s <= 0:
        # Non-monotonic or oscillatory convergence
        convergence_type = "Oscillatory or Divergent"
        p = float(order_p_theoretical)
        asymptotic = False
    else:
        convergence_type = "Monotonic Convergence"
        if abs(r21 - r32) < 1e-4:
            p = math.log(abs(s)) / math.log(r21)
        else:
            # Fixed-point iteration for unequal refinement ratios (Celik et al. 2008)
            p_curr = float(order_p_theoretical)
            for _ in range(50):
                q_p = math.log((r21**p_curr - s) / (r21**p_curr - 1.0)) if (r21**p_curr - s) > 0 else 0.0
                p_next = (1.0 / math.log(r21)) * abs(math.log(abs(s)) + q_p)
                if abs(p_next - p_curr) < 1e-5:
                    break
                p_curr = p_next
            p = p_curr

    # Bound apparent order to physical range (0.5 to 4.0) to prevent numerical divergence
    p_clamped = max(0.5, min(p, 4.0))
    
    # Factor of safety: 1.25 for 3 grids with consistent apparent order
    if safety_factor is None:
        fs = 1.25 if abs(p_clamped - order_p_theoretical) < 0.5 else 3.0
    else:
        fs = float(safety_factor)
        
    rel_err_21 = abs((f2 - f1) / f1) if abs(f1) > 1e-12 else abs(f2 - f1)
    
    denominator = (r21 ** p_clamped) - 1.0
    gci_fine = (fs * rel_err_21 / denominator) * 100.0 if denominator > 1e-6 else 999.0
    
    # Asymptotic range of convergence check:
    # r21^p * GCI_fine / GCI_medium should be approximately 1.0
    rel_err_32 = abs((f3 - f2) / f2) if abs(f2) > 1e-12 else abs(f3 - f2)
    denom_32 = (r32 ** p_clamped) - 1.0
    gci_med = (fs * rel_err_32 / denom_32) * 100.0 if denom_32 > 1e-6 else 999.0
    
    asymp_ratio = (gci_med / ((r21 ** p_clamped) * gci_fine)) if gci_fine > 1e-6 else 1.0
    is_asymptotic = (0.90 <= asymp_ratio <= 1.10) if convergence_type == "Monotonic Convergence" else False
    
    if gci_fine <= 1.0:
        verdict = "GRID_INDEPENDENT"
        rec = "Excellent mesh convergence (GCI < 1.0%). Discretization error is negligible."
    elif gci_fine <= 3.0:
        verdict = "ACCEPTABLE_VERIFICATION"
        rec = "Acceptable industrial engineering tolerance (GCI <= 3.0%)."
    else:
        verdict = "MESH_REFINEMENT_REQUIRED"
        rec = f"GCI = {round(gci_fine, 2)}% exceeds 3.0% threshold. Grid refinement required in high-gradient regions."
        
    return {
        "apparent_order_p": round(float(p), 4),
        "clamped_order_p": round(float(p_clamped), 4),
        "theoretical_order": float(order_p_theoretical),
        "relative_error_eps21_percent": round(float(rel_err_21 * 100.0), 4),
        "gci_fine_percent": round(float(gci_fine), 4),
        "gci_medium_percent": round(float(gci_med), 4),
        "asymptotic_ratio": round(float(asymp_ratio), 4),
        "is_asymptotic_range": is_asymptotic,
        "convergence_type": convergence_type,
        "verdict": verdict,
        "recommendation": rec
    }

