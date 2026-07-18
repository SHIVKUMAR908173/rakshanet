from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
)
import numpy as np
from sklearn.metrics import roc_curve
 
def evaluate_classifier(y_true, y_pred, y_scores) -> dict:
    return {
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "auc_roc": roc_auc_score(y_true, y_scores),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }

def select_threshold_for_target_fpr(
    y_true, y_scores, target_fpr: float = 0.05
) -> float:
    fpr, tpr, thresholds = roc_curve(y_true, y_scores)
    idx = np.argmin(np.abs(fpr - target_fpr))
    return float(thresholds[idx])
