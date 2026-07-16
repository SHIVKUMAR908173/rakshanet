"""
Fusion Meta-classifier training script for Phishing Classification.

Trains a Logistic Regression model that takes the predicted probabilities
from the Text model (DistilBERT) and URL model (XGBoost), plus explicit
disagreement features, to output a final phishing probability.
"""

import os
import pickle
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("train_fusion")

MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../ml/models/fusion_model"))
os.makedirs(MODEL_DIR, exist_ok=True)

# In a real training pipeline, we would:
# 1. Take the validation set (not used for training base models)
# 2. Run the trained Text model to get P(text_phish)
# 3. Run the trained URL model to get P(url_phish)
# 4. Extract header features (e.g., SPF fail)
# 5. Train this fusion model on those probabilities and features

def generate_simulated_base_predictions(n_samples=2000):
    """
    Generate simulated base model predictions for the prototype.
    In production, these come from inferencing the val/test sets with
    the actual trained DistilBERT and XGBoost models.
    """
    np.random.seed(42)
    
    # 50% benign, 50% phish
    labels = np.random.randint(0, 2, n_samples)
    
    # Simulate text model probabilities (adds some noise)
    text_probs = np.where(
        labels == 1,
        np.clip(np.random.normal(0.8, 0.15, n_samples), 0, 1),
        np.clip(np.random.normal(0.2, 0.15, n_samples), 0, 1)
    )
    
    # Simulate url model probabilities
    url_probs = np.where(
        labels == 1,
        np.clip(np.random.normal(0.75, 0.2, n_samples), 0, 1),
        np.clip(np.random.normal(0.25, 0.2, n_samples), 0, 1)
    )
    
    # Simulate evasion attempts (model disagreement)
    # Evasion 1: Clean text, malicious URL (5% of phish)
    evasion_mask_1 = (labels == 1) & (np.random.random(n_samples) < 0.05)
    text_probs[evasion_mask_1] = np.random.normal(0.2, 0.1, sum(evasion_mask_1))
    
    # Evasion 2: Malicious text, clean URL (5% of phish)
    evasion_mask_2 = (labels == 1) & (np.random.random(n_samples) < 0.05)
    url_probs[evasion_mask_2] = np.random.normal(0.2, 0.1, sum(evasion_mask_2))
    
    # Generate disagreement feature explicitly
    disagreement = np.abs(text_probs - url_probs) > 0.4
    
    # Simulate header features
    spf_fail = (labels == 1) & (np.random.random(n_samples) < 0.3)
    
    return pd.DataFrame({
        'text_prob': text_probs,
        'url_prob': url_probs,
        'model_disagreement': disagreement.astype(int),
        'spf_fail': spf_fail.astype(int),
        'label': labels
    })


def main():
    logger.info("Loading base model predictions on validation set...")
    # For prototype, we generate simulated probabilities
    df = generate_simulated_base_predictions()
    
    # Split into train and test for the meta-classifier
    train_size = int(len(df) * 0.8)
    train_df = df.iloc[:train_size]
    test_df = df.iloc[train_size:]
    
    features = ['text_prob', 'url_prob', 'model_disagreement', 'spf_fail']
    
    X_train = train_df[features]
    y_train = train_df['label']
    
    X_test = test_df[features]
    y_test = test_df['label']
    
    logger.info("Training Fusion Meta-Classifier (Logistic Regression)...")
    model = LogisticRegression(class_weight='balanced')
    model.fit(X_train, y_train)
    
    logger.info("Evaluating Meta-Classifier...")
    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]
    
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, preds, average='binary')
    acc = accuracy_score(y_test, preds)
    auc = roc_auc_score(y_test, probs)
    
    logger.info(f"Accuracy:  {acc:.4f}")
    logger.info(f"Precision: {precision:.4f}")
    logger.info(f"Recall:    {recall:.4f}")
    logger.info(f"F1 Score:  {f1:.4f}")
    logger.info(f"AUC:       {auc:.4f}")
    
    logger.info(f"\nModel Coefficients:")
    for feat, coef in zip(features, model.coef_[0]):
        logger.info(f"  {feat}: {coef:.4f}")
    logger.info(f"  Intercept: {model.intercept_[0]:.4f}")
    
    model_path = os.path.join(MODEL_DIR, "logistic_fusion_model.pkl")
    logger.info(f"Saving fusion model to {model_path}")
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
        
    logger.info("Fusion model training complete.")

if __name__ == "__main__":
    main()
