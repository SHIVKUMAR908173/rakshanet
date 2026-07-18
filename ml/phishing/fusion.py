import numpy as np
from sklearn.linear_model import LogisticRegression
 
def fit_fusion_layer(
    text_scores: np.ndarray,
    structural_scores: np.ndarray,
    disagreement: np.ndarray,
    y: np.ndarray,
) -> LogisticRegression:
    X_meta = np.column_stack(
        [text_scores, structural_scores, disagreement]
    )
    meta = LogisticRegression(class_weight="balanced", max_iter=1000)
    meta.fit(X_meta, y)
    return meta
 
def combined_phishing_score(
    text_score: float, structural_score: float, meta: LogisticRegression
) -> float:
    disagreement = abs(text_score - structural_score)
    x = np.array([[text_score, structural_score, disagreement]])
    return float(meta.predict_proba(x)[0, 1])
