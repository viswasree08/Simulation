"""
Comprehensive Unit Test Suite for engineering_core and its modules.
Tests physical correctness, mathematical constraints, edge cases, and unit conversions.
"""

import math
import pytest
import numpy as np

from engineering_core.units import (
    validate_positive,
    validate_in_range,
    to_si_length,
    to_si_velocity,
    to_si_pressure,
    to_kelvin
)

from engineering_core.fluid_properties import (
    sutherland_viscosity,
    standard_atmosphere_isa,
    get_fluid_properties,
    ISA_RHO0,
    ISA_MU0
)

from engineering_core.aerodynamics import (
    reynolds_number,
    mach_number,
    dynamic_pressure,
    classify_flow_regime,
    thin_airfoil_theory_cl
)

from engineering_core.boundary_layer import (
    skin_friction_coefficient_flat_plate,
    wall_shear_stress,
    friction_velocity,
    first_cell_height,
    boundary_layer_thickness_flat_plate,
    generate_geometric_layer_stack
)

from engineering_core.mesh_calculator import (
    calculate_external_aero_domain_bounds,
    calculate_snappy_hex_mesh_layers
)

from engineering_core.turbulence import (
    turbulence_inlet_boundary_conditions,
    assess_wall_treatment
)

from engineering_core.numerical_methods import (
    pressure_coefficient,
    compute_rolling_standard_deviation,
    courant_number_1d
)

from engineering_core.verification import (
    calculate_grid_convergence_index
)

from engineering_core.uncertainty import (
    combined_standard_uncertainty,
    expanded_uncertainty,
    asme_vv20_validation_comparison
)


# ==========================================
# 1. UNITS & VALIDATION TESTS
# ==========================================
def test_units_validation():
    assert validate_positive(10.5, "test") == 10.5
    with pytest.raises(ValueError):
        validate_positive(-1.0, "test")
    with pytest.raises(ValueError):
        validate_positive(0.0, "test", strictly_positive=True)
    assert validate_positive(0.0, "test", strictly_positive=False) == 0.0
    with pytest.raises(TypeError):
        validate_positive("invalid", "test")

    assert validate_in_range(5.0, "val", 1.0, 10.0) == 5.0
    with pytest.raises(ValueError):
        validate_in_range(0.5, "val", 1.0, 10.0)


def test_unit_conversions():
    assert math.isclose(to_si_length(1.0, "in"), 0.0254)
    assert math.isclose(to_si_length(1.0, "ft"), 0.3048)
    assert math.isclose(to_si_length(1000.0, "mm"), 1.0)
    assert math.isclose(to_si_velocity(36.0, "km/h"), 10.0)
    assert math.isclose(to_si_pressure(1.0, "bar"), 100000.0)
    assert math.isclose(to_kelvin(0.0, "C"), 273.15)
    assert math.isclose(to_kelvin(32.0, "F"), 273.15)


# ==========================================
# 2. FLUID PROPERTIES TESTS
# ==========================================
def test_fluid_properties_isa():
    isa_sl = standard_atmosphere_isa(0.0)
    assert math.isclose(isa_sl["temperature_k"], 288.15, rel_tol=1e-3)
    assert math.isclose(isa_sl["pressure_pa"], 101325.0, rel_tol=1e-3)
    assert math.isclose(isa_sl["density_kg_m3"], 1.225, rel_tol=1e-2)
    assert math.isclose(isa_sl["speed_of_sound_ms"], 340.28, rel_tol=1e-2)

    # Sutherland viscosity at 288.15K should match ~1.789e-5
    mu_sl = sutherland_viscosity(288.15)
    assert math.isclose(mu_sl, 1.789e-5, rel_tol=1e-2)

    # 5000m altitude check
    isa_5k = standard_atmosphere_isa(5000.0)
    assert isa_5k["temperature_k"] < isa_sl["temperature_k"]
    assert isa_5k["pressure_pa"] < isa_sl["pressure_pa"]
    assert isa_5k["density_kg_m3"] < isa_sl["density_kg_m3"]


def test_fluid_properties_catalog():
    air = get_fluid_properties("air_sea_level")
    assert air["density_kg_m3"] == 1.225
    water = get_fluid_properties("water_20c")
    assert water["density_kg_m3"] == 998.2


# ==========================================
# 3. AERODYNAMICS TESTS
# ==========================================
def test_aerodynamics():
    # U = 40 m/s, c = 1.0 m, rho = 1.225, mu = 1.789e-5
    # Re = 1.225 * 40 * 1.0 / 1.789e-5 = 2,738,960.31
    re = reynolds_number(40.0, 1.0)
    assert math.isclose(re, 2738960.31, rel_tol=1e-4)

    ma = mach_number(40.0, 340.28)
    assert math.isclose(ma, 40.0 / 340.28, rel_tol=1e-4)

    # Dynamic pressure q = 0.5 * 1.225 * 40^2 = 980 Pa
    q = dynamic_pressure(40.0)
    assert math.isclose(q, 980.0, rel_tol=1e-5)

    regime = classify_flow_regime(re, ma)
    assert "Incompressible" in regime["flow_regime"]
    assert "Turbulent" in regime["flow_regime"]

    # Thin airfoil theory: Cl = 2 * pi * alpha_rad. At 4 deg = 4 * pi / 180 * 2 * pi = ~0.4386
    cl = thin_airfoil_theory_cl(4.0)
    assert math.isclose(cl, 0.4386, rel_tol=1e-2)


# ==========================================
# 4. BOUNDARY LAYER TESTS
# ==========================================
def test_boundary_layer():
    re = 2738960.31
    cf = skin_friction_coefficient_flat_plate(re, method="schlichting")
    assert 0.0025 < cf < 0.0040

    tau_w = wall_shear_stress(cf, 980.0)
    u_tau = friction_velocity(tau_w, 1.225)
    nu = 1.789e-5 / 1.225
    delta_s = first_cell_height(1.0, u_tau, nu)

    # First cell height for U=40, c=1.0 at y+=1 is ~9.4e-6 m (0.0094 mm)
    assert 5e-6 < delta_s < 1.5e-5

    stack = generate_geometric_layer_stack(first_cell_m=delta_s, growth_rate=1.15, num_layers=28)
    assert stack["num_layers"] == 28
    assert len(stack["layer_heights_m"]) == 28
    # Last layer should match h1 * (1.15)^27
    expected_final = delta_s * (1.15 ** 27)
    assert math.isclose(stack["final_layer_thickness_m"], expected_final, rel_tol=1e-4)


# ==========================================
# 5. MESH CALCULATOR TESTS
# ==========================================
def test_mesh_calculator():
    bounds = calculate_external_aero_domain_bounds(chord_m=1.0, inlet_factor=15.0, outlet_factor=25.0)
    assert bounds["inlet_distance_m"] == 15.0
    assert bounds["outlet_distance_m"] == 25.0
    assert bounds["bounds"]["min_x"] == -15.0
    assert bounds["bounds"]["max_x"] == 26.0

    snappy_layers = calculate_snappy_hex_mesh_layers(first_cell_m=1e-5, num_layers=28, expansion_ratio=1.15)
    assert snappy_layers["nSurfaceLayers"] == 28
    assert snappy_layers["math_consistency_check"]["is_geometrically_consistent"] is True


# ==========================================
# 6. TURBULENCE TESTS
# ==========================================
def test_turbulence():
    inflow = turbulence_inlet_boundary_conditions(velocity_ms=40.0, turbulent_intensity_percent=1.0)
    assert inflow["k_m2_s2"] > 0
    assert inflow["omega_per_s"] > 0
    assert inflow["epsilon_m2_s3"] > 0

    # Test y+ regime assessment
    res_sublayer = assess_wall_treatment(0.8)
    assert res_sublayer["is_physically_recommended"] is True
    assert "Viscous Sublayer" in res_sublayer["regime"]

    res_buffer = assess_wall_treatment(15.0)
    assert res_buffer["is_physically_recommended"] is False
    assert "Buffer Layer" in res_buffer["regime"]

    res_loglaw = assess_wall_treatment(50.0)
    assert res_loglaw["is_physically_recommended"] is True
    assert "Log-Law" in res_loglaw["regime"]


# ==========================================
# 7. NUMERICAL METHODS TESTS
# ==========================================
def test_numerical_methods():
    # Test kinematic Cp (OpenFOAM p / rho)
    # If p_OF = 800 m^2/s^2 at U = 40 m/s: Cp = 800 / (0.5 * 40^2) = 800 / 800 = 1.0 (stagnation)
    cp_stag = pressure_coefficient(surface_pressure=800.0, freestream_velocity_ms=40.0, is_kinematic_pressure=True)
    assert math.isclose(cp_stag, 1.0, rel_tol=1e-5)

    # Array test
    pressures = [800.0, 400.0, 0.0]
    cps = pressure_coefficient(surface_pressure=pressures, freestream_velocity_ms=40.0, is_kinematic_pressure=True)
    assert math.isclose(cps[0], 1.0)
    assert math.isclose(cps[1], 0.5)
    assert math.isclose(cps[2], 0.0)

    # Rolling std dev
    series = [0.0210] * 50
    stats = compute_rolling_standard_deviation(series, window_size=50)
    assert stats["is_converged_statistically"] is True
    assert math.isclose(stats["standard_deviation"], 0.0, abs_tol=1e-7)

    cfl = courant_number_1d(velocity_ms=40.0, delta_t_s=0.0001, delta_x_m=0.01)
    assert math.isclose(cfl, 0.4)


# ==========================================
# 8. VERIFICATION (ASME V&V 20 GCI) TESTS
# ==========================================
def test_verification_gci():
    # Systematic grid refinement: f1=fine, f2=medium, f3=coarse
    # Example monotonic series: f1=0.0210, f2=0.0215, f3=0.0224 with r=1.3
    res = calculate_grid_convergence_index(f1=0.0210, f2=0.0215, f3=0.0224, r21=1.3, r32=1.3)
    assert res["apparent_order_p"] > 0
    assert res["gci_fine_percent"] > 0
    assert "verdict" in res

    # Machine zero difference check
    res_zero = calculate_grid_convergence_index(f1=0.0210, f2=0.0210, f3=0.0210, r21=1.3)
    assert res_zero["gci_fine_percent"] == 0.0
    assert res_zero["verdict"] == "GRID_INDEPENDENT"


# ==========================================
# 9. UNCERTAINTY TESTS
# ==========================================
def test_uncertainty():
    # Combined uncertainty: c1=1.0, u1=0.02, c2=2.0, u2=0.01 -> sqrt(0.02^2 + 0.02^2) = 0.02828
    u_c = combined_standard_uncertainty(sensitivities=[1.0, 2.0], standard_uncertainties=[0.02, 0.01])
    assert math.isclose(u_c, math.sqrt(0.0004 + 0.0004), rel_tol=1e-4)

    exp_res = expanded_uncertainty(combined_uncertainty=u_c, coverage_factor=2.0)
    assert math.isclose(exp_res["expanded_uncertainty"], 2.0 * u_c)

    # ASME V&V 20 validation comparison
    val_res = asme_vv20_validation_comparison(s_val=0.021, d_val=0.020, u_num=0.0005, u_input=0.0005, u_data=0.001)
    assert val_res["is_validated_within_uncertainty"] is True

