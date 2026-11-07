# OpenFOAM v2212 Case Compatibility & Runtime Audit

**Project:** EngineerMind AI / AeroForge Systems  
**Auditor:** Senior OpenFOAM (OpenCFD/ESI) & Container Integration Engineer  
**Verified Target Container:** `opencfd/openfoam-default:2212` (`api=2212`, `patch=230110`, `build=_c9081d5d-20230220`)  
**Container Environment Sourcing:** `/usr/lib/openfoam/openfoam2212/etc/bashrc`  
**Date:** November 2026  
**Status:** **AUDIT COMPLETED — CRITICAL COMPATIBILITY DEFECTS IDENTIFIED**

---

## 1. Executive Summary

This audit performs an end-to-end verification of OpenFOAM case construction, dictionary syntax, utility command compatibility, and pipeline execution logic against the verified **OpenCFD OpenFOAM v2212** Docker container.

### Key Finding:
While the spatial layout, mathematical dimensioning, and boundary patch sizing produced by `engineering_core` are physically sound, **attempting to run the generated case directly in OpenFOAM v2212 failed on 4 critical syntax and configuration incompatibilities**:
1. `system/fvSchemes` and `system/fvSolution` contain invalid double-braces `{{ ... }}` in generated files, causing immediate parser abort.
2. `constant/momentumTransport` is ignored by incompressible `simpleFoam` in v2212; `simpleFoam` strictly requires `constant/turbulenceProperties` with `RASModel kOmegaSST;`.
3. `system/fvSchemes` is missing the mandatory `wallDist { method meshWave; }` sub-dictionary required for the $k$-$\omega$ SST turbulence model.
4. `system/controlDict`'s `forceCoeffs` definition lacks the mandatory `CofR (x y z);` (Center of Rotation) vector, aborting execution during solver startup.
5. In `openfoam_pipeline.py`, the feature extraction command is named `surfaceFeatures` (Foundation fork syntax) instead of `surfaceFeatureExtract` (OpenCFD/ESI v2212 binary name), and it expects `system/surfaceFeatureExtractDict`.

---

## 2. Complete Compatibility Findings Matrix

| Finding ID | Component / File | Subject / Parameter | Classification | Summary of Issue |
| :---: | :--- | :--- | :---: | :--- |
| **AUD-01** | `openfoam_pipeline.py:222` | Binary Name for Feature Extraction | **FAIL** | Pipeline invokes `surfaceFeatures`, which does not exist in OpenCFD v2212. Must be `surfaceFeatureExtract`. |
| **AUD-02** | `solver_generator.py:101`, `case_builder.py:190` | Feature Extraction Dictionary Name & Syntax | **FAIL** | Generates `system/surfaceFeaturesDict`, but v2212 `surfaceFeatureExtract` strictly expects `system/surfaceFeatureExtractDict` with `extractionMethod extractFromSurface;`. |
| **AUD-03** | `solver_generator.py:313-428` | Dictionary Brace Syntax in fvSchemes & fvSolution | **FAIL** | Double curly braces `{{` and `}}` are written literally to disk, causing parser error `Found { but expected }` at line 9. |
| **AUD-04** | `case_builder.py:213`, `openfoam_bridge.py:420` | Turbulence Properties File Name | **FAIL** | Writes `constant/momentumTransport`, but `simpleFoam` in v2212 aborts with: `cannot find file constant/turbulenceProperties`. |
| **AUD-05** | `solver_generator.py:313`, `openfoam_bridge.py` | Missing `wallDist` in `system/fvSchemes` | **FAIL** | $k$-$\omega$ SST model requires wall distance computation. Solver aborts: `Entry 'method' not found in dictionary system/fvSchemes.wallDist`. |
| **AUD-06** | `openfoam_bridge.py:380`, `solver_generator.py:285` | `controlDict` `forceCoeffs` Center of Rotation | **FAIL** | `forceCoeffs` dictionary omits `CofR (x y z);`. Solver aborts: `Entry 'origin' not found in dictionary controlDict.functions.forceCoeffs`. |
| **AUD-07** | `openfoam_bridge.py:105`, `case_builder.py:189` | `system/blockMeshDict` 3D Symmetry & Topology | **PASS** | 3D hexahedral enclosure, 8 vertices, pure `type symmetry;` boundaries, 0 non-planar faces. Verified in container. |
| **AUD-08** | `openfoam_bridge.py:180` | `snappyHexMesh` Geometric Layer Progression | **PASS** | $h_1 = 9.4\times 10^{-6}\text{ m}, h_{28} = 4.11\times 10^{-4}\text{ m}$, consistent progression without 9x conflict. |
| **AUD-09** | `openfoam_bridge.py:480-575` | Initial & Boundary Fields `0/U`, `0/p`, `0/k`, `0/omega`, `0/nut` | **PASS** | Valid dimensions, exact units, compliant wall functions (`kLowReWallFunction`, `omegaWallFunction`, `nutkWallFunction`). |
| **AUD-10** | `openfoam_pipeline.py:151-216` | Synthetic Simulation Fallback Tagging | **WARNING** | Synthetic runner marks cases `PASSED` and writes fake residuals without labeling provenance. Must be explicitly tagged `SYNTHETIC_SIMULATION`. |

---

## 3. Detailed Audit Findings & Evidence

### 3.1 Binary Name Mismatch (`AUD-01`)
- **Location:** `openfoam_pipeline.py:222`
- **Existing Code:**
  ```python
  commands = [
      ("BLOCKMESH", ["blockMesh"]),
      ("SURFACEFEATURES", ["surfaceFeatures"]),
      ("SNAPPY", ["snappyHexMesh", "-overwrite"]),
      ("CHECKMESH", ["checkMesh"]),
      ("SOLVING", ["simpleFoam"])
  ]
  ```
- **Evidence:** Running `which surfaceFeatures` inside `opencfd/openfoam-default:2212` yields exit code 1 (`not found`). Sourcing OpenFOAM v2212 shows the binary is `/usr/lib/openfoam/openfoam2212/platforms/linux64GccDPInt32Opt/bin/surfaceFeatureExtract`.
- **Required Correction:** Replace `surfaceFeatures` with `surfaceFeatureExtract`.

---

### 3.2 Feature Extraction Dictionary Name & Syntax (`AUD-02`)
- **Location:** `solver_generator.py:101`, `case_builder.py:190`
- **Existing Output:** File written to `system/surfaceFeaturesDict` with content:
  ```
  FoamFile { ... object surfaceFeaturesDict; }
  surfaces ("wing.stl" { includedAngle 150; });
  ```
- **Evidence:** `surfaceFeatureExtract` in OpenCFD v2212 ignores `surfaceFeaturesDict` and looks strictly for `system/surfaceFeatureExtractDict`. Moreover, v2212 syntax requires:
  ```
  wing.stl
  {
      extractionMethod    extractFromSurface;
      includedAngle       150;
      writeObj            yes;
  }
  ```
- **Required Correction:** Rename output dictionary to `system/surfaceFeatureExtractDict` and update syntax to OpenCFD v2212 specification.

---

### 3.3 Literal Double-Curly Braces in `fvSchemes` and `fvSolution` (`AUD-03`)
- **Location:** `solver_generator.py:313-428`
- **Existing Code:** Python multi-line raw strings were authored with `{{` and `}}` (intended as format escape characters), but returned directly as non-f-strings (`def generate_fv_schemes() -> str:`). Consequently, the actual files on disk contain literal `{{` and `}}`.
- **Evidence:** Running `checkMesh` in the container against the generated case failed immediately:
  ```
  --> FOAM FATAL IO ERROR: (openfoam-2212 patch=230110)
  Found { but expected }
  file: system/fvSchemes at line 9.
  FOAM exiting
  ```
- **Required Correction:** Replace `{{` and `}}` with single `{` and `}` in `solver_generator.py` and `openfoam_bridge.py`.

---

### 3.4 Incompressible Solver Turbulence Properties Mismatch (`AUD-04`)
- **Location:** `case_builder.py:213`, `openfoam_bridge.py:420`
- **Existing Code:** Writes `constant/momentumTransport` with `simulationType RAS; RAS { model kOmegaSST; }`.
- **Evidence:** While compressible solvers (`rhoSimpleFoam`, `rhoPimpleFoam`) in v2212 transitioned to `momentumTransport`, the standard incompressible solver `simpleFoam` in OpenCFD v2212 still requires `constant/turbulenceProperties`:
  ```
  --> FOAM FATAL ERROR: (openfoam-2212 patch=230110)
  cannot find file "/case/constant/turbulenceProperties"
  FOAM exiting
  ```
- **Required Correction:** Write both `constant/turbulenceProperties` (for `simpleFoam` compatibility) and `constant/momentumTransport`, with standard v2212 syntax:
  ```
  simulationType  RAS;
  RAS
  {
      RASModel        kOmegaSST;
      turbulence      on;
      printCoeffs     on;
  }
  ```

---

### 3.5 Missing `wallDist` in `fvSchemes` (`AUD-05`)
- **Location:** `solver_generator.py:313`, `openfoam_bridge.py`
- **Evidence:** Running `simpleFoam -dry-run` in the container failed with:
  ```
  --> FOAM FATAL IO ERROR: (openfoam-2212 patch=230110)
  Entry 'method' not found in dictionary "/case/system/fvSchemes.wallDist"
  ```
- **Required Correction:** Add the standard `wallDist` entry to `system/fvSchemes`:
  ```
  wallDist
  {
      method          meshWave;
  }
  ```

---

### 3.6 `controlDict` `forceCoeffs` Center of Rotation (`AUD-06`)
- **Location:** `openfoam_bridge.py:380`
- **Existing Code:** Omits the `CofR` keyword from `functions.forceCoeffs`.
- **Evidence:** Running `simpleFoam -dry-run` failed with:
  ```
  --> FOAM FATAL IO ERROR: (openfoam-2212 patch=230110)
  Entry 'origin' not found in dictionary "/case/system/controlDict.functions.forceCoeffs"
  ```
  OpenCFD v2212's `libforces.so` expects `CofR (x y z);` (representing the moment reference center / origin).
- **Required Correction:** Add `CofR ({chord_m * 0.25} 0 0);` to `forceCoeffs` in `controlDict`.

---

### 3.7 Verified Passing Features (`AUD-07` through `AUD-09`)
- **Mesh Topology (`blockMesh`):** Executed cleanly in the container:
  ```
  boundingBox: (-15 -15 -1) (26 15 1)
  nPoints: 106323, nCells: 98400, nFaces: 302960
  All patches (inlet, outlet, topBottomFrontBack) topology: OK.
  Mesh non-orthogonality Max: 0, Skewness: 4.26e-14.
  Mesh OK.
  ```
- **Prism Layer Heights:** Sourced from `engineering_core`, eliminating the legacy 9x layer thickness discrepancy.
- **Initial Fields:** Verified dimensions and boundary types for `0/U`, `0/p`, `0/k`, `0/omega`, and `0/nut`.

---

## 4. Prioritized Action Plan for Implementation

Before enabling the real Docker container execution adapter (Phase 3 of Task 06), the following fixes must be applied:

1. **[P0] Fix Double-Braces in Dictionaries (`AUD-03`):**
   - Correct `generate_fv_schemes` and `generate_fv_solution` in `solver_generator.py` and `openfoam_bridge.py` so valid ASCII dictionary syntax is generated.
2. **[P0] Add `constant/turbulenceProperties` (`AUD-04`):**
   - Ensure `case_builder.py` writes `constant/turbulenceProperties` with `RASModel kOmegaSST;` for `simpleFoam`.
3. **[P0] Add `wallDist` to `fvSchemes` (`AUD-05`):**
   - Add `wallDist { method meshWave; }` to `fvSchemes`.
4. **[P0] Add `CofR` to `controlDict` (`AUD-06`):**
   - Include `CofR ({chord_m * 0.25} 0 0);` in `generate_control_dict_v2212`.
5. **[P0] Align Feature Extractor Name & Dict (`AUD-01`, `AUD-02`):**
   - In `openfoam_pipeline.py`, change command `surfaceFeatures` to `surfaceFeatureExtract`.
   - In `solver_generator.py` and `case_builder.py`, generate `system/surfaceFeatureExtractDict`.
6. **[P1] Provenance & Synthetic Flagging (`AUD-10`):**
   - Ensure `CASE_EXECUTION_STATE` and database records store `execution_engine: "REAL_OPENFOAM_DOCKER"` vs `"SYNTHETIC_SIMULATION"`.

---

## 5. Audit Conclusion

The OpenFOAM v2212 case generation has clear root causes identified for all parser and solver errors discovered via live container testing. No project source files have been altered during this audit.

Awaiting review of this report before proceeding to code corrections.

