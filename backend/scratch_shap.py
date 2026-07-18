import joblib
import shap
import pandas as pd
import numpy as np

# Load model
model = joblib.load('d:/Rakshanet/ml/models/phishing_text_model.pkl')
tfidf = model.named_steps['tfidf']
clf = model.named_steps['clf']

# Sample text
text = "urgent action required verify your account immediately"
X = tfidf.transform([text])

# Explain
explainer = shap.LinearExplainer(clf, tfidf.transform(["hello team, just wanted to check on the project status", "urgent action required", "please review the attached document when you have time"]))
shap_values = explainer.shap_values(X)

print("SHAP values shape:", shap_values.shape)
print("SHAP values:", shap_values)

# Get top features
feature_names = tfidf.get_feature_names_out()
# Since we only have 1 sample, shap_values is an array
contributions = {}
for i, val in enumerate(shap_values[0]):
    if abs(val) > 0.01:
        contributions[feature_names[i]] = val
        
print("Contributions:", contributions)
