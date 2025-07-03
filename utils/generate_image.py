import os
import requests
import base64
from typing import Optional, Dict, Any

def generate_image(prompt: str, samples: int = 1) -> Optional[Dict[str, Any]]:
    """
    Generate an image using Stability AI API v2beta (1.5 megapixels)
    
    Args:
        prompt (str): The text prompt for image generation
        samples (int): Number of images to generate (default: 1)
    
    Returns:
        Optional[Dict]: Dictionary containing success status and image data or error message
    """
    try:
        # Get API key from environment
        api_key = os.getenv('DREAMSTUDIO_API_KEY')
        if not api_key:
            return {
                "success": False,
                "error": "DREAMSTUDIO_API_KEY not found in environment variables"
            }
        
        # API endpoint (new v2beta endpoint)
        url = "https://api.stability.ai/v2beta/stable-image/generate/core"
        
        # Request headers (following the exact specification)
        headers = {
            "authorization": f"Bearer {api_key}",
            "accept": "image/*",
            "stability-client-id": "ballu-telegram-bot",
            "stability-client-version": "1.0.0"
        }
        
        # Request body as multipart/form-data (following the exact specification)
        files = {
            "prompt": (None, prompt),
            "output_format": (None, "png"),
            "aspect_ratio": (None, "1:1"),
            "style_preset": (None, "photographic")
        }
        
        print(f"🎨 Generating image with prompt: {prompt}")
        print(f"🎨 API URL: {url}")
        print(f"🎨 Headers: {headers}")
        print(f"🎨 Files: {files}")
        
        # Make API request
        response = requests.post(url, headers=headers, files=files, timeout=60)
        
        if response.status_code == 200:
            # The response should be the image data directly
            image_bytes = response.content
            
            return {
                "success": True,
                "image_bytes": image_bytes,
                "prompt": prompt
            }
        else:
            error_msg = f"API request failed with status {response.status_code}"
            print(f"❌ Response status: {response.status_code}")
            print(f"❌ Response headers: {response.headers}")
            print(f"❌ Response text: {response.text}")
            
            try:
                error_data = response.json()
                print(f"❌ Error data: {error_data}")
                
                # Parse the error response according to the API specification
                if "errors" in error_data and len(error_data["errors"]) > 0:
                    error_msg += f": {', '.join(error_data['errors'])}"
                elif "name" in error_data:
                    error_msg += f": {error_data['name']}"
                elif "message" in error_data:
                    error_msg += f": {error_data['message']}"
                else:
                    error_msg += f": {error_data}"
            except Exception as e:
                print(f"❌ Error parsing JSON: {str(e)}")
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