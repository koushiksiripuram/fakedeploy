from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from db import users_collection, queries_collection
from scrape import extract_features
from model_infer import predict as model_predict
from datetime import datetime
from bson.timestamp import Timestamp
auth_bp = Blueprint("auth", __name__)
query_bp = Blueprint("query", __name__)
bcrypt = Bcrypt()

ADMIN_USERNAMES = ["admin1", "admin2"]

# ---------------- AUTH ---------------- #

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    fullname = data.get("fullname")
    email = data.get("email")
    username = data.get("username")
    password = data.get("password")

    if not fullname or not email or not username or not password:
        return jsonify({"error": "All fields are required"}), 400

    if users_collection.find_one({"username": username}):
        return jsonify({"error": "User already exists"}), 400

    role = "admin" if username in ADMIN_USERNAMES else "user"
    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

    users_collection.insert_one({
        "fullname": fullname,
        "email": email,
        "username": username,
        "password": hashed_pw,
        "role": role
    })

    return jsonify({"message": "User created successfully"}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = users_collection.find_one({"username": username})
    if not user or not bcrypt.check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    # ✅ Create JWT token (identity as dict)
    token = create_access_token(identity=username)
    return jsonify({
        "message": "Login successful",
        "token": token,
        "role": user.get("role", "user")
    }), 200


# ---------------- USER PROFILE ---------------- #

@auth_bp.route("/user/profile", methods=["GET"])
@jwt_required()
def get_profile():
    identity = get_jwt_identity()

    # Handle both dict and string payloads safely
    username = identity.get("username") if isinstance(identity, dict) else identity

    if not username:
        return jsonify({"error": "Invalid or missing token identity"}), 400

    user = users_collection.find_one({"username": username}, {"_id": 0, "password": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user), 200


@auth_bp.route("/user/update", methods=["PUT"])
@jwt_required()
def update_profile():
    identity = get_jwt_identity()
    username = identity.get("username") if isinstance(identity, dict) else identity

    data = request.get_json()
    fullname = data.get("fullname")
    email = data.get("email")

    if not fullname or not email:
        return jsonify({"error": "Full name and email are required"}), 400

    result = users_collection.update_one(
        {"username": username},
        {"$set": {"fullname": fullname, "email": email}}
    )

    if result.matched_count == 0:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"message": "Profile updated successfully"}), 200
# ---------------- UPDATE PASSWORD ---------------- #
@auth_bp.route('/user/password', methods=['PUT'])
@jwt_required()
def update_password():
    identity = get_jwt_identity()
    username = identity.get("username") if isinstance(identity, dict) else identity

    data = request.get_json() or {}
    current = data.get('currentPassword')
    new = data.get('newPassword')

    if not current or not new:
        return jsonify({"error": 'currentPassword and newPassword are required'}), 400

    user = users_collection.find_one({"username": username})
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Stored bcrypt hash is in user["password"]
    if not bcrypt.check_password_hash(user["password"], current):
        return jsonify({"error": 'Current password is incorrect'}), 400

    new_hash = bcrypt.generate_password_hash(new).decode('utf-8')
    users_collection.update_one({"username": username}, {"$set": {"password": new_hash}})

    return jsonify({"message": 'Password updated'}), 200

# ---------------- QUERIES ---------------- #

@query_bp.route("/add", methods=["POST"])
@jwt_required()
def add_query():
    identity = get_jwt_identity()
    username = identity.get("username") if isinstance(identity, dict) else identity

    data = request.get_json()
    website = data.get("website")
    result_status = data.get("result")

    if not website or not result_status:
        return jsonify({"error": "Missing website or result"}), 400

    user = users_collection.find_one({"username": username}, {"_id": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404

    query_doc = {
        "username": username,
        "fullname": user.get("fullname", ""),
        "website": website,
        "result": result_status,
        "timestamp": datetime.utcnow().isoformat()
    }

    queries_collection.insert_one(query_doc)
    return jsonify({"message": "Query added successfully"}), 201

@query_bp.route("/user", methods=["GET"])
@jwt_required()
def get_user_queries():
    username = get_jwt_identity()

    user_queries = list(queries_collection.find(
        {"username": username}, {"_id": 0}
    ).sort("timestamp", -1))

    # ✅ Convert MongoDB timestamps to string
    for q in user_queries:
        if "timestamp" in q:
            ts = q["timestamp"]
            if isinstance(ts, Timestamp):
                q["timestamp"] = datetime.fromtimestamp(ts.time).strftime("%Y-%m-%d %H:%M:%S")
            else:
                q["timestamp"] = str(ts)

    return jsonify(user_queries), 200

@query_bp.route("/add_public", methods=["POST"])
def add_query_public():
    data = request.get_json() or {}
    website = data.get("website")
    result_status = data.get("result")

    if not website or not result_status:
        return jsonify({"error": "Missing website or result"}), 400

    query_doc = {
        "username": "guest",
        "fullname": "Guest",
        "website": website,
        "result": result_status,
        "timestamp": datetime.utcnow().isoformat()
    }

    queries_collection.insert_one(query_doc)
    return jsonify({"message": "Query added successfully (guest)"}), 201

# ---------------- FEATURE EXTRACTION ---------------- #

@query_bp.route("/extract", methods=["POST"]) 
@jwt_required()
def extract_for_user():
    try:
        data = request.get_json() or {}
        url = data.get("website") or data.get("url")
        if not url:
            return jsonify({"error": "Missing website/url"}), 400
        feats = extract_features(url)
        return jsonify({
            "website": url,
            "features": feats
        }), 200
    except Exception as e:
        return jsonify({"error": "Feature extraction failed", "details": str(e)}), 500


# ---------------- PREDICTION (MODEL) ---------------- #

@query_bp.route("/predict", methods=["POST"]) 
@jwt_required()
def predict_for_user():
    try:
        data = request.get_json() or {}
        url = data.get("website") or data.get("url")
        if not url:
            return jsonify({"error": "Missing website/url"}), 400
        feats = extract_features(url)
        label = model_predict(feats)  # 0 or 1
        result = "Fake" if int(label) == 1 else "Legit"
        # Optionally log
        identity = get_jwt_identity()
        username = identity.get("username") if isinstance(identity, dict) else identity
        if username:
            user = users_collection.find_one({"username": username}, {"_id": 0})
            queries_collection.insert_one({
                "username": username,
                "fullname": (user or {}).get("fullname", ""),
                "website": url,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            })
        return jsonify({
            "website": url,
            "features": feats,
            "label": int(label),
            "result": result
        }), 200
    except Exception as e:
        return jsonify({"error": "Prediction failed", "details": str(e)}), 500


@query_bp.route("/predict_public", methods=["POST"]) 
def predict_public():
    try:
        data = request.get_json() or {}
        url = data.get("website") or data.get("url")
        if not url:
            return jsonify({"error": "Missing website/url"}), 400
        feats = extract_features(url)
        label = model_predict(feats)
        result = "Fake" if int(label) == 1 else "Legit"
        return jsonify({
            "website": url,
            "features": feats,
            "label": int(label),
            "result": result
        }), 200
    except Exception as e:
        return jsonify({"error": "Prediction failed", "details": str(e)}), 500


@query_bp.route("/extract_public", methods=["POST"]) 
def extract_public():
    try:
        data = request.get_json() or {}
        url = data.get("website") or data.get("url")
        if not url:
            return jsonify({"error": "Missing website/url"}), 400
        feats = extract_features(url)
        return jsonify({
            "website": url,
            "features": feats
        }), 200
    except Exception as e:
        return jsonify({"error": "Feature extraction failed", "details": str(e)}), 500
