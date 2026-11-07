# Engineering Computation Architecture Audit
**EngineerMind AI / AeroForge Systems CAE Platform**  
*Lead Scientific Python & Aerospace CFD Architecture Audit*  
*Date: November 2026 | Target CFD Solver: OpenFOAM v2212 (OpenCFD/ESI) | Target Execution: Docker Containerized Environment*

---

## 1. Executive Summary & Audit Scope

This audit evaluates every mathematical, aerodynamic, geometrical, and numerical calculation currently implemented in the **EngineerMind AI** backend. 

The primary objective is to prepare the platform for restructuring into an independent, deterministic scientific computation engine: `engineering_core/`. 

### Key Findings
1. **Mathematical Accuracy & Empirical Foundations:** The baseline aerodynamic relations (flat-plate boundary layer, skin friction, dynamic pressure, non-dimensional wall distance $y^+$, ASME V&V 20 GCI) are grounded in established aerospace literature (Schlichting, White, Roache, Wilcox). However, several relations rely on hardcoded sea-level ambient conditions ($\rho = 1.225\text{ kg/m}^3, \mu = 1.789 \times 10^{-5}\text{ Pa}\cdot\text{s}$) with no temperature or pressure altitude corrections.
2. **Duplicated Calculation Logic:** Calculation of domain boundaries, first-cell heights, layer counts, and dictionary files is fragmented across three distinct modules: `aerocore.py`, `solver_generator.py`, and `case_builder.py`.
3. **Mathematical Inconsistencies:** 
   - In `solver_generator.py`, `snappyHexMeshDict` sets `finalLayerThickness = first_cell_m * 5.0` while prescribing $N=28$ layers and expansion ratio $r=1.15$. The true geometric progression yields a final layer thickness $(1.15)^{27} \times \Delta s \approx 43.7 \times \Delta s$, causing a 9-fold mismatch between prescribed parameters and mesher execution.
   - In `cfd_visualizer.py`, pressure coefficient ($C_p$) extraction hardcodes $q_\infty = \frac{1}{2}(1.225)(40.0)^2 = 980\text{ Pa}$ instead of using the user-specified case velocity.
4. **Pseudo-AI / Heuristics Requiring Determinization:** The module `ai_copilot.py` currently executes deterministic threshold rules disguised as heuristic reasoning. These must be migrated to deterministic rule checkers within `engineering_core/verification.py` and `engineering_core/boundary_layer.py`.

---

## 2. Complete Inventory of Implemented Mathematical Calculations

---

### Module 1: `aerocore.py`

#### Calculation 1.1: Free-Stream Dynamic Pressure ($q_\infty$)
* **Location:** `aerocore.py:22` in `compute_physics()`
* **Mathematical Equation:**
  $$q_\infty = \frac{1}{2} \rho_\infty U_\infty^2$$
* **Inputs & Units:**
  - $U_\infty$: Free-stream velocity $[\text{m/s}]$ (`velocity: float`)
  - $\rho_\infty$: Fluid density $[\text{kg/m}^3]$ (Hardcoded constant $= 1.225$)
* **Outputs & Units:**
  - $q_\infty$: Dynamic pressure $[\text{Pa}]$ (`q: float`)
* **Assumptions & Limitations:**
  - Assumes standard sea-level air at $15^\circ\text{C}$ (ISA).
  - Density is non-configurable; incompressible formulation.
* **Scientific Reference:** Anderson, J. D. (2010), *Fundamentals of Aerodynamics*, 5th Ed., Section 3.2.
* **Mathematical Correctness:** **Correct** for incompressible standard air.
* **Existing Tests:** Covered indirectly in `test_e2e_openfoam_and_vtk.py`.
* **Missing Tests:** Unit test verifying scaling with arbitrary velocities and configurable fluid densities.

---

#### Calculation 1.2: Reynolds Number ($Re$)
* **Location:** `aerocore.py:20` in `compute_physics()`
* **Mathematical Equation:**
  $$Re = \frac{\rho_\infty U_\infty c}{\mu_\infty} = \frac{U_\infty c}{\nu_\infty}$$
* **Inputs & Units:**
  - $U_\infty$: Free-stream velocity $[\text{m/s}]$ (`velocity: float`)
  - $c$: Characteristic chord length $[\text{m}]$ (`chord_length: float`)
  - $\rho_\infty$: Fluid density $[\text{kg/m}^3]$ (Hardcoded $= 1.225$)
  - $\mu_\infty$: Dynamic viscosity $[\text{Pa}\cdot\text{s}]$ (Hardcoded $= 1.789 \times 10^{-5}$)
* **Outputs & Units:**
  - $Re$: Reynolds number $[-]$ (`re_val: float`)
* **Assumptions & Limitations:**
  - Constant viscosity (Sutherland's law temperature dependence omitted).
  - 1D scalar chord length; non-aligned 3D swept geometries require projected chord.
* **Scientific Reference:** Schlichting, H. (1979), *Boundary-Layer Theory*, McGraw-Hill, Chapter 1.
* **Mathematical Correctness:** **Correct** for reference standard air.
* **Existing Tests:** `test_e2e_openfoam_run.py` tests case creation with $Re$.
* **Missing Tests:** Unit test with known reference aerofoil test points (e.g., NACA 0012 validation cases at $Re = 3 \times 10^6, 6 \times 10^6$).

---

#### Calculation 1.3: Mach Number ($Ma$)
* **Location:** `aerocore.py:21` in `compute_physics()`
* **Mathematical Equation:**
  $$Ma = \frac{U_\infty}{a_\infty} = \frac{U_\infty}{\sqrt{\gamma R T_\infty}}$$
* **Inputs & Units:**
  - $U_\infty$: Free-stream velocity $[\text{m/s}]$ (`velocity: float`)
  - $a_\infty$: Speed of sound $[\text{m/s}]$ (Hardcoded constant $= 340.3$)
* **Outputs & Units:**
  - $Ma$: Mach number $[-]$ (`mach: float`)
* **Assumptions & Limitations:**
  - Assumes dry air with $\gamma = 1.4$, $R = 287.058\text{ J/(kg}\cdot\text{K)}$, $T_\infty = 288.15\text{ K} \implies a = 340.294\text{ m/s}$.
  - Fails if operating altitude or ambient temperature deviates from sea level.
* **Scientific Reference:** Liepmann, H. W., & Roshko, A. (1957), *Elements of Gasdynamics*, Chapter 1.
* **Mathematical Correctness:** **Correct** for sea-level standard conditions.
* **Existing Tests:** Indirectly evaluated in end-to-end tests.
* **Missing Tests:** Parametric unit tests across transonic and supersonic threshold checks ($Ma \ge 0.3$).

---

#### Calculation 1.4: External Turbulent Skin Friction Coefficient ($C_f$)
* **Location:** `aerocore.py:39` in `compute_physics()` (when `regime == "external_aerodynamics"`)
* **Mathematical Equation:**
  $$C_f = 0.0583 \cdot Re^{-0.2} = \frac{0.0583}{Re^{1/5}}$$
* **Inputs & Units:**
  - $Re$: Reynolds number $[-]$
* **Outputs & Units:**
  - $C_f$: Estimated mean flat-plate turbulent skin friction coefficient $[-]$
* **Assumptions & Limitations:**
  - Assumes 1/7th power-law turbulent velocity profile on a smooth flat plate with zero pressure gradient ($dp/dx = 0$).
  - Valid only for $5 \times 10^5 \le Re \le 10^7$.
  - Does not account for laminar run, boundary layer transition point, surface roughness ($k_s$), or adverse pressure gradients causing boundary layer thickening/separation.
* **Scientific Reference:** White, F. M. (2006), *Viscous Fluid Flow*, 3rd Ed., Eq. (6-78); Schlichting (1979).
* **Mathematical Correctness:** **Correct** for 1/7th power-law flat plate correlation.
* **Existing Tests:** None validating numerical value against White/Schlichting benchmark tables.
* **Missing Tests:** Direct unit tests comparing $C_f$ against Prandtl-Schlichting formula $C_f = (2\log_{10}Re - 0.65)^{-2.3}$ and White's correlation.

---

#### Calculation 1.5: Internal Pipe/Nozzle Friction Factor ($C_f$)
* **Location:** `aerocore.py:25` in `compute_physics()` (when `regime == "internal_nozzle"`)
* **Mathematical Equation:**
  $$C_f = 0.079 \cdot Re^{-0.25}$$
* **Inputs & Units:**
  - $Re$: Reynolds number based on diameter/chord $[-]$
* **Outputs & Units:**
  - $C_f$: Fanning friction factor $[-]$
* **Assumptions & Limitations:**
  - Uses the Blasius pipe friction correlation for smooth pipes ($f = 0.3164 Re^{-0.25}$).
  - Since $C_f = \frac{f}{4} = \frac{0.3164}{4} Re^{-0.25} \approx 0.0791 Re^{-0.25}$, this computes the Fanning friction coefficient.
  - Valid only for turbulent pipe flow $4 \times 10^3 < Re < 10^5$.
* **Scientific Reference:** Blasius, H. (1913), *Das Ähnlichkeitsgesetz bei Reibungsvorgängen in Flüssigkeiten*, VDI-Forschungsheft 131.
* **Mathematical Correctness:** **Correct** (Fanning definition).
* **Existing Tests:** None.
* **Missing Tests:** Unit test comparing against Darcy-Weisbach Colebrook equation.

---

#### Calculation 1.6: Wall Shear Stress ($\tau_w$) and Friction Velocity ($u_\tau$)
* **Location:** `aerocore.py:40-41`
* **Mathematical Equations:**
  $$\tau_w = q_\infty \cdot C_f = \frac{1}{2} \rho_\infty U_\infty^2 C_f$$
  $$u_\tau = \sqrt{\frac{\tau_w}{\rho_\infty}} = U_\infty \sqrt{\frac{C_f}{2}}$$
* **Inputs & Units:**
  - $q_\infty$: Dynamic pressure $[\text{Pa}]$
  - $C_f$: Skin friction coefficient $[-]$
  - $\rho_\infty$: Fluid density $[\text{kg/m}^3]$
* **Outputs & Units:**
  - $\tau_w$: Wall shear stress $[\text{Pa}]$
  - $u_\tau$: Friction velocity $[\text{m/s}]$
* **Assumptions & Limitations:**
  - Boundary layer wall equilibrium hypothesis.
* **Scientific Reference:** Wilcox, D. C. (2006), *Turbulence Modeling for CFD*, DCW Industries, Chapter 3.
* **Mathematical Correctness:** **Correct**.
* **Existing Tests:** Tested only as part of `compute_physics` JSON payload.
* **Missing Tests:** Direct unit tests verifying dimensional consistency: $[u_\tau] = \sqrt{\text{Pa}/(\text{kg/m}^3)} = \text{m/s}$.

---

#### Calculation 1.7: First Cell Normal Height ($\Delta s$) for Target $y^+$
* **Location:** `aerocore.py:42`
* **Mathematical Equation:**
  $$\Delta s = \frac{y^+ \mu_\infty}{\rho_\infty u_\tau} = \frac{y^+ \nu_\infty}{u_\tau}$$
* **Inputs & Units:**
  - $y^+$: Non-dimensional wall distance $[-]$ (`target_y_plus: float`)
  - $\mu_\infty$: Dynamic viscosity $[\text{Pa}\cdot\text{s}]$ ($1.789 \times 10^{-5}$)
  - $\rho_\infty$: Fluid density $[\text{kg/m}^3]$ ($1.225$)
  - $u_\tau$: Friction velocity $[\text{m/s}]$
* **Outputs & Units:**
  - $\Delta s$: First cell centroid distance / wall spacing $[\text{m}]$ (`delta_s_m`) and $[\text{mm}]$ (`delta_s_mm`)
* **Assumptions & Limitations:**
  - In OpenFOAM finite-volume cell-centered meshes, $y^+$ is evaluated at the **cell centroid** ($y_P = \Delta s / 2$). Some aerodynamicists define $\Delta s$ as cell height ($2 y_P$) whereas others define it as centroid distance.
  - The implementation uses $\Delta s = \frac{y^+ \nu}{u_\tau}$ directly as the total layer height in `snappyHexMeshDict`. This represents a factor-of-2 conservative design choice (centroid lands at $y^+/2$).
* **Scientific Reference:** Wilcox, D. C. (2006), Section 4.2; NASA Langley Research Center CFD Verification Guidelines.
* **Mathematical Correctness:** **Correct**, with centroid vs. cell height definition noted.
* **Existing Tests:** Covered in end-to-end suite ($y^+ = 1.0 \implies \Delta s \approx 0.0084\text{ mm}$ for $U=40, c=1.0$).
* **Missing Tests:** Boundary checks: $y^+ \to 0$ exception handling, extreme high $Re$ values.

---

#### Calculation 1.8: Turbulent Boundary Layer Thickness ($\delta$)
* **Location:** `aerocore.py:43`
* **Mathematical Equation:**
  $$\delta(c) = \frac{0.37 \cdot c}{Re^{0.2}} = 0.37 \cdot c \cdot Re^{-1/5}$$
* **Inputs & Units:**
  - $c$: Chord length $[\text{m}]$
  - $Re$: Reynolds number $[-]$
* **Outputs & Units:**
  - $\delta$: 99% Boundary layer thickness at trailing edge $[\text{m}]$ (`delta_m`) and $[\text{mm}]$ (`delta_mm`)
* **Assumptions & Limitations:**
  - Turbulent boundary layer starting from $x=0$ (fully turbulent flat plate, zero laminar run).
* **Scientific Reference:** Schlichting (1979), Chapter 21, Eq. (21.11).
* **Mathematical Correctness:** **Correct**.
* **Existing Tests:** None.
* **Missing Tests:** Unit test verifying scaling with $c^{0.8}$ and $U^{-0.2}$.

---

#### Calculation 1.9: Friction Drag Force Estimate ($F_{\text{drag}}$)
* **Location:** `aerocore.py:44`
* **Mathematical Equation:**
  $$F_{\text{drag}} = 2.0 \cdot q_\infty \cdot c \cdot C_f$$
* **Inputs & Units:**
  - $q_\infty$: Dynamic pressure $[\text{Pa}]$
  - $c$: Chord $[\text{m}]$
  - $C_f$: Skin friction coefficient $[-]$
* **Outputs & Units:**
  - $F_{\text{drag}}$: Friction drag per unit span $[\text{N/m}]$
* **Assumptions & Limitations:**
  - Assumes two-sided 2D aerofoil of unit span ($b = 1.0\text{ m}$), total wetted area $S_{\text{wet}} \approx 2 \cdot b \cdot c$.
  - Ignores form factor / pressure drag ($C_{dp}$), wave drag ($C_{dw}$), and induced drag ($C_{di}$).
* **Scientific Reference:** Hoerner, S. F. (1965), *Fluid-Dynamic Drag*, Chapter 6.
* **Mathematical Correctness:** **Correct** for two-sided flat plate skin-friction estimate.
* **Existing Tests:** Evaluated inside `hand_calculation` payload.
* **Missing Tests:** Verification against integrated shear stress $\int_0^c 2 \tau_w(x) dx$.

---

#### Calculation 1.10: Theoretical Thin Aerofoil Lift Curve Slope & Lift at $4^\circ$
* **Location:** `aerocore.py:45-46`
* **Mathematical Equations:**
  $$\frac{dC_L}{d\alpha} = 0.11\text{ deg}^{-1} \quad \left(\approx 2\pi\text{ rad}^{-1} \times \frac{\pi}{180} = 0.10966\text{ deg}^{-1}\right)$$
  $$C_L(\alpha = 4^\circ) = \left(\frac{dC_L}{d\alpha}\right) \cdot \alpha = 0.11 \times 4.0 = 0.44$$
* **Inputs & Units:**
  - $\alpha = 4.0^\circ$ [degrees]
* **Outputs & Units:**
  - Lift curve slope $[\text{deg}^{-1}]$ and Lift coefficient at $4^\circ$ $[-]$
* **Assumptions & Limitations:**
  - Classical 2D thin aerofoil theory ($dC_l/d\alpha = 2\pi$ per radian).
  - Assumes symmetric aerofoil with zero camber ($C_{L0} = 0$).
  - Linear range assumption; fails near stall ($\alpha > 12^\circ$).
* **Scientific Reference:** Abbott, I. H., & Von Doenhoff, A. E. (1959), *Theory of Wing Sections*, Dover.
* **Mathematical Correctness:** **Correct** for ideal 2D thin aerofoil linear regime.
* **Existing Tests:** Validated in `hand_calculation` payload.
* **Missing Tests:** Camber correction: $C_L = 2\pi(\alpha - \alpha_{L0})$.

---

#### Calculation 1.11: ASME V&V 20 Roache Grid Convergence Index (GCI)
* **Location:** `aerocore.py:99-148` in `calculate_roache_gci()`
* **Mathematical Equations:**
  1. Refinement ratio: $r = 1.414$ (default)
  2. Relative error: $\epsilon_{21} = \left|\frac{f_2 - f_1}{f_1}\right|$ where $f_1 = \text{fine}, f_2 = \text{medium}, f_3 = \text{coarse}$
  3. Apparent order of accuracy:
     $$p = \frac{\left|\ln\left|\frac{f_3 - f_2}{f_2 - f_1}\right|\right|}{\ln(r)}$$
  4. Fine Grid Convergence Index:
     $$GCI_{\text{fine}} = \frac{F_s \cdot \epsilon_{21}}{r^p - 1} \times 100\%$$
     with ASME safety factor $F_s = 1.25$ for 3-grid studies.
* **Inputs & Units:**
  - $f_{\text{coarse}}, f_{\text{medium}}, f_{\text{fine}}$: Scalar target metrics (e.g. $C_d, C_l$) $[-]$
  - $r$: Grid refinement ratio $[-]$ (default $\sqrt{2} \approx 1.414$)
* **Outputs & Units:**
  - $p$: Apparent order $[-]$
  - $\epsilon_{21}$: Relative error $[\%]$
  - $GCI_{\text{fine}}$: Fine grid uncertainty $[\%]$
  - Verdict: `PASS` if $GCI < 3.0\%$ else `MESH_REFINEMENT_REQUIRED`
* **Assumptions & Limitations:**
  - Assumes constant refinement ratio between grid pairs ($r_{21} = r_{32} = r$). Non-uniform refinement ratios require transcendental equation solving:
    $$p = \frac{1}{\ln(r_{21})} |\ln|(r_{21}^p - 1) / (r_{32}^p - 1)| + q|$$
  - Assumes monotonic convergence ($f_1 < f_2 < f_3$ or $f_1 > f_2 > f_3$). Oscillatory convergence ($ (f_2 - f_1)/(f_3 - f_2) < 0 $) causes mathematical singularity in $\ln(\text{ratio})$ which is currently caught by a generic try-except setting $p=2.0$.
  - Singularity handling: If $(r^p - 1) < 10^{-6}$, hardcodes `denom = 0.001`.
* **Scientific Reference:** 
  - ASME V&V 20-2009, *Standard for Verification and Validation in Computational Fluid Dynamics and Heat Transfer*.
  - Roache, P. J. (1998), *Verification and Validation in Computational Science and Engineering*, Hermosa Publishers.
* **Mathematical Correctness:** **Correct** for uniform $r$ monotonic triplet; needs formal handling for non-monotonic/oscillatory divergence.
* **Existing Tests:** Covered in `main.py` endpoint tests.
* **Missing Tests:** Unit test on standard ASME V&V 20 benchmark dataset with known exact $p$ and $GCI$.

---

### Module 2: `cad_engine.py`

#### Calculation 2.1: Bounding Box, Chord ($c$), and Span ($b$)
* **Location:** `cad_engine.py:97-102` in `inspect_geometry()`
* **Mathematical Equations:**
  $$c = \max(10^{-4}, X_{\max} - X_{\min})$$
  $$b = \max(10^{-4}, Z_{\max} - Z_{\min})$$
* **Inputs & Units:**
  - Triangulated vertices array $V \in \mathbb{R}^{N \times 3}$ $[\text{m}]$
* **Outputs & Units:**
  - $c$: Characteristic chord length $[\text{m}]$
  - $b$: Span length $[\text{m}]$
  - Extents: $[X_{\min}, X_{\max}], [Y_{\min}, Y_{\max}], [Z_{\min}, Z_{\max}]$ $[\text{m}]$
* **Assumptions & Limitations:**
  - **CRITICAL ORIENTATION ASSUMPTION:** Assumes the aerofoil chord lies along the Cartesian $X$-axis and the spanwise dimension lies along the $Z$-axis. If a CAD model is exported along $Y$ or pitched at an angle, $X_{\max} - X_{\min}$ is the projected bounding box rather than true aerodynamic chord!
* **Scientific Reference:** Standard computational geometry bounding algorithms.
* **Mathematical Correctness:** **Correct** only when geometry axes align with global frame.
* **Existing Tests:** Verified with synthetic NACA box in `test_cad_engine` check.
* **Missing Tests:** Unit tests for misaligned/rotated CAD models (e.g., rotated by $45^\circ$, where Principal Component Analysis (PCA) or Minimum Bounding Box is required).

---

#### Calculation 2.2: Trailing Edge Thickness ($t_{TE}$) Check
* **Location:** `cad_engine.py:108-125`
* **Mathematical Equations:**
  $$V_{TE} = \{ v \in V \mid v_x \ge X_{\min} + 0.98 c \}$$
  $$t_{TE} = \max_{v \in V_{TE}}(v_y) - \min_{v \in V_{TE}}(v_y)$$
  $$\text{Defeaturing Trigger: } t_{TE} < 0.001 \cdot c \implies \text{BLUNT\_EDGE\_REQUIRED}$$
* **Inputs & Units:**
  - Vertex coordinates $[\text{m}]$, Chord length $c$ $[\text{m}]$
* **Outputs & Units:**
  - $t_{TE}$: Trailing edge thickness $[\text{mm}]$
  - Flag: `PASS` or `BLUNT WARNING`
* **Assumptions & Limitations:**
  - Assumes trailing edge is situated at $X_{\max}$ and thickness is oriented along the Cartesian $Y$-axis.
  - Slicing at $x \ge 0.98c$ can catch wingtips or control horns if the wing has taper or sweep.
* **Scientific Reference:** OpenFOAM Meshing Best Practice Guidelines: Trailing edge cell pinching and non-orthogonality near singular wedge points.
* **Mathematical Correctness:** **Correct** for unswept profile aligned on $X-Y$ plane.
* **Existing Tests:** None with real blunt/sharp aerofoil STLs.
* **Missing Tests:** Test comparing NACA 0012 sharp trailing edge vs. NACA 0012 blunt trailing edge ($t_{TE} = 0.002c$).

---

#### Calculation 2.3: Farfield Computational Domain Bounds
* **Location:** `cad_engine.py:126-130`
* **Mathematical Equations:**
  $$X_{\text{inlet}} = 15.0 \cdot c, \quad X_{\text{outlet}} = 25.0 \cdot c, \quad Y_{\text{lateral}} = 15.0 \cdot c$$
* **Inputs & Units:**
  - $c$: Chord length $[\text{m}]$
* **Outputs & Units:**
  - Inlet distance $[\text{m}]$, Outlet distance $[\text{m}]$, Lateral cushion $[\text{m}]$
* **Assumptions & Limitations:**
  - Unbounded external flow field.
  - Blockage ratio $B < 1.0\%$ for aerofoils with $t/c \le 0.15$.
* **Scientific Reference:** Franke et al. (2007), *Best Practice Guideline for the CFD Simulation of Flows in the Urban Environment*, COST Action 732.
* **Mathematical Correctness:** **Correct** for external aerodynamic standard domains.
* **Existing Tests:** Checked in case creation endpoints.
* **Missing Tests:** Unit test verifying domain bounds update dynamically when chord changes.

---

### Module 3: `solver_generator.py` & `case_builder.py`

#### Calculation 3.1: Farfield Block Mesh Vertices & Cells
* **Location:** `solver_generator.py:15-26` in `generate_block_mesh_dict()`
* **Mathematical Equations:**
  $$X \in [-15c, +25c], \quad Y \in [-15c, +15c], \quad Z \in [-5c, +5c]$$
  $$N_{\text{cells}} = N_x \times N_y \times N_z = 60 \times 40 \times 20 = 48,000 \text{ background hex cells}$$
* **Inputs & Units:**
  - $c$: Chord length $[\text{m}]$
* **Outputs & Units:**
  - OpenFOAM `blockMeshDict` ASCII format.
* **Assumptions & Limitations:**
  - Uniform Cartesian background grid ($\text{simpleGrading (1 1 1)}$). Background cell sizes:
    $$\Delta x_{\text{bg}} = \frac{40c}{60} = 0.667c, \quad \Delta y_{\text{bg}} = \frac{30c}{40} = 0.75c, \quad \Delta z_{\text{bg}} = \frac{10c}{20} = 0.5c$$
  - Sizing is coarse and relies entirely on `snappyHexMesh` castellation levels to refine near the body.
* **Scientific Reference:** OpenFOAM User Guide v2212: `blockMesh` utility.
* **Mathematical Correctness:** **Correct**.
* **Existing Tests:** Verified in `test_e2e_openfoam_run.py`.

---

#### Calculation 3.2: Prism Layer Inflation Parameters
* **Location:** `solver_generator.py:202-225` in `generate_snappy_hex_mesh_dict()`
* **Mathematical Equations & Parameters:**
  - `relativeSizes false;`
  - `nSurfaceLayers = layers;` ($28$ for $y^+ \le 1.0$, $12$ for $y^+ > 1.0$)
  - `expansionRatio = 1.15;`
  - `finalLayerThickness = first_cell_m * 5.0;`
  - `minThickness = first_cell_m * 0.5;`
* **Mathematical Inconsistency / Conflict:**
  - In a geometric progression with first layer thickness $h_1 = \Delta s$, expansion ratio $r = 1.15$, and $N = 28$ layers:
    $$h_N = h_1 \cdot r^{N-1} = \Delta s \cdot (1.15)^{27} \approx 43.74 \cdot \Delta s$$
  - Total stack height:
    $$H_{\text{stack}} = \sum_{i=0}^{N-1} h_1 r^i = h_1 \frac{r^N - 1}{r - 1} = \Delta s \frac{1.15^{28} - 1}{0.15} \approx 324.9 \cdot \Delta s$$
  - The code prescribes: `finalLayerThickness = first_cell_m * 5.0`.
  - Setting $h_N = 5 h_1$ with $r = 1.15$ forces `snappyHexMesh` layer addition to either reduce the layer count or compress the expansion ratio ($r_{\text{eff}} = 5^{1/27} \approx 1.061$).
* **Scientific Reference:** OpenFOAM v2212 Source Guide: `addLayersControls`.
* **Mathematical Correctness:** **INCONSISTENT.** `finalLayerThickness` should either be omitted (allowing OpenFOAM to derive it from $r$ and $N$) or calculated rigorously as $h_1 \cdot r^{N-1}$.
* **Existing Tests:** None verifying geometric layer progression.
* **Missing Tests:** Unit test verifying total layer stack height satisfies:
  $$\delta_{\text{stack}} \approx 0.3 \delta \text{ to } 0.8 \delta$$

---

#### Calculation 3.3: Force Coefficients Reference Area ($A_{\text{ref}}$) and Center of Rotation ($C_{\text{ofR}}$)
* **Location:** `solver_generator.py:257, 307-308` in `generate_control_dict()`
* **Mathematical Equations:**
  $$A_{\text{ref}} = c \cdot b = c \cdot (2.0 c) = 2 c^2$$
  $$C_{\text{ofR}} = (0.25 c, 0, 0)$$
* **Inputs & Units:**
  - $c$: Chord length $[\text{m}]$
  - $b$: Span length $[\text{m}]$ (default $= 2.0 c$)
* **Outputs & Units:**
  - $A_{\text{ref}}$: Reference area $[\text{m}^2]$
  - $C_{\text{ofR}}$: Quarter-chord aerodynamic pitch center $[\text{m}]$
* **Assumptions & Limitations:**
  - Assumes rectangular planform ($A = c \times b$).
  - For tapered or delta wings, $A_{\text{ref}}$ must be computed from projected surface area, and $C_{\text{ofR}}$ must be located at the Mean Aerodynamic Chord (MAC) quarter-chord point ($x_{\text{ac}} = x_{\text{LE,MAC}} + 0.25 c_{\text{MAC}}$).
* **Scientific Reference:** Anderson (2010), Chapter 1.
* **Mathematical Correctness:** **Correct** for rectangular wing profiles.
* **Existing Tests:** Verified in `test_e2e_openfoam_run.py`.

---

### Module 4: `main.py` (Diagnostics & Log Parsing)

#### Calculation 4.1: Drag Coefficient Rolling Statistics ($\bar{C}_d$ and $\sigma(C_d)$)
* **Location:** `main.py:570-573` in `parse_simulation_log()`
* **Mathematical Equations:**
  $$\bar{C}_d = \frac{1}{N} \sum_{i=1}^N C_{d,i}$$
  $$\sigma(C_d) = \sqrt{\frac{1}{N} \sum_{i=1}^N (C_{d,i} - \bar{C}_d)^2}$$
  where $N = \min(50, \text{number of logged iterations})$.
* **Inputs & Units:**
  - $C_d$ sequence from OpenFOAM solver log $[-]$
* **Outputs & Units:**
  - $\sigma(C_d)$: Population standard deviation of drag coefficient $[-]$
* **Assumptions & Limitations:**
  - Population variance ($1/N$) is used instead of unbiased sample variance ($1/(N-1)$). For $N=50$, difference is negligible ($< 2\%$), but for small samples ($N < 10$) it underpredicts variance.
  - Convergence verdict requires $\text{Continuity} \le 10^{-4}$ AND $\sigma(C_d) < 10^{-4}$.
  - In production aerospace CFD, continuity residuals must typically drop below $10^{-5}$ or $10^{-6}$ for RANS convergence.
* **Scientific Reference:** Ferziger, J. H., & Peric, M. (2002), *Computational Methods for Fluid Dynamics*, Springer.
* **Mathematical Correctness:** **Correct** (population standard deviation formulation).
* **Existing Tests:** Tested in `test_e2e_openfoam_run.py` and `test_e2e_openfoam_and_vtk.py`.
* **Missing Tests:** Verification against NumPy `np.std(ddof=1)`.

---

### Module 5: `cfd_visualizer.py`

#### Calculation 5.1: 3D Velocity Magnitude ($|U|$)
* **Location:** `cfd_visualizer.py:117` in `parse_vtk_polydata()`
* **Mathematical Equation:**
  $$|U| = \sqrt{U_x^2 + U_y^2 + U_z^2}$$
* **Inputs & Units:**
  - Velocity components $U_x, U_y, U_z$ $[\text{m/s}]$
* **Outputs & Units:**
  - Magnitude $|U|$ $[\text{m/s}]$
* **Scientific Reference:** Euclidean vector norm.
* **Mathematical Correctness:** **Correct**.
* **Existing Tests:** Tested in `test_e2e_openfoam_and_vtk.py`.

---

#### Calculation 5.2: Pressure Coefficient Field ($C_p$)
* **Location:** `cfd_visualizer.py:140-145`
* **Mathematical Equation:**
  $$C_p = \frac{p - p_\infty}{q_\infty} = \frac{p - p_\infty}{\frac{1}{2} \rho_\infty U_\infty^2}$$
* **Inputs & Units:**
  - Kinematic pressure $p / \rho$ $[\text{m}^2/\text{s}^2]$ or static pressure $p$ $[\text{Pa}]$
* **Critical Bug / Flaw in Existing Implementation:**
  ```python
  p_inf = 0.0
  q_inf = 0.5 * 1.225 * (40.0 ** 2) # ~980 Pa
  cp_field = [round((p_val - p_inf) / q_inf, 4) for p_val in p_field]
  ```
  - **HARDCODED VELOCITY:** $q_\infty$ is hardcoded with $U_\infty = 40.0\text{ m/s}$ regardless of the actual simulation case velocity! If the user ran a case at $U_\infty = 80\text{ m/s}$, $C_p$ is calculated with a 4-fold error in dynamic pressure!
  - **PRESSURE DIMENSIONALITY:** In incompressible OpenFOAM (`simpleFoam`), the solved field `p` is kinematic pressure:
    $$p_{\text{OF}} = \frac{p_{\text{static}}}{\rho} \quad [\text{m}^2/\text{s}^2]$$
    Therefore, the true pressure coefficient must be:
    $$C_p = \frac{p_{\text{OF}} - p_{\text{OF},\infty}}{\frac{1}{2} U_\infty^2}$$
    Dividing by $q_\infty = \frac{1}{2}\rho U_\infty^2$ introduces a dimensional error of $1/\rho$ if $p$ is kinematic.
* **Scientific Reference:** Anderson (2010), Chapter 3; OpenFOAM `simpleFoam` field definitions.
* **Mathematical Correctness:** **INCORRECT.** Hardcoded velocity and unit mismatch between kinematic pressure and dynamic pressure.
* **Existing Tests:** VTK parse test checks `cp_stats["max"] > 0.5`, passing only because sample data is generated with $U=40$.
* **Missing Tests:** Unit test verifying $C_p$ with dynamic $U_\infty \ne 40$ and correct kinematic pressure scaling.

---

#### Calculation 5.3: Synthetic NACA 0012 Surface Coordinate & Aerodynamic Distribution
* **Location:** `cfd_visualizer.py:182-208` in `generate_sample_naca0012_vtk()`
* **Mathematical Equations:**
  1. Cosine discretization:
     $$\theta_i = \frac{i}{N-1} \pi, \quad x_i = \frac{c}{2} (1 - \cos\theta_i)$$
  2. NACA 4-digit thickness equation:
     $$y_t(x) = 0.12 c \left( 0.2969\sqrt{\frac{x}{c}} - 0.1260\left(\frac{x}{c}\right) - 0.3516\left(\frac{x}{c}\right)^2 + 0.2843\left(\frac{x}{c}\right)^3 - 0.1015\left(\frac{x}{c}\right)^4 \right)$$
  3. Synthetic surface pressure distribution:
     - For $x/c < 0.05$ (Stagnation zone):
       $$C_p = 1.0 - \left(\frac{x/c}{0.05}\right) \cdot 1.8$$
       $$U = U_\infty \left(\frac{x/c}{0.05}\right) \cdot 1.15$$
     - For $x/c \ge 0.05$ (Suction & recovery zone):
       $$C_p = -0.8 + (x/c - 0.05) \cdot 0.8$$
       $$U = U_\infty [1.25 - (x/c) \cdot 0.35]$$
* **Assumptions & Limitations:**
  - Analytical formula used only for testing and demonstration VTK generation.
* **Scientific Reference:** NACA Report No. 460 (Jacobs, Ward, & Pinkerton, 1933).
* **Mathematical Correctness:** **Correct** for NACA 0012 profile; piecewise linear $C_p$ is a synthetic approximation for testing.
* **Existing Tests:** Covered in `test_e2e_openfoam_and_vtk.py`.

---

## 3. Heuristic / Pseudo-AI Logic Requiring Determinization

### Current `ai_copilot.py`
The file `ai_copilot.py` currently contains:
```python
def evaluate_copilot_case(case_data: dict, physics_data: dict) -> dict:
    y_plus = case_data.get("target_y_plus", 1.0)
    re = physics_data.get("reynolds_number", 0.0)
    mach = physics_data.get("mach_number", 0.0)
    ...
    if 5.0 < y_plus < 30.0:
        findings.append("CRITICAL: Buffer Layer Violation (5 < y+ < 30)...")
    elif y_plus <= 1.0:
        findings.append("Optimal Wall-Resolved Sublayer Resolution...")
    ...
    if mach >= 0.3:
        findings.append("Compressibility Flag: Mach >= 0.300...")
```

### Analysis & Required Migration
- **Nature of Logic:** These are **strictly deterministic boundary checks**, not probabilistic or machine-learned inferences.
- **Problems:** 
  1. Branded as "AI", creating false expectations of stochastic LLM reasoning.
  2. Isolated from the primary `aerocore.py` calculation pipeline, requiring multiple API round-trips.
  3. Hardcoded thresholds without severity rankings or continuous penalty metrics.
- **Target Package:** Must be moved into `engineering_core/verification.py` as pure deterministic rule verification functions:
  - `verify_wall_resolution(target_y_plus: float) -> ValidationResult`
  - `verify_mach_regime(mach_number: float) -> ValidationResult`
  - `verify_mesh_orthogonality(max_non_ortho: float) -> ValidationResult`

---

## 4. Identified Inconsistencies & Duplicated Calculation Logic

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DUPLICATION & INCONSISTENCY MAP                       │
├──────────────────────────────┬──────────────────────────────┬───────────────┤
│ Concept / Calculation        │ Implementations              │ Inconsistency │
├──────────────────────────────┼──────────────────────────────┼───────────────┤
│ Farfield Domain Cushion      │ - aerocore.py (15c, 25c, 15c)│ aerocore.py   │
│                              │ - cad_engine.py (15c,25c,15c)│ sets lateral  │
│                              │ - solver_generator.py (Z=5c) │ = 15c; solver │
│                              │                              │ sets Z = 5c   │
├──────────────────────────────┼──────────────────────────────┼───────────────┤
│ Air Viscosity                │ - aerocore.py: 1.789e-5 Pa·s │ Case builder  │
│                              │ - case_builder.py: 1.46e-5   │ nu is 1.46e-5 │
│                              │ - openfoam_pipeline.py:1.46e5│ while aerocore│
│                              │                              │ uses 1.4604e-5│
├──────────────────────────────┼──────────────────────────────┼───────────────┤
│ Dynamic Pressure in VTK      │ - aerocore.py (q = 0.5*ρ*U²) │ cfd_visualizer│
│                              │ - cfd_visualizer.py (U=40)   │ hardcodes     │
│                              │                              │ U=40 m/s      │
├──────────────────────────────┼──────────────────────────────┼───────────────┤
│ Snappy Layer Growth          │ - solver_generator.py        │ h_N = 5*h_1   │
│                              │ - case_builder.py            │ conflicts     │
│                              │                              │ with r=1.15   │
├──────────────────────────────┼──────────────────────────────┼───────────────┤
│ OpenFOAM Case Dictionaries   │ - solver_generator.py        │ Maintained in │
│                              │ - case_builder.py            │ 3 separate    │
│                              │ - openfoam_pipeline.py       │ source files  │
└──────────────────────────────┴──────────────────────────────┴───────────────┘
```

---

## 5. Architectural Blueprint for `engineering_core/`

The proposed `engineering_core/` package establishes a strictly deterministic, fully typed, zero-dependency (relying only on NumPy/SciPy/standard library) scientific foundation:

```
engineering_core/
│
├── __init__.py                 # Clean package public exports
├── units.py                    # Dimensional quantities, SI conversions, scale factors (mm -> m)
├── fluid_properties.py         # Standard atmospheres (ISA 1976), Sutherland's law, ideal gas law
├── aerodynamics.py             # Re, Ma, q, dynamic viscosity, lift curve slope, drag estimation
├── boundary_layer.py           # Cf correlations, tau_w, u_tau, delta_s, delta_99, prism stack growth
├── mesh_calculator.py          # Farfield domain cushions, snappyHexMesh layer geometric progression
├── turbulence.py               # k-omega SST inlet boundary conditions (k, omega, nut estimations)
├── numerical_methods.py        # Vector operations, VTK polydata scalar extractions, rolling force stats
├── verification.py             # ASME V&V 20 Roache GCI, mesh quality checks, buffer layer validators
└── uncertainty.py              # Grid convergence error bands, spatial discretization uncertainty
```

### Module Responsibilities & Planned Interface Specifications

#### 1. `units.py`
- Enforces strict SI base units ($[\text{m}], [\text{s}], [\text{kg}], [\text{Pa}], [\text{K}]$).
- Conversions: `to_meters(val, unit)`, `to_pascals(val, unit)`.
- Handles CAD coordinate scaling (e.g. auto-detecting millimeters from bounding boxes $> 50$ and applying $10^{-3}$ factor).

#### 2. `fluid_properties.py`
- Implements 1976 US Standard Atmosphere (`isa_atmosphere(altitude_m: float)`):
  $$T(z) = T_0 - L \cdot z, \quad p(z) = p_0 \left(1 - \frac{L z}{T_0}\right)^{\frac{g}{R L}}, \quad \rho = \frac{p}{R T}$$
- Implements Sutherland's Law for dynamic viscosity:
  $$\mu(T) = \mu_0 \left(\frac{T}{T_0}\right)^{3/2} \frac{T_0 + S}{T + S}$$
  with $T_0 = 273.15\text{ K}$, $\mu_0 = 1.716 \times 10^{-5}\text{ Pa}\cdot\text{s}$, $S = 110.4\text{ K}$.

#### 3. `aerodynamics.py`
- Free-stream Reynolds number, Mach number, dynamic pressure with variable $\rho, T, \mu$.
- Incompressible vs. compressible regime threshold classifier ($Ma \ge 0.3$).

#### 4. `boundary_layer.py`
- Flat-plate skin friction formulas:
  - White-Christoph correlation.
  - Prandtl-Schlichting: $C_f = (2 \log_{10} Re - 0.65)^{-2.3}$.
- Wall friction velocity: $u_\tau = U_\infty \sqrt{C_f / 2}$.
- First cell height for cell centroid ($y_P$) or total cell height ($\Delta s$):
  $$\Delta s = \frac{y^+ \nu}{u_\tau}$$
- Boundary layer thickness $\delta_{99}(x)$.
- Full geometric inflation layer calculator:
  $$h_i = \Delta s \cdot r^{i-1}, \quad H_{\text{total}} = \Delta s \frac{r^N - 1}{r - 1}, \quad h_{\text{final}} = \Delta s \cdot r^{N-1}$$

#### 5. `mesh_calculator.py`
- Farfield bounding domain calculator:
  - Inlet: $15c$, Outlet: $25c$, Top/Bottom: $15c$, Span: $b + 2c$ or $10c$.
  - Generates exact block vertices and non-empty symmetry boundary patches.
- SnappyHexMesh layer configuration with consistent expansion ratio and final layer thickness.

#### 6. `turbulence.py`
- OpenFOAM $k$-$\omega$ SST initial and inlet field generator:
  - Turbulent intensity: $I = 0.01$ (low/external aero) to $0.05$ (medium).
  - Turbulent kinetic energy: $k = \frac{3}{2} (U_\infty I)^2$.
  - Turbulent length scale: $l = 0.07 c$.
  - Specific dissipation rate: $\omega = \frac{C_\mu^{-1/4} \sqrt{k}}{l} \approx \frac{\sqrt{k}}{C_\mu^{1/4} l}$ with $C_\mu = 0.09$.
  - Turbulent kinematic viscosity: $\nu_t = \frac{k}{\omega}$.

#### 7. `numerical_methods.py`
- Correct pressure coefficient: $C_p = \frac{p_{\text{kinematic}}}{\frac{1}{2} U_\infty^2}$.
- Rolling population and sample standard deviation with customizable window.

#### 8. `verification.py`
- Generalized Roache GCI supporting variable refinement ratios ($r_{21} \ne r_{32}$) and non-monotonic/oscillatory detection.
- Deterministic checks for:
  - Buffer layer invalidity ($5 < y^+ < 30$).
  - Compressibility invalidity ($Ma \ge 0.3$ on `simpleFoam`).
  - Trailing edge pinching ($t_{TE} < 0.001c$).

---

## 6. Recommended Migration Sequence

To ensure zero downtime, preserve all existing API routes, and maintain continuous test passing, the following phased migration sequence is recommended:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      PHASED MIGRATION ROADMAP                          │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE 1: Build & Unit-Test `engineering_core/`                         │
│  - Create `engineering_core/` package without touching existing files. │
│  - Implement units, fluid properties, aerodynamics, boundary layer,    │
│    turbulence, and verification modules.                               │
│  - Write 100% comprehensive unit tests with scientific reference data. │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE 2: Re-Route `aerocore.py`                                        │
│  - Refactor `aerocore.py` to act as a thin wrapper delegating to       │
│    `engineering_core`.                                                 │
│  - Verify existing API endpoints (`/calculate-physics`) pass without   │
│    breaking frontend JSON schema contracts.                            │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE 3: Unify Case & Mesh Generation                                  │
│  - Replace duplicated dictionary generators in `solver_generator.py`   │
│    and `case_builder.py` with `mesh_calculator.py` & `turbulence.py`.  │
│  - Correct snappyHexMesh layer thickness progression formula.          │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE 4: Fix VTK Cp Calculation & Determinize Copilot                  │
│  - Fix dynamic $U_\infty$ and kinematic pressure scaling in            │
│    `cfd_visualizer.py`.                                                │
│  - Migrate `ai_copilot.py` to call `verification.py`.                  │
├────────────────────────────────────────────────────────────────────────┤
│ PHASE 5: Containerized OpenFOAM v2212 Execution Bridge                 │
│  - Connect `openfoam_pipeline.py` to a Docker OpenFOAM container       │
│    (`opencfd/openfoam-default:2212`) for real headless solves.         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Sign-Off & Verification Checklist

- [x] All 7 target modules and test suites audited line-by-line.
- [x] Mathematical equations, units, inputs, and outputs documented for each calculation.
- [x] Scientific literature references cited (Schlichting, White, Roache, ASME V&V 20, Wilcox, Anderson).
- [x] Unverified assumptions and mathematical inconsistencies identified.
- [x] Pseudo-AI heuristic logic pinpointed for deterministic refactoring.
- [x] Clean blueprint for `engineering_core/` established.
- [x] Strict rule respected: zero existing source code modified; audit document generated in isolation.

**Status: AUDIT COMPLETE. WAITING FOR APPROVAL TO PROCEED TO PHASE 1 IMPLEMENTATION.**

