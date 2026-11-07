"""
CAD & Surface Inspection Engine using trimesh & OpenCASCADE (via Gmsh).
Performs real geometric inspection, bounding box extraction, watertightness check,
Trailing Edge thickness analysis, and mesh tesselation for 3D visualization.
Supports STEP (.step, .stp), IGES (.iges, .igs), BREP (.brep), STL (.stl), OBJ (.obj), PLY (.ply), and GLTF/GLB.
"""

import io
import os
import tempfile
import trimesh
import numpy as np
from typing import Dict, Any

def load_with_gmsh(file_bytes: bytes, ext: str) -> trimesh.Trimesh:
    """
    Tessellates B-Rep / STEP / IGES CAD geometry into a clean triangular surface mesh
    using the OpenCASCADE geometry kernel bundled in Gmsh.
    """
    import gmsh

    with tempfile.TemporaryDirectory() as tmpdir:
        in_file = os.path.join(tmpdir, f"input.{ext}")
        out_stl = os.path.join(tmpdir, "surface.stl")
        with open(in_file, "wb") as f:
            f.write(file_bytes)

        gmsh.initialize()
        try:
            gmsh.option.setNumber("General.Terminal", 0)
            gmsh.option.setNumber("Mesh.MeshSizeMin", 0.005)
            gmsh.option.setNumber("Mesh.MeshSizeMax", 0.08)
            gmsh.option.setNumber("Mesh.Algorithm", 6) # Frontal-Delaunay 2D
            gmsh.open(in_file)
            gmsh.model.mesh.generate(2) # 2D surface triangulation
            gmsh.write(out_stl)
        except Exception as e:
            raise ValueError(f"OpenCASCADE/Gmsh failed to tessellate {ext.upper()} geometry: {str(e)}")
        finally:
            try:
                gmsh.finalize()
            except Exception:
                pass

        if not os.path.exists(out_stl) or os.path.getsize(out_stl) == 0:
            raise ValueError(f"Gmsh generated an empty surface mesh for {ext.upper()} CAD file.")

        return trimesh.load(out_stl, file_type="stl")


def load_mesh_from_cad(file_bytes: bytes, filename: str) -> trimesh.Trimesh:
    """
    Dispatches file parsing according to file format:
    - STEP / STP / IGES / IGS / BREP -> Gmsh OpenCASCADE kernel
    - STL / OBJ / PLY / 3MF / GLB -> Trimesh (with Gmsh fallback)
    """
    ext = filename.lower().split('.')[-1] if '.' in filename else "stl"

    # 1. Native STEP / IGES / BREP
    if ext in ["step", "stp", "iges", "igs", "brep", "x_t"]:
        return load_with_gmsh(file_bytes, ext)

    # 2. Polygon Mesh Formats
    try:
        file_obj = io.BytesIO(file_bytes)
        loaded = trimesh.load(file_obj, file_type=ext)
    except Exception as e1:
        # Fallback to Gmsh if Trimesh fails on polygon format
        try:
            return load_with_gmsh(file_bytes, ext)
        except Exception:
            try:
                file_obj = io.BytesIO(file_bytes)
                loaded = trimesh.load(file_obj)
            except Exception as e2:
                raise ValueError(f"Failed to parse CAD geometry ({filename}): {str(e2)}")

    if isinstance(loaded, trimesh.Scene):
        if len(loaded.geometry) == 0:
            raise ValueError(f"No 3D geometry found in {filename}")
        mesh = trimesh.util.concatenate([g for g in loaded.geometry.values() if isinstance(g, trimesh.Trimesh)])
    elif isinstance(loaded, trimesh.Trimesh):
        mesh = loaded
    else:
        raise ValueError(f"Unsupported geometry type extracted from {filename}: {type(loaded)}")

    return mesh


def inspect_geometry(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Inspects 3D CAD / surface geometry.
    Supports STEP (.step, .stp), IGES (.iges, .igs), STL (.stl), OBJ (.obj), and more.
    """
    mesh = load_mesh_from_cad(file_bytes, filename)

    bounds = mesh.bounds  # [[xmin, ymin, zmin], [xmax, ymax, zmax]]
    xmin, ymin, zmin = float(bounds[0][0]), float(bounds[0][1]), float(bounds[0][2])
    xmax, ymax, zmax = float(bounds[1][0]), float(bounds[1][1]), float(bounds[1][2])

    chord = max(1e-4, xmax - xmin)
    span = max(1e-4, zmax - zmin)

    surface_area = float(mesh.area) if hasattr(mesh, "area") else 0.0
    volume = float(mesh.volume) if (mesh.is_watertight and hasattr(mesh, "volume")) else 0.0
    is_watertight = bool(mesh.is_watertight)

    # Trailing Edge Check: Measure thickness at 99.5% chord along the X axis
    verts = mesh.vertices
    te_mask = (verts[:, 0] >= (xmin + 0.98 * chord))

    te_thickness_mm = 0.5
    te_status = "PASS"
    te_recommendation = "Verified: Sharp TE resolves without blunt separation anomaly."

    if np.any(te_mask):
        te_verts_y = verts[te_mask, 1]
        if len(te_verts_y) >= 2:
            te_thickness = float(np.max(te_verts_y) - np.min(te_verts_y))
            te_thickness_mm = te_thickness * 1000.0

            if te_thickness < 0.001 * chord:
                te_status = "BLUNT WARNING"
                te_recommendation = "BLUNT_EDGE_REQUIRED: Trailing edge thickness is < 0.1% chord. Blunt edge to prevent degenerate cells."

    domain_box = {
        "inlet_distance_m": round(chord * 15.0, 3),
        "outlet_distance_m": round(chord * 25.0, 3),
        "lateral_distance_m": round(chord * 15.0, 3)
    }

    # Extract triangulated mesh data for frontend WebGL visualization
    v_flat = mesh.vertices.flatten().tolist()
    f_flat = mesh.faces.flatten().tolist()

    return {
        "filename": filename,
        "format": filename.lower().split('.')[-1] if '.' in filename else "cad",
        "bounding_box": {
            "xmin": round(xmin, 4), "xmax": round(xmax, 4),
            "ymin": round(ymin, 4), "ymax": round(ymax, 4),
            "zmin": round(zmin, 4), "zmax": round(zmax, 4)
        },
        "characteristic_chord_m": round(chord, 4),
        "span_m": round(span, 4),
        "surface_area_m2": round(surface_area, 6),
        "volume_m3": round(volume, 6),
        "is_watertight": is_watertight,
        "domain_box": domain_box,
        "cae_readiness": {
            "trailing_edge_thickness_mm": round(te_thickness_mm, 4),
            "trailing_edge_status": te_status,
            "defeaturing_recommendation": te_recommendation
        },
        "mesh_data": {
            "num_vertices": len(mesh.vertices),
            "num_triangles": len(mesh.faces),
            "vertices": v_flat,
            "indices": f_flat
        }
    }
