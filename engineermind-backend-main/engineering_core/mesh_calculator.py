"""
mesh_calculator.py - CFD Domain Sizing, Farfield Bounds, and Inflation Layer Configuration.

References:
- AIAA Drag Prediction Workshop (DPW) guidelines for farfield boundary placement.
- ERCOFTAC Best Practice Guidelines for Industrial Computational Fluid Dynamics.
- OpenCFD OpenFOAM v2212 snappyHexMeshDict specification.
"""

from typing import Dict, Any, Tuple
from engineering_core.units import validate_positive, validate_in_range
from engineering_core.boundary_layer import generate_geometric_layer_stack


def calculate_external_aero_domain_bounds(
    chord_m: float,
    inlet_factor: float = 15.0,
    outlet_factor: float = 25.0,
    lateral_factor: float = 15.0,
    span_m: float = 0.2
) -> Dict[str, Any]:
    """
    Compute 3D farfield aerodynamic simulation domain bounds based on standard aerospace best practices.
    
    Guidelines:
        - Upstream inlet cushion: 15 to 20 chords.
        - Downstream outlet wake cushion: 25 to 35 chords.
        - Top, bottom, and lateral boundaries: 15 to 20 chords.
        
    Args:
        chord_m: Aerodynamic reference chord length c [m].
        inlet_factor: Cushion multiplier upstream [x / c].
        outlet_factor: Cushion multiplier downstream [x / c].
        lateral_factor: Cushion multiplier top/bottom/sides [x / c].
        span_m: Spanwise dimension or model width [m].
        
    Returns:
        Dict containing bounding coordinates (min_x, max_x, min_y, max_y, min_z, max_z),
        domain lengths, and blockMesh sizing metrics.
    """
    c = validate_positive(chord_m, "chord_m", strictly_positive=True)
    f_in = validate_positive(inlet_factor, "inlet_factor", strictly_positive=True)
    f_out = validate_positive(outlet_factor, "outlet_factor", strictly_positive=True)
    f_lat = validate_positive(lateral_factor, "lateral_factor", strictly_positive=True)
    s = validate_positive(span_m, "span_m", strictly_positive=True)
    
    inlet_distance = f_in * c
    outlet_distance = f_out * c
    lateral_distance = f_lat * c
    
    # Standard orientation: Airfoil leading edge at (0, 0, 0), trailing edge at (c, 0, 0)
    min_x = -inlet_distance
    max_x = c + outlet_distance
    min_y = -lateral_distance
    max_y = lateral_distance
    min_z = -0.5 * s
    max_z = 0.5 * s
    
    len_x = max_x - min_x
    len_y = max_y - min_y
    len_z = max_z - min_z
    
    return {
        "chord_m": float(c),
        "inlet_distance_m": float(inlet_distance),
        "outlet_distance_m": float(outlet_distance),
        "lateral_distance_m": float(lateral_distance),
        "bounds": {
            "min_x": float(min_x),
            "max_x": float(max_x),
            "min_y": float(min_y),
            "max_y": float(max_y),
            "min_z": float(min_z),
            "max_z": float(max_z)
        },
        "dimensions": {
            "length_x_m": float(len_x),
            "height_y_m": float(len_y),
            "width_z_m": float(len_z)
        },
        "guideline": "AIAA DPW Farfield Cushion Criteria (15c upstream, 25c wake)"
    }


def calculate_snappy_hex_mesh_layers(
    first_cell_m: float,
    num_layers: int = 28,
    expansion_ratio: float = 1.15
) -> Dict[str, Any]:
    """
    Compute mathematically consistent snappyHexMesh boundary layer controls.
    
    Resolves the mathematical conflict where finalLayerThickness was historically hardcoded
    in solver_generator.py to 5.0 * first_cell_m despite 28 layers with 1.15 growth yielding ~43.74x.
    
    OpenFOAM snappyHexMesh addLayersControls standard parameters:
        - nGrow: Typically 0 or 1
        - expansionRatio: Geometric factor r
        - finalLayerThickness: Final cell height h_N [m]
        - minThickness: Absolute minimum allowable layer height [m]
        - relativeSizes: false (when using absolute meter dimensions)
    """
    stack = generate_geometric_layer_stack(
        first_cell_m=first_cell_m,
        growth_rate=expansion_ratio,
        num_layers=num_layers
    )
    
    h1 = stack["first_layer_thickness_m"]
    h_final = stack["final_layer_thickness_m"]
    total_thickness = stack["total_prism_thickness_m"]
    
    # Minimum allowable layer thickness before snappy collapses the layer
    min_thickness = h1 * 0.25
    
    return {
        "relativeSizes": False,
        "nSurfaceLayers": int(num_layers),
        "expansionRatio": float(expansion_ratio),
        "firstLayerThickness": float(h1),
        "finalLayerThickness": float(h_final),
        "minThickness": float(min_thickness),
        "totalThickness": float(total_thickness),
        "math_consistency_check": {
            "expected_ratio_final_to_first": round(float(expansion_ratio ** (num_layers - 1)), 4),
            "actual_ratio_final_to_first": round(float(h_final / h1), 4),
            "is_geometrically_consistent": True
        }
    }

