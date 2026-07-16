"""
XGBoost URL model training script for Phishing Classification.

Trains an XGBoost classifier on structural URL features extracted during
the feature engineering step.
"""

import os
import pickle
import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score, confusion_matrix
import logging

from feature_engineering import process_dataframe

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("train_url_model")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/phishing/processed"))
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../ml/models/url_model"))

os.makedirs(MODEL_DIR, exist_ok=True)

# Define feature columns matching the output of feature_engineering.py
URL_FEATURES = [
    "url_length",
    "is_ip_literal",
    "is_shortener",
    "subdomain_depth",
    "brand_spoofing",
    "suspicious_path",
    "is_https",
    "num_dots",
    "num_hyphens",
    "num_special_chars",
]

def evaluate_model(model, X, y, dataset_name="Validation"):
    """Evaluate model performance and print metrics."""
    preds = model.predict(X)
    probs = model.predict_proba(X)[:, 1]
    
    precision, recall, f1, _ = precision_recall_fscore_support(y, preds, average='binary')
    acc = accuracy_score(y, preds)
    auc = roc_auc_score(y, probs)
    
    logger.info(f"--- {dataset_name} Metrics ---")
    logger.info(f"Accuracy:  {acc:.4f}")
    logger.info(f"Precision: {precision:.4f}")
    logger.info(f"Recall:    {recall:.4f}")
    logger.info(f"F1 Score:  {f1:.4f}")
    logger.info(f"AUC:       {auc:.4f}")
    
    cm = confusion_matrix(y, preds)
    logger.info(f"Confusion Matrix:\n{cm}")
    
    return {'acc': acc, 'prec': precision, 'rec': recall, 'f1': f1, 'auc': auc}


def main():
    logger.info("Loading datasets...")
    train_df = pd.read_csv(os.path.join(DATA_DIR, "train.csv"))
    val_df = pd.read_csv(os.path.join(DATA_DIR, "val.csv"))
    
    logger.info("Extracting features...")
    # process_dataframe applies extract_url_features to the 'url' column
    train_features_df = process_dataframe(train_df)
    val_features_df = process_dataframe(val_df)
    
    # Filter to only keep rows where URL feature extraction succeeded (or filled with 0s)
    # The process_dataframe script creates these columns
    
    X_train = train_features_df[URL_FEATURES].fillna(0)
    y_train = train_features_df['label']
    
    X_val = val_features_df[URL_FEATURES].fillna(0)
    y_val = val_features_df['label']
    
    logger.info("Initializing XGBoost classifier...")
    # Hyperparameters would be tuned via GridSearch/Optuna in production
    model = xgb.XGBClassifier(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='auc'
    )
    
    logger.info("Training model...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        early_stopping_rounds=20,
        verbose=10
    )
    
    logger.info("Evaluating model...")
    evaluate_model(model, X_train, y_train, "Training")
    evaluate_model(model, X_val, y_val, "Validation")
    
    logger.info("Saving feature importances...")
    importances = pd.DataFrame({
        'feature': URL_FEATURES,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    logger.info(f"\nFeature Importances:\n{importances}")
    
    model_path = os.path.join(MODEL_DIR, "xgboost_url_model.pkl")
    logger.info(f"Saving model to {model_path}")
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
        
    logger.info("URL model training script complete.")

if __name__ == "__main__":
    main()
