from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/telegram_bot_db')
client = MongoClient(MONGODB_URL)
db = client.telegram_bot_db

# Collections
users_collection = db.users
chat_history_collection = db.chat_history

def create_user(user_id, first_name, username=None):
    """Create or update user in database"""
    user_data = {
        "user_id": user_id,
        "first_name": first_name,
        "username": username,
        "created_at": datetime.now(),
        "preferences": {},
        "total_messages": 0
    }
    
    users_collection.update_one(
        {"user_id": user_id}, 
        {"$setOnInsert": user_data}, 
        upsert=True
    )

def save_chat_message(user_id, user_message, bot_response, message_type="general"):
    """Save chat message to history"""
    chat_data = {
        "user_id": user_id,
        "user_message": user_message,
        "bot_response": bot_response,
        "message_type": message_type,  # weather, stock, news, general
        "timestamp": datetime.now()
    }
    
    chat_history_collection.insert_one(chat_data)
    
    # Update user message count
    users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"total_messages": 1}}
    )

def get_user_chat_history(user_id, limit=10):
    """Get user's recent chat history"""
    history = chat_history_collection.find(
        {"user_id": user_id}
    ).sort("timestamp", -1).limit(limit)
    
    return list(history)

def get_user_info(user_id):
    """Get user information"""
    return users_collection.find_one({"user_id": user_id})