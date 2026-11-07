# Engineering Core Implementation Report — Task 02

**Project:** EngineerMind AI / AeroForge Systems  
**Module:** `engineering_core/` (Independent Scientific Computation Layer)  
**Date:** November 2026  
**Status:** Completed & Validated (100% Deterministic Python, Zero AI Dependency)

---

## 1. Executive Summary

In accordance with **TASK 02**, all mathematical, aerothermal, boundary layer, grid inflation, turbulence inlet, numerical reduction, and ASME V&V 20 verification algorithms have been refactored out of monolithic route handlers and heuristic scripts into an independent, modular scientific computing package: `engineering_core/`.

All 10 proposed core modules have been created under `engineermind-backend-main/engineering_core/`. Existing caller code (`aerocore.py`) has been refactored to delegate directly to `engineering_core`, preserving 100% backward compatibility for all API endpoints and database models without regressions.

---

## 2. Implemented Modules and Physical Specifications

### 2.1 `units.py`
- **Purpose:** Physical dimension verification, unit validation, and standard SI conversions.
- **Key Functions:**
  - `validate_positive(val, name, strictly_positive=True)`: Enforces strictly positive physical quantities (length, velocity, density, viscosity).
  - `validate_in_range(val, name, min_val, max_val)`: Bounded parameter validation.
  - `to_si_length`, `to_si_velocity`, `to_si_pressure`, `to_kelvin`: Deterministic unit converters for imperial/metric aerospace units.

### 2.2 `fluid_properties.py`
- **Purpose:** Thermophysical gas dynamics and atmospheric modeling.
- **Scientific References:**
  - U.S. Standard Atmosphere (1976), NOAA/NASA/USAF.
  - Sutherland, W. (1893), *The viscosity of gases and molecular force*, Phil. Mag.
- **Key Functions:**
  - `sutherland_viscosity(temperature_k)`: Temperature-dependent dynamic viscosity $\mu(T)$ via Sutherland's 3-parameter equation.
  - `standard_atmosphere_isa(altitude_m)`: Troposphere atmospheric conditions ($T(h), p(h), \rho(h), a(h), \nu(h)$).
  - `get_fluid_properties(fluid)`: Fluid property catalog (`air_sea_level`, `water_20c`).

### 2.3 `aerodynamics.py`
- **Purpose:** Non-dimensional aerodynamic governing metrics and classical lift theory.
- **Scientific References:**
  - Anderson, J. D., *Fundamentals of Aerodynamics*, 6th Edition (McGraw-Hill, 2016).
  - Abbott, I. H., and von Doenhoff, A. E., *Theory of Wing Sections* (Dover, 1959).
- **Key Functions:**
  - `reynolds_number(velocity_ms, chord_m, rho, mu)`: $Re = \frac{\rho U c}{\mu}$.
  - `mach_number(velocity_ms, speed_of_sound_ms)`: $Ma = \frac{U}{a}$.
  - `dynamic_pressure(velocity_ms, rho)`: $q_\infty = \frac{1}{2}\rho U_\infty^2$.
  - `classify_flow_regime(re, ma)`: Incompressible vs. Subsonic Compressible vs. Transonic vs. Supersonic regime bounds.
  - `thin_airfoil_theory_cl(alpha_deg)`: Sectional lift slope $C_l = 2\pi\alpha$ (inviscid, small angle).

### 2.4 `boundary_layer.py`
- **Purpose:** Viscous shear stress, friction velocity, first cell spacing, and geometric prism layer inflation.
- **Scientific References:**
  - Schlichting, H., and Gersten, K., *Boundary-Layer Theory*, 9th Edition (Springer, 2017).
  - White, F. M., *Viscous Fluid Flow*, 3rd Edition (McGraw-Hill, 2006).
- **Key Functions:**
  - `skin_friction_coefficient_flat_plate(re_x, method)`: Schlichting ($C_f = [2\log_{10}(Re_x) - 0.65]^{-2.3}$) and Prandtl 1/7th power law ($C_f = 0.0592 Re_x^{-0.2}$).
  - `wall_shear_stress(cf, q_inf)`: $\tau_w = C_f q_\infty$.
  - `friction_velocity(tau_w, rho)`: $u_\tau = \sqrt{\frac{\tau_w}{\rho}}$.
  - `first_cell_height(target_y_plus, u_tau, nu)`: $\Delta s = \frac{y^+ \nu}{u_\tau}$.
  - `boundary_layer_thickness_flat_plate(x_m, re_x)`: $\delta_{99} = \frac{0.37 x}{Re_x^{0.2}}$.
  - `generate_geometric_layer_stack(first_cell_m, growth_rate, num_layers)`: Rigorous geometric series calculation $h_i = h_1 r^{i-1}$, computing exact total thickness and cumulative layer nodes.

### 2.5 `mesh_calculator.py`
- **Purpose:** Domain cushion extents and snappyHexMesh boundary layer parameter alignment.
- **Scientific References:**
  - AIAA Drag Prediction Workshop (DPW) Farfield Guidelines.
  - OpenCFD OpenFOAM v2212 snappyHexMeshDict specification.
- **Key Functions:**
  - `calculate_external_aero_domain_bounds(chord_m, inlet_factor=15, outlet_factor=25, lateral_factor=15)`: Domain sizing conforming to AIAA DPW recommendations.
  - `calculate_snappy_hex_mesh_layers(first_cell_m, num_layers=28, expansion_ratio=1.15)`: Generates geometrically consistent `firstLayerThickness`, `finalLayerThickness` ($h_N = h_1 r^{N-1}$), and `minThickness`, eliminating the 9x discrepancy previously identified.

### 2.6 `turbulence.py`
- **Purpose:** Inflow turbulence boundary condition derivation and wall treatment assessment.
- **Scientific References:**
  - Menter, F. R., *Two-equation eddy-viscosity turbulence models for engineering applications*, AIAA Journal, 32(8), 1994.
  - NASA Langley Turbulence Modeling Resource (TMR): SST-2003 model specifications.
- **Key Functions:**
  - `turbulence_inlet_boundary_conditions(velocity_ms, turbulent_intensity_percent, turbulent_length_scale_m, viscosity_ratio, nu)`: Derives $k = \frac{3}{2}(U_\infty I)^2$, $\omega = \frac{\sqrt{k}}{C_\mu^{0.25} l}$, $\epsilon = \frac{C_\mu k^{1.5}}{l}$, and $\nu_t = \frac{k}{\omega}$.
  - `assess_wall_treatment(target_y_plus)`: Evaluates viscous sublayer ($y^+ \le 1$), buffer layer ($5 \le y^+ \le 30$ warning / invalidity), and log-law layer ($30 < y^+ \le 300$), outputting recommended OpenFOAM BCs (`nutkWallFunction`, `kLowReWallFunction`, `omegaWallFunction`).

### 2.7 `numerical_methods.py`
- **Purpose:** Spatial and temporal numerical reductions, pressure coefficient calculation, and statistical convergence.
- **Scientific References:**
  - Ferziger, J. H., and Peric, M., *Computational Methods for Fluid Dynamics* (Springer, 2002).
- **Key Functions:**
  - `pressure_coefficient(surface_pressure, freestream_velocity_ms, freestream_pressure_pa, rho, is_kinematic_pressure)`: Handles both standard physical gauge pressure and OpenFOAM kinematic pressure ($p/\rho$ in $\text{m}^2/\text{s}^2$).
  - `compute_rolling_standard_deviation(values, window_size=50)`: Calculates $\mu, \sigma, \frac{\sigma}{|\mu|}$ over a rolling window to detect asymptotic convergence of force coefficients.
  - `courant_number_1d(velocity_ms, delta_t_s, delta_x_m)`: $Co = \frac{U \Delta t}{\Delta x}$.

### 2.8 `verification.py`
- **Purpose:** Grid Independence and ASME V&V 20 discretization uncertainty quantification.
- **Scientific References:**
  - ASME V&V 20-2009 Standard for Verification and Validation in CFD and Heat Transfer.
  - Celik, I. B., et al. (2008), *Procedure for Estimation and Reporting of Uncertainty Due to Discretization in CFD Applications*, ASME J. Fluids Eng.
- **Key Functions:**
  - `calculate_grid_convergence_index(f1, f2, f3, r21, r32, order_p_theoretical, safety_factor)`:
    - Calculates apparent spatial order of accuracy $p$.
    - Performs fixed-point iteration for unequal grid refinement ratios.
    - Computes relative fine grid error $\epsilon_{21}$ and $GCI_{fine}$ with factor of safety $F_s = 1.25$ or $3.0$.
    - Evaluates asymptotic range ratio $\frac{GCI_{32}}{r_{21}^p GCI_{21}} \approx 1.0$.

### 2.9 `uncertainty.py`
- **Purpose:** Uncertainty propagation and ASME V&V 20 validation comparison.
- **Scientific References:**
  - ISO/IEC Guide 98-3:2008 (GUM): *Guide to the expression of uncertainty in measurement*.
  - Coleman, H. W., and Steele, W. G., *Experimentation, Validation, and Uncertainty Analysis for Engineers* (Wiley, 2009).
- **Key Functions:**
  - `combined_standard_uncertainty(sensitivities, standard_uncertainties)`: $u_c = \sqrt{\sum (c_i u_i)^2}$.
  - `expanded_uncertainty(combined_uncertainty, coverage_factor=2.0)`: $U_e = k u_c$ (95.45% confidence).
  - `asme_vv20_validation_comparison(s_val, d_val, u_num, u_input, u_data)`: Compares simulation error $E = S - D$ against validation uncertainty $u_{val} = \sqrt{u_{num}^2 + u_{input}^2 + u_{data}^2}$.

### 2.10 `__init__.py`
- Exposes all verified scientific functions in a unified namespace (`from engineering_core import ...`).

---

## 3. Backwards Compatibility & Migration

- `aerocore.py` was refactored to delegate directly to `engineering_core` while preserving its exact API interface and dictionary output contracts for:
  - `compute_physics(velocity, chord_length, target_y_plus, regime)`
  - `calculate_roache_gci(f_coarse, f_medium, f_fine, r)`
- All calling endpoints (`/api/physics/compute`, `/api/verification/gci`, `/api/cases`) continue to function without any breaking schema changes.

---

## 4. Test Suite Execution & Verification

A dedicated unit test suite was implemented in `engineermind-backend-main/test_engineering_core.py`.

### Execution Results:
```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-7.4.4, pluggy-1.6.0
rootdir: C:\Users\abhin\OneDrive\Documents\anitgravity\games\Simulation-main\engineermind-backend-main
plugins: anyio-4.12.1, asyncio-0.23.8
collected 11 items

test_engineering_core.py::test_units_validation PASSED                   [  9%]
test_engineering_core.py::test_unit_conversions PASSED                   [ 18%]
test_engineering_core.py::test_fluid_properties_isa PASSED               [ 27%]
test_engineering_core.py::test_fluid_properties_catalog PASSED           [ 36%]
test_engineering_core.py::test_aerodynamics PASSED                       [ 45%]
test_engineering_core.py::test_boundary_layer PASSED                     [ 54%]
test_engineering_core.py::test_mesh_calculator PASSED                    [ 63%]
test_engineering_core.py::test_turbulence PASSED                         [ 72%]
test_engineering_core.py::test_numerical_methods PASSED                  [ 81%]
test_engineering_core.py::test_verification_gci PASSED                   [ 90%]
test_engineering_core.py::test_uncertainty PASSED                        [100%]

============================= 11 passed in 0.41s ==============================
```

- **Pass Rate:** 11 of 11 unit tests passed (100%).
- **Regressions:** None. `aerocore.py` tests executed and confirmed identical outputs.
- **Git Commit:** As commanded, zero git commits or pushes were performed.

