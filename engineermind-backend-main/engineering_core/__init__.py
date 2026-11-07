"""
engineering_core - Modular Deterministic Engineering Computation Engine for EngineerMind AI.

This package provides independent, mathematically validated scientific algorithms
for aerodynamics, boundary layer physics, turbulence modeling, grid generation,
and ASME V&V 20 numerical verification.
"""

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
    ISA_P0,
    ISA_T0,
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

__all__ = [
    # Units
    "validate_positive",
    "validate_in_range",
    "to_si_length",
    "to_si_velocity",
    "to_si_pressure",
    "to_kelvin",
    # Fluid Properties
    "sutherland_viscosity",
    "standard_atmosphere_isa",
    "get_fluid_properties",
    "ISA_P0",
    "ISA_T0",
    "ISA_RHO0",
    "ISA_MU0",
    # Aerodynamics
    "reynolds_number",
    "mach_number",
    "dynamic_pressure",
    "classify_flow_regime",
    "thin_airfoil_theory_cl",
    # Boundary Layer
    "skin_friction_coefficient_flat_plate",
    "wall_shear_stress",
    "friction_velocity",
    "first_cell_height",
    "boundary_layer_thickness_flat_plate",
    "generate_geometric_layer_stack",
    # Mesh Calculator
    "calculate_external_aero_domain_bounds",
    "calculate_snappy_hex_mesh_layers",
    # Turbulence
    "turbulence_inlet_boundary_conditions",
    "assess_wall_treatment",
    # Numerical Methods
    "pressure_coefficient",
    "compute_rolling_standard_deviation",
    "courant_number_1d",
    # Verification
    "calculate_grid_convergence_index",
    # Uncertainty
    "combined_standard_uncertainty",
    "expanded_uncertainty",
    "asme_vv20_validation_comparison"
]

