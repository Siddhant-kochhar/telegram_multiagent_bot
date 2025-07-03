import os
import requests
import redis
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

# Redis connection for caching
redis_available = False
redis_client = None

try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True, socket_connect_timeout=2, socket_timeout=2)
    # Test the connection
    redis_client.ping()
    redis_available = True
    print("✅ Redis connected successfully!")
except Exception as e:
    print(f"⚠️ Redis not available: {str(e)}")
    redis_available = False
    redis_client = None

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

def get_location_name_from_coordinates(lat: float, lon: float) -> str:
    """
    Get human-readable location name from coordinates using Google Geocoding API
    """
    try:
        api_key = os.getenv('GOOGLE_PLACES_API_KEY')
        if not api_key:
            return f"{lat:.4f}, {lon:.4f}"
        
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "latlng": f"{lat},{lon}",
            "key": api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "OK" and data.get("results"):
                # Get the most relevant result
                result = data["results"][0]
                # Try to get a readable address
                for component in result.get("address_components", []):
                    if "locality" in component.get("types", []):
                        return component.get("long_name", f"{lat:.4f}, {lon:.4f}")
                
                # Fallback to formatted address
                return result.get("formatted_address", f"{lat:.4f}, {lon:.4f}")
        
        return f"{lat:.4f}, {lon:.4f}"
    except Exception as e:
        print(f"❌ Error getting location name: {str(e)}")
        return f"{lat:.4f}, {lon:.4f}"

def get_places_nearby(lat: float, lon: float, query: str = "restaurants", radius: int = 5000, page: int = 0) -> Optional[Dict[str, Any]]:
    """
    Find places near the given coordinates using Google Places API with caching and pagination
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        query (str): Search query (e.g., "restaurants", "pubs", "cafes")
        radius (int): Search radius in meters (default: 5000)
        page (int): Page number for pagination (0 = first 5, 1 = next 5, etc.)
    
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
        
        # Create cache key
        cache_key = f"places:{lat:.4f}:{lon:.4f}:{query}:{radius}"
        
        # Check cache first (only for page 0)
        if page == 0 and redis_available:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    try:
                        cached_result = json.loads(cached_data)
                        # Check if cache is still valid (30 minutes)
                        cache_time = cached_result.get("cache_time", 0)
                        if datetime.now().timestamp() - cache_time < 1800:  # 30 minutes
                            print(f"📦 Using cached places data for {query}")
                            return cached_result
                    except:
                        pass
            except Exception as e:
                print(f"⚠️ Redis cache error: {str(e)}")
        
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
                
                for place in data["results"]:
                    place_info = {
                        "name": place.get("name", "Unknown"),
                        "address": place.get("vicinity", "Address not available"),
                        "rating": place.get("rating", "No rating"),
                        "price_level": place.get("price_level", "Price not available"),
                        "types": place.get("types", []),
                        "place_id": place.get("place_id", ""),  # Keep for reference
                        "maps_link": f"https://www.google.com/maps/search/?api=1&query={requests.utils.quote(place.get('name', 'Unknown') + ' ' + place.get('vicinity', ''))}" if place.get('name') else ""
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
                
                # Get location name
                location_name = get_location_name_from_coordinates(lat, lon)
                
                result = {
                    "success": True,
                    "places": places,
                    "query": query,
                    "location": location_name,
                    "coordinates": f"{lat}, {lon}",
                    "count": len(places),
                    "page": page,
                    "has_more": len(places) > (page + 1) * 5,
                    "cache_time": datetime.now().timestamp()
                }
                
                # Cache the result (only for page 0)
                if page == 0 and redis_available:
                    try:
                        redis_client.setex(cache_key, 1800, json.dumps(result))  # Cache for 30 minutes
                        print(f"📦 Cached places data for {query}")
                    except Exception as e:
                        print(f"⚠️ Failed to cache places data: {str(e)}")
                
                return result
            elif data.get("status") == "ZERO_RESULTS":
                # Try with a larger radius if no results found
                if radius < 20000:  # Try up to 20km
                    print(f"🔍 No results found with {radius}m radius, trying with larger radius...")
                    return get_places_nearby(lat, lon, query, radius * 2, page)
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

def format_places_response(places_data: Dict[str, Any], page: int = 0) -> str:
    """
    Format places data into a readable response with pagination
    """
    if not places_data.get("success"):
        return f"❌ {places_data.get('error', 'Unknown error')}"
    
    places = places_data.get("places", [])
    query = places_data.get("query", "places")
    location = places_data.get("location", "your location")
    
    if not places:
        return f"😕 No {query} found near {location}"
    
    # Pagination: show 5 places per page
    start_idx = page * 5
    end_idx = start_idx + 5
    current_places = places[start_idx:end_idx]
    
    if not current_places:
        return f"😕 No more {query} to show. Try a different search!"
    
    # Get emoji based on query type
    query_emoji = "🍽️"
    query_lower = query.lower()
    if "pub" in query_lower or "bar" in query_lower:
        query_emoji = "🍺"
    elif "cafe" in query_lower or "coffee" in query_lower:
        query_emoji = "☕"
    
    response = f"{query_emoji} Nearby {query.title()} for You\n\n"
    
    for i, place in enumerate(current_places, start_idx + 1):
        name = place.get("name", "Unknown")
        address = place.get("address", "Address not available")
        distance = place.get("distance", 0)
        rating = place.get("rating", "No rating")
        maps_link = place.get("maps_link", "")
        
        # Convert distance to readable format
        if distance < 1000:
            distance_str = f"{distance}m"
        else:
            distance_str = f"{distance/1000:.1f} km"
        
        # Format rating
        rating_str = ""
        if rating != "No rating":
            rating_str = f"⭐ {rating} | "
        
        response += f"{i}. **{name}**\n"
        response += f"   {rating_str}📍 {distance_str} away\n"
        response += f"   📲 [Open in Maps]({maps_link})\n\n"
    
    # Add pagination info
    total_pages = (len(places) + 4) // 5  # Ceiling division
    current_page = page + 1
    
    if total_pages > 1:
        response += f"📄 Page {current_page} of {total_pages}\n"
        if current_page < total_pages:
            response += f"💡 Type 'show more {query}' to see the next 5 places!"
    
    return response

def get_places_with_pagination(lat: float, lon: float, query: str, page: int = 0) -> Dict[str, Any]:
    """
    Get places with pagination support
    """
    try:
        # For page 0, get fresh data or from cache
        if page == 0:
            return get_places_nearby(lat, lon, query, page=page)
        
        # For subsequent pages, try to get from cache first
        cache_key = f"places:{lat:.4f}:{lon:.4f}:{query}:5000"
        if redis_available:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    try:
                        cached_result = json.loads(cached_data)
                        # Check if cache is still valid
                        cache_time = cached_result.get("cache_time", 0)
                        if datetime.now().timestamp() - cache_time < 1800:  # 30 minutes
                            # Return paginated result from cached data
                            places = cached_result.get("places", [])
                            start_idx = page * 5
                            end_idx = start_idx + 5
                            current_places = places[start_idx:end_idx]
                            
                            if current_places:
                                return {
                                    "success": True,
                                    "places": current_places,
                                    "query": query,
                                    "location": cached_result.get("location", f"{lat:.4f}, {lon:.4f}"),
                                    "coordinates": f"{lat}, {lon}",
                                    "count": len(current_places),
                                    "page": page,
                                    "has_more": len(places) > end_idx,
                                    "from_cache": True
                                }
                    except:
                        pass
            except Exception as e:
                print(f"⚠️ Redis cache error in pagination: {str(e)}")
        
        # If cache miss, get fresh data
        return get_places_nearby(lat, lon, query, page=page)
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        } 