import pandas as pd
import xgboost as xgb
from sklearn.model_selection import StratifiedKFold
 
STRUCTURAL_FEATURES = [
    "is_ip_literal", "uses_shortener", "subdomain_depth",
    "path_length", "has_https", "brand_keyword_outside_domain",
    "domain_age_days", "cert_issuer_age_days", "brand_similarity",
]
 
def train_structural_model(
    X: pd.DataFrame, y: pd.Series, n_splits: int = 5
):
    params = {
        "objective": "binary:logistic",
        "eval_metric": "aucpr",
        "max_depth": 6,
        "eta": 0.08,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "scale_pos_weight": (y == 0).sum() / (y == 1).sum(),
    }
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    models = []
    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
        X_train = X.iloc[train_idx][STRUCTURAL_FEATURES]
        X_val = X.iloc[val_idx][STRUCTURAL_FEATURES]
        dtrain = xgb.DMatrix(X_train, label=y.iloc[train_idx])
        dval = xgb.DMatrix(X_val, label=y.iloc[val_idx])
        booster = xgb.train(
            params, dtrain, num_boost_round=400,
            evals=[(dval, "val")],
            early_stopping_rounds=25,
            verbose_eval=False,
        )
        models.append(booster)
        print(
            f"fold {fold}: "
            f"best_iteration={booster.best_iteration}  "
            f"best_score={booster.best_score:.4f}"
        )
    return models
