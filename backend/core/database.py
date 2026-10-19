from pymongo import MongoClient
from ..core.config import MONGO_URI, MONGO_DB_NAME

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

if not MONGO_URI:
    raise Exception("❌ MONGO_URI missing in .env")

hr_users = db["hr_users"] 