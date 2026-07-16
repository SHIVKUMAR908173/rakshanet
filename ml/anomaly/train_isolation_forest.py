"""
Isolation Forest training script for Login/Auth Anomaly Detection.

Trains an unsupervised Isolation Forest model on authentication features.
"""

import os
import pickle
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import logging

from feature_engineering import process_anomaly_dataframe

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("train_iforest")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/anomaly/processed"))
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../ml/models/anomaly_model"))

os.makedirs(MODEL_DIR, exist_ok=True)

def main():
    logger.info("Loading datasets...")
    train_df = pd.read_csv(os.path.join(DATA_DIR, "train.csv"))
    val_df = pd.read_csv(os.path.join(DATA_DIR, "val.csv"))
    
    logger.info("Extracting features...")
    auth_train, _ = process_anomaly_dataframe(train_df)
    auth_val, _ = process_anomaly_dataframe(val_df)
    
    if len(auth_train) == 0:
        logger.error("No authentication records found in training data.")
        return
        
    # Unsupervised: train only on features, not labels
    # However, to simulate real-world where we assume most training data is benign
    features = [c for c in auth_train.columns if c != "label"]
    
    X_train = auth_train[features]
    y_train_true = auth_train["label"]
    
    X_val = auth_val[features]
    y_val_true = auth_val["label"]
    
    logger.info("Initializing Isolation Forest...")
    # contamination is the expected proportion of outliers (anomalies)
    # We set it low (e.g. 5%) as we assume most logins are legitimate
    model = IsolationForest(
        n_estimators=150,
        max_samples='auto',
        contamination=0.05,
        random_state=42,
        n_jobs=-1
    )
    
    logger.info("Training Isolation Forest...")
    model.fit(X_train)
    
    logger.info("Evaluating Model...")
    # Predict returns 1 for inliers (benign), -1 for outliers (anomaly)
    # Convert to our schema: 0 = benign, 1 = anomaly
    def map_predictions(preds):
        return [1 if p == -1 else 0 for p in preds]
        
    val_preds = map_predictions(model.predict(X_val))
    
    precision, recall, f1, _ = precision_recall_fscore_support(y_val_true, val_preds, average='binary')
    acc = accuracy_score(y_val_true, val_preds)
    
    logger.info("--- Validation Metrics ---")
    logger.info(f"Accuracy:  {acc:.4f}")
    logger.info(f"Precision: {precision:.4f}")
    logger.info(f"Recall:    {recall:.4f}")
    logger.info(f"F1 Score:  {f1:.4f}")
    
    cm = confusion_matrix(y_val_true, val_preds)
    logger.info(f"Confusion Matrix:\n{cm}")
    
    model_path = os.path.join(MODEL_DIR, "isolation_forest.pkl")
    logger.info(f"Saving model to {model_path}")
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
        
    logger.info("Isolation Forest training complete.")

if __name__ == "__main__":
    main()
