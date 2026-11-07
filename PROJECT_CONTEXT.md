# EngineerMind AI / AeroForge Systems — Comprehensive Project Architecture & Context Audit

> **Document Type:** Principal Software Architecture & Engineering Audit  
> **Repository:** `Simulation-main` / `engineermind-frontend-main` / `engineermind-backend-main`  
> **Last Updated:** November 2026  
> **Status:** Production-Ready Pre-Flight CAE Simulation Workstation / Real OpenCASCADE B-Rep Tessellation Engine / OpenFOAM Solver Pipeline & Synthetic Fallback Runner  

---

## 1. Product Vision & Target Audience

### 1.1 Core Vision
**EngineerMind AI** (presented in the unified corporate UI as **AeroForge Systems / EngineerMind CAE**) is a high-precision, web-native pre-flight aerodynamic workbench and computational fluid dynamics (CFD) orchestrator designed specifically for **OpenFOAM**.

In classical aerospace and defense workflows, pre-processing an OpenFOAM case is manual, error-prone, and disconnected:
- Engineers spend hours calculating first-cell normal wall heights ($\Delta s$) to satisfy non-dimensional wall distance ($y^+$) criteria for turbulence models.
- Practitioners frequently construct meshes with first-cell placements in the logarithmic buffer layer ($5 < y^+ < 30$), which invalidates standard two-equation RANS formulations ($k$-$\omega$ SST, $k$-$\epsilon$).
- Dictionaries (`blockMeshDict`, `snappyHexMeshDict`, `fvSchemes`, `fvSolution`) are edited by hand with rigid syntax that fails silently or diverges during runtime.
- Verification & Validation (V&V) standards (specifically **ASME V&V 20-2009** Grid Convergence Index / Roache GCI) are rarely computed systematically across coarse, medium, and fine grids.
- 3D CAD models (STEP, IGES, STL) require heavy, expensive commercial desktop packages (CATIA, ANSYS SpaceClaim, Siemens NX) just to inspect chord length, span, trailing edge thickness, and watertightness.

### 1.2 Target Audience
- **Aerospace & Defense Aerodynamicists:** Engineers running external flow over aerofoils, UAVs, missile airframes, and control surfaces.
- **CAE Simulation Leads:** Teams requiring standardized, auditable OpenFOAM case directories with automated mesh grading, boundary condition checks, and convergence tracking.
- **R&D Test Engineers:** Users who need rapid, browser-native geometry inspection and simulation configuration without installing gigabytes of legacy desktop CAD software.

### 1.3 Key Value Proposition
1. **Zero-Guesswork Boundary Layer Sizing:** Automatically computes skin friction coefficient $C_f$, wall shear stress $\tau_w$, friction velocity $u_\tau$, first cell height $\Delta s$, and prism layer stack height ($\delta$) from flight conditions ($U_\infty, \rho, \mu, c, y^+$).
2. **Industrial CAD Ingestion (STEP / IGES / STL / OBJ):** Native server-side B-Rep tessellation via the OpenCASCADE geometry kernel (through Gmsh), extracting exact dimensions, surface area, volume, and trailing-edge thickness.
3. **ANSYS & Blender-Grade 3D Viewport:** High-fidelity Three.js WebGL viewport featuring procedural 3D NACA 0012 aerofoil profiles, ANSYS feature edge extraction (`THREE.EdgesGeometry`), 4 CAD materials (Titanium Slate, Aerospace Cyan, Studio Ceramic, Carbon Stealth), interactive 3D navigation gizmo triad, and camera-tracking headlights.
4. **Deterministic Pre-Flight Diagnostics:** Flags compressibility limits ($Ma \ge 0.3$), buffer layer invalidity ($5 < y^+ < 30$), and trailing-edge singularities ($t_{TE} < 0.001c$) *before* launching the solver.
5. **Automated OpenFOAM Case Generation:** Generates syntax-compliant OpenFOAM directories (`0/`, `constant/`, `system/`) ready for native execution or downloadable `.zip` archives.

---

## 2. System Architecture & Communication Topology

### 2.1 Technology Stack
- **Frontend Layer:**
  - Modern HTML5, Vanilla JavaScript (ES2022+), CSS3 with custom design tokens.
  - **3D Graphics & Visualization:** Three.js (`r128`), `STLLoader.js`, `OrbitControls.js`.
  - **Icons & Typography:** Lucide Icons (CDN), custom local Arimo web font family (`fonts/Arimo-*.ttf`), JetBrains Mono for telemetry readouts.
  - **Single Page Architecture (SPA):** Seamless view switching between AeroForge Company Overview and EngineerMind Simulation Lab without destroying the WebGL context.
- **Backend API Layer:**
  - **Framework:** FastAPI (Python 3.10+) running on Uvicorn (`http://127.0.0.1:8000`).
  - **Database & ORM:** SQLite (`engineermind.db`) via SQLAlchemy ORM.
  - **CAD & Geometry Kernel:** `gmsh` (OpenCASCADE 7.x B-Rep engine), `trimesh`, `numpy`, `scipy`.
  - **Aerodynamics & Numerics:** Custom pure-Python numerical engines (`aerocore.py`, `cad_engine.py`, `case_builder.py`).
- **CFD & Post-Processing:**
  - OpenFOAM (v2012 / v2206 / v2312 or OpenFOAM 9/10/11) subprocess invocation.
  - Custom ASCII VTK PolyData parser (`cfd_visualizer.py`) for surface scalar mapping ($C_p, p, |U|$).

### 2.2 Directory & Repository Structure

```
Simulation-main/
│
├── index.html                           # Unified Production Frontend (AeroForge Hero + 4-Zone Workstation + ANSYS Viewport)
├── PROJECT_CONTEXT.md                   # Authoritative Engineering Architecture & System Audit (This Document)
├── README.md                            # High-Level Project Overview
│
├── fonts/                               # Local Arimo Font Package
│   ├── Arimo-Regular.ttf
│   ├── Arimo-Bold.ttf
│   ├── Arimo-Italic.ttf
│   └── Arimo-BoldItalic.ttf
│
├── engineermind-backend-main/           # Core FastAPI Backend Service
│   ├── main.py                          # FastAPI Application Routes, CORS, Upload Endpoints, & Database Hooks
│   ├── models.py                        # SQLAlchemy ORM Models (Project, SimulationCase, Result, LogEntry)
│   ├── aerocore.py                      # Deterministic Aero Physics, Flat-Plate BL, ASME V&V 20 Roache GCI
│   ├── cad_engine.py                    # OpenCASCADE Gmsh & Trimesh Inspector, Watertightness, TE Check, Buffer Generator
│   ├── case_builder.py                  # Disk-based OpenFOAM Case Generator & Zip Packager
│   ├── openfoam_pipeline.py             # Subprocess Pipeline Executor, Progress Tracker, & Synthetic Fallback Runner
│   ├── solver_generator.py              # OpenFOAM String Template Generator (blockMeshDict, fvSchemes, etc.)
│   ├── ai_copilot.py                    # Rule-based Pre-Flight Heuristic Expert System & Residual Diagnostics
│   ├── knowledge_engine.py              # RAG-style Peer-Reviewed Aerodynamics Reference Engine
│   ├── cfd_visualizer.py                # VTK PolyData Parser & NACA 0012 Synthetic Generator
│   └── tests/
│       ├── test_e2e_openfoam_run.py     # Pipeline Integration & Execution Test
│       └── test_e2e_openfoam_and_vtk.py # Case Generation & VTK Extraction Test
│
├── openfoam_cases/                      # Generated Working Case Directories on Disk
│   └── case_{id}/                       # Case Folders (0/, constant/, system/)
│
└── engineermind-frontend-main/          # Legacy Standalone Frontend Prototype (Reference Only)
    └── index.html
```

### 2.3 Component Communication Diagram

```
[Browser Client: index.html]
    │
    ├── 1. POST /calculate-physics (Debounced 150ms) ────────> aerocore.py (Boundary layer math)
    │                                                         │
    ├── 2. POST /api/cad/inspect (STEP/STP/IGES/STL upload) ──> cad_engine.py (OpenCASCADE / Trimesh analysis & mesh buffers)
    │                                                         │
    ├── 3. POST /api/projects/{id}/cases (Create Run) ────────> models.py (SQLite DB write)
    │                                                         │
    ├── 4. POST /api/cases/{id}/build-case ───────────────────> case_builder.py (Disk write: 0/, constant/, system/)
    │                                                         │
    ├── 5. POST /api/cases/{id}/run-openfoam ─────────────────> openfoam_pipeline.py (Subprocess blockMesh/simpleFoam)
    │                                                         │  [If host binaries missing: triggers synthetic runner]
    │                                                         │
    ├── 6. GET /api/cases/{id}/logs (Polling 1.5s) <────────── openfoam_pipeline.py (Log stream & residuals)
    │                                                         │
    ├── 7. POST /api/cases/{id}/diagnose-logs ────────────────> ai_copilot.py (Residual divergence & anomaly checks)
    │                                                         │
    └── 8. POST /api/vtk/inspect (foamToVTK PolyData) ────────> cfd_visualizer.py (Scalar field float arrays)
```

---

## 3. Implemented & Verified Features

| Feature | Primary File Path | Verified Functionality |
| :--- | :--- | :--- |
| **OpenCASCADE CAD Engine (STEP/STP/IGES)** | [cad_engine.py](file:///c:/Users/abhin/OneDrive/Documents/anitgravity/games/Simulation-main/engineermind-backend-main/cad_engine.py) | Full support for `.step`, `.stp`, `.iges`, `.igs`, `.brep`, `.stl`, `.obj`, `.ply`, `.glb`. Uses OpenCASCADE via Gmsh for Frontal-Delaunay 2D surface triangulation. Extracts chord, span, area, volume, watertightness, and trailing edge thickness at $99.5\%$ chord. |
| **ANSYS & Blender 3D Viewport** | [index.html](file:///c:/Users/abhin/OneDrive/Documents/anitgravity/games/Simulation-main/index.html#L2700-L2770) | Persistent WebGL viewport with procedural 3D NACA 0012 aerofoil, floating glass toolbar (Edges, Smooth, Wireframe, Normals), 4 PBR materials (Titanium, Aerospace Cyan, Ceramic, Carbon), interactive 3D navigation triad gizmo, and camera-tracking headlight. |
| **Boundary Layer Sizing Engine** | [aerocore.py](file:///c:/Users/abhin/OneDrive/Documents/anitgravity/games/Simulation-main/engineermind-backend-main/aerocore.py) | Full turbulent flat-plate boundary layer calculations ($Re, Ma, C_f, \tau_w, u_\tau, \Delta s, \delta$, layer count at expansion ratio $r=1.15$). Paints immediate 2D prism stack with color-coded buffer warnings. |
| **Three.js Buffer Geometry Pipe** | [cad_engine.py](file:///c:/Users/abhin/OneDrive/Documents/anitgravity/games/Simulation-main/engineermind-backend-main/cad_engine.py#L130-L160) | Serializes triangulated surface into flat `vertices`, `normals`, and `indices` JSON payloads; [index.html](file:///c:/Users/abhin/OneDrive/Documents/anitgravity/games/Simulation-main/index.html) binds directly to `THREE.BufferGeometry` with dynamic frustum scaling (`near = radius/800`, `far = radius*150`). |
| **OpenFOAM Case Builder (Disk)** | [case_builder.py](file:///c:/Users/abhin/OneDrive/Documents/anitgravity/games/Simulation-main/engineermind-backend-main/case_builder.py) | Writes genuine OpenFOAM case structures (`0/U`, `0/p`, `0/k`, `0/omega`, `0/nut`, `constant/transportProperties`, `constant/turbulenceProperties`, `system/blockMeshDict`, `system/snappyHexMeshDict`, `system/fvSchemes`, `system/fvSolution`, `system/controlDict`) to disk; packages cases into `.zip` downloads. |
| **ASME V&V 20 Roache GCI** | [aerocore.py](file:///c:/Users/abhin/OneDrive/Documents/anitgravity/games/Simulation-main/engineermind-backend-main/aerocore.py#L125-L185) | Calculates grid refinement ratios ($r_{21}, r_{32}$), apparent order of accuracy ($p$), Richardson extrapolated values, and Fine Grid Convergence Index ($GCI_{fine}^{21}$). |
| **Residual Diagnostics & Anomaly Detector** | [ai_copilot.py](file:///c:/Users/abhin/OneDrive/Documents/anitgravity/games/Simulation-main/engineermind-backend-main/ai_copilot.py#L60-L120) | Scans iteration logs for continuity/pressure residual spikes, divergence (`NaN`/`Infinity`), standard deviation asymptotic flatlining, and boundary layer violations. |
| **ASCII VTK PolyData Parser** | [cfd_visualizer.py](file:///c:/Users/abhin/OneDrive/Documents/anitgravity/games/Simulation-main/engineermind-backend-main/cfd_visualizer.py) | Parses legacy VTK format meshes; extracts vertex coordinate arrays, polygon indices, and point data scalars ($C_p, p, |U|$); maps them via Three.js vertex colors. |
| **Multi-View SPA Routing Shell** | [index.html](file:///c:/Users/abhin/OneDrive/Documents/anitgravity/games/Simulation-main/index.html#L3130-L3200) | Seamless switching between `Company Overview` and `Simulation Lab` without reloading the page or destroying the WebGL context. Reverted all backgrounds to pure solid `#000` void and `var(--bg-primary)`. |

---

## 4. End-to-End Simulation Workflow

### Step 1: Geometry Upload & Ingestion
1. The user drops or selects an `.step`, `.stp`, `.iges`, `.igs`, `.stl`, or `.obj` file on the interface.
2. The frontend triggers `POST /api/cad/inspect` with binary multipart form data.
3. `cad_engine.py` dispatches parsing:
   - For B-Rep formats (`.step`, `.stp`, `.iges`, `.igs`): Initializes OpenCASCADE via `gmsh`, meshes the 2D surface, and writes an optimized triangulated representation.
   - For mesh formats (`.stl`, `.obj`): Loads directly via `trimesh`.
   - Checks watertightness (`mesh.is_watertight`).
   - Checks trailing edge thickness: $t_{TE} = Y_{max}(x_{TE}) - Y_{min}(x_{TE})$ at $x_{TE} = X_{min} + 0.995c$. If $t_{TE} < 0.001c$, it emits warning flag `BLUNT_EDGE_REQUIRED`.
   - Returns bounding box, surface area, volume, and serialized Three.js vertex/index buffers.
4. Three.js mounts the geometry, extracts `THREE.EdgesGeometry` for crisp feature lines, attaches the camera headlight, and centers the camera on the bounding sphere.

### Step 2: Flow Physics & Boundary Layer Sizing
1. User adjusts Free-Stream Velocity ($U_\infty$), Chord ($c$), and Target $y^+$.
2. Sliders dispatch debounced (150ms) HTTP requests to `POST /calculate-physics`.
3. `aerocore.py` calculates the required first-cell normal wall distance $\Delta s$ and boundary layer thickness $\delta$.
4. The 2D Boundary Layer Prism Stack magnifier canvas immediately draws the inflation layers:
   - Green for resolved sublayer ($y^+ \le 1.0$ or $y^+ \le 5.0$).
   - Cyan for log-law wall function ($y^+ \ge 30.0$).
   - Crimson for the invalid buffer layer ($5.0 < y^+ < 30.0$).

### Step 3: OpenFOAM Case Synthesis
1. User clicks **"Generate OpenFOAM Dictionaries"** or **"Initialize Case"**.
2. Case record is written to SQLite (`models.py`).
3. `case_builder.py` constructs a full directory on disk:
   - `openfoam_cases/case_{id}/`
   - Sets farfield domain cushions: $[-15c, +25c]$ in $X$, $[-15c, +15c]$ in $Y$, $[-5c, +5c]$ in $Z$.
   - Configures `system/snappyHexMeshDict` with `addLayersControls` matching the exact $\Delta s$ and layer count calculated in Step 2.
   - Creates a downloadable `.zip` file of the directory.

### Step 4: Execution & Monitoring
1. User clicks **"Execute Solver"** (`POST /api/cases/{id}/run-openfoam`).
2. `openfoam_pipeline.py` initializes:
   - Checks if native OpenFOAM is on the system PATH (`check_openfoam_installed()`).
   - If present: launches subprocesses sequentially (`blockMesh` $\to$ `surfaceFeatures` $\to$ `snappyHexMesh` $\to$ `simpleFoam`).
   - If absent: launches the asynchronous synthetic runner fallback (`run_mock_openfoam_pipeline`) to simulate iteration logs, residuals, and aerodynamic coefficients.
3. Client polls `GET /api/cases/{id}/logs` every 1.5 seconds, populating the residual chart and terminal console.

### Step 5: Post-Processing & VTK Field Rendering
1. Upon run completion, the pipeline triggers `foamToVTK` (or serves a sample aerofoil VTK dataset).
2. The user uploads or loads a `.vtk` file (`POST /api/vtk/inspect`).
3. `cfd_visualizer.py` parses the scalar data and normalizes values to $[0.0, 1.0]$.
4. Three.js applies a rainbow colormap (Blue $\to$ Cyan $\to$ Yellow $\to$ Red) onto the mesh surface vertices.

---

## 5. OpenFOAM Integration: Real Execution vs. Simulated Fallback

### 5.1 Native Subprocess Execution Pipeline
In [openfoam_pipeline.py](file:///c:/Users/abhin/OneDrive/Documents/anitgravity/games/Simulation-main/engineermind-backend-main/openfoam_pipeline.py), the execution logic is structured as follows:

```python
def check_openfoam_installed() -> bool:
    return (shutil.which("simpleFoam") is not None) and (shutil.which("blockMesh") is not None)
```

When native OpenFOAM is installed on the host operating system:
- **Solver Invocation:** `subprocess.Popen` executes `blockMesh`, `snappyHexMesh -overwrite`, and `simpleFoam`.
- **Live Output Streaming:** `stdout` is piped line-by-line into the database `LogEntry` table.
- **Residual Extraction:** Real-time regex parsers extract residuals for `p`, `Ux`, `Uy`, `k`, and `omega` directly from `log.simpleFoam`.
- **Force Coefficients:** OpenFOAM `postProcess -func forceCoeffs` monitors lift ($C_l$) and drag ($C_d$).

### 5.2 The Synthetic Fallback Runner (Current Windows Host Behavior)
> [!IMPORTANT]
> Because standard Windows environments typically lack native OpenFOAM binaries on the system `PATH` (which usually require WSL2 or Ubuntu Docker containers), `check_openfoam_installed()` evaluates to `False`.

When binaries are absent, the system automatically redirects execution to `run_mock_openfoam_pipeline()`:
- It generates simulated log entries over 15 iterations.
- Emits pre-calculated residual decays for `Ux`, `Uy`, and `p`.
- Writes synthetic `coefficient.dat` files with $C_d = 0.00845$ and $C_l = 0.421$.
- Generates synthetic VTK PolyData via `generate_sample_naca_vtk()`.

**Verification Status:** The Python orchestrator, database tracking, log streaming, and dictionary generators are fully implemented and functional. However, actual numerical Navier-Stokes solves rely on the synthetic runner when host OpenFOAM binaries are not present.

---

## 6. AI Capabilities: Rule-Based Expert vs. Generative Models

### 6.1 True Nature of the AI System
The "AI Copilot" in EngineerMind is **not an external Large Language Model (LLM)** API integration (there are no active OpenAI, Gemini, or Claude API endpoints in the backend solver path). 

Instead, it is a **deterministic, rule-based CAE Expert Diagnostic System** combined with an indexed **Aerodynamic Retrieval Engine**:

1. **Log Diagnostics Engine ([ai_copilot.py](file:///c:/Users/abhin/OneDrive/Documents/anitgravity/games/Simulation-main/engineermind-backend-main/ai_copilot.py)):**
   - **Spike Detector:** Identifies sudden jumps in pressure residuals ($\Delta R_p > 0.05$).
   - **Divergence Detector:** Scans for `NaN`, `Fatal Error`, or exponential growth indicative of Courant-number instabilities ($Co > 1.0$).
   - **Asymptotic Convergence Checker:** Computes moving standard deviation $\sigma$ across the last 10 iterations. If $\sigma < 10^{-4}$, marks solver as converged.
2. **Pre-Flight Heuristic Rule Set ([ai_copilot.py](file:///c:/Users/abhin/OneDrive/Documents/anitgravity/games/Simulation-main/engineermind-backend-main/ai_copilot.py#L20-L55)):**
   - **Compressibility Rule:** If $Ma \ge 0.3$, alerts user: *"Incompressible simpleFoam invalid. Compressible solver (rhoSimpleFoam) required."*
   - **Buffer Layer Rule:** If $5.0 < y^+ < 30.0$, alerts user: *"Invalid wall resolution. Adjust $\Delta s$ to achieve $y^+ \le 1.0$ (resolved) or $y^+ \ge 30.0$ (wall functions)."*
3. **Knowledge Retrieval Engine ([knowledge_engine.py](file:///c:/Users/abhin/OneDrive/Documents/anitgravity/games/Simulation-main/engineermind-backend-main/knowledge_engine.py)):**
   - Tokenizes queries against a curated knowledge base of peer-reviewed literature (Wilcox, Menter 1994, Roache 1998, Schlichting).
   - Provides definitions and numerical bounds for aerodynamic variables ($y^+$, $u_\tau$, GCI, CFL, $k$-$\omega$ SST).

---

## 7. Engineering Formulas & Scientific Accuracy

### 7.1 Aerodynamics & Boundary Layer Math
All equations in [aerocore.py](file:///c:/Users/abhin/OneDrive/Documents/anitgravity/games/Simulation-main/engineermind-backend-main/aerocore.py) adhere strictly to standard aerodynamic theory:

1. **Reynolds Number ($Re$):**
   $$Re = \frac{\rho \cdot U_\infty \cdot c}{\mu}$$

2. **Mach Number ($Ma$):**
   $$Ma = \frac{U_\infty}{\sqrt{\gamma \cdot R_{spec} \cdot T_\infty}}$$
   *(With $\gamma = 1.4$ and $R_{spec} = 287.058\text{ J/(kg}\cdot\text{K)}$)*

3. **Skin Friction Coefficient ($C_f$):**
   - Turbulent flat plate (Schlichting correlation):
     $$C_f = \left(2 \cdot \log_{10}(Re) - 0.65\right)^{-2.3}$$

4. **Wall Shear Stress ($\tau_w$) and Friction Velocity ($u_\tau$):**
   $$\tau_w = \frac{1}{2} C_f \cdot \rho \cdot U_\infty^2 \quad\Longrightarrow\quad u_\tau = \sqrt{\frac{\tau_w}{\rho}}$$

5. **First Cell Height ($\Delta s$):**
   $$\Delta s = \frac{y^+ \cdot \mu}{\rho \cdot u_\tau}$$

6. **Turbulent Boundary Layer Thickness ($\delta$):**
   $$\delta = 0.37 \cdot c \cdot Re^{-1/5}$$

7. **Prism Layer Geometric Progression:**
   $$\delta_{stack} = \Delta s \sum_{i=0}^{N-1} r^i = \Delta s \left(\frac{r^N - 1}{r - 1}\right)$$
   *(Configured with default expansion ratio $r = 1.15$)*

### 7.2 Verification & Validation: ASME V&V 20 Roache GCI
Implemented in [aerocore.py](file:///c:/Users/abhin/OneDrive/Documents/anitgravity/games/Simulation-main/engineermind-backend-main/aerocore.py#L125-L185):
- Grid refinement ratio: $r_{21} = h_2 / h_1$, $r_{32} = h_3 / h_2$.
- Apparent order of accuracy $p$:
  $$p = \frac{|\ln|(\phi_3 - \phi_2)/(\phi_2 - \phi_1)| + q|}{\ln(r_{21})}$$
- Fine Grid Convergence Index ($GCI_{fine}^{21}$):
  $$GCI_{fine}^{21} = \frac{F_s \cdot |e_{21}|}{r_{21}^p - 1}$$
  *(With ASME safety factor $F_s = 1.25$ for 3-grid studies)*

### 7.3 Scientific Limitations
- **Flat-Plate Assumption:** Boundary layer calculations assume flat-plate boundary layer development. Severe adverse pressure gradients ($\nabla p > 0$) or strong separation bubbles will locally modify the actual $y^+$ distribution.
- **Incompressible Boundary:** The default solver setup is strictly incompressible (`simpleFoam`). Transonic or supersonic flows require compressibility corrections and `rhoSimpleFoam`.

---

## 8. Incomplete, Mocked, or Partial Features

1. **Native Windows OpenFOAM Binary Execution:**
   - Real OpenFOAM binaries are currently absent from the Windows host environment. Subprocess calls fall back cleanly to `run_mock_openfoam_pipeline()`. Full production deployment requires a WSL2 or Docker execution container.
2. **Dual Frontend Synchronization:**
   - The root [`index.html`](file:///c:/Users/abhin/OneDrive/Documents/anitgravity/games/Simulation-main/index.html) is the primary production SPA with all latest 3D viewport, CAD, and router features.
   - The legacy prototype in `engineermind-frontend-main/index.html` remains outdated and should eventually be archived or removed.
3. **Dual OpenFOAM Dictionary Generators:**
   - Dictionaries are still generated in both `solver_generator.py` (string templates for UI preview) and `case_builder.py` (disk-based file writer). These should be unified under a single templating service.

---

## 9. Known Bugs & Technical Debt (Audit & Resolution Status)

| Debt Item | Initial Finding | Current Resolution Status |
| :--- | :--- | :--- |
| **Crude Box Geometry Baseline** | Viewport initially loaded a cyan `BoxGeometry(1.8, 0.12, 4.2)` block. | **RESOLVED:** Replaced with procedural 3D NACA 0012 aerofoil (`createNACA0012Geometry`) with realistic thickness, camber, and span. |
| **Blank Wall Prism Resolution Canvas** | `drawBoundaryLayerWidget` was not invoked on workstation transition, leaving canvas blank. | **RESOLVED:** Added explicit paint calls on DOM load, slider inputs, and `btnInitWorkflow.onclick`. |
| **Missing STEP/STP/IGES Support** | File pickers restricted to `.stl,.obj` and Trimesh lacked B-Rep NURBS tessellation. | **RESOLVED:** Integrated OpenCASCADE via `gmsh 4.15.2` in `cad_engine.py` and updated file input `accept` attributes. |
| **Thin Geometry Invisibility on Orbit** | Thin wings/plates disappeared when orbiting to backface due to single-sided culling & unlit backfaces. | **RESOLVED:** Added camera-tracking directional headlight (`camera.add(headLight)`), `side: THREE.DoubleSide`, ambient floor (`emissive: 0x182436`), and dynamic frustum (`near = radius/800`, `far = radius*150`). |
| **Unwanted Purple Background Gradient** | Purple `#63e` gradient was bleeding through transparent WebGL canvas. | **RESOLVED:** Reverted `html` and `body` to `var(--bg-primary)`, set `#viewport3D` to `#000`, and set `alpha: false` with `renderer.setClearColor(0x000000, 1.0)`. |
| **Duplicate Dictionary Logic** | `solver_generator.py` and `case_builder.py` duplicate OpenFOAM text formatting. | **OPEN / PENDING:** Consolidate all dictionary generation into `case_builder.py`. |
| **Hardcoded Database Paths** | `sqlite:///./engineermind.db` can create duplicate databases if launched from different working directories. | **OPEN / PENDING:** Bind SQLite URI to absolute directory path. |

---

## 10. Current Development Status & Recommended Priorities

### 10.1 Completed Milestones
- [x] Zero-fallback backend aerodynamic math engine (`aerocore.py`).
- [x] Disk-level OpenFOAM case generator (`case_builder.py`) with complete directory tree.
- [x] OpenCASCADE CAD inspection & tessellation engine for STEP, STP, IGES, BREP, STL, and OBJ (`cad_engine.py`).
- [x] ANSYS & Blender-grade 3D WebGL viewport with feature edge extraction, materials suite, and orientation gizmo.
- [x] Camera-tracking headlight and dynamic frustum scaling preventing backface culling and near-plane vanishing.
- [x] ASME V&V 20 Roache Grid Convergence Index module.
- [x] Three.js persistent 3D WebGL viewport and VTK scalar colormap rendering.
- [x] Unified AeroForge / EngineerMind multi-view header router.
- [x] Local Arimo typography integration across all UI components.
- [x] Verified automated end-to-end unit tests on synthetic STEP/STP solids.

### 10.2 Recommended Next Priorities
1. **WSL2 / Docker OpenFOAM Bridge:**
   - Configure a containerized worker (`openfoam/openfoam10-default`) to execute native `blockMesh` and `simpleFoam` on Windows hosts.
2. **Consolidate Dictionary Generators:**
   - Deprecate `solver_generator.py` and route all frontend dictionary previews through `case_builder.py`.
3. **Archive Legacy Frontend:**
   - Remove or deprecate `engineermind-frontend-main/` to eliminate codebase divergence.
4. **Absolute Database Path Binding:**
   - Ensure `models.py` uses `Path(__file__).parent / "engineermind.db"` to prevent fragmented database instances.
