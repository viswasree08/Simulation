"""
tests/engineering_core/test_uncertainty.py - ISO GUM and ASME V&V 20 Uncertainty Verification.
"""

import pytest
import math
from engineering_core.uncertainty import (
    combined_standard_uncertainty,
    expanded_uncertainty,
    asme_vv20_validation_comparison
)


def test_combined_uncertainty_benchmarks():
    """
    Verify ISO GUM law of propagation:
        u_c = sqrt( sum (c_i * u_i)^2 )
    Case: Linear system Y = 2*X1 - 3*X2
        c1 = 2.0, u1 = 0.05
        c2 = -3.0, u2 = 0.04
        u_c^2 = (2.0 * 0.05)^2 + (-3.0 * 0.04)^2 = 0.1^2 + (-0.12)^2 = 0.01 + 0.0144 = 0.0244
        u_c = sqrt(0.0244) = 0.15620499...
    """
    u_c = combined_standard_uncertainty(
        sensitivities=[2.0, -3.0],
        standard_uncertainties=[0.05, 0.04]
    )
    assert math.isclose(u_c, 0.156205, rel_tol=1e-5)


def test_combined_uncertainty_dimension_mismatch():
    """Verify mismatched input lengths raise ValueError."""
    with pytest.raises(ValueError, match="matching length"):
        combined_standard_uncertainty([1.0, 2.0], [0.1])

    with pytest.raises(ValueError, match="empty parameter lists"):
        combined_standard_uncertainty([], [])


def test_expanded_uncertainty_k2():
    """
    Verify expanded uncertainty U_e = k * u_c.
    At k = 2.0 (standard 95.45% coverage interval):
        u_c = 0.05 => U_e = 0.10
    """
    res = expanded_uncertainty(combined_uncertainty=0.05, coverage_factor=2.0)
    assert math.isclose(res["expanded_uncertainty"], 0.10, abs_tol=1e-7)
    assert res["approximate_confidence_level_percent"] == 95.45


def test_asme_vv20_validation_comparison_cases():
    """
    Verify ASME V&V 20 validation metric:
        E = S - D
        u_val = sqrt(u_num^2 + u_input^2 + u_data^2)
        Validated if |E| <= u_val.
    """
    # Case 1: Validated within uncertainty
    # S = 0.0215, D = 0.0210 => E = 0.0005
    # u_num = 0.0004, u_in = 0.0003, u_d = 0.0005
    # u_val = sqrt(16 + 9 + 25) * 1e-4 = sqrt(50) * 1e-4 = 0.0007071
    # |E| = 0.0005 <= 0.0007071 => Validated!
    res1 = asme_vv20_validation_comparison(
        s_val=0.0215,
        d_val=0.0210,
        u_num=0.0004,
        u_input=0.0003,
        u_data=0.0005
    )
    assert res1["is_validated_within_uncertainty"] is True
    assert math.isclose(res1["comparison_error_E"], 0.0005, abs_tol=1e-6)
    assert math.isclose(res1["validation_uncertainty_u_val"], 0.00071, rel_tol=1e-3)

    # Case 2: Not validated (Error exceeds uncertainty bounds)
    # S = 0.0250, D = 0.0210 => E = 0.0040 > 0.0007071 => Failed validation
    res2 = asme_vv20_validation_comparison(
        s_val=0.0250,
        d_val=0.0210,
        u_num=0.0004,
        u_input=0.0003,
        u_data=0.0005
    )
    assert res2["is_validated_within_uncertainty"] is False

