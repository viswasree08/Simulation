"""
Verified Knowledge Glossary Engine.
Authoritative, peer-reviewed aerothermal, CFD, and ASME V&V 20 definitions.
"""

from typing import Dict, Any, Optional

KNOWLEDGE_BASE: Dict[str, Dict[str, str]] = {
    "reynolds": {
        "term_id": "reynolds",
        "title": "Reynolds Number (Re)",
        "equation_latex": "Re = \\frac{\\rho U_\\infty c}{\\mu} = \\frac{U_\\infty c}{\\nu}",
        "definition": "Ratio of inertial forces to viscous forces within a fluid subjected to relative internal movement due to different fluid velocities.",
        "governing_conditions": "Governs boundary layer state (laminar, transitional, or turbulent). For aerofoils, Re > 5e5 is predominantly turbulent.",
        "failure_modes": "Underestimating Re leads to unphysical laminar separation bubble prediction or inaccurate drag polar estimation.",
        "reference": "Schlichting, H. (1979). Boundary-Layer Theory. McGraw-Hill."
    },
    "mach": {
        "term_id": "mach",
        "title": "Mach Number (Ma)",
        "equation_latex": "Ma = \\frac{U_\\infty}{a} = \\frac{U_\\infty}{\\sqrt{\\gamma R T}}",
        "definition": "Dimensionless quantity representing the ratio of flow velocity past a boundary to the local speed of sound in that medium.",
        "governing_conditions": "Ma < 0.3 satisfies incompressible formulation (density constant). Ma ≥ 0.3 requires compressible Navier-Stokes formulation.",
        "failure_modes": "Using incompressible solvers above Ma 0.3 ignores thermodynamic compressibility, shock formation, and wave drag.",
        "reference": "Anderson, J. D. (2010). Fundamentals of Aerodynamics. McGraw-Hill."
    },
    "y_plus": {
        "term_id": "y_plus",
        "title": "Non-Dimensional Wall Distance (y+)",
        "equation_latex": "y^+ = \\frac{y u_\\tau}{\\nu} = \\frac{y \\sqrt{\\tau_w / \\rho}}{\\nu}",
        "definition": "Non-dimensional distance from the solid wall to the first grid node, measuring the local boundary layer mesh resolution.",
        "governing_conditions": "y+ ≤ 1 for Low-Re resolved viscous sublayer. 30 < y+ < 300 for empirical log-law wall functions.",
        "failure_modes": "Buffer layer placement (5 < y+ < 30) violates both laminar and turbulent log-law assumptions, generating massive skin-friction errors.",
        "reference": "Wilcox, D. C. (2006). Turbulence Modeling for CFD. DCW Industries."
    },
    "k_omega_sst": {
        "term_id": "k_omega_sst",
        "title": "Menter Shear Stress Transport (k-ω SST)",
        "equation_latex": "\\frac{\\partial(\\rho k)}{\\partial t} + \\nabla \\cdot (\\rho \\mathbf{u} k) = \\tilde{P}_k - \\beta^* \\rho k \\omega + \\nabla \\cdot [(\\mu + \\sigma_k \\mu_t)\\nabla k]",
        "definition": "Two-equation eddy-viscosity model blending standard k-ω in the sublayer with k-ε in the free stream via a hyperbolic blending function.",
        "governing_conditions": "Preferred standard for adverse pressure gradient flows, boundary layer separation, and aerodynamic drag predictions.",
        "failure_modes": "Excessive turbulent kinetic energy generation in stagnation regions without Kato-Launder limiter.",
        "reference": "Menter, F. R. (1994). Two-Equation Eddy-Viscosity Turbulence Models for Engineering Applications. AIAA Journal."
    },
    "linear_upwind": {
        "term_id": "linear_upwind",
        "title": "Bounded Linear Upwind Discretization",
        "equation_latex": "\\phi_f = \\phi_U + \\nabla \\phi_U \\cdot (\\vec{x}_f - \\vec{x}_U)",
        "definition": "Second-order spatial discretization scheme with gradient reconstruction from the upwind cell center, enforcing boundedness via TVD slope limiters.",
        "governing_conditions": "Mandatory for production aerodynamic CFD to eliminate first-order numerical diffusion while preventing unphysical oscillations.",
        "failure_modes": "First-order upwind smears boundary layers and trailing edge wake vortices; unbounded second-order schemes may produce dispersion ripples.",
        "reference": "Versteeg, H. K., & Malalasekera, W. (2007). An Introduction to Computational Fluid Dynamics. Pearson."
    },
    "blockage_ratio": {
        "term_id": "blockage_ratio",
        "title": "Wind Tunnel Blockage Ratio (B)",
        "equation_latex": "B = \\frac{A_{\\text{model}}}{A_{\\text{domain}}} \\times 100\\%",
        "definition": "Ratio of the frontal projected cross-sectional area of the test model to the cross-sectional area of the farfield computational domain.",
        "governing_conditions": "Must remain below 1.5% to 3.0% for unbounded external aerodynamics simulations without requiring empirical blockage corrections.",
        "failure_modes": "Excessive blockage artificially accelerates bypass flow, increases suction peaks, and overpredicts lift and pressure drag.",
        "reference": "Barlow, J. B., Rae, W. H., & Pope, A. (1999). Low-Speed Wind Tunnel Testing. John Wiley & Sons."
    },
    "false_convergence": {
        "term_id": "false_convergence",
        "title": "False Convergence Diagnostic",
        "equation_latex": "\\Delta \\phi = \\phi^k - \\phi^{k-1} \\to 0 \\quad \\text{while} \\quad R(\\phi^k) = \\|A\\phi^k - b\\| > \\epsilon",
        "definition": "Condition where iterative solution updates become negligibly small while actual governing Navier-Stokes residuals remain stalled or elevated.",
        "governing_conditions": "Commonly occurs under severe under-relaxation (e.g., α_p < 0.1) or with inappropriate turbulence wall damping.",
        "failure_modes": "Accepting stalled solutions leads to inaccurate force polars and undetected flow separations masked by artificial numerical damping.",
        "reference": "Ferziger, J. H., & Peric, M. (2002). Computational Methods for Fluid Dynamics. Springer."
    },
    "roache_gci": {
        "term_id": "roache_gci",
        "title": "Roache Grid Convergence Index (GCI)",
        "equation_latex": "GCI_{\\text{fine}} = \\frac{F_s |\\epsilon_{21}|}{r^p - 1} \\times 100\\%, \\quad \\epsilon_{21} = \\left|\\frac{f_2 - f_1}{f_1}\\right|",
        "definition": "ASME V&V 20 standard metric quantifying spatial discretization uncertainty across systematically refined grid triplets.",
        "governing_conditions": "Requires consistent grid refinement ratio r ≥ 1.3 across at least 3 geometrically similar meshes.",
        "failure_modes": "Calculating GCI without verifying asymptotic convergence range (observed order p matching theoretical order) invalidates error bands.",
        "reference": "Roache, P. J. (1998). Verification and Validation in Computational Science and Engineering. Hermosa Publishers."
    }
}

def get_concept(term_id: str) -> Optional[Dict[str, str]]:
    """Retrieve concept definition from knowledge base."""
    return KNOWLEDGE_BASE.get(term_id)
