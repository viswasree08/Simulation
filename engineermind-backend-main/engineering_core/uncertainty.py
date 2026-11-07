"""
uncertainty.py - Experimental and Simulation Uncertainty Quantification.

References:
- Coleman, H. W., and Steele, W. G., "Experimentation, Validation, and Uncertainty Analysis for Engineers",
  3rd Edition (Wiley, 2009).
- ISO/IEC Guide 98-3:2008 (GUM): "Uncertainty of measurement -- Part 3: Guide to the expression of uncertainty in measurement".
- ASME V&V 20-2009 Standard for Verification and Validation in Computational Fluid Dynamics.
"""

import math
from typing import Dict, Any, List
from engineering_core.units import validate_positive, validate_in_range


def combined_standard_uncertainty(
    sensitivities: List[float],
    standard_uncertainties: List[float]
) -> float:
    """
    Calculate combined standard uncertainty u_c based on the ISO GUM / Coleman & Steele law of propagation:
        u_c = sqrt( sum_{i=1}^N (c_i * u_i)^2 )
        
    Args:
        sensitivities: Partial derivatives (influence coefficients c_i = dY/dX_i).
        standard_uncertainties: Standard uncertainties u_i for each independent parameter.
        
    Returns:
        float: Combined standard uncertainty u_c.
    """
    if len(sensitivities) != len(standard_uncertainties):
        raise ValueError("Sensitivities and uncertainties arrays must have matching length.")
    if len(sensitivities) == 0:
        raise ValueError("Cannot calculate uncertainty with empty parameter lists.")
        
    variance_sum = 0.0
    for c, u in zip(sensitivities, standard_uncertainties):
        variance_sum += (float(c) * float(u)) ** 2
        
    return float(math.sqrt(variance_sum))


def expanded_uncertainty(
    combined_uncertainty: float,
    coverage_factor: float = 2.0
) -> Dict[str, Any]:
    """
    Compute expanded uncertainty U_e:
        U_e = k_cov * u_c
        
    Args:
        combined_uncertainty: Combined standard uncertainty u_c.
        coverage_factor: Coverage factor k_cov (typically 2.0 for approx. 95% confidence interval).
        
    Returns:
        Dict with expanded uncertainty and confidence interval.
    """
    u_c = validate_positive(combined_uncertainty, "combined_uncertainty", strictly_positive=False)
    k = validate_positive(coverage_factor, "coverage_factor", strictly_positive=True)
    
    u_exp = u_c * k
    return {
        "combined_standard_uncertainty": float(u_c),
        "coverage_factor": float(k),
        "expanded_uncertainty": float(u_exp),
        "approximate_confidence_level_percent": 95.45 if abs(k - 2.0) < 0.05 else None
    }


def asme_vv20_validation_comparison(
    s_val: float,
    d_val: float,
    u_num: float,
    u_input: float,
    u_data: float
) -> Dict[str, Any]:
    """
    Perform ASME V&V 20 validation comparison between simulation (S) and experimental data (D).
    
    Comparison error:
        E = S - D
        
    Validation uncertainty:
        u_val = sqrt(u_num^2 + u_input^2 + u_data^2)
        
    Validation check:
        If |E| <= u_val: The simulation is validated to the level of u_val.
        If |E| > u_val: Discrepancy exceeds combined modeling and measurement uncertainty.
        
    Args:
        s_val: Simulation output value S.
        d_val: Benchmark experimental or target value D.
        u_num: Numerical simulation uncertainty (e.g. from GCI).
        u_input: Input parameter uncertainty propagation.
        u_data: Experimental data measurement uncertainty.
        
    Returns:
        Dict containing comparison error E, validation uncertainty u_val, and validation status.
    """
    e = float(s_val - d_val)
    u_n = validate_positive(u_num, "u_num", strictly_positive=False)
    u_in = validate_positive(u_input, "u_input", strictly_positive=False)
    u_d = validate_positive(u_data, "u_data", strictly_positive=False)
    
    u_val = math.sqrt(u_n**2 + u_in**2 + u_d**2)
    is_validated = bool(abs(e) <= u_val)
    
    return {
        "simulation_value_S": float(s_val),
        "experimental_value_D": float(d_val),
        "comparison_error_E": round(float(e), 5),
        "validation_uncertainty_u_val": round(float(u_val), 5),
        "is_validated_within_uncertainty": is_validated,
        "standard_reference": "ASME V&V 20-2009 Standard for Verification and Validation"
    }

