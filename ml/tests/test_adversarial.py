import pandas as pd
 
def build_adversarial_phishing_set(
    clean_lures: list, suspicious_urls: list
) -> pd.DataFrame:
    """Pairs clean-sounding email text with structurally
    suspicious URLs, and vice versa, to test whether the fusion
    layer's disagreement signal catches evasive combinations."""
    rows = []
    for text in clean_lures:
        for url in suspicious_urls:
            rows.append({
                "body": text, "url": url, "label": 1,
                "case": "clean_text_suspicious_url",
            })
    return pd.DataFrame(rows)
