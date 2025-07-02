import os 
import requests
from dotenv import load_dotenv
from datetime import datetime

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
            if 'main' in data and 'weather' in data and 'wind' in data:
                temp = data['main']['temp']
                feels_like = data['main'].get('feels_like', temp)
                humidity = data['main'].get('humidity', '-')
                wind_speed = data['wind'].get('speed', '-')
                description = data['weather'][0]['description']
                city = data['name']
                country = data['sys']['country']
                date_str = datetime.now().strftime('%A, %d %B %Y')

                # Suggestion based on condition
                condition = description.lower()
                if 'rain' in condition or 'shower' in condition:
                    tip = "Don't forget your umbrella! ☔ Stay dry!"
                elif 'clear' in condition or 'sun' in condition:
                    tip = "It's a sunny day! 😎 Don't forget your sunglasses and sunscreen."
                elif 'cloud' in condition:
                    tip = "A bit cloudy today. Perfect for a walk! ☁️"
                elif 'snow' in condition:
                    tip = "Brrr! It's snowy. Dress warmly and stay safe! ❄️🧣"
                elif 'storm' in condition or 'thunder' in condition:
                    tip = "Stormy weather ahead. Stay indoors and stay safe! ⛈️"
                elif 'mist' in condition or 'fog' in condition:
                    tip = "It's misty out there. Drive carefully! 🌫️"
                else:
                    tip = "Have a wonderful day! 😊"

                return (
                    f"\n💬 🌤️ Weather in {city}, {country}\n\n"
                    f"📅 Date: {date_str}  \n"
                    f"🌡️ Temperature: {temp}°C (Feels like {feels_like}°C)  \n"
                    f"💧 Humidity: {humidity}%  \n"
                    f"🌬️ Wind Speed: {wind_speed} m/s  \n"
                    f"🌥️ Condition: {description.title()}\n\n"
                    f"📍 {tip}"
                )
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