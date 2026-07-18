import joblib
import shap
import numpy as np

# Load model
model = joblib.load('d:/Rakshanet/ml/models/anomaly_isolation_forest.pkl')

# Sample data
X = np.array([[12, 0, 0.5]])

# Explain
try:
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    print("SHAP values shape:", shap_values.shape)
    print("SHAP values:", shap_values)
except Exception as e:
    print("Error:", e)
