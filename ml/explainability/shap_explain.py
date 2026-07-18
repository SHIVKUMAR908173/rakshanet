import pandas as pd
import shap
 
STRUCTURAL_FEATURES = [
    "is_ip_literal", "uses_shortener", "subdomain_depth",
    "path_length", "has_https", "brand_keyword_outside_domain",
    "domain_age_days", "cert_issuer_age_days", "brand_similarity",
]
 
def explain_structural_prediction(
    booster, row: pd.DataFrame, top_k: int = 4
):
    explainer = shap.TreeExplainer(booster)
    shap_values = explainer.shap_values(row[STRUCTURAL_FEATURES])
    pairs = zip(STRUCTURAL_FEATURES, shap_values[0])
    contributions = sorted(
        pairs, key=lambda kv: abs(kv[1]), reverse=True
    )
    return contributions[:top_k]
 
def explain_text_prediction(
    model, tokenizer, subject: str, body: str, predict_fn, top_k: int = 4
):
    """predict_fn: callable(list[str]) -> np.ndarray of phishing
    probabilities, wrapping the fine-tuned text model for SHAP's
    model-agnostic text explainer."""
    explainer = shap.Explainer(predict_fn, tokenizer)
    shap_values = explainer([f"{subject} [SEP] {body}"])
    pairs = zip(shap_values[0].data, shap_values[0].values)
    tokens_and_scores = sorted(
        pairs, key=lambda kv: abs(kv[1]), reverse=True
    )
    return tokens_and_scores[:top_k]
