from app.db import user_collection, inventory_collection
from bson.objectid import ObjectId
from app.db import licenses_collection
from werkzeug.security import generate_password_hash, check_password_hash



class User:
    @staticmethod
    def create_user(username, email, password):
        # Hash the password before storing it
        hashed_password = generate_password_hash(password)
        user_collection.insert_one({"username": username, "email": email, "password": hashed_password})

    @staticmethod
    def find_user(email):
        return user_collection.find_one({"email": email})

    @staticmethod
    def verify_password(stored_password, provided_password):
        # Compare the stored hashed password with the provided password
        return check_password_hash(stored_password, provided_password)

class Inventory:
    @staticmethod
    def add_item(name, quantity, category):
        inventory_collection.insert_one({"name": name, "quantity": quantity, "category": category})

    @staticmethod
    def get_inventory():
        return list(inventory_collection.find())
    

class License:
    @staticmethod
    def add_license(license_type, expiration_date, status):
        """Add a new license to the database."""
        licenses_collection.insert_one({
            "type": license_type,
            "expiration_date": expiration_date,
            "status": status
        })

    @staticmethod
    def get_all_licenses():
        """Get all licenses from the database."""
        return list(licenses_collection.find())

    @staticmethod
    def get_license_by_id(license_id):
        """Get a specific license by its ID."""
        return licenses_collection.find_one({"_id": license_id})

    @staticmethod
    def update_license(license_id, license_type, expiration_date, status):
        """Update an existing license in the database."""
        licenses_collection.update_one(
            {"_id": license_id},
            {"$set": {
                "type": license_type,
                "expiration_date": expiration_date,
                "status": status
            }}
        )

    @staticmethod
    def delete_license(license_id):
        """Delete a license from the database using its ID."""
        licenses_collection.delete_one({"_id": ObjectId(license_id)})



class Inventory:
    @staticmethod
    def add_item(name, quantity, category, buy_price, sell_price, image_url=None):
        """Add a new item to the inventory."""
        inventory_collection.insert_one({
            "name": name,
            "quantity": quantity,
            "category": category,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "image_url": image_url
        })

    @staticmethod
    def get_inventory():
        """Get all inventory items."""
        return list(inventory_collection.find())

    @staticmethod
    def get_item_by_id(item_id):
        """Get an inventory item by its ID."""
        return inventory_collection.find_one({"_id": ObjectId(item_id)})

    @staticmethod
    def update_item(item_id, name=None, quantity=None, category=None, buy_price=None, sell_price=None, image_url=None):
        """Update an existing item in the inventory."""
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if quantity is not None:
            update_data["quantity"] = quantity
        if category is not None:
            update_data["category"] = category
        if buy_price is not None:
            update_data["buy_price"] = buy_price
        if sell_price is not None:
            update_data["sell_price"] = sell_price
        if image_url is not None:
            update_data["image_url"] = image_url

        if update_data:
            inventory_collection.update_one(
                {"_id": ObjectId(item_id)},
                {"$set": update_data}
            )

    @staticmethod
    def delete_item(item_id):
        """Delete an item from the inventory."""
        inventory_collection.delete_one({"_id": ObjectId(item_id)})