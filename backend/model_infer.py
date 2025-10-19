import os
import pickle
from typing import Dict, List

import numpy as np

# Adjust this path if you place the model elsewhere
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")

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

print("Bla Bla Bla Bla Bla")

def _load_pickle(path: str):
    with open(path, "rb") as f:
        return pickle.load(f)

try:
    if os.path.exists(MODEL_PATH):
        _model = _load_pickle(MODEL_PATH)
        print("✅ Model loaded successfully!")
    else:
        print("❌ Model file not found!")
        
except Exception as e:
    print(f"❌ Error loading model: {e}")
    _model = None
# Load model/scaler at import time (fail gracefully if missing)


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
    return X



def predict(features: Dict[str, float]) -> int:
    print(f"🎯 Starting prediction with features: {list(features.keys())}")
    
    if _model is None:
        error_msg = "model.pkl not found or failed to load"
        print(f"❌ {error_msg}")
        raise RuntimeError(error_msg)
        
    try:
        X = _to_row(features)
        print(f"📊 Processed input shape: {X.shape}")
        
        y = _model.predict(X)
        print(f"🎯 Raw prediction result: {y}")
        
        # y could be array([1]) or probabilities depending on model; assume class labels
        try:
            result = int(y[0])
            print(f"✅ Final prediction: {result}")
            return result
        except Exception:
            result = int(y)
            print(f"✅ Final prediction (fallback): {result}")
            return result
            
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        raise RuntimeError(f"Prediction failed: {str(e)}")
