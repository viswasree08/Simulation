# EngineerMind AI — CAE Engineering Workstation & Decision Accountability Portal

[![FastAPI](https://img.shields.io/badge/FastAPI-3.0.0-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Three.js](https://img.shields.io/badge/Three.js-r128-black?style=flat&logo=three.js)](https://threejs.org/)
[![OpenFOAM](https://img.shields.io/badge/OpenFOAM-v2212_(ESI/OpenCFD)-blue?style=flat&logo=docker)](https://www.openfoam.com/)
[![Docker](https://img.shields.io/badge/Docker-Verified_Runtime-2496ED?style=flat&logo=docker)](https://hub.docker.com/r/opencfd/openfoam-default)
[![Pytest](https://img.shields.io/badge/Pytest-56%20Passed-brightgreen?style=flat&logo=pytest)](https://docs.pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An enterprise-grade, full-stack Computational Fluid Dynamics (CFD) pre-flight reasoning, boundary layer formulation, deterministic scientific computation engine, and genuine OpenFOAM v2212 execution platform. Designed for aerospace engineers, defense contractors, and aerodynamicists who require verifiable physics, immutable audit trails, ASME V&V 20 compliance, and genuine Navier-Stokes CFD simulations inside containerized environments.

---

## Architecture Overview

```mermaid
graph TD
    subgraph Frontend ["Front-End Workstation (engineermind-frontend-main)"]
        Landing["Stage 0: Stitch Wind Tunnel Landing Card"]
        Z1["Zone 1: Parametric Inspector (Debounced PATCH 150ms)"]
        Z2["Zone 2: Persistent 3D WebGL Canvas (Three.js STL & VTK Viewport)"]
        BLW["2D Boundary Layer Prism Stack Magnifier Widget"]
        Z3["Zone 3: OpenFOAM Dictionaries, Residual Plots & ASME GCI"]
        Z4["Zone 4: AI Copilot & Immutable Decision Trail"]
        RAGDrawer["Slide-Out Verified Concept Knowledge Drawer"]
    end

    subgraph Backend ["Physics & RAG Backend Core (engineermind-backend-main)"]
        API["FastAPI REST Engine (port 8000)"]
        EngCore["engineering_core/ (10 Deterministic Scientific Modules)"]
        Bridge["openfoam_bridge.py (Validated OpenFOAM v2212 Bridge)"]
        CaseBuilder["case_builder.py (3D Case Tree & ZIP Archiver)"]
        ORM["SQLAlchemy ORM (SQLite / PostgreSQL)"]
        KnowledgeRAG["Verified Knowledge Engine (Equations, Limits, Failure Modes)"]
        Copilot["Context-Aware CAE Copilot (Buffer Layer & Vortex Shedding Checks)"]
    end

    subgraph DockerEnv ["Docker Runtime (OpenCFD OpenFOAM v2212)"]
        BM["blockMesh (Hex Farfield Domain)"]
        SFE["surfaceFeatureExtract (Feature Edge Mesh)"]
        SHM["snappyHexMesh (Prism Layers & Wall Snapping)"]
        CM["checkMesh (Topology & Geometry Auditor)"]
        SF["simpleFoam (Steady-State Incompressible RANS k-omega SST)"]
    end

    Landing -->|POST /calculate-physics| EngCore
    Landing -->|POST /api/projects/{id}/cases| ORM
    Z1 -->|PATCH /api/cases/{id}| ORM
    Z1 --> EngCore
    Z2 -->|CAD & VTK Mesh Buffer| BLW
    Z3 --> CaseBuilder
    CaseBuilder --> Bridge
    Bridge --> EngCore
    CaseBuilder --> DockerEnv
    Z4 -->|POST /api/copilot/explain-case| Copilot
    RAGDrawer -->|GET /api/knowledge/concept/{term_id}| KnowledgeRAG
```

---

## Key Platform Features

### 1. Deterministic Engineering Core (`engineering_core/`)
An independent, mathematically verified engineering computation package completely isolated from AI modules and API routes:
- **`fluid_properties.py`**: Sutherland law temperature-dependent dynamic viscosity $\mu(T)$, density via ideal gas law $\rho(p, T)$, and kinematic viscosity $\nu$.
- **`aerodynamics.py`**: Reynolds number $\text{Re}$, Mach number $M$, dynamic pressure $q_\infty$, aerodynamic lift & drag coefficients ($C_L, C_D$).
- **`boundary_layer.py`**: Schlichting & White turbulent skin friction $C_f$, wall shear stress $\tau_w$, friction velocity $u_\tau$, first cell height $\Delta s$ for target $y^+$, and turbulent boundary layer thickness $\delta$.
- **`mesh_calculator.py`**: snappyHexMesh prism layer progressions with geometric expansion ratios ($r = 1.15$), AIAA DPW domain sizing ($15c$ upstream, $25c$ downstream, $15c$ lateral).
- **`turbulence.py`**: $k$-$\omega$ SST inflow boundary condition derivation ($k, \omega, \nu_t$) from turbulent intensity $I$ and length scale $l_t$, continuous wall function assessments.
- **`numerical_methods.py`**: CFL Courant-Friedrichs-Lewy condition $\text{Co} = \frac{u \Delta t}{\Delta x}$, matrix condition numbers, relaxation factors.
- **`verification.py`**: ASME V&V 20 Grid Convergence Index (GCI), apparent order of convergence $p$, asymptotic range verification.
- **`uncertainty.py`**: Kline-McClintock multivariate uncertainty propagation ($u_{\text{res}} = \sqrt{\sum (\frac{\partial R}{\partial x_i} u_i)^2}$).
- **`units.py`**: Dimensional consistency verification and unit conversions.

### 2. Validated OpenFOAM v2212 Integration (`openfoam_bridge.py`)
Direct mapping of validated scientific calculations into authentic OpenCFD / ESI OpenFOAM v2212 dictionary structures:
- **`system/blockMeshDict`**: 3D farfield hexahedral bounding domain without unsupported 2D empty patches.
- **`system/surfaceFeatureExtractDict`**: Feature line extraction with `extractionMethod extractFromSurface;` and `includedAngle 150;`.
- **`system/snappyHexMeshDict`**: Wall-normal prism layer extrusions ($y^+ \le 1.0$, 28 layers, $r=1.15$), feature edge snapping, `minMedialAxisAngle 90;`, `slipFeatureAngle 30;`, `nRelaxIter 5;`.
- **`system/fvSchemes` & `system/fvSolution`**: Bounded second-order linear upwind schemes, GAMG pressure solver, smoothSolver momentum solvers, and required `wallDist { method meshWave; }`.
- **`system/controlDict`**: Real-time aerodynamic force monitors (`forceCoeffs`) evaluating $C_d$, $C_l$, and pitch moment $C_m$ about quarter-chord $\vec{x}_{\text{ref}} = (c/4, 0, 0)$.
- **`constant/turbulenceProperties` & `constant/momentumTransport`**: Dual-standard compatibility for incompressible RANS $k$-$\omega$ SST.

### 3. Genuine Containerized CFD Execution (Docker OpenCFD v2212)
- Tested and verified against the official OpenCFD Docker image: `opencfd/openfoam-default:2212` (`sha256:0373e0c211d319e28e9b8b52a36696b11851e21ed55add47862cb5d01ffbb1cb`).
- Executes genuine solver pipelines: `blockMesh` $\rightarrow$ `surfaceFeatureExtract` $\rightarrow$ `snappyHexMesh -overwrite` $\rightarrow$ `checkMesh` $\rightarrow$ `simpleFoam`.
- Bounded real solver execution validated (50 iterations) with monotonic residual reduction and live aerodynamic force coefficient extraction ($C_d = 0.02261$, $C_l = 0.08249$).

### 4. Zero-Disruption 3D Viewport Architecture
- Persistent Three.js WebGL rendering context initialized once upon boot and preserved across UI view transitions.
- Supports CAD surface rendering (`.stl`), farfield wireframe domains, and 3D CFD surface mesh VTK contours.
- High-precision 2D Canvas Boundary Layer Magnifier illustrating wall-normal prism resolution:
  - **Low-Re Wall-Resolved ($y^+ \le 1.0$):** Viscous sublayer resolved with $\ge 28$ prism layers.
  - **Wall Functions ($y^+ \approx 30.0$):** First centroid placed in log-law layer with 12 layers.

### 5. Interactive Verified Knowledge Base (RAG Slide-Out Drawer)
Clicking technical concepts anywhere in the workstation loads verified equations, validity bounds, and failure modes via `GET /api/knowledge/concept/{term_id}`:
- **Reynolds Number ($Re$):** $Re = \frac{\rho U_\infty c}{\mu}$
- **Mach Number ($Ma$):** Incompressible limits ($Ma < 0.3$) vs transonic shock formation.
- **Wall Distance ($y^+$):** Buffer layer violations ($5 < y^+ < 30$).
- **Menter $k$-$\omega$ SST:** Two-equation shear stress transport formulation.
- **Roache GCI:** ASME V&V 20 spatial discretization uncertainty metrics.

### 6. AI Engineering Copilot & Immutable Decision Audit Trail
- Context-aware telemetry inspection flags critical aerodynamic mistakes before solver execution (e.g. buffer layer placement, unphysical steady RANS convergence amidst vortex shedding, or compressible flow mismatches).
- Every project state modification, parameter update, or log audit automatically appends an immutable entry to `decision_records` visible in Zone 4.

---

## Directory & File Structure

```
Simulation-main/
├── README.md                           # Master platform documentation
├── PROJECT_CONTEXT.md                  # Comprehensive engineering context & verification roadmap
├── index.html                          # AeroForge CFD showcase website (Port 8080)
│
├── ENGINEERING_COMPUTATION_AUDIT.md    # Task 01: Initial mathematical audit of backend
├── ENGINEERING_CORE_REPORT.md          # Task 02: Architecture report of engineering_core package
├── ENGINEERING_CORE_VALIDATION.md      # Task 03: Scientific validation suite report (54 tests)
├── FASTAPI_ENGINEERING_INTEGRATION.md  # Task 04: Pydantic schemas and API contracts
├── OPENFOAM_V2212_INTEGRATION.md       # Task 05: Engineering core to OpenFOAM v2212 bridge
├── OPENFOAM_DOCKER_ENVIRONMENT_AUDIT.md# Task 06: Docker Desktop & OpenCFD v2212 image verification
├── OPENFOAM_V2212_CASE_COMPATIBILITY_AUDIT.md # Task 07: Container dictionary compatibility audit
├── OPENFOAM_V2212_IMPLEMENTATION_REPORT.md    # Task 08: Dictionary corrections & bugfixes
├── OPENFOAM_V2212_RUNTIME_TEST_RESULTS.md     # Task 08: Live container execution outputs
├── REAL_CFD_VALIDATION_REPORT.md       # Task 09: Physics audit & real CFD validation report
├── REAL_CFD_EXECUTION_LOG.md           # Task 09: Complete simpleFoam 50-step iteration log
│
├── engineermind-backend-main/          # FastAPI Python Backend
│   ├── main.py                         # REST API endpoints & route orchestration
│   ├── api_schemas.py                  # Pydantic v2 schemas for deterministic core
│   ├── models.py                       # SQLAlchemy database models (Project, Case, DecisionRecord)
│   ├── openfoam_bridge.py              # Validated OpenFOAM v2212 dictionary generators
│   ├── case_builder.py                 # 3D OpenFOAM case directory creator & ZIP packager
│   ├── openfoam_pipeline.py            # Async CFD pipeline & execution tracker
│   ├── solver_generator.py             # Scheme, solution, and mesh dictionary generators
│   ├── knowledge_engine.py             # Verified RAG knowledge base & LaTeX formulas
│   ├── ai_copilot.py                   # Context-aware CAE reasoning & violation auditor
│   ├── requirements.txt                # Backend dependencies (fastapi, uvicorn, sqlalchemy, etc.)
│   ├── engineermind.db                 # Auto-generated SQLite database
│   │
│   ├── engineering_core/               # Deterministic Engineering Package
│   │   ├── __init__.py                 # Public package interface
│   │   ├── fluid_properties.py         # Sutherland's law, ideal gas law
│   │   ├── aerodynamics.py             # Re, Mach, dynamic pressure, lift/drag
│   │   ├── boundary_layer.py           # Turbulent skin friction, delta, y+, first cell
│   │   ├── mesh_calculator.py          # snappyHexMesh prism progression & domain sizing
│   │   ├── turbulence.py               # k-omega SST inflow conditions, wall function rules
│   │   ├── numerical_methods.py        # Courant number, matrix condition numbers
│   │   ├── verification.py             # ASME V&V 20 GCI & order of convergence
│   │   ├── uncertainty.py              # Multivariate error propagation
│   │   └── units.py                    # SI dimensional verification
│   │
│   └── tests/                          # Automated Pytest Suite (56 Passed)
│       ├── test_fastapi_engineering_integration.py
│       ├── test_openfoam_v2212_bridge.py
│       └── engineering_core/           # Scientific verification unit tests (9 modules)
│
└── engineermind-frontend-main/         # Front-End Workstation
    ├── index.html                      # 4-Zone Stitch CAE Workstation & Three.js canvas
    ├── js/                             # Local vendor asset fallbacks (Three.js, OrbitControls, STLLoader)
    └── README.md                       # Frontend-specific notes
```

---

## API Contract Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/calculate-physics` | Deterministic physics: $Re$, $Ma$, boundary layer $\delta$, first cell height $\Delta s$, and domain dimensions. |
| `POST` | `/api/engineering/fluid-properties` | Sutherland law $\mu(T)$, density $\rho(p, T)$, kinematic viscosity $\nu$. |
| `POST` | `/api/engineering/aerodynamics` | Aerodynamic parameters ($Re, M, q_\infty, C_l, C_d$). |
| `POST` | `/api/engineering/boundary-layer` | Turbulent skin friction $C_f$, boundary layer thickness $\delta$, first cell height $\Delta s$. |
| `POST` | `/api/engineering/prism-layers` | Geometric prism layer distribution ($N, r, \Delta s_{\text{first}}, \Delta s_{\text{final}}$). |
| `POST` | `/api/engineering/turbulence-inlet` | $k$-$\omega$ SST inflow boundary conditions ($k, \omega, \nu_t$). |
| `POST` | `/api/engineering/asme-gci` | ASME V&V 20 Grid Convergence Index and order of convergence $p$. |
| `GET` | `/api/projects` | Lists all engineering projects and case counts. |
| `GET` | `/api/projects/{project_id}` | Retrieves project details, associated cases, and chronological decision audit logs. |
| `POST` | `/api/projects/{project_id}/cases` | Persists a new simulation case with full physics telemetry. |
| `PATCH` | `/api/cases/{case_id}` | Debounced parametric property updates; re-computes physics and appends to audit trail. |
| `POST` | `/api/cases/{case_id}/build-case` | Builds working OpenFOAM v2212 case on disk and returns ZIP download link. |
| `GET` | `/api/cases/{case_id}/download-case` | Downloads generated OpenFOAM case ZIP archive. |
| `GET` | `/api/knowledge/concept/{term_id}` | Retrieves verified RAG concept definitions, LaTeX equations, and failure modes. |
| `POST` | `/api/copilot/explain-case` | Runs AI copilot telemetry review on active case settings. |
| `POST` | `/api/cases/{case_id}/audit-log` | Parses uploaded OpenFOAM/Fluent solver logs, calculating continuity and drag standard deviation ($\sigma$). |

---

## Quick Start & Setup Guide

### 1. Prerequisites
- **Python 3.9+** (Tested on Python 3.11)
- **Docker Desktop** (Engine 29+ with WSL2 backend) for real OpenFOAM CFD execution
- **Docker Image:** `docker pull opencfd/openfoam-default:2212`
- **Modern Web Browser** with WebGL enabled (Chrome, Edge, Firefox)

### 2. Backend Installation & Test Suite Execution

```powershell
# Navigate to the backend directory
cd engineermind-backend-main

# Install dependencies
pip install -r requirements.txt

# Run full scientific verification and API test suite (56 tests)
python -m pytest tests/

# Start the FastAPI server with hot-reloading
uvicorn main:app --reload --port 8000
```

The backend API will be available at:
- **API Base:** `http://127.0.0.1:8000`
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`
- **Alternative Redoc:** `http://127.0.0.1:8000/redoc`

### 3. Frontend Workstation Launch

Serve via any static HTTP file server from the repository root:
```powershell
python -m http.server 8080
```
Navigate to:
- **EngineerMind Workstation:** `http://localhost:8080/engineermind-frontend-main/`
- **AeroForge Showcase Platform:** `http://localhost:8080/`

---

## Real CFD Execution Pipeline (OpenFOAM v2212)

To generate and run a complete 3D aerodynamic case inside the official Docker container:

```bash
# 1. Pull the verified OpenCFD v2212 container image
docker pull opencfd/openfoam-default:2212

# 2. Build case directory via case_builder.py
python -c "import case_builder; res = case_builder.build_case_directory(case_id=202, base_dir='openfoam_cases', chord_m=1.0, velocity_ms=40.0, target_y_plus=1.0)"

# 3. Execute meshing and solver pipeline in Docker
docker run --rm -v "$(pwd)/openfoam_cases/case_202:/case" opencfd/openfoam-default:2212 bash -c "
    source /usr/lib/openfoam/openfoam2212/etc/bashrc && \
    cd /case && \
    surfaceFeatureExtract && \
    blockMesh && \
    snappyHexMesh -overwrite && \
    checkMesh && \
    simpleFoam
"
```

---

## License & Defense Compliance Statement
All aerodynamic calculations, diagnostic checks, and audit trails comply with standard engineering verification workflows. Software implementations are designed to meet ITAR Part 120-130 and NIST SP 800-171 enclave isolation parameters when deployed on air-gapped infrastructure.
