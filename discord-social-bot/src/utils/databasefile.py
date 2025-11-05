# src/utils/database.py
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
#testfetch123
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME", "social_bot")

# Create the client and connect to the DB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def get_collection(name: str):
    """Return a collection by name."""
    return db[name]
