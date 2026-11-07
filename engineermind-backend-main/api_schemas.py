"""
api_schemas.py - Strongly-Typed Pydantic Schemas for Engineering Computation Endpoints.

Provides rigorous data validation, physical dimension specifications, SI unit annotations,
and transparent validation reporting for aerospace engineering calculations.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


# ==========================================
# 1. Physics & Boundary Layer Schemas
# ==========================================
class CaseInput(BaseModel):
    velocity: float = Field(..., gt=0, description="Freestream flow speed U_inf in meters per second [m/s]")
    chord_length: float = Field(..., gt=0, description="Aerodynamic reference chord length c in meters [m]")
    target_y_plus: float = Field(..., gt=0, description="Target non-dimensional wall distance y+ [-]")
    regime: str = Field(default="external_aerodynamics", description="Flow regime: 'external_aerodynamics' or 'internal_nozzle'")


class HandCalculationReport(BaseModel):
    reynolds_number: float = Field(..., description="Reynolds number Re [-]")
    dynamic_pressure_pa: float = Field(..., description="Dynamic pressure q_inf [Pa]")
    skin_friction_coeff: float = Field(..., description="Skin friction coefficient Cf [-]")
    wall_shear_stress_pa: float = Field(..., description="Wall shear stress tau_w [Pa]")
    friction_velocity_ms: float = Field(..., description="Friction velocity u_tau [m/s]")
    first_cell_height_mm: float = Field(..., description="First cell spacing delta_s in millimeters [mm]")
    first_cell_height_m: Optional[float] = Field(None, description="First cell spacing delta_s in meters [m]")
    boundary_layer_thickness_mm: float = Field(..., description="Boundary layer thickness delta_99 in millimeters [mm]")
    estimated_friction_drag_n_per_m: float = Field(..., description="Sectional friction drag [N/m]")
    theoretical_cl_alpha_per_deg: float = Field(..., description="Thin airfoil theory lift slope [1/deg]")
    theoretical_cl_at_4deg: float = Field(..., description="Thin airfoil theory lift at alpha=4 deg [-]")
    expected_cd0_range: str = Field(..., description="Expected parasitic zero-lift drag coefficient range")


class PhysicsOutput(BaseModel):
    reynolds_number: float
    mach_number: float
    flow_regime: str
    boundary_layer_thickness_mm: float
    skin_friction_coeff: float
    wall_shear_stress_pa: float
    friction_velocity_ms: float
    first_cell_height_mm: float
    first_cell_height_m: Optional[float] = None
    recommended_prism_layers: int
    recommended_growth_rate: float
    inlet_distance_m: float
    outlet_distance_m: float
    lateral_distance_m: float
    recommended_turbulence_model: str
    wall_treatment_rationale: str
    hand_calculation: HandCalculationReport
    calculation_method: Optional[str] = "engineering_core (Deterministic Physics)"
    is_verified: Optional[bool] = True


# ==========================================
# 2. Atmosphere & Fluid Properties Schemas
# ==========================================
class AtmosphereRequest(BaseModel):
    altitude_m: float = Field(default=0.0, ge=-500.0, le=11000.0, description="Geometric altitude above MSL [m]")


class AtmosphereResponse(BaseModel):
    altitude_m: float
    temperature_k: float
    pressure_pa: float
    density_kg_m3: float
    speed_of_sound_ms: float
    dynamic_viscosity_pa_s: float
    kinematic_viscosity_m2_s: float
    method: str
    assumptions: str


# ==========================================
# 3. Turbulence Boundary Conditions Schemas
# ==========================================
class TurbulenceInletRequest(BaseModel):
    velocity_ms: float = Field(..., gt=0, description="Freestream flow velocity [m/s]")
    turbulent_intensity_percent: float = Field(default=1.0, gt=0, le=50.0, description="Turbulence intensity I in %")
    turbulent_length_scale_m: Optional[float] = Field(default=0.01, gt=0, description="Turbulent length scale l [m]")
    viscosity_ratio: Optional[float] = Field(default=None, gt=0, description="Turbulent viscosity ratio nut/nu [-]")


class TurbulenceInletResponse(BaseModel):
    k_m2_s2: float
    omega_per_s: float
    epsilon_m2_s3: float
    eddy_viscosity_nut_m2_s: float
    turbulence_intensity_percent: float
    model_reference: str


class WallTreatmentRequest(BaseModel):
    target_y_plus: float = Field(..., gt=0, description="Target wall-normal spacing y+ [-]")


class WallTreatmentResponse(BaseModel):
    target_y_plus: float
    regime: str
    is_physically_recommended: bool
    warning: Optional[str] = None
    rationale: str
    openfoam_boundary_conditions: Dict[str, str]


# ==========================================
# 4. Mesh & Domain Sizing Schemas
# ==========================================
class DomainSizingRequest(BaseModel):
    chord_m: float = Field(..., gt=0, description="Airfoil reference chord [m]")
    inlet_factor: float = Field(default=15.0, gt=0, description="Upstream cushion [chord lengths]")
    outlet_factor: float = Field(default=25.0, gt=0, description="Downstream wake cushion [chord lengths]")
    lateral_factor: float = Field(default=15.0, gt=0, description="Lateral/height cushion [chord lengths]")
    span_m: float = Field(default=0.2, gt=0, description="3D spanwise extrusion width [m]")


class DomainSizingResponse(BaseModel):
    chord_m: float
    inlet_distance_m: float
    outlet_distance_m: float
    lateral_distance_m: float
    bounds: Dict[str, float]
    dimensions: Dict[str, float]
    guideline: str


class SnappyLayersRequest(BaseModel):
    first_cell_m: float = Field(..., gt=0, description="First cell height h1 [m]")
    num_layers: int = Field(default=28, ge=1, le=100, description="Number of prism layers N")
    expansion_ratio: float = Field(default=1.15, gt=1.0, le=1.5, description="Expansion ratio r")


class SnappyLayersResponse(BaseModel):
    relativeSizes: bool
    nSurfaceLayers: int
    expansionRatio: float
    firstLayerThickness: float
    finalLayerThickness: float
    minThickness: float
    totalThickness: float
    math_consistency_check: Dict[str, Any]


# ==========================================
# 5. Verification & Uncertainty Schemas
# ==========================================
class GciRequestDTO(BaseModel):
    f_coarse: float = Field(..., gt=0, description="Solution on coarse grid (h3)")
    f_medium: float = Field(..., gt=0, description="Solution on medium grid (h2)")
    f_fine: float = Field(..., gt=0, description="Solution on fine grid (h1)")
    r: float = Field(default=1.414, gt=1.0, description="Grid refinement ratio r = h_coarse / h_fine")


class GciResponseDTO(BaseModel):
    apparent_order_p: float
    theoretical_order: float
    relative_error_eps21_percent: float
    gci_fine_percent: float
    is_asymptotic_range: bool
    verdict: str
    recommendation: str
    standard_reference: Optional[str] = "ASME V&V 20-2009 / Celik et al. (2008)"


class AsmeValidationRequest(BaseModel):
    simulation_val: float = Field(..., description="Simulation predicted value S")
    benchmark_val: float = Field(..., description="Benchmark/experimental target value D")
    u_num: float = Field(default=0.0, ge=0, description="Numerical simulation uncertainty")
    u_input: float = Field(default=0.0, ge=0, description="Input parameter uncertainty")
    u_data: float = Field(default=0.0, ge=0, description="Experimental measurement uncertainty")


class AsmeValidationResponse(BaseModel):
    simulation_value_S: float
    experimental_value_D: float
    comparison_error_E: float
    validation_uncertainty_u_val: float
    is_validated_within_uncertainty: bool
    standard_reference: str

