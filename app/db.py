from pymongo import MongoClient

connection_string = "mongodb+srv://test:test@chatroom.5vtda.mongodb.net/"

# Connect to MongoDB
client = MongoClient(connection_string) 
db = client["mydatabase"] 

# Define collections
user_collection = db["users"]
inventory_collection = db["inventory"]
sales_tracking_collection = db["sales_tracking"]
buy_tracking_collection = db["buy_tracking"]
salaries_collection = db["salaries"]
licenses_collection = db["licenses"]
cart_collection = db["cart"]  
