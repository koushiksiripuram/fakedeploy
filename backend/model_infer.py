import os
import pickle
from typing import Dict, List

import numpy as np

# Adjust this path if you place the model elsewhere
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "scaler.pkl")

# IMPORTANT: Must match training feature order EXACTLY
FEATURES_IN_ORDER: List[str] = [
    "having_IP_Address",
    "URL_Length",
    "Shortining_Service",
    "having_At_Symbol",
    "double_slash_redirecting",
    "Prefix_Suffix",
    "having_Sub_Domain",
    "SSLfinal_State",
    "Domain_registeration_length",
    "Favicon",
    "port",
    "HTTPS_token",
    "Request_URL",
    "URL_of_Anchor",
    "Links_in_tags",
    "SFH",
    "Submitting_to_email",
    "Abnormal_URL",
    "Redirect",
    "on_mouseover",
    "RightClick",
    "popUpWidnow",
    "Iframe",
    "age_of_domain",
    "DNSRecord",
    "web_traffic",
    "Page_Rank",
    "Google_Index",
    "Links_pointing_to_page",
    "Statistical_report",
]

_model = None
_scaler = None


def _load_pickle(path: str):
    with open(path, "rb") as f:
        return pickle.load(f)


# Load model/scaler at import time (fail gracefully if missing)
try:
    if os.path.exists(MODEL_PATH):
        _model = _load_pickle(MODEL_PATH)
    if os.path.exists(SCALER_PATH):
        _scaler = _load_pickle(SCALER_PATH)
except Exception as e:
    # Keep None; routes will handle missing model error
    _model = None
    _scaler = None


def _to_row(features: Dict[str, float]) -> np.ndarray:
    row = []
    for k in FEATURES_IN_ORDER:
        v = features.get(k, 0)
        try:
            v = float(v)
        except Exception:
            v = 0.0
        row.append(v)
    X = np.array(row, dtype=float).reshape(1, -1)
    if _scaler is not None:
        try:
            X = _scaler.transform(X)
        except Exception:
            # ignore scaler failure, use unscaled
            pass
    return X


def predict(features: Dict[str, float]) -> int:
    if _model is None:
        raise RuntimeError("model.pkl not found or failed to load")
    X = _to_row(features)
    y = _model.predict(X)
    # y could be array([1]) or probabilities depending on model; assume class labels
    try:
        return int(y[0])
    except Exception:
        return int(y)
