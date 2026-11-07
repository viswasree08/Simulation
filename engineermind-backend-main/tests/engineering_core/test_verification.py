"""
tests/engineering_core/test_verification.py - ASME V&V 20 and Grid Convergence Index Verification.
"""

import pytest
import math
from engineering_core.verification import calculate_grid_convergence_index


def test_gci_celik_published_benchmark():
    """
    Verify GCI against Celik et al. (2008) ASME benchmark example:
    Three grids for axial velocity:
        Fine grid h1: f1 = 6.063
        Medium grid h2: f2 = 5.972 (r21 = 1.3)
        Coarse grid h3: f3 = 5.863 (r32 = 1.3)
    Analytical derivation:
        eps21_abs = 5.972 - 6.063 = -0.091
        eps32_abs = 5.863 - 5.972 = -0.109
        ratio s = -0.109 / -0.091 = 1.197802...
        apparent order p = ln(1.197802) / ln(1.3) = 0.180488 / 0.262364 = 0.6879...
        Relative fine error = |(5.972 - 6.063) / 6.063| = 0.091 / 6.063 = 0.01501 (1.501%)
    """
    res = calculate_grid_convergence_index(
        f1=6.063,
        f2=5.972,
        f3=5.863,
        r21=1.3,
        r32=1.3,
        order_p_theoretical=2.0
    )

    assert math.isclose(res["apparent_order_p"], 0.6879, rel_tol=1e-2)
    assert math.isclose(res["relative_error_eps21_percent"], 1.501, rel_tol=1e-2)
    assert res["convergence_type"] == "Monotonic Convergence"
    assert res["gci_fine_percent"] > 0.0


def test_gci_second_order_roache_example():
    """
    Verify classical 2nd-order test case from Roache (1998):
        f(h) = f_exact + c * h^2
        h1 = 1.0 => f1 = 1.000 + 0.1 * 1.0 = 1.100
        h2 = 2.0 (r=2.0) => f2 = 1.000 + 0.1 * 4.0 = 1.400
        h3 = 4.0 (r=2.0) => f3 = 1.000 + 0.1 * 16.0 = 2.600
    Apparent order:
        (f3 - f2) / (f2 - f1) = (2.6 - 1.4) / (1.4 - 1.1) = 1.2 / 0.3 = 4.0
        p = ln(4.0) / ln(2.0) = 2.00000 (Exact 2nd-order recovery!)
    """
    res = calculate_grid_convergence_index(
        f1=1.1,
        f2=1.4,
        f3=2.6,
        r21=2.0,
        r32=2.0,
        order_p_theoretical=2.0,
        safety_factor=1.25
    )

    assert math.isclose(res["apparent_order_p"], 2.0, abs_tol=1e-6)
    assert math.isclose(res["clamped_order_p"], 2.0, abs_tol=1e-6)

    # Relative error eps21 = (1.4 - 1.1) / 1.1 = 0.3 / 1.1 = 0.272727 (27.27%)
    # GCI_fine = 1.25 * (0.3 / 1.1) / (2.0^2 - 1) * 100% = 1.25 * 0.272727 / 3 * 100% = 11.3636%
    assert math.isclose(res["gci_fine_percent"], 11.3636, rel_tol=1e-3)
    assert res["verdict"] == "MESH_REFINEMENT_REQUIRED"


def test_gci_identical_grids_machine_precision():
    """Verify machine-precision identical grids evaluate safely to 0% error without division by zero."""
    res = calculate_grid_convergence_index(
        f1=0.0215,
        f2=0.0215,
        f3=0.0215,
        r21=1.3
    )
    assert res["relative_error_eps21_percent"] == 0.0
    assert res["gci_fine_percent"] == 0.0
    assert res["verdict"] == "GRID_INDEPENDENT"
    assert res["is_asymptotic_range"] is True


def test_gci_invalid_refinement_ratios():
    """Verify refinement ratios <= 1.0 raise ValueError."""
    with pytest.raises(ValueError, match="strictly greater than 1.0"):
        calculate_grid_convergence_index(1.0, 1.2, 1.4, r21=0.9)

    with pytest.raises(ValueError, match="strictly greater than 1.0"):
        calculate_grid_convergence_index(1.0, 1.2, 1.4, r21=1.0)

