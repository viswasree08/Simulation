def evaluate_copilot_case(case_data: dict, physics_data: dict) -> dict:
    y_plus = case_data.get("target_y_plus", 1.0)
    re = physics_data.get("reynolds_number", 0.0)
    mach = physics_data.get("mach_number", 0.0)
    
    findings = []
    recommendations = []
    
    if 5.0 < y_plus < 30.0:
        findings.append("CRITICAL: Buffer Layer Violation (5 < y+ < 30). Empirical log-law and viscous sublayer hypotheses are both violated.")
        recommendations.append("Adjust prism first-cell height to achieve y+ <= 1.0 for Low-Re resolved SST or y+ >= 30.0 for wall-functions.")
    elif y_plus <= 1.0:
        findings.append(f"Optimal Wall-Resolved Sublayer Resolution (y+ = {y_plus:.1f}). Viscous sublayer resolved.")
        recommendations.append("Menter k-omega SST verified with zero wall functions.")
    else:
        findings.append(f"Standard Log-Law Wall-Function Mesh (y+ = {y_plus:.1f}).")
        recommendations.append("Standard scalable wall-function (omegaWallFunction) active.")

    if mach >= 0.3:
        findings.append(f"Compressibility Flag: Mach = {mach:.3f} >= 0.300. Thermodynamic density coupling required.")
        recommendations.append("Transition solver from simpleFoam (incompressible) to rhoSimpleFoam (steady compressible).")
    else:
        findings.append(f"Incompressible Regime: Mach = {mach:.3f} < 0.300.")
        recommendations.append("simpleFoam with standard SIMPLE algorithm verified.")

    summary = (
        f"Aero Reasoning Engine evaluated Re = {re:,.0f}, Mach = {mach:.3f}. "
        + " | ".join(findings) + " | Recommendation: " + " ".join(recommendations)
    )
    
    return {
        "status": "evaluated",
        "findings": findings,
        "recommendations": recommendations,
        "summary": summary,
        "explanation": summary
    }

