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
    resources={r"/*": {"origins": ALLOWED_ORIGINS}},
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

# ---------------- Run Server ---------------- #
if __name__ == "__main__":
    app.run(debug=True, port=5000)
