import os

from pymongo import MongoClient

from config import Config

# The MongoDB Atlas connection string carries the database username and
# password, so it is read from the environment through Config and must never be
# hardcoded here again. Fail loudly when it is missing instead of falling back
# to a placeholder that would only produce a confusing connection error.
connection_string = Config.MONGO_URI
if not connection_string:
    raise RuntimeError(
        "MONGO_URI is not set. Copy .env.example to .env and provide the "
        "MongoDB connection string before starting the app."
    )

# Connect to MongoDB
client = MongoClient(connection_string)
db = client[os.environ.get("MONGO_DB_NAME", "mydatabase")]

# Define collections
user_collection = db["users"]
inventory_collection = db["inventory"]
sales_tracking_collection = db["sales_tracking"]
buy_tracking_collection = db["buy_tracking"]
salaries_collection = db["salaries"]
licenses_collection = db["licenses"]
cart_collection = db["cart"]
