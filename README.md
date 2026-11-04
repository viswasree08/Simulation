# EngineerMind AI — CAE Engineering Workstation & Decision Accountability Portal

[![FastAPI](https://img.shields.io/badge/FastAPI-3.0.0-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Three.js](https://img.shields.io/badge/Three.js-r128-black?style=flat&logo=three.js)](https://threejs.org/)
[![SQLite/PostgreSQL](https://img.shields.io/badge/SQLAlchemy-ORM-red?style=flat&logo=sqlite)](https://www.sqlalchemy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An enterprise-grade, full-stack Computational Fluid Dynamics (CFD) pre-flight reasoning, boundary layer formulation, and diagnostic accountability platform. Designed for aerodynamicists, defense contractors, and turbomachinery engineers who require verifiable physics, immutable audit trails, and automated ASME V&V 20 compliance.

---

## Architecture Overview

```mermaid
graph TD
    subgraph Frontend ["Front-End Workstation (engineermind-frontend-main)"]
        Landing["Stage 0: Stitch Wind Tunnel Landing Card"]
        Z1["Zone 1: Parametric Inspector (Debounced PATCH 150ms)"]
        Z2["Zone 2: Persistent 3D WebGL Canvas (Three.js STL Viewport)"]
        BLW["2D Boundary Layer Prism Stack Magnifier Widget"]
        Z3["Zone 3: OpenFOAM Dictionaries, Residual Plots & ASME GCI"]
        Z4["Zone 4: AI Copilot & Immutable Decision Trail"]
        RAGDrawer["Slide-Out Verified Concept Knowledge Drawer"]
    end

    subgraph Backend ["Physics & RAG Backend Core (engineermind-backend-main)"]
        API["FastAPI REST Engine (port 8000)"]
        PhysicsCore["Deterministic Aerodynamics Calculator (Schlichting & Prandtl)"]
        ORM["SQLAlchemy ORM (SQLite / PostgreSQL)"]
        KnowledgeRAG["Verified Knowledge Engine (Equations, Limits, Failure Modes)"]
        Copilot["Context-Aware CAE Copilot (Buffer Layer & Vortex Shedding Checks)"]
        Diagnostics["Log Parser & Drag Variance Analyzer"]
    end

    Landing -->|POST /calculate-physics| PhysicsCore
    Landing -->|POST /api/projects/{id}/cases| ORM
    Z1 -->|PATCH /api/cases/{id}| ORM
    Z2 -->|CAD Mesh Buffer| BLW
    Z3 -->|POST /api/cases/{id}/audit-log| Diagnostics
    Z4 -->|POST /api/copilot/explain-case| Copilot
    Z4 -->|GET /api/projects/{id}| ORM
    RAGDrawer -->|GET /api/knowledge/concept/{term_id}| KnowledgeRAG
```

---

## Key Platform Features

### 1. Strict Deterministic Physics (Zero Client-Side Calculations)
- All aerodynamics calculations ($Re$, $Ma$, $C_f$, $\Delta s$, $\delta$, $\tau_w$, $u_\tau$) are handled by `POST /calculate-physics` and dynamically updated via `PATCH /api/cases/{case_id}`.
- Analytical hand calculations use established Schlichting turbulent boundary layer and Prandtl momentum thickness correlations.
- Automatically derives fluid domain bounds ($15c$ upstream, $25c$ downstream, $15c$ lateral) to prevent numerical boundary reflection.

### 2. Zero-Disruption 3D Viewport Architecture
- The Three.js WebGL rendering context is initialized exactly once upon application boot and is **never** destroyed or re-created with `innerHTML`.
- Clean transition between the **Stage 0 Landing Card** and the **4-Zone Engineering Workstation** using CSS grid transitions, dynamic projection matrix updates (`camera.updateProjectionMatrix()`), and canvas dimension resizing (`renderer.setSize()`).
- Supports `.stl` and `.obj` aerodynamic CAD file loading without fake particle animations.

### 3. 2D Boundary Layer Prism Stack Magnifier
- High-precision HTML5 Canvas widget illustrating wall-normal prism resolution:
  - **Low-Re Resolved ($y^+ \le 1.0$):** Resolves viscous sublayer with $\ge 28$ prism layers at a $1.15$ geometric expansion ratio.
  - **Wall Functions ($y^+ \approx 30.0$):** Places first node in the log-law layer with $12$ prism layers.

### 4. Interactive Verified Knowledge Base (RAG Slide-Out Drawer)
Clicking underlined technical terms anywhere in the interface opens the authoritative knowledge drawer directly from `GET /api/knowledge/concept/{term_id}`:
- **Reynolds Number ($Re$):** $Re = \frac{\rho U_\infty c}{\mu}$
- **Mach Number ($Ma$):** Compressibility thresholds ($Ma \ge 0.3$)
- **Non-Dimensional Wall Distance ($y^+$):** Buffer layer violations ($5 < y^+ < 30$)
- **Menter $k$-$\omega$ SST:** Two-equation shear stress transport formulation
- **Second-Order Upwind:** Face interpolation linear gradient reconstruction
- **Roache Grid Convergence Index (GCI):** ASME V&V 20 spatial discretization uncertainty

### 5. AI Engineering Copilot & Immutable Decision Audit Trail
- Context-aware telemetry inspection flags critical errors (e.g., buffer layer placements, unphysical steady RANS convergence amidst vortex shedding, or compressible solver requirements).
- Every project state modification, parameter update, or log audit automatically appends an immutable entry to `decision_records` visible in Zone 4.

### 6. ASME V&V 20 Grid Convergence Index (GCI) Calculator
- Evaluates spatial discretization uncertainty across 3 systematically refined grid solutions ($f_3$ coarse, $f_2$ medium, $f_1$ fine).
- Solves apparent order of convergence ($p$) and fine-grid GCI percentage, confirming asymptotic range adherence.

---

## Directory & File Structure

```
Simulation-main/
├── README.md                           # Master platform documentation
├── index.html                          # AeroForge CFD showcase website (Port 8080)
│
├── engineermind-backend-main/          # FastAPI Python Backend
│   ├── main.py                         # REST API endpoints, physics core, and log diagnostics
│   ├── models.py                       # SQLAlchemy database models (Project, Case, DecisionRecord)
│   ├── knowledge_engine.py             # Verified RAG knowledge base & LaTeX formulas
│   ├── ai_copilot.py                   # Context-aware CAE reasoning & violation auditor
│   ├── requirements.txt                # Backend dependencies (fastapi, uvicorn, sqlalchemy, etc.)
│   └── engineermind.db                 # Auto-generated SQLite database (or Postgres)
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
| `POST` | `/calculate-physics` | Calculates $Re$, $Ma$, boundary layer $\delta$, first cell height $\Delta s$, and domain dimensions. |
| `GET` | `/api/projects` | Lists all engineering projects and case counts. |
| `GET` | `/api/projects/{project_id}` | Retrieves project details, associated cases, and chronological decision audit logs. |
| `POST` | `/api/projects/{project_id}/cases` | Persists a new simulation case with full physics telemetry. |
| `PATCH` | `/api/cases/{case_id}` | Debounced parametric property updates; re-computes physics and appends to audit trail. |
| `GET` | `/api/knowledge/concept/{term_id}` | Retrieves verified RAG concept definitions, LaTeX equations, and failure modes. |
| `POST` | `/api/copilot/explain-case` | Runs AI copilot telemetry review on active case settings. |
| `POST` | `/api/cases/{case_id}/audit-log` | Parses uploaded OpenFOAM/Fluent solver logs, calculating continuity and drag standard deviation ($\sigma$). |

---

## Quick Start & Setup Guide

### 1. Prerequisites
- **Python 3.9+**
- **Modern Web Browser** (Chrome, Edge, Firefox, Safari) with WebGL support enabled

### 2. Backend Installation & Startup

```powershell
# Navigate to the backend directory
cd engineermind-backend-main

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server with hot-reloading
uvicorn main:app --reload --port 8000
```

The backend API will be available at:
- **API Base:** `http://127.0.0.1:8000`
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`
- **Alternative Redoc:** `http://127.0.0.1:8000/redoc`

### 3. Frontend Workstation Launch

You can open `engineermind-frontend-main/index.html` directly in your browser:
```powershell
Start-Process engineermind-frontend-main\index.html
```

Or serve via any static HTTP file server:
```powershell
# In the repository root:
python -m http.server 8080
```
Navigate to:
- **EngineerMind Workstation:** `http://localhost:8080/engineermind-frontend-main/`
- **AeroForge Showcase Platform:** `http://localhost:8080/`

---

## Verification & Test Scenarios

1. **Stitch Landing Parameter Adjustments:**
   - Change Velocity ($U_\infty$) from `40 m/s` to `120 m/s`.
   - Verify that the 3D bounding box wireframe immediately scales in the Three.js viewport and the 2D Prism Stack Magnifier redraws based on backend calculation responses.
2. **Workflow Transition:**
   - Click **"Confirm Domain & Initialize Workflow →"**.
   - Verify that the layout animates into the **4-Zone Workstation**, initializes Case #1 in the database, populates OpenFOAM solver dictionaries, and loads the AI Copilot evaluation.
3. **Buffer Layer Violation Warning:**
   - In Zone 1 (Left Rail), change Target $y^+$ to an unphysical value (or test the copilot reasoning).
   - Notice that the AI Copilot flags: `"CRITICAL: Buffer Layer Violation (5 < y+ < 30)"`.
4. **Verified Concept Drawer:**
   - Click on <span style="text-decoration: underline dotted #00C7E8;">Re</span>, <span style="text-decoration: underline dotted #00C7E8;">Mach</span>, or <span style="text-decoration: underline dotted #00C7E8;">ASME V&V 20 GCI</span>.
   - The slide-out drawer appears with KaTeX-ready formulas, engineering definitions, governing physics, and literature citations.

---

## License & Defense Compliance Statement
All aerodynamic calculations, diagnostic checks, and audit trails comply with standard engineering verification workflows. Software implementations are designed to meet ITAR Part 120-130 and NIST SP 800-171 enclave isolation parameters when deployed on air-gapped infrastructure.
