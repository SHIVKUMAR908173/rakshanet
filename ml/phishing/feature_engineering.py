"""
Feature Engineering Script for Phishing Classification Engine.

Extracts URL structural features and text heuristic features to be used by
the XGBoost model and fusion classifier.
"""

import re
from urllib.parse import urlparse
import pandas as pd
import tldextract

# Re-use the keyword lists from the backend service for consistency
URGENCY_KEYWORDS = [
    "urgent", "immediately", "action required", "account suspended",
    "verify your", "confirm your", "update your", "click here",
    "expires today", "last warning", "final notice", "act now",
    "turant", "jaldi", "khatarnak", "suraksha", "khata band",  
]

CREDENTIAL_HARVEST_KEYWORDS = [
    "password", "login", "sign in", "credentials", "otp", "pin",
    "bank account", "credit card", "debit card", "upi", "pan card",
    "aadhaar", "kyc", "netbanking", "ifsc",
    "paasward", "khata", "jamaa",
]

SUSPICIOUS_BRAND_DOMAINS = [
    "sbi", "icici", "hdfc", "axis", "kotak", "paytm", "phonepe",
    "googlepay", "gpay", "bharatpe", "razorpay", "npci", "upi",
    "irctc", "aadhaar", "uidai", "incometax", "gst", "epfo",
]

SHORTENER_DOMAINS = [
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly",
    "is.gd", "buff.ly", "rebrand.ly", "cutt.ly",
]


def extract_url_features(url: str) -> dict:
    """Extract structural features from a URL for the XGBoost model."""
    features = {
        "url_length": len(url),
        "is_ip_literal": 0,
        "is_shortener": 0,
        "subdomain_depth": 0,
        "brand_spoofing": 0,
        "suspicious_path": 0,
        "is_https": 1,
        "num_dots": url.count("."),
        "num_hyphens": url.count("-"),
        "num_special_chars": sum(1 for c in url if not c.isalnum()),
    }
    
    try:
        parsed = urlparse(url)
        ext = tldextract.extract(url)
        
        hostname = parsed.hostname or ""
        path = parsed.path or ""
        
        features["is_https"] = 1 if parsed.scheme == "https" else 0
        
        # IP literal URL
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", hostname):
            features["is_ip_literal"] = 1
            
        # URL shortener
        if any(s in hostname for s in SHORTENER_DOMAINS):
            features["is_shortener"] = 1
            
        # Subdomain depth
        features["subdomain_depth"] = len(ext.subdomain.split(".")) if ext.subdomain else 0
        
        # Brand spoofing check
        for brand in SUSPICIOUS_BRAND_DOMAINS:
            if brand in ext.subdomain and brand not in ext.domain:
                features["brand_spoofing"] = 1
                break
                
        # Suspicious path
        suspicious_paths = ["login", "verify", "secure", "update", "confirm", "account"]
        if any(sp in path.lower() for sp in suspicious_paths):
            features["suspicious_path"] = 1
            
    except Exception:
        pass
        
    return features


def extract_text_features(text: str) -> dict:
    """Extract basic heuristic features from text (used as auxiliary features)."""
    if not isinstance(text, str):
        text = str(text)
        
    text_lower = text.lower()
    word_count = max(len(text.split()), 1)
    
    urgency_hits = sum(1 for kw in URGENCY_KEYWORDS if kw in text_lower)
    credential_hits = sum(1 for kw in CREDENTIAL_HARVEST_KEYWORDS if kw in text_lower)
    
    return {
        "text_length": len(text),
        "word_count": word_count,
        "urgency_density": urgency_hits / word_count,
        "credential_density": credential_hits / word_count,
        "exclamation_ratio": text.count("!") / word_count,
        "caps_ratio": sum(1 for c in text if c.isupper()) / max(len(text), 1),
    }


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply feature extraction to the entire dataframe."""
    
    # Extract URL features
    if "url" in df.columns:
        url_features = df["url"].apply(lambda x: pd.Series(extract_url_features(x if pd.notna(x) else "")))
        df = pd.concat([df, url_features], axis=1)
        
    # Extract Text features
    if "text" in df.columns:
        text_features = df["text"].apply(lambda x: pd.Series(extract_text_features(x if pd.notna(x) else "")))
        df = pd.concat([df, text_features], axis=1)
        
    return df
