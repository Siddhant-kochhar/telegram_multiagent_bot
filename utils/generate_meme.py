import os
import requests
import random
from typing import Optional, Dict, Any, List

def get_popular_memes() -> Optional[Dict[str, Any]]:
    """
    Get popular memes from Imgflip API
    Returns a list of available meme templates
    """
    try:
        url = "https://api.imgflip.com/get_memes"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return {
                    "success": True,
                    "memes": data["data"]["memes"]
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to get memes from Imgflip API"
                }
        else:
            return {
                "success": False,
                "error": f"API request failed with status {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error fetching memes: {str(e)}"
        }

def generate_meme(template_id: str, top_text: str = "", bottom_text: str = "", 
                 username: str = None, password: str = None) -> Optional[Dict[str, Any]]:
    """
    Generate a meme using Imgflip API
    
    Args:
        template_id (str): The meme template ID
        top_text (str): Text for the top of the meme
        bottom_text (str): Text for the bottom of the meme
        username (str): Imgflip username (optional, uses default if not provided)
        password (str): Imgflip password (optional, uses default if not provided)
    
    Returns:
        Optional[Dict]: Dictionary containing meme data or error message
    """
    try:
        # Get credentials from environment or use defaults
        imgflip_username = username or os.getenv('IMGFLIP_USERNAME', 'imgflip_hubot')
        imgflip_password = password or os.getenv('IMGFLIP_PASSWORD', 'imgflip_hubot')
        
        # Debug: Check if credentials are loaded
        print(f"🎭 Using Imgflip credentials:")
        print(f"🎭 Username: {imgflip_username}")
        print(f"🎭 Password: {'*' * len(imgflip_password) if imgflip_password else 'None'}")
        
        # Check if using fallback credentials
        if imgflip_username == 'imgflip_hubot' and imgflip_password == 'imgflip_hubot':
            print("⚠️  Using fallback credentials - check your .env file!")
            print("💡 Make sure you have IMGFLIP_USERNAME and IMGFLIP_PASSWORD in your .env file")
        
        url = "https://api.imgflip.com/caption_image"
        
        # Prepare form data
        data = {
            "template_id": template_id,
            "username": imgflip_username,
            "password": imgflip_password,
            "text0": top_text,
            "text1": bottom_text,
            "font": "impact",
            "max_font_size": 50
        }
        
        # Remove empty text parameters
        if not top_text:
            data.pop("text0", None)
        if not bottom_text:
            data.pop("text1", None)
        
        print(f"🎭 Generating meme with template {template_id}")
        print(f"🎭 Top text: '{top_text}'")
        print(f"🎭 Bottom text: '{bottom_text}'")
        
        response = requests.post(url, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return {
                    "success": True,
                    "url": result["data"]["url"],
                    "page_url": result["data"]["page_url"],
                    "template_id": template_id,
                    "top_text": top_text,
                    "bottom_text": bottom_text
                }
            else:
                error_msg = result.get("error_message", "Unknown error")
                return {
                    "success": False,
                    "error": f"Imgflip API error: {error_msg}"
                }
        else:
            return {
                "success": False,
                "error": f"API request failed with status {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error generating meme: {str(e)}"
        }

def generate_random_meme(top_text: str = "", bottom_text: str = "", 
                        username: str = None, password: str = None) -> Optional[Dict[str, Any]]:
    """
    Generate a meme using a random popular template
    
    Args:
        top_text (str): Text for the top of the meme
        bottom_text (str): Text for the bottom of the meme
        username (str): Imgflip username (optional)
        password (str): Imgflip password (optional)
    
    Returns:
        Optional[Dict]: Dictionary containing meme data or error message
    """
    try:
        # Get popular memes
        memes_data = get_popular_memes()
        if not memes_data["success"]:
            return memes_data
        
        # Select a random meme template
        memes = memes_data["memes"]
        if not memes:
            return {
                "success": False,
                "error": "No meme templates available"
            }
        
        # Pick a random meme (prefer 2-box memes for top/bottom text)
        suitable_memes = [m for m in memes if m.get("box_count", 0) >= 2]
        if not suitable_memes:
            suitable_memes = memes  # Fallback to any meme
        
        selected_meme = random.choice(suitable_memes)
        
        print(f"🎭 Selected meme template: {selected_meme['name']} (ID: {selected_meme['id']})")
        
        # Generate the meme
        return generate_meme(
            template_id=selected_meme["id"],
            top_text=top_text,
            bottom_text=bottom_text,
            username=username,
            password=password
        )
    except Exception as e:
        return {
            "success": False,
            "error": f"Error generating random meme: {str(e)}"
        }

def search_meme_templates(query: str) -> Optional[Dict[str, Any]]:
    """
    Search for meme templates by name
    
    Args:
        query (str): Search query for meme names
    
    Returns:
        Optional[Dict]: Dictionary containing matching meme templates
    """
    try:
        memes_data = get_popular_memes()
        if not memes_data["success"]:
            return memes_data
        
        query_lower = query.lower()
        matching_memes = []
        
        for meme in memes_data["memes"]:
            if query_lower in meme["name"].lower():
                matching_memes.append(meme)
        
        return {
            "success": True,
            "memes": matching_memes,
            "query": query,
            "count": len(matching_memes)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error searching meme templates: {str(e)}"
        }

def get_meme_suggestions() -> List[str]:
    """
    Get a list of popular meme template names for suggestions
    """
    try:
        memes_data = get_popular_memes()
        if not memes_data["success"]:
            return ["One Does Not Simply", "Ancient Aliens", "Two Buttons"]
        
        # Return names of popular memes
        return [meme["name"] for meme in memes_data["memes"][:10]]
    except:
        return ["One Does Not Simply", "Ancient Aliens", "Two Buttons", "Drake Hotline Bling", "Distracted Boyfriend"]

def format_meme_response(meme_data: Dict[str, Any]) -> str:
    """
    Format meme data into a readable response
    """
    if not meme_data.get("success"):
        return f"❌ {meme_data.get('error', 'Unknown error')}"
    
    url = meme_data.get("url", "")
    page_url = meme_data.get("page_url", "")
    top_text = meme_data.get("top_text", "")
    bottom_text = meme_data.get("bottom_text", "")
    
    response = "🎭 **Your Meme is Ready!**\n\n"
    
    if top_text:
        response += f"📝 **Top:** {top_text}\n"
    if bottom_text:
        response += f"📝 **Bottom:** {bottom_text}\n"
    
    response += f"\n🖼️ [View Meme]({url})\n"
    response += f"🌐 [View on Imgflip]({page_url})\n"
    
    return response 