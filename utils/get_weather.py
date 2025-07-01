import os 
import requests
from dotenv import load_dotenv

load_dotenv()

weather_api_token = os.getenv('WEATHER_API_KEY')




def detect_weather_request(message):
    weather_keywords = ['weather', 'temperature', 'temp', 'hot', 'cold', 'rain', 'sunny', 'cloudy']
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in weather_keywords)

def extract_city_from_message(message):
    # Simple city extraction - we'll improve this later
    words = message.split()
    # Look for words after "in" or "weather"
    for i, word in enumerate(words):
        if word.lower() in ['in', 'for'] and i + 1 < len(words):
            return words[i + 1].strip('.,!?')
    
    # If no "in" found, assume last word might be city
    if len(words) > 1:
        return words[-1].strip('.,!?')
    
    return "London"  # Default city

def get_weather(city_name):
    print(f"🌤️ WEATHER FUNCTION CALLED with city: {city_name}")
    try:
        # Check if API key is configured
        if not weather_api_token or weather_api_token == 'None':
            print(f"❌ Weather API key not configured")
            return "Sorry, the weather service is not configured. Please check the weather API key."
        
        # Clean up city name
        city_name = city_name.strip()
        print(f"🌤️ Getting weather for: {city_name}")
        print(f"🌤️ API Key (first 10 chars): {weather_api_token[:10] if weather_api_token else 'None'}...")
        
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={weather_api_token}&units=metric"
        print(f"🌤️ Making request to: {url[:50]}...")
        
        response = requests.get(url)
        data = response.json()
        
        print(f"🌤️ Weather API response status: {response.status_code}")
        print(f"🌤️ Weather API response: {data}")
        
        if response.status_code != 200:
            print(f"🌤️ Weather API error: {data}")

        # Check for API errors
        if response.status_code == 200:
            if 'main' in data and 'weather' in data:
                temp = data['main']['temp']
                description = data['weather'][0]['description']
                city = data['name']
                country = data['sys']['country']

                return f"🌤️ Weather in {city}, {country}:\n🌡️ Temperature: {temp}°C\n☁️ Condition: {description.title()}"
            else:
                return f"Sorry, I couldn't get complete weather data for {city_name}. Please try again."
        elif response.status_code == 404:
            return f"Sorry, I couldn't find weather data for '{city_name}'. Please check the city name and try again."
        elif response.status_code == 401:
            return "Sorry, there's an issue with the weather service configuration. Please try again later."
        else:
            return f"Sorry, I couldn't get weather data for {city_name}. Please try again later."
    
    except requests.exceptions.RequestException as e:
        return f"Sorry, I'm having trouble connecting to the weather service. Please try again later."
    except Exception as e:
        print(f"Weather API error for {city_name}: {str(e)}")
        return f"Sorry, I encountered an error while getting weather data for {city_name}. Please try again."

# Test the weather function (add this temporarily)
if __name__ == "__main__":
    print("🧪 Testing weather function...")
    result = get_weather("London")
    print(f"🧪 Test result: {result}")