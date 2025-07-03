from fastapi import FastAPI, Request
import os 
import requests
from dotenv import load_dotenv
import google.generativeai as genai
from utils.get_weather import get_weather
from utils.get_stock import get_stock_price
from utils.get_news import get_news
from utils.generate_image import generate_image
from utils.get_places import get_places_nearby, get_user_location_from_telegram, format_places_response
from prompts.ballu_prompts import (
    BALLU_BASE_PROMPT, 
    FUNCTION_CALLING_PROMPT, 
    FOLLOW_UP_PROMPT,
    get_intent_and_parameters_with_gemini
)

# MongoDB imports and setup
from pymongo import MongoClient
from datetime import datetime
import json

load_dotenv()  # take environment variables

# API keys
telegram_api = os.getenv('TELEGRAM_TOKEN','None')
weather_api_token = os.getenv('WEATHER_API_KEY','None')
stock_api = os.getenv('STOCK_API_KEY','None')
news_api = os.getenv('NEWS_API_KEY','None')
gemini_api = os.getenv('GEMINI_API_KEY','None')

# MongoDB connection
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/telegram_bot_db')
try:
    client = MongoClient(MONGODB_URL)
    db = client.telegram_bot_db
    
    # Collections
    users_collection = db.users
    chat_history_collection = db.chat_history
    processed_messages_collection = db.processed_messages  # For deduplication
    
    # Test connection
    client.admin.command('ping')
    print("✅ MongoDB connected successfully!")
except Exception as e:
    print(f"❌ MongoDB connection failed: {str(e)}")
    print("Bot will continue without database functionality")
    db = None

# Configure Gemini with Function Calling
genai.configure(api_key=gemini_api)

# Define function schemas for Gemini
function_declarations = [
    {
        "name": "get_weather",
        "description": "Get current weather information for a specific city",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name to get weather for (e.g., 'Mumbai', 'New York', 'London')"
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "get_stock_price",
        "description": "Get current stock price and information for a specific stock symbol",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol (e.g., 'AAPL', 'GOOGL', 'TSLA', 'RELIANCE.NS' for Indian stocks)"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_news",
        "description": "Get latest news articles. Can get general news or search for specific topics",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "News search query. Use 'general' for latest news, or specific topics like 'technology', 'sports', 'politics'"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "generate_image",
        "description": "Generate an image based on a text prompt using AI",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The text description of the image you want to generate (e.g., 'a beautiful sunset over mountains', 'a cute cat playing with a ball')"
                }
            },
            "required": ["prompt"]
        }
    },
    {
        "name": "get_places_nearby",
        "description": "Find restaurants, bars, cafes, and other places near a specific location",
        "parameters": {
            "type": "object",
            "properties": {
                "lat": {
                    "type": "number",
                    "description": "Latitude coordinate of the location"
                },
                "lon": {
                    "type": "number",
                    "description": "Longitude coordinate of the location"
                },
                "query": {
                    "type": "string",
                    "description": "Type of places to search for (e.g., 'restaurants', 'pubs', 'cafes', 'bars')"
                }
            },
            "required": ["lat", "lon", "query"]
        }
    }
]

# Create Gemini model with function calling
model = genai.GenerativeModel(
    'gemini-1.5-flash',
    tools=[{"function_declarations": function_declarations}]
)

# Function handler mapping
function_handlers = {
    "get_weather": get_weather,
    "get_stock_price": get_stock_price,
    "get_news": get_news,
    "generate_image": generate_image,
    "get_places_nearby": get_places_nearby
}

# Debug: Print function handlers on startup
print(f"🔧 Available function handlers: {list(function_handlers.keys())}")
print(f"🔧 Weather function: {get_weather}")
print(f"🔧 Stock function: {get_stock_price}")
print(f"🔧 News function: {get_news}")
print(f"🔧 Image generation function: {generate_image}")
print(f"🔧 Places function: {get_places_nearby}")

# Use prompts from the prompts module

# MongoDB helper functions
def create_or_update_user(user_id, first_name, username=None):
    """Create or update user in database"""
    if db is None:
        return
    
    try:
        users_collection.update_one(
            {"user_id": user_id}, 
            {
                "$setOnInsert": {
                    "user_id": user_id,
                    "created_at": datetime.now(),
                    "preferences": {},
                    "total_messages": 0
                },
                "$set": {
                    "last_active": datetime.now(),
                    "first_name": first_name,
                    "username": username
                }
            }, 
            upsert=True
        )
        print(f"✅ User {user_id} ({first_name}) updated in database")
    except Exception as e:
        print(f"❌ Error updating user: {str(e)}")

def save_chat_message(user_id, user_message, bot_response, message_type="general", function_used=None):
    """Save chat message to history"""
    if db is None:
        return
    
    try:
        chat_data = {
            "user_id": user_id,
            "user_message": user_message,
            "bot_response": bot_response,
            "message_type": message_type,
            "function_used": function_used,
            "timestamp": datetime.now()
        }
        
        chat_history_collection.insert_one(chat_data)
        
        # Update user message count
        users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"total_messages": 1}}
        )
        print(f"💾 Chat saved: {user_id} - {message_type} - Function: {function_used}")
    except Exception as e:
        print(f"❌ Error saving chat: {str(e)}")

def get_user_chat_history(user_id, limit=5):
    """Get user's recent chat history for context"""
    if db is None:
        return []
    
    try:
        history = chat_history_collection.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit)
        
        return list(history)
    except Exception as e:
        print(f"❌ Error getting chat history: {str(e)}")
        return []

def get_user_info(user_id):
    """Get user information"""
    if db is None:
        return None
    
    try:
        return users_collection.find_one({"user_id": user_id})
    except Exception as e:
        print(f"❌ Error getting user info: {str(e)}")
        return None

def is_first_time_user(user_id):
    """Check if user is first time user"""
    if db is None:
        return False
    
    try:
        user = users_collection.find_one({"user_id": user_id})
        return user is None
    except Exception as e:
        print(f"❌ Error checking first time user: {str(e)}")
        return False

def is_message_processed(message_id):
    """Check if message has already been processed to prevent infinite loops"""
    if db is None:
        return False
    
    try:
        processed = processed_messages_collection.find_one({"message_id": message_id})
        return processed is not None
    except Exception as e:
        print(f"❌ Error checking processed message: {str(e)}")
        return False

def mark_message_processed(message_id):
    """Mark message as processed"""
    if db is None:
        return
    
    try:
        processed_messages_collection.insert_one({
            "message_id": message_id,
            "processed_at": datetime.now()
        })
    except Exception as e:
        print(f"❌ Error marking message as processed: {str(e)}")

def send_welcome_message(chat_id, user_name):
    """Send welcome message to first-time user"""
    try:
        welcome_text = f"""
🎉 Welcome {user_name}! I'm Ballu, your friendly AI assistant! 🤖

🌟 **What I can help you with:**

🌤️ **Weather Updates** - Ask me about weather in any city!
   • "Weather in Mumbai"
   • "How's the weather in New York?"

📊 **Stock Information** - Get real-time stock prices!
   • "Stock price of AAPL"
   • "What's TSLA trading at?"

📰 **Latest News** - Stay updated with current events!
   • "Latest news"
   • "Technology news"
   • "Sports headlines"

💬 **General Chat** - Just want to talk? I'm here for that too!

I'm still learning and growing, so feel free to ask me anything! What would you like to know about today? 😊
        """
        
        # Send welcome image first
        try:
            send_welcome_image(chat_id)
        except Exception as e:
            print(f"⚠️ Could not send welcome image: {str(e)}")
        
        # Then send welcome text
        send_telegram_message(chat_id, welcome_text)
        
        print(f"🎉 Welcome message sent to {user_name} ({chat_id})")
        
    except Exception as e:
        print(f"❌ Error sending welcome message: {str(e)}")

def send_welcome_image(chat_id):
    """Send welcome image to user"""
    try:
        if telegram_api == 'None':
            return
            
        # Check if welcome.jpeg exists
        import os
        if not os.path.exists("welcome.jpg"):
            print("⚠️ welcome.jpeg not found, skipping image")
            return
            
        url = f"https://api.telegram.org/bot{telegram_api}/sendPhoto"
        
        with open("welcome.jpg", "rb") as photo:
            files = {"photo": photo}
            data = {"chat_id": chat_id, "caption": "Welcome to Ballu! 🤖✨"}
            
            response = requests.post(url, data=data, files=files)
            
            if response.status_code == 200:
                print(f"📸 Welcome image sent to {chat_id}")
            else:
                print(f"❌ Failed to send welcome image: {response.json()}")
                
    except Exception as e:
        print(f"❌ Error sending welcome image: {str(e)}")

def send_generated_image(chat_id, image_bytes, caption="Generated by Ballu! 🎨"):
    """Send generated image to user"""
    try:
        if telegram_api == 'None':
            return False
            
        url = f"https://api.telegram.org/bot{telegram_api}/sendPhoto"
        
        # Create a temporary file-like object from bytes
        import io
        photo_file = io.BytesIO(image_bytes)
        photo_file.name = 'generated_image.png'  # Give it a name for Telegram
        
        files = {"photo": photo_file}
        data = {"chat_id": chat_id, "caption": caption}
        
        response = requests.post(url, data=data, files=files)
        
        if response.status_code == 200:
            print(f"🎨 Generated image sent to {chat_id}")
            return True
        else:
            print(f"❌ Failed to send generated image: {response.json()}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending generated image: {str(e)}")
        return False

def process_function_call(function_call):
    """Process a function call from Gemini"""
    function_name = function_call.name
    function_args = {}
    
    # Extract arguments from function call
    for key, value in function_call.args.items():
        function_args[key] = value
    
    print(f"🔧 Calling function: {function_name} with args: {function_args}")
    
    # Call the appropriate function
    if function_name in function_handlers:
        try:
            result = function_handlers[function_name](**function_args)
            return {
                "function_name": function_name,
                "result": result,
                "success": True
            }
        except Exception as e:
            return {
                "function_name": function_name,
                "result": f"Error calling {function_name}: {str(e)}",
                "success": False
            }
    else:
        return {
            "function_name": function_name,
            "result": f"Unknown function: {function_name}",
            "success": False
        }

def is_greeting(message):
    """Check if the message is a greeting"""
    greeting_words = [
        'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
        'morning', 'afternoon', 'evening', 'greetings', 'salutations',
        'howdy', 'yo', 'sup', 'what\'s up', 'wassup', 'hiya', 'hello there',
        'good day', 'good night', 'night', 'bye', 'goodbye', 'see you',
        'take care', 'farewell', 'ciao', 'adios', 'au revoir'
    ]
    
    message_lower = message.lower().strip()
    
    # Check for exact matches
    if message_lower in greeting_words:
        return True
    
    # Check if message starts with greeting words
    for greeting in greeting_words:
        if message_lower.startswith(greeting + ' ') or message_lower == greeting:
            return True
    
    # Check for common greeting patterns
    greeting_patterns = [
        r'^hi\s+ballu',
        r'^hello\s+ballu',
        r'^hey\s+ballu',
        r'^hi\s+there',
        r'^hello\s+there',
        r'^hey\s+there'
    ]
    
    import re
    for pattern in greeting_patterns:
        if re.match(pattern, message_lower):
            return True
    
    return False

def get_intelligent_response(user_message, user_id=None, chat_id=None):
    """Get response from Gemini with intelligent intent recognition and function calling"""
    try:
        # Check if this is a greeting first
        if is_greeting(user_message):
            print(f"👋 Detected greeting: {user_message}")
            greeting_response = f"""
👋 Hi there! I'm Ballu, your friendly AI assistant! 🤖

I was created by Siddhant Kochhar and Shreya Sharma, two passionate final year undergraduate students who love building AI assistants like me.

🌟 **What I can help you with:**

🌤️ **Weather Updates** - Ask me about weather in any city!
📊 **Stock Information** - Get real-time stock prices!
📰 **Latest News** - Stay updated with current events!
🎨 **Image Generation** - Create beautiful images from text descriptions!
🍽️ **Places Search** - Find restaurants, bars, and cafes near you!
💬 **General Chat** - Just want to talk? I'm here for that too!

What would you like to know about today? 😊
            """
            
            return {
                "response": greeting_response,
                "function_used": "greeting",
                "function_success": True,
                "send_image": True  # Flag to send welcome image
            }
        
        # Step 1: Use Gemini to determine intent and extract parameters
        intent, parameters = get_intent_and_parameters_with_gemini(user_message)
        print(f"🎯 Gemini detected intent: {intent}")
        print(f"📋 Gemini extracted parameters: {parameters}")
        print(f"🔍 User message: '{user_message}'")
        print(f"🔍 Intent in allowed list: {intent in ['weather', 'stock', 'news', 'image', 'places']}")
        print(f"🔍 Parameters exist: {parameters is not None}")
        
        # Fallback: If intent extraction failed, try to detect image generation manually
        if intent is None and any(word in user_message.lower() for word in ['image', 'picture', 'generate', 'create']):
            print(f"🔄 Fallback: Detecting image intent manually")
            intent = "image"
            parameters = None
        
        # Additional fallback: If intent is still None, treat as general conversation
        if intent is None:
            print(f"🔄 Fallback: No intent detected, treating as general conversation")
            intent = "general"
            parameters = None
        
        # Special handling for location-based queries
        if intent == "places" and chat_id and not parameters.get("lat") and not parameters.get("lon"):
            # Check if user has a stored location
            stored_location = None
            if user_id and db is not None:
                user_info = get_user_info(user_id)
                if user_info and "last_location" in user_info:
                    stored_location = user_info["last_location"]
            
            if stored_location:
                # Use stored location
                lat = stored_location["lat"]
                lon = stored_location["lon"]
                query = parameters.get("query", "restaurants")
                
                # Call places function with stored location
                function_result = process_function_call_direct("get_places_nearby", {
                    "lat": lat,
                    "lon": lon,
                    "query": query
                })
                
                if function_result["success"]:
                    places_data = function_result["result"]
                    formatted_response = format_places_response(places_data)
                    return {
                        "response": formatted_response,
                        "function_used": "get_places_nearby",
                        "function_success": True,
                        "send_image": False
                    }
                else:
                    return {
                        "response": f"❌ Sorry, I couldn't find places near your location. {function_result['result'].get('error', 'Unknown error')}",
                        "function_used": "get_places_nearby",
                        "function_success": False,
                        "send_image": False
                    }
            else:
                # User wants to find places but hasn't shared location
                location_request = get_user_location_from_telegram(chat_id, telegram_api)
                if location_request:
                    return {
                        "response": "📍 I'd love to help you find places! Please share your location using the button below, and then tell me what type of places you're looking for (restaurants, bars, cafes, etc.).",
                        "function_used": "location_request",
                        "function_success": True,
                        "send_image": False
                    }
                else:
                    return {
                        "response": "📍 I'd love to help you find places! Please share your location and tell me what type of places you're looking for (restaurants, bars, cafes, etc.).",
                        "function_used": "location_request",
                        "function_success": False,
                        "send_image": False
                    }
        
        # Step 2: If we have a clear intent and parameters, call the function directly
        if intent in ["weather", "stock", "news", "image", "places"] and parameters:
            function_name = f"get_{intent}"
            if intent == "weather":
                function_name = "get_weather"
            elif intent == "stock":
                function_name = "get_stock_price"
            elif intent == "news":
                function_name = "get_news"
            elif intent == "image":
                function_name = "generate_image"
            elif intent == "places":
                function_name = "get_places_nearby"
            
            # Convert parameters to match function signatures
            if intent == "weather" and "city" in parameters:
                # get_weather expects city_name as positional argument
                function_result = process_function_call_direct(function_name, {"city_name": parameters["city"]})
            elif intent == "stock" and "symbol" in parameters:
                # get_stock_price expects symbol as positional argument
                function_result = process_function_call_direct(function_name, {"symbol": parameters["symbol"]})
            elif intent == "news" and "query" in parameters:
                # get_news expects query as positional argument
                function_result = process_function_call_direct(function_name, {"query": parameters["query"]})
            elif intent == "image" and "prompt" in parameters:
                # generate_image expects prompt as positional argument
                function_result = process_function_call_direct(function_name, {"prompt": parameters["prompt"]})
            elif intent == "places" and all(key in parameters for key in ["lat", "lon", "query"]):
                # get_places_nearby expects lat, lon, and query as arguments
                function_result = process_function_call_direct(function_name, {
                    "lat": float(parameters["lat"]),
                    "lon": float(parameters["lon"]),
                    "query": parameters["query"]
                })
            else:
                # Fallback to original method
                function_result = process_function_call_direct(function_name, parameters)
            
            # Handle image generation specially
            if intent == "image" and function_result["success"]:
                # For image generation, we need to return the image data
                image_data = function_result["result"]
                if image_data.get("success") and "image_bytes" in image_data:
                    return {
                        "response": f"🎨 Here's your generated image based on: '{parameters['prompt']}'",
                        "function_used": function_name,
                        "function_success": True,
                        "send_image": False,  # We'll handle image sending separately
                        "generated_image": image_data["image_bytes"],
                        "image_caption": f"🎨 Generated by Ballu: {parameters['prompt']}"
                    }
                else:
                    return {
                        "response": f"❌ Sorry, I couldn't generate the image. {image_data.get('error', 'Unknown error')}",
                        "function_used": function_name,
                        "function_success": False,
                        "send_image": False
                    }
            
            # Handle places search specially
            elif intent == "places" and function_result["success"]:
                # For places search, format the response nicely
                places_data = function_result["result"]
                formatted_response = format_places_response(places_data)
                return {
                    "response": formatted_response,
                    "function_used": function_name,
                    "function_success": True,
                    "send_image": False
                }
            
            # --- BYPASS GEMINI FOR WEATHER ---
            elif intent == "weather":
                return {
                    "response": function_result["result"],
                    "function_used": function_name,
                    "function_success": function_result["success"],
                    "send_image": False
                }
            # --- END BYPASS ---

            # Generate natural response with the result for other functions
            follow_up_prompt = FOLLOW_UP_PROMPT.format(
                user_message=user_message,
                function_name=function_name,
                function_result=function_result["result"]
            )
            final_response = genai.GenerativeModel('gemini-1.5-flash').generate_content(follow_up_prompt)
            return {
                "response": final_response.text,
                "function_used": function_name,
                "function_success": function_result["success"],
                "send_image": False
            }
        
        # Step 3: If no clear parameters but intent is detected, ask for clarification
        elif intent in ["weather", "stock", "news", "image", "places"]:
            if intent == "image":
                # Special handling for image generation without prompt
                clarification_prompt = f"""
                {BALLU_BASE_PROMPT}
                
                The user wants to generate an image but hasn't specified what they want to see.
                Please ask them what kind of image they'd like me to create in a friendly, conversational way.
                Give them some examples like "a beautiful sunset", "a cute cat", "a futuristic city", etc.
                
                User message: "{user_message}"
                """
            else:
                clarification_prompt = f"""
                {BALLU_BASE_PROMPT}
                
                The user is asking about {intent}, but I need more specific information.
                Please ask them for the details I need in a friendly, conversational way.
                
                User message: "{user_message}"
                """
            
            response = genai.GenerativeModel('gemini-1.5-flash').generate_content(clarification_prompt)
            
            return {
                "response": response.text,
                "function_used": None,
                "function_success": None,
                "send_image": False
            }
        
        # Step 4: For general conversation, use Gemini with Ballu's personality
        else:
            # Get user context if available
            context = ""
            if user_id and db is not None:
                user_info = get_user_info(user_id)
                chat_history = get_user_chat_history(user_id, limit=3)
                
                if user_info:
                    context = f"User: {user_info.get('first_name', 'Unknown')} (Messages: {user_info.get('total_messages', 0)})\n"
                
                if chat_history:
                    context += "Recent conversation:\n"
                    for chat in reversed(chat_history):
                        context += f"User: {chat['user_message'][:100]}...\n"
                        context += f"Ballu: {chat['bot_response'][:100]}...\n"
                    context += f"Current message: {user_message}"
            
            # Create prompt with Ballu's personality and context
            prompt = BALLU_BASE_PROMPT + "\n\n" + (context + user_message if context else user_message)
            
            response = genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt)
            
            return {
                "response": response.text,
                "function_used": None,
                "function_success": None,
                "send_image": False
            }
        
    except Exception as e:
        print(f"❌ Error in intelligent response: {str(e)}")
        return {
            "response": f"Sorry, I encountered an error: {str(e)}",
            "function_used": None,
            "function_success": None,
            "send_image": False
        }

def process_function_call_direct(function_name, parameters):
    """Process a function call directly with parameters"""
    print(f"🔧 Calling function directly: {function_name} with args: {parameters}")
    
    if function_name in function_handlers:
        try:
            print(f"🔧 Function handler found: {function_name}")
            print(f"🔧 Calling {function_name} with parameters: {parameters}")
            
            # Call the function and capture the result
            result = function_handlers[function_name](**parameters)
            print(f"🔧 Function result: {result}")
            
            return {
                "function_name": function_name,
                "result": result,
                "success": True
            }
        except Exception as e:
            print(f"❌ Error in process_function_call_direct: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "function_name": function_name,
                "result": f"Error calling {function_name}: {str(e)}",
                "success": False
            }
    else:
        print(f"❌ Function {function_name} not found in handlers: {list(function_handlers.keys())}")
        return {
            "function_name": function_name,
            "result": f"Unknown function: {function_name}",
            "success": False
        }

# FastAPI app
app = FastAPI(title="Ballu - Intelligent Telegram Bot", version="1.0.0")

# Endpoint to check server health 
@app.get('/')
def check_health():
    status = {
        "message": "Ballu - Intelligent Telegram Bot with Function Calling",
        "mongodb_connected": db is not None,
        "gemini_functions": len(function_declarations),
        "available_functions": list(function_handlers.keys()),
        "creators": "Siddhant Kochhar & Shreya Sharma"
    }
    if db is not None:
        try:
            user_count = users_collection.count_documents({})
            chat_count = chat_history_collection.count_documents({})
            status["users"] = user_count
            status["total_chats"] = chat_count
        except:
            pass
    
    return status

def send_telegram_message(chat_id, text):
    try:
        if telegram_api == 'None':
            print("Warning: TELEGRAM_TOKEN not set")
            return {"error": "Telegram token not configured"}
        
        url = f"https://api.telegram.org/bot{telegram_api}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text
        }
        response = requests.post(url, json=data)
        return response.json()
    except Exception as e:
        print(f"Error sending telegram message: {str(e)}")
        return {"error": str(e)}

# Main webhook endpoint with intelligent function calling
@app.post('/webhook')
async def telegram_function(request: Request):
    try:
        # Extracting data from the request
        data = await request.json()

        # Extract message and user information
        message_data = data.get('message', {})
        message_id = message_data.get('message_id')
        user_message = message_data.get('text', 'No text')
        chat_id = message_data.get('chat', {}).get('id')
        
        # Extract user information
        user_data = message_data.get('from', {})
        user_id = user_data.get('id')
        first_name = user_data.get('first_name', 'Unknown')
        username = user_data.get('username')
        
        print(f"📨 Message from {first_name} ({user_id}): {user_message}")
        
        # Check if message has already been processed to prevent infinite loops
        if message_id and is_message_processed(message_id):
            print(f"🔄 Message {message_id} already processed, skipping...")
            return {"status": "message already processed"}
        
        # Check if this is a first-time user
        is_new_user = False
        if user_id:
            is_new_user = is_first_time_user(user_id)
            create_or_update_user(user_id, first_name, username)
            
            # Send welcome message for first-time users
            if is_new_user:
                send_welcome_message(chat_id, first_name)
                print(f"🎉 New user {first_name} ({user_id}) joined!")
        
        # Process message with intelligent function calling
        if chat_id and user_message != 'No text':
            print(f"🔄 Processing message: '{user_message}' for user {user_id} in chat {chat_id}")
            try:
                # Get intelligent response (Gemini decides which functions to call)
                ai_result = get_intelligent_response(user_message, user_id, chat_id)
                print(f"✅ AI result: {ai_result}")
            except Exception as e:
                print(f"❌ Error in get_intelligent_response: {str(e)}")
                import traceback
                traceback.print_exc()
                ai_result = {
                    "response": "Sorry, I encountered an error processing your request. Please try again!",
                    "function_used": None,
                    "function_success": False,
                    "send_image": False
                }
            
            bot_response = ai_result["response"]
            function_used = ai_result["function_used"]
            send_image = ai_result.get("send_image", False)
            generated_image = ai_result.get("generated_image")
            image_caption = ai_result.get("image_caption")
            
            # Send response to user
            send_telegram_message(chat_id, bot_response)
            
            # Send welcome image if greeting was detected
            if send_image:
                try:
                    send_welcome_image(chat_id)
                    print(f"📸 Welcome image sent to {chat_id} for greeting")
                except Exception as e:
                    print(f"⚠️ Could not send welcome image: {str(e)}")
            
            # Send generated image if available
            if generated_image:
                try:
                    success = send_generated_image(chat_id, generated_image, image_caption)
                    if success:
                        print(f"🎨 Generated image sent to {chat_id}")
                    else:
                        print(f"❌ Failed to send generated image to {chat_id}")
                except Exception as e:
                    print(f"⚠️ Could not send generated image: {str(e)}")
            
            # Determine message type based on function used
            message_type = function_used if function_used else "general"
            
            # Save chat to database
            if user_id:
                save_chat_message(user_id, user_message, bot_response, message_type, function_used)
            
            # Mark message as processed to prevent infinite loops
            if message_id:
                mark_message_processed(message_id)

        return {"status": "message processed"}
    
    except Exception as e:
        print(f"❌ Error processing webhook: {str(e)}")
        return {"status": "error", "message": str(e)}

# Endpoint to get user statistics
@app.get('/user/{user_id}')
def get_user_stats(user_id: int):
    if db is None:
        return {"error": "Database not connected"}
    
    user_info = get_user_info(user_id)
    chat_history = get_user_chat_history(user_id, limit=10)
    
    # Count function usage
    function_usage = {}
    for chat in chat_history:
        func = chat.get('function_used')
        if func:
            function_usage[func] = function_usage.get(func, 0) + 1
    
    return {
        "user_info": user_info,
        "recent_chats": len(chat_history),
        "function_usage": function_usage,
        "chat_history": chat_history
    }

# Endpoint to test function calling manually
@app.post('/test-function')
async def test_function_calling(request: Request):
    data = await request.json()
    user_message = data.get('message', 'Hello')
    
    result = get_intelligent_response(user_message)
    return result

# Endpoint to test intent extraction
@app.post('/test-intent')
async def test_intent_extraction(request: Request):
    data = await request.json()
    user_message = data.get('message', 'Hello')
    
    from prompts.ballu_prompts import get_intent_and_parameters_with_gemini
    intent, parameters = get_intent_and_parameters_with_gemini(user_message)
    
    return {
        "user_message": user_message,
        "intent": intent,
        "parameters": parameters
    }