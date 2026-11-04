import re
import math
from typing import Dict, Any, List

def parse_vtk_polydata(file_content: str) -> Dict[str, Any]:
    """
    Parses an ASCII legacy VTK POLYDATA file (commonly produced by foamToVTK).
    Extracts:
    - Points coordinates [x, y, z, ...]
    - Polygon / triangle face connectivity indices
    - PointData scalar fields (e.g., p, U, Cp)
    """
    lines = file_content.splitlines()
    num_points = 0
    points: List[float] = []
    faces: List[int] = []
    
    point_data_count = 0
    scalars: Dict[str, List[float]] = {}
    current_scalar_name = None
    reading_scalars = False
    reading_points = False
    reading_polygons = False
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue
            
        parts = line.split()
        
        # 1. POINTS header
        if parts[0] == "POINTS":
            num_points = int(parts[1])
            reading_points = True
            reading_polygons = False
            reading_scalars = False
            i += 1
            while i < len(lines) and len(points) < num_points * 3:
                p_line = lines[i].strip()
                if p_line:
                    for val in p_line.split():
                        try:
                            points.append(float(val))
                        except ValueError:
                            pass
                i += 1
            continue

        # 2. POLYGONS header
        elif parts[0] == "POLYGONS":
            num_polys = int(parts[1])
            total_ints = int(parts[2])
            reading_polygons = True
            reading_points = False
            reading_scalars = False
            i += 1
            while i < len(lines) and len(faces) < total_ints:
                f_line = lines[i].strip()
                if f_line:
                    for val in f_line.split():
                        try:
                            faces.append(int(val))
                        except ValueError:
                            pass
                i += 1
            continue

        # 3. POINT_DATA header
        elif parts[0] == "POINT_DATA":
            point_data_count = int(parts[1])
            reading_points = False
            reading_polygons = False
            i += 1
            continue

        # 4. SCALARS / FIELD definition
        elif parts[0] == "SCALARS":
            current_scalar_name = parts[1]
            scalars[current_scalar_name] = []
            reading_scalars = True
            # Skip the next LOOKUP_TABLE line
            i += 1
            if i < len(lines) and lines[i].strip().startswith("LOOKUP_TABLE"):
                i += 1
            while i < len(lines) and len(scalars[current_scalar_name]) < point_data_count:
                s_line = lines[i].strip()
                if s_line.startswith("SCALARS") or s_line.startswith("VECTORS") or s_line.startswith("FIELD"):
                    break
                if s_line:
                    for val in s_line.split():
                        try:
                            scalars[current_scalar_name].append(float(val))
                        except ValueError:
                            pass
                i += 1
            continue

        # 5. VECTORS field (e.g. U vector -> compute magnitude |U|)
        elif parts[0] == "VECTORS":
            current_vector_name = parts[1]
            mag_name = f"{current_vector_name}_magnitude"
            scalars[mag_name] = []
            i += 1
            vec_components: List[float] = []
            while i < len(lines) and len(scalars[mag_name]) < point_data_count:
                v_line = lines[i].strip()
                if v_line.startswith("SCALARS") or v_line.startswith("VECTORS") or v_line.startswith("FIELD"):
                    break
                if v_line:
                    for val in v_line.split():
                        try:
                            vec_components.append(float(val))
                            if len(vec_components) == 3:
                                mag = math.sqrt(vec_components[0]**2 + vec_components[1]**2 + vec_components[2]**2)
                                scalars[mag_name].append(round(mag, 4))
                                vec_components = []
                        except ValueError:
                            pass
                i += 1
            continue

        i += 1

    # Convert polygon stream [n, v1, v2, v3, n, v1, v2, v3, ...] to pure triangle index list
    triangle_indices: List[int] = []
    idx = 0
    while idx < len(faces):
        vert_count = faces[idx]
        idx += 1
        poly_verts = faces[idx:idx + vert_count]
        idx += vert_count
        # Fan triangulation
        for k in range(1, len(poly_verts) - 1):
            triangle_indices.extend([poly_verts[0], poly_verts[k], poly_verts[k + 1]])

    # Calculate Cp if p exists (Cp = (p - p_inf) / (0.5 * rho * U_inf^2))
    p_field = scalars.get("p", None)
    if p_field:
        p_inf = 0.0
        q_inf = 0.5 * 1.225 * (40.0 ** 2) # ~980 Pa
        cp_field = [round((p_val - p_inf) / q_inf, 4) for p_val in p_field]
        scalars["Cp"] = cp_field

    # Compute min/max stats for each scalar
    scalar_stats = {}
    for name, arr in scalars.items():
        if arr:
            scalar_stats[name] = {
                "min": min(arr),
                "max": max(arr),
                "count": len(arr)
            }

    return {
        "num_vertices": len(points) // 3,
        "num_triangles": len(triangle_indices) // 3,
        "vertices": points,
        "indices": triangle_indices,
        "scalars": scalars,
        "scalar_stats": scalar_stats
    }

def generate_sample_naca0012_vtk(chord_m: float = 1.0, span_m: float = 2.0, u_inf: float = 40.0) -> str:
    """Generates a realistic valid VTK POLYDATA file representing a NACA 0012 aerofoil surface with p and U scalar fields."""
    points = []
    faces = []
    p_vals = []
    u_vals = []
    
    # 20 chordwise stations, 5 spanwise stations
    n_chord = 16
    n_span = 4
    q_inf = 0.5 * 1.225 * (u_inf ** 2)
    
    for j in range(n_span):
        z = -span_m / 2.0 + (j / (n_span - 1)) * span_m
        for i in range(n_chord):
            # Cosine spacing
            theta = (i / (n_chord - 1)) * math.pi
            x = (chord_m / 2.0) * (1.0 - math.cos(theta))
            # NACA 0012 thickness formula
            t = 0.12 * chord_m * (
                0.2969 * math.sqrt(max(0.0, x / chord_m))
                - 0.1260 * (x / chord_m)
                - 0.3516 * ((x / chord_m) ** 2)
                + 0.2843 * ((x / chord_m) ** 3)
                - 0.1015 * ((x / chord_m) ** 4)
            )
            # Upper surface
            points.extend([round(x, 4), round(t, 4), round(z, 4)])
            
            # Physics distribution: high stagnation pressure at leading edge (x=0), suction peak around x/c = 0.12
            xc = x / chord_m
            if xc < 0.05:
                # Stagnation zone
                cp = 1.0 - (xc / 0.05) * 1.8
                vel = u_inf * (xc / 0.05) * 1.15
            else:
                # Recovery zone
                cp = -0.8 + (xc - 0.05) * 0.8
                vel = u_inf * (1.25 - xc * 0.35)
                
            p = cp * q_inf
            p_vals.append(round(p, 2))
            u_vals.append([round(vel, 2), 0.0, 0.0])

    num_pts = (n_chord * n_span)
    
    # Face connectivity
    for j in range(n_span - 1):
        for i in range(n_chord - 1):
            p1 = j * n_chord + i
            p2 = p1 + 1
            p3 = (j + 1) * n_chord + i + 1
            p4 = (j + 1) * n_chord + i
            faces.append([p1, p2, p3])
            faces.append([p1, p3, p4])

    lines = [
        "# vtk DataFile Version 3.0",
        "OpenFOAM foamToVTK Surface Mesh Output - NACA 0012",
        "ASCII",
        "DATASET POLYDATA",
        f"POINTS {num_pts} float"
    ]
    
    # Write vertices
    for idx in range(0, len(points), 3):
        lines.append(f"{points[idx]} {points[idx+1]} {points[idx+2]}")
        
    # Write polygons
    lines.append(f"POLYGONS {len(faces)} {len(faces) * 4}")
    for f in faces:
        lines.append(f"3 {f[0]} {f[1]} {f[2]}")
        
    # Write PointData
    lines.append(f"POINT_DATA {num_pts}")
    lines.append("SCALARS p float 1")
    lines.append("LOOKUP_TABLE default")
    for p in p_vals:
        lines.append(f"{p}")
        
    lines.append("VECTORS U float")
    for u in u_vals:
        lines.append(f"{u[0]} {u[1]} {u[2]}")

    return "\n".join(lines)
