from dataclasses import dataclass
 
@dataclass
class RiskWeights:
    w_phishing: float = 0.45
    w_anomaly: float = 0.40
    w_correlation_bonus: float = 0.15
 
def compute_risk_score(
    phishing_score: float,
    anomaly_score: float,
    correlated_within_window: bool,
    weights: RiskWeights = RiskWeights(),
) -> float:
    base = (
        weights.w_phishing * phishing_score
        + weights.w_anomaly * anomaly_score
    )
    bonus = weights.w_correlation_bonus if correlated_within_window else 0.0
    return min(base + bonus, 1.0)
 
def assign_severity(risk_score: float) -> str:
    if risk_score >= 0.85:
        return "critical"
    elif risk_score >= 0.65:
        return "high"
    elif risk_score >= 0.40:
        return "medium"
    return "low"
