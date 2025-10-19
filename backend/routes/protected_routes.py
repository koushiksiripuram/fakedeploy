from flask import Blueprint, jsonify,request
from db import users_collection, queries_collection
from bson.timestamp import Timestamp
from datetime import datetime
protected_bp = Blueprint("protected", __name__)

@protected_bp.route("/users", methods=["GET"])
def get_all_users():
    users = list(users_collection.find({}, {"_id": 0, "password": 0}))
    return jsonify(users), 200

@protected_bp.route("/users/<username>", methods=["PUT"])
def update_user(username):
    data = request.get_json()
    fullname = data.get("fullname")
    email = data.get("email")
    result = users_collection.update_one(
        {"username": username},
        {"$set": {"fullname": fullname, "email": email}}
    )
    if result.matched_count == 0:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"message": "User updated successfully"}), 200

@protected_bp.route("/users/<username>", methods=["DELETE"])
def delete_user(username):
    result = users_collection.delete_one({"username": username})
    if result.deleted_count == 0:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"message": "User deleted successfully"}), 200

@protected_bp.route("/queries", methods=["GET"])
def get_all_queries():
    queries = list(queries_collection.find({}, {"_id": 0}))
    for q in queries:
        if "timestamp" in q:
            ts = q["timestamp"]
            if isinstance(ts, Timestamp):
                q["timestamp"] = datetime.fromtimestamp(ts.time).strftime("%Y-%m-%d %H:%M:%S")
            else:
                q["timestamp"] = str(ts)
    return jsonify(queries), 200