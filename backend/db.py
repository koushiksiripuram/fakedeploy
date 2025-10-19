from pymongo import MongoClient
from config import Config

# MongoDB connection
client = MongoClient(Config.MONGO_URI)

try:
    client.admin.command("ping")
    print("✅ Connected to MongoDB Atlas successfully!")
except Exception as e:
    print("❌ MongoDB connection failed:", e)

# Get database + users collection
db = client["fakewebsite"]
users_collection = db["users"]
queries_collection=db["queries"]