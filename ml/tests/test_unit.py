import pytest
import sys
import os

# Add ml to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.features_phishing import url_structural_features
from scoring.risk import assign_severity, compute_risk_score
from phishing.fusion import combined_phishing_score

class DummyMetaModel:
    def predict_proba(self, x):
        import numpy as np
        # Disagreement is the third feature (index 2).
        # We simulate the evasion test logic where high disagreement boosts the phishing probability.
        # x is [[text_score, structural_score, disagreement]]
        text_score = x[0, 0]
        structural_score = x[0, 1]
        disagreement = x[0, 2]
        
        # Base probability is just the average of the two scores for dummy purposes.
        # Evasion boost: If disagreement is high, increase probability.
        prob = (text_score + structural_score) / 2.0 + (disagreement * 0.5)
        # return mock output format for predict_proba
        return np.array([[1 - prob, prob]])

def dummy_meta_model():
    return DummyMetaModel()

def test_url_structural_features_flags_ip_literal():
    feats = url_structural_features("http://192.168.10.4/login")
    assert feats["is_ip_literal"] is True
 
def test_assign_severity_boundaries():
    assert assign_severity(0.90) == "critical"
    assert assign_severity(0.70) == "high"
    assert assign_severity(0.50) == "medium"
    assert assign_severity(0.10) == "low"
 
def test_risk_score_correlation_bonus_applied():
    base = compute_risk_score(0.5, 0.5, correlated_within_window=False)
    boosted = compute_risk_score(0.5, 0.5, correlated_within_window=True)
    assert boosted > base
 
def test_fusion_flags_evasive_combination():
    # Clean text (low text_score) + suspicious URL (high structural_score)
    # should still be pushed up by the disagreement term.
    score_aligned = combined_phishing_score(0.1, 0.1, dummy_meta_model())
    score_evasive = combined_phishing_score(0.1, 0.9, dummy_meta_model())
    assert score_evasive > score_aligned
