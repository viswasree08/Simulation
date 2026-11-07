import pytest
import os
import time
from fastapi.testclient import TestClient

from main import app
from models import SessionLocal, Project, SimulationCase
from cfd_visualizer import parse_vtk_polydata, generate_sample_naca0012_vtk

client = TestClient(app)

def test_e2e_openfoam_and_vtk_pipeline():
    """
    Automated Test Execution for Priority Task:
    1. Initialize automated test case with U=40 m/s, c=1.0 m, target y+=1.0.
    2. Run case directory generation & assert dictionaries have valid syntax without 2D empty patches.
    3. Test parse_simulation_log against a real sample log containing continuity and force monitors,
       verifying convergence status and rolling sigma(Cd) update accurately.
    4. Verify that POST /api/cfd/parse-results processes a test VTK polydata file and returns valid vertex color arrays.
    """
    print("\n--- TEST 1: Initializing Case with U=40 m/s, c=1.0m, y+=1.0 ---")
    p_resp = client.get("/api/projects")
    assert p_resp.status_code == 200
    projects = p_resp.json()
    assert len(projects) > 0
    project_id = projects[0]["id"]

    case_payload = {
        "name": "NACA0012_VTK_Verification_Run",
        "velocity_ms": 40.0,
        "chord_m": 1.0,
        "target_y_plus": 1.0,
        "solver": "OpenFOAM",
        "regime": "external_aerodynamics"
    }
    c_resp = client.post(f"/api/projects/{project_id}/cases", json=case_payload)
    assert c_resp.status_code == 200
    case_data = c_resp.json()
    case_id = case_data["id"]
    print(f"Created Case #{case_id}: {case_data['name']}")

    print("\n--- TEST 2: Validating 3D Case Generation (No 2D Empty Patches) ---")
    pipe_resp = client.post("/api/pipeline/create-case", json={"case_id": case_id, "stl_filename": "test_naca0012.stl"})
    assert pipe_resp.status_code == 200
    pipe_data = pipe_resp.json()
    assert pipe_data["dictionaries_valid"] is True
    
    case_path = pipe_data["case_path"]
    bm_path = os.path.join(case_path, "system", "blockMeshDict")
    with open(bm_path, "r", encoding="utf-8") as f:
        bm_text = f.read()
        assert "symmetry" in bm_text
        assert "empty" not in bm_text.lower()
        # Verify 3D domain bounds [-15c, 25c], [-15c, 15c], [-5c, 5c]
        assert "-15.0 -15.0 -5.0" in bm_text
        assert "25.0 -15.0 -5.0" in bm_text
        print("Verified blockMeshDict: 3D farfield enclosure confirmed; zero 2D empty patches.")

    cd_path = os.path.join(case_path, "system", "controlDict")
    with open(cd_path, "r", encoding="utf-8") as f:
        cd_text = f.read()
        assert "forceCoeffs" in cd_text
        assert "wing.*" in cd_text
        print("Verified controlDict: runtime forces monitor registered for wing.*.")

    print("\n--- TEST 3: Testing parse_simulation_log Against Real Continuity & Force Monitors ---")
    # Sample OpenFOAM log text with asymptotic decay and stable drag monitor
    sample_log = """
    # SimpleFoam Solver Convergence Run
    Time = 100
    smoothSolver:  Solving for Ux, Initial residual = 0.045, Final residual = 0.0034
    GAMG:  Solving for p, Initial residual = 0.12, Final residual = 0.00042
    iter 100 continuity 4.2e-4 Cd 0.00920
    iter 200 continuity 1.5e-4 Cd 0.00865
    iter 300 continuity 4.8e-5 Cd 0.00847
    iter 400 continuity 1.1e-5 Cd 0.00845
    iter 500 continuity 7.9e-6 Cd 0.00845
    """
    audit_resp = client.post(
        f"/api/cases/{case_id}/audit-log",
        files={"file": ("log.simpleFoam", sample_log.encode("utf-8"), "text/plain")}
    )
    assert audit_resp.status_code == 200
    audit_res = audit_resp.json()
    assert audit_res["is_converged"] is True
    assert "PASSED" in audit_res["diagnostic_flag"]
    assert audit_res["final_continuity"] <= 1e-4
    assert audit_res["drag_std_dev"] < 1e-4
    print(f"Verified Diagnostic Log Parser: Flag = '{audit_res['diagnostic_flag']}' | Final Cont = {audit_res['final_continuity']} | Drag std = {audit_res['drag_std_dev']:.6f}")

    print("\n--- TEST 4: Validating Real VTK PolyData Ingestion API ---")
    sample_vtk_text = generate_sample_naca0012_vtk(chord_m=1.0, span_m=2.0, u_inf=40.0)
    assert len(sample_vtk_text) > 100
    assert "DATASET POLYDATA" in sample_vtk_text

    vtk_resp = client.post(
        "/api/cfd/parse-results",
        files={"file": ("naca0012_surface.vtk", sample_vtk_text.encode("utf-8"), "application/octet-stream")}
    )
    assert vtk_resp.status_code == 200
    vtk_data = vtk_resp.json()
    
    assert vtk_data["num_vertices"] > 0
    assert vtk_data["num_triangles"] > 0
    assert len(vtk_data["vertices"]) == vtk_data["num_vertices"] * 3
    assert len(vtk_data["indices"]) == vtk_data["num_triangles"] * 3
    assert "p" in vtk_data["scalars"]
    assert "Cp" in vtk_data["scalars"]
    assert "U_magnitude" in vtk_data["scalars"]
    
    cp_stats = vtk_data["scalar_stats"]["Cp"]
    assert cp_stats["min"] < 0.0 # Suction peak
    assert cp_stats["max"] > 0.5 # Stagnation pressure
    print(f"Verified VTK Ingestion API: Parsed {vtk_data['num_vertices']} vertices, {vtk_data['num_triangles']} triangles.")
    print(f"Verified Scalar Arrays: {vtk_data['available_fields']}")
    print(f"Surface Cp Range: [{cp_stats['min']:.3f}, {cp_stats['max']:.3f}]")

    print("\n>>> All Automated End-to-End OpenFOAM & VTK Tests PASSED! <<<")

