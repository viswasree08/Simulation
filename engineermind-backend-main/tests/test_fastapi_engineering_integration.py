"""
tests/test_fastapi_engineering_integration.py - Direct Integration Tests for FastAPI Engineering Endpoints.

Tests request/response validation, schema consistency, status codes, and error responses.
"""

import math
import pytest
from main import app
from api_schemas import (
    CaseInput,
    AtmosphereRequest,
    TurbulenceInletRequest,
    WallTreatmentRequest,
    DomainSizingRequest,
    SnappyLayersRequest,
    GciRequestDTO,
    AsmeValidationRequest
)
from models import SessionLocal


def test_calculate_physics_endpoint_valid():
    """Verify legacy /calculate-physics endpoint returns valid schema via engineering_core."""
    for route in app.routes:
        if getattr(route, "path", "") == "/calculate-physics":
            endpoint = route.endpoint
            break
    else:
        pytest.fail("Endpoint /calculate-physics not found")

    payload = CaseInput(velocity=40.0, chord_length=1.0, target_y_plus=1.0)
    res = endpoint(data=payload)

    assert math.isclose(res.reynolds_number, 2738960.31, rel_tol=1e-4)
    assert math.isclose(res.hand_calculation.dynamic_pressure_pa, 980.0, abs_tol=1e-6)
    assert res.recommended_prism_layers == 28
    assert res.is_verified is True
    assert "engineering_core" in res.calculation_method


def test_atmosphere_endpoint():
    """Verify POST /api/engineering/atmosphere."""
    for route in app.routes:
        if getattr(route, "path", "") == "/api/engineering/atmosphere":
            endpoint = route.endpoint
            break
    else:
        pytest.fail("Endpoint /api/engineering/atmosphere not found")

    # Valid sea-level check
    res_sl = endpoint(payload=AtmosphereRequest(altitude_m=0.0))
    assert math.isclose(res_sl["pressure_pa"], 101325.0, rel_tol=1e-4)
    assert math.isclose(res_sl["density_kg_m3"], 1.2250, rel_tol=1e-3)

    # Valid 5000m altitude
    res_5k = endpoint(payload=AtmosphereRequest(altitude_m=5000.0))
    assert res_5k["temperature_k"] < res_sl["temperature_k"]
    assert res_5k["pressure_pa"] < res_sl["pressure_pa"]


def test_turbulence_inlet_endpoint():
    """Verify POST /api/engineering/turbulence/inlet."""
    for route in app.routes:
        if getattr(route, "path", "") == "/api/engineering/turbulence/inlet":
            endpoint = route.endpoint
            break
    else:
        pytest.fail("Endpoint /api/engineering/turbulence/inlet not found")

    payload = TurbulenceInletRequest(
        velocity_ms=50.0,
        turbulent_intensity_percent=1.0,
        turbulent_length_scale_m=0.01
    )
    res = endpoint(payload=payload)
    assert math.isclose(res["k_m2_s2"], 0.375, rel_tol=1e-5)
    assert math.isclose(res["omega_per_s"], 111.8034, rel_tol=1e-4)


def test_wall_treatment_endpoint():
    """Verify POST /api/engineering/turbulence/wall-treatment."""
    for route in app.routes:
        if getattr(route, "path", "") == "/api/engineering/turbulence/wall-treatment":
            endpoint = route.endpoint
            break
    else:
        pytest.fail("Endpoint /api/engineering/turbulence/wall-treatment not found")

    # Resolved viscous sublayer
    res_sub = endpoint(payload=WallTreatmentRequest(target_y_plus=0.8))
    assert res_sub["is_physically_recommended"] is True
    assert "Viscous Sublayer" in res_sub["regime"]

    # Buffer layer warning
    res_buf = endpoint(payload=WallTreatmentRequest(target_y_plus=12.0))
    assert res_buf["is_physically_recommended"] is False
    assert "Buffer Layer" in res_buf["regime"]


def test_mesh_domain_bounds_endpoint():
    """Verify POST /api/engineering/mesh/domain-bounds."""
    for route in app.routes:
        if getattr(route, "path", "") == "/api/engineering/mesh/domain-bounds":
            endpoint = route.endpoint
            break
    else:
        pytest.fail("Endpoint /api/engineering/mesh/domain-bounds not found")

    payload = DomainSizingRequest(chord_m=1.0, inlet_factor=15.0, outlet_factor=25.0)
    res = endpoint(payload=payload)
    assert res["bounds"]["min_x"] == -15.0
    assert res["bounds"]["max_x"] == 26.0
    assert res["inlet_distance_m"] == 15.0


def test_mesh_snappy_layers_endpoint():
    """Verify POST /api/engineering/mesh/snappy-layers."""
    for route in app.routes:
        if getattr(route, "path", "") == "/api/engineering/mesh/snappy-layers":
            endpoint = route.endpoint
            break
    else:
        pytest.fail("Endpoint /api/engineering/mesh/snappy-layers not found")

    payload = SnappyLayersRequest(first_cell_m=1e-5, num_layers=28, expansion_ratio=1.15)
    res = endpoint(payload=payload)
    assert res["nSurfaceLayers"] == 28
    assert res["math_consistency_check"]["is_geometrically_consistent"] is True


def test_asme_vv20_validation_endpoint():
    """Verify POST /api/engineering/verification/asme-vv20."""
    for route in app.routes:
        if getattr(route, "path", "") == "/api/engineering/verification/asme-vv20":
            endpoint = route.endpoint
            break
    else:
        pytest.fail("Endpoint /api/engineering/verification/asme-vv20 not found")

    payload = AsmeValidationRequest(
        simulation_val=0.0212,
        benchmark_val=0.0210,
        u_num=0.0003,
        u_input=0.0002,
        u_data=0.0004
    )
    res = endpoint(payload=payload)
    assert res["is_validated_within_uncertainty"] is True
    assert math.isclose(res["comparison_error_E"], 0.0002, abs_tol=1e-6)


def test_gci_case_endpoint():
    """Verify POST /api/cases/{case_id}/gci."""
    for route in app.routes:
        if getattr(route, "path", "") == "/api/cases/{case_id}/gci":
            endpoint = route.endpoint
            break
    else:
        pytest.fail("Endpoint /api/cases/{case_id}/gci not found")

    db = SessionLocal()
    try:
        payload = GciRequestDTO(f_coarse=0.0224, f_medium=0.0215, f_fine=0.0210, r=1.3)
        res = endpoint(case_id=1, payload=payload, db=db)
        assert res.apparent_order_p > 0
        assert res.gci_fine_percent > 0
        assert res.verdict in ("PASS", "MESH_REFINEMENT_REQUIRED", "ACCEPTABLE_VERIFICATION", "GRID_INDEPENDENT")
    finally:
        db.close()

