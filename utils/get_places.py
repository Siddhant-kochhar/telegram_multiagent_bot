import os
import requests
from typing import Optional, Dict, Any, List

def get_user_location_from_telegram(chat_id: int, telegram_api: str) -> Optional[Dict[str, float]]:
    """
    Request user's location from Telegram
    Returns None if user doesn't share location
    """
    try:
        # Send a message asking for location
        message_url = f"https://api.telegram.org/bot{telegram_api}/sendMessage"
        message_data = {
            "chat_id": chat_id,
            "text": "📍 Please share your location so I can find places near you!",
            "reply_markup": {
                "keyboard": [[{"text": "📍 Share Location", "request_location": True}]],
                "resize_keyboard": True,
                "one_time_keyboard": True
            }
        }
        
        response = requests.post(message_url, json=message_data)
        if response.status_code == 200:
            print(f"📍 Location request sent to {chat_id}")
            return {"status": "requested"}
        else:
            print(f"❌ Failed to send location request: {response.json()}")
            return None
            
    except Exception as e:
        print(f"❌ Error requesting location: {str(e)}")
        return None

def get_places_nearby(lat: float, lon: float, query: str = "restaurants", radius: int = 5000) -> Optional[Dict[str, Any]]:
    """
    Find places near the given coordinates using Google Places API
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        query (str): Search query (e.g., "restaurants", "pubs", "cafes")
        radius (int): Search radius in meters (default: 5000 - increased for better coverage)
    
    Returns:
        Optional[Dict]: Dictionary containing places data or error message
    """
    try:
        # Get API key from environment
        api_key = os.getenv('GOOGLE_PLACES_API_KEY')
        if not api_key:
            return {
                "success": False,
                "error": "GOOGLE_PLACES_API_KEY not found in environment variables"
            }
        
        # Google Places API endpoint
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        
        # Request parameters
        params = {
            "location": f"{lat},{lon}",
            "radius": radius,
            "key": api_key,
            "type": "restaurant"  # Default type
        }
        
        # Map query to Google Places types
        type_mapping = {
            "restaurants": "restaurant",
            "pubs": "bar",
            "bars": "bar",
            "cafes": "cafe",
            "coffee": "cafe",
            "food": "restaurant",
            "dining": "restaurant",
            "nightlife": "bar"
        }
        
        # If query matches a type, use it
        query_lower = query.lower()
        for key, place_type in type_mapping.items():
            if key in query_lower:
                params["type"] = place_type
                break
        
        # If no specific type found, use text search instead
        if params["type"] == "restaurant" and query_lower != "restaurants":
            # Use text search for more flexible queries
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                "query": f"{query} near {lat},{lon}",
                "key": api_key,
                "radius": radius
            }
        
        print(f"🔍 Searching for {query} near {lat}, {lon}")
        print(f"🔍 Using URL: {url}")
        print(f"🔍 Radius: {radius}m")
        
        # Make API request
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("status") == "OK" and "results" in data:
                places = []
                
                for place in data["results"][:10]:  # Limit to 10 results
                    place_info = {
                        "name": place.get("name", "Unknown"),
                        "address": place.get("vicinity", "Address not available"),
                        "rating": place.get("rating", "No rating"),
                        "price_level": place.get("price_level", "Price not available"),
                        "types": place.get("types", [])
                    }
                    
                    # Calculate distance if available
                    if "geometry" in place and "location" in place["geometry"]:
                        place_lat = place["geometry"]["location"]["lat"]
                        place_lng = place["geometry"]["location"]["lng"]
                        # Simple distance calculation (approximate)
                        import math
                        distance = math.sqrt((lat - place_lat)**2 + (lon - place_lng)**2) * 111000  # Rough conversion to meters
                        place_info["distance"] = int(distance)
                    
                    # Add opening hours if available
                    if "opening_hours" in place:
                        place_info["open_now"] = place["opening_hours"].get("open_now", "Unknown")
                    
                    places.append(place_info)
                
                return {
                    "success": True,
                    "places": places,
                    "query": query,
                    "location": f"{lat}, {lon}",
                    "count": len(places)
                }
            elif data.get("status") == "ZERO_RESULTS":
                # Try with a larger radius if no results found
                if radius < 20000:  # Try up to 20km
                    print(f"🔍 No results found with {radius}m radius, trying with larger radius...")
                    return get_places_nearby(lat, lon, query, radius * 2)
                else:
                    return {
                        "success": False,
                        "error": f"No {query} found within 20km of your location. You might be in a remote area."
                    }
            else:
                error_msg = f"Google Places API error: {data.get('status', 'Unknown error')}"
                if data.get("error_message"):
                    error_msg += f" - {data['error_message']}"
                
                return {
                    "success": False,
                    "error": error_msg
                }
        else:
            error_msg = f"API request failed with status {response.status_code}"
            try:
                error_data = response.json()
                if "error_message" in error_data:
                    error_msg += f": {error_data['error_message']}"
            except:
                error_msg += f": {response.text}"
            
            return {
                "success": False,
                "error": error_msg
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timed out. Please try again."
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Network error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }

def format_places_response(places_data: Dict[str, Any]) -> str:
    """
    Format places data into a readable response
    """
    if not places_data.get("success"):
        return f"❌ {places_data.get('error', 'Unknown error')}"
    
    places = places_data.get("places", [])
    query = places_data.get("query", "places")
    location = places_data.get("location", "your location")
    
    if not places:
        return f"😕 No {query} found near {location}"
    
    response = f"🍽️ Found {len(places)} {query} near {location}:\n\n"
    
    for i, place in enumerate(places, 1):
        name = place.get("name", "Unknown")
        address = place.get("address", "Address not available")
        distance = place.get("distance", 0)
        rating = place.get("rating", "No rating")
        price_level = place.get("price_level", "Price not available")
        open_now = place.get("open_now", "Unknown")
        
        # Convert distance to readable format
        if distance < 1000:
            distance_str = f"{distance}m"
        else:
            distance_str = f"{distance/1000:.1f}km"
        
        # Format price level
        price_str = ""
        if price_level != "Price not available":
            price_str = "💰" * price_level
        
        # Format open now status
        open_str = ""
        if open_now == True:
            open_str = "🟢 Open now"
        elif open_now == False:
            open_str = "🔴 Closed"
        
        response += f"{i}. **{name}**\n"
        response += f"   📍 {address}\n"
        response += f"   📏 {distance_str} away\n"
        
        if rating != "No rating":
            response += f"   ⭐ {rating}/5\n"
        
        if price_str:
            response += f"   {price_str}\n"
        
        if open_str:
            response += f"   {open_str}\n"
        
        response += "\n"
    
    return response 