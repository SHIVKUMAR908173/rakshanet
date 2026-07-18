"""
Phishing Scorer Service — loads trained models and scores incoming email events.

Uses a two-part classifier:
  1. Text model (DistilBERT) — scores urgency/credential-harvest language
  2. URL model (XGBoost) — scores structural URL features
  3. Fusion meta-classifier (Logistic Regression) — combines both with
     disagreement-as-signal logic per Section 9.1.2

For the prototype/demo phase, this module includes a heuristic fallback
scorer that runs when trained models are not yet available.
"""

import re
import math
import os
import joblib
import shap
import logging

logger = logging.getLogger("rakshanet.phishing_scorer")

# Try loading the ML model
ML_MODEL_PATH = os.environ.get("PHISHING_TEXT_MODEL_PATH", "/app/ml_models/phishing_text_model.pkl")
# Handle local dev path fallback
if not os.path.exists(ML_MODEL_PATH):
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml", "models", "phishing_text_model.pkl"))
    if os.path.exists(local_path):
        ML_MODEL_PATH = local_path

ml_model = None
ml_explainer = None
try:
    if os.path.exists(ML_MODEL_PATH):
        ml_model = joblib.load(ML_MODEL_PATH)
        # Background data for SHAP explainer
        background_data = [
            "hello team, just wanted to check on the project status",
            "urgent action required",
            "please review the attached document when you have time",
            "your password expires today click here to update"
        ]
        tfidf = ml_model.named_steps['tfidf']
        clf = ml_model.named_steps['clf']
        ml_explainer = shap.LinearExplainer(clf, tfidf.transform(background_data))
        logger.info(f"Loaded Phishing ML Model from {ML_MODEL_PATH}")
except Exception as e:
    logger.warning(f"Failed to load Phishing ML model: {e}")


# ── Heuristic keyword lists for fallback scoring ──

URGENCY_KEYWORDS = [
    "urgent", "immediately", "action required", "account suspended",
    "verify your", "confirm your", "update your", "click here",
    "expires today", "last warning", "final notice", "act now",
    "limited time", "security alert", "unauthorized", "suspicious activity",
    "turant", "jaldi", "khatarnak", "suraksha", "khata band",  # Hindi transliterated
    "tatkaal", "chetavni",  # Hindi: immediate, warning
]

CREDENTIAL_HARVEST_KEYWORDS = [
    "password", "login", "sign in", "credentials", "otp", "pin",
    "bank account", "credit card", "debit card", "upi", "pan card",
    "aadhaar", "kyc", "netbanking", "ifsc",  # India-specific
    "paasward", "khata", "jamaa",  # Hindi transliterated
]

SUSPICIOUS_BRAND_DOMAINS = [
    "sbi", "icici", "hdfc", "axis", "kotak", "paytm", "phonepe",
    "googlepay", "gpay", "bharatpe", "razorpay", "npci", "upi",
    "irctc", "aadhaar", "uidai", "incometax", "gst", "epfo",
    "digilocker", "cowin", "gov.in", "nic.in",
]

SHORTENER_DOMAINS = [
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly",
    "is.gd", "buff.ly", "rebrand.ly", "cutt.ly",
]


def _score_text_heuristic(subject: str, body: str) -> tuple[float, dict]:
    """
    Returns a tuple of (score, shap_contributions).
    If ML is available, computes true SHAP values.
    Otherwise uses heuristic fallback.
    """
    combined = f"{subject} {body}".lower()
    if not combined.strip():
        return 0.0, {}

    if ml_model is not None and ml_explainer is not None:
        try:
            tfidf = ml_model.named_steps['tfidf']
            clf = ml_model.named_steps['clf']
            X_vec = tfidf.transform([combined])
            prob_phishing = clf.predict_proba(X_vec)[0][1]
            
            # Compute SHAP
            shap_values = ml_explainer.shap_values(X_vec)
            feature_names = tfidf.get_feature_names_out()
            contributions = {}
            for i, val in enumerate(shap_values[0]):
                if abs(val) > 0.05:  # Only include meaningful contributions
                    contributions[f"word_{feature_names[i]}"] = float(val)
                    
            return float(prob_phishing), contributions
        except Exception as e:
            logger.warning(f"ML text scoring failed, falling back to heuristic: {e}")

    word_count = max(len(combined.split()), 1)

    urgency_hits = sum(1 for kw in URGENCY_KEYWORDS if kw in combined)
    credential_hits = sum(1 for kw in CREDENTIAL_HARVEST_KEYWORDS if kw in combined)

    # Normalize: more keyword density → higher score
    urgency_score = min(urgency_hits / 3.0, 1.0)
    credential_score = min(credential_hits / 2.0, 1.0)

    # Exclamation marks and ALL CAPS as additional urgency signals
    exclamation_ratio = combined.count("!") / word_count
    caps_ratio = sum(1 for c in f"{subject} {body}" if c.isupper()) / max(
        len(f"{subject} {body}"), 1
    )

    text_score = (
        0.35 * urgency_score
        + 0.35 * credential_score
        + 0.15 * min(exclamation_ratio * 5, 1.0)
        + 0.15 * min(caps_ratio * 3, 1.0)
    )

    heuristic_contributions = {
        "text_urgency": urgency_score * 0.35,
        "text_credential": credential_score * 0.35
    }

    return round(min(text_score, 1.0), 4), heuristic_contributions


def _score_url_heuristic(urls: list[str]) -> float:
    """
    Heuristic URL scoring based on structural features.
    Returns the max suspicious score across all URLs (0.0 - 1.0).
    """
    if not urls:
        return 0.0

    max_score = 0.0

    for url in urls:
        score = 0.0
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ""
            path = parsed.path or ""

            # IP literal URL (e.g. http://192.168.1.1/login)
            if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", hostname):
                score += 0.3

            # URL shortener
            if any(s in hostname for s in SHORTENER_DOMAINS):
                score += 0.2

            # Deep subdomain (more than 3 levels)
            subdomain_depth = hostname.count(".")
            if subdomain_depth > 3:
                score += 0.15

            # Brand keyword in subdomain but not in registered domain
            hostname_parts = hostname.split(".")
            subdomain_part = ".".join(hostname_parts[:-2]) if len(hostname_parts) > 2 else ""
            for brand in SUSPICIOUS_BRAND_DOMAINS:
                if brand in subdomain_part and brand not in ".".join(hostname_parts[-2:]):
                    score += 0.25
                    break

            # Suspicious path keywords
            suspicious_paths = ["login", "verify", "secure", "update", "confirm", "account"]
            if any(sp in path.lower() for sp in suspicious_paths):
                score += 0.1

            # Non-HTTPS
            if parsed.scheme == "http":
                score += 0.1

            # Very long URL (often used to hide the real destination)
            if len(url) > 150:
                score += 0.1

        except Exception:
            score += 0.15  # Unparseable URL is suspicious

        max_score = max(max_score, min(score, 1.0))

    return round(max_score, 4)


def score_email(
    subject: str,
    body: str,
    urls: list[str],
    headers: Optional[dict] = None,
) -> dict:
    """
    Score an email for phishing probability.

    Returns:
        dict with text_score, url_score, combined_score, verdict, model_disagreement,
        and feature_contributions for SHAP-like explainability.
    """
    text_score, text_contributions = _score_text_heuristic(subject, body)
    url_score = _score_url_heuristic(urls)

    # ── Header-based signals ──
    header_penalty = 0.0
    header_contributions = {}
    if headers:
        spf = headers.get("spf", "").lower()
        dkim = headers.get("dkim", "").lower()
        dmarc = headers.get("dmarc", "").lower()

        if spf == "fail":
            header_penalty += 0.15
            header_contributions["spf_fail"] = 0.15
        if dkim == "fail":
            header_penalty += 0.15
            header_contributions["dkim_fail"] = 0.15
        if dmarc == "fail":
            header_penalty += 0.1
            header_contributions["dmarc_fail"] = 0.1

    # ── Fusion: meta-classifier approximation ──
    # Disagreement-as-signal: when text and URL models disagree,
    # treat it as a moderate-risk signal (Section 9.1.2)
    model_disagreement = abs(text_score - url_score) > 0.4
    disagreement_bonus = 0.15 if model_disagreement else 0.0

    combined_score = (
        0.40 * text_score
        + 0.35 * url_score
        + 0.10 * header_penalty
        + 0.15 * disagreement_bonus
    )
    combined_score = round(min(combined_score + header_penalty * 0.5, 1.0), 4)

    # ── Verdict ──
    if combined_score >= 0.7:
        verdict = "phishing"
    elif combined_score >= 0.4:
        verdict = "suspicious"
    else:
        verdict = "benign"

    # ── Feature contributions (SHAP-like) ──
    contributions = {
        **text_contributions,
        "url_structural_score": round(url_score, 4),
        "model_disagreement_signal": disagreement_bonus,
        **header_contributions,
    }

    return {
        "text_score": text_score,
        "url_score": url_score,
        "combined_score": combined_score,
        "verdict": verdict,
        "model_disagreement": model_disagreement,
        "feature_contributions": contributions,
    }
