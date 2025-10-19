from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os
from config import Config
from routes.auth_routes import auth_bp, query_bp
from routes.protected_routes import protected_bp

# ---------------- Flask Setup ---------------- #
app = Flask(__name__)
app.config["SECRET_KEY"] = Config.SECRET_KEY
app.config["JWT_SECRET_KEY"] = Config.SECRET_KEY

# ---------------- JWT Setup ---------------- #
jwt = JWTManager(app)

# ---------------- Blueprints ---------------- #
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(protected_bp, url_prefix="/api/protected")
app.register_blueprint(query_bp, url_prefix="/api/query")

# ---------------- CORS Configuration ---------------- #
# (Allows frontend → backend communication with Authorization headers)
ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "https://fakedeploy.onrender.com",  # Add your Render URL
    "http://fakedeploy.onrender.com",   # Add HTTP version too
]
PROD_ORIGIN = os.getenv("FRONTEND_ORIGIN")
if PROD_ORIGIN and PROD_ORIGIN not in ALLOWED_ORIGINS:
    ALLOWED_ORIGINS.append(PROD_ORIGIN)

CORS(
    app,
    supports_credentials=True,
    resources={r"/*": {"origins":"*"}},
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Authorization"]
)

# ---------------- Debug Helpers ---------------- #
# This will print headers for every request (to confirm token is received)
@app.before_request
def debug_headers():
    print("\n---- REQUEST DEBUG ----")
    print("Path:", request.path)
    print("Headers:", dict(request.headers))
    print("-----------------------\n")

# Catch JWT issues and print why they failed
@jwt.invalid_token_loader
def invalid_token_callback(reason):
    print("❌ Invalid token:", reason)
    return jsonify({"error": "Invalid token", "details": reason}), 422

@jwt.unauthorized_loader
def missing_token_callback(reason):
    print("❌ Missing token:", reason)
    return jsonify({"error": "Missing token", "details": reason}), 422

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    print("❌ Token expired")
    return jsonify({"error": "Token expired"}), 401
@app.route('/api/debug/files')
def debug_files():
    import os
    backend_files = os.listdir(os.path.dirname(__file__))
    return jsonify({
        "backend_files": backend_files,
        "model_exists": "model.pkl" in backend_files,
        "current_directory": os.path.dirname(__file__)
    })

@app.route('/api/debug/model-status')
def model_status():
    try:
        from model_infer import _model, MODEL_PATH
        import os
        
        status = {
            "model_file_exists": os.path.exists(MODEL_PATH),
            "model_loaded": _model is not None,
            "model_type": str(type(_model)) if _model is not None else "None",
            "model_path": MODEL_PATH,
            "backend_files": os.listdir(os.path.dirname(__file__))
        }
        
        # Try to test if model can make a prediction
        if _model is not None:
            try:
                # Test with dummy features
                test_features = {feature: 0 for feature in [
                    "having_IP_Address", "URL_Length", "Shortining_Service", "having_At_Symbol",
                    "double_slash_redirecting", "Prefix_Suffix", "having_Sub_Domain", "SSLfinal_State",
                    "Domain_registeration_length", "Favicon", "port", "HTTPS_token", "Request_URL",
                    "URL_of_Anchor", "Links_in_tags", "SFH", "Submitting_to_email", "Abnormal_URL",
                    "Redirect", "on_mouseover", "RightClick", "popUpWidnow", "Iframe", "age_of_domain",
                    "DNSRecord", "web_traffic", "Page_Rank", "Google_Index", "Links_pointing_to_page",
                    "Statistical_report"
                ]}
                from model_infer import predict as model_predict
                test_result = model_predict(test_features)
                status["prediction_test"] = "success"
                status["test_prediction"] = test_result
            except Exception as e:
                status["prediction_test"] = "failed"
                status["prediction_error"] = str(e)
        else:
            status["prediction_test"] = "not_attempted"
            status["prediction_error"] = "Model not loaded"
            
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            "error": f"Failed to check model status: {str(e)}"
        }), 500
# ---------------- Run Server ---------------- #
if __name__ == "__main__":
    app.run(debug=True, port=5000)
