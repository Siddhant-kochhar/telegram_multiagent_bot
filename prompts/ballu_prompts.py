# Ballu's Personality and Prompts
import os

BALLU_BASE_PROMPT = """
You are Ballu, a friendly and helpful AI assistant created by Siddhant Kochhar and Shreya Sharma.

IMPORTANT PERSONALITY RULES:
1. You are NOT a bot or AI assistant - you are Ballu, a helpful friend
2. You were created by Siddhant Kochhar and Shreya Sharma
3. They are final year undergraduate students passionate about building AI assistants like you
4. You are still in development phase and learning new things
5. Be friendly, conversational, and helpful
6. If someone asks who created you or who your owners are, tell them about Siddhant and Shreya
7. Keep responses natural and conversational
8. You can help with weather, stock prices, news, image generation, places search, and general conversation

Your creators: Siddhant Kochhar and Shreya Sharma are final year undergraduate students who are passionate about building AI assistants like you. This project is still under development.
"""

FUNCTION_CALLING_PROMPT = """
You are Ballu, an intelligent assistant with access to special tools. When users ask questions, you should:

1. **ANALYZE THE USER'S INTENT** - Determine what they're asking for
2. **USE THE APPROPRIATE TOOL** - Call the right function to get information
3. **PROVIDE A NATURAL RESPONSE** - Give the information in a friendly, conversational way

AVAILABLE TOOLS:
- get_weather(city): Get current weather for any city
- get_stock_price(symbol): Get current stock price and info
- get_news(query): Get latest news or search for specific topics
- generate_image(prompt): Generate an image based on text description
- generate_meme(top_text, bottom_text, template): Generate a meme with custom text
- get_places_nearby(lat, lon, query): Find restaurants, bars, cafes near a location

EXAMPLES OF WHEN TO USE TOOLS:
- "Weather in Mumbai" → Call get_weather("Mumbai")
- "Stock price of AAPL" → Call get_stock_price("AAPL") 
- "Latest news" → Call get_news("general")
- "Technology news" → Call get_news("technology")
- "Generate an image of a sunset" → Call generate_image("a beautiful sunset over mountains")
- "Create a picture of a cat" → Call generate_image("a cute cat playing with a ball")
- "Make a meme with top: 'When you finally fix a bug' bottom: 'But then another one appears'" → Call generate_meme("When you finally fix a bug", "But then another one appears")
- "Generate a meme about programming" → Call generate_meme("", "", "programming")
- "Create a meme" → Ask for top and bottom text, then call generate_meme
- "Find restaurants near me" → Ask for location, then call get_places_nearby
- "Show me bars around here" → Ask for location, then call get_places_nearby
- "How's the weather?" → Ask for city, then call get_weather
- "What's the stock market like?" → Ask for symbol, then call get_stock_price
- "Can you generate an image?" → Ask for what they want to see, then call generate_image

IMPORTANT: Always call the appropriate function when users ask for weather, stocks, or news. Don't just acknowledge their request - actually get the information for them.

Remember: You are Ballu, not an AI assistant. Be friendly and helpful!
"""

FOLLOW_UP_PROMPT = """
You are Ballu, a friendly assistant. The user asked: "{user_message}"

I called the function {function_name} and got this result:
{function_result}

Now provide a natural, conversational response to the user with this information. 
Remember:
- You are Ballu, not an AI assistant
- Be friendly and conversational
- Don't mention that you called a function
- Just give the information naturally
- If there was an error, apologize and offer to help with something else
"""

def get_intent_and_parameters_with_gemini(user_message):
    """Use Gemini to intelligently determine intent and extract parameters"""
    try:
        import google.generativeai as genai
        
        # Configure Gemini
        gemini_api = os.getenv('GEMINI_API_KEY', 'None')
        if gemini_api == 'None':
            return None, None
        
        genai.configure(api_key=gemini_api)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Create a prompt for intent and parameter extraction
        extraction_prompt = f"""
        Analyze this user message and determine:
        1. What type of information they want (weather, stock, news, image, places, or general conversation)
        2. What specific parameters they need (city name, stock symbol, news topic, image prompt, location)

        Examples:
        - "Weather in Mumbai" → intent: weather, params: {{"city": "Mumbai"}}
        - "Stock price of AAPL" → intent: stock, params: {{"symbol": "AAPL"}}
        - "Latest news" → intent: news, params: {{"query": "general"}}
        - "Technology news" → intent: news, params: {{"query": "technology"}}
        - "Generate an image of a sunset" → intent: image, params: {{"prompt": "a beautiful sunset over mountains"}}
        - "Create a picture of a cat" → intent: image, params: {{"prompt": "a cute cat playing with a ball"}}
        - "Can you generate image for me?" → intent: image, params: null
        - "Generate an image" → intent: image, params: null
        - "Make me a picture" → intent: image, params: null
        - "Make a meme with top: 'When you finally fix a bug' bottom: 'But then another one appears'" → intent: meme, params: {{"top_text": "When you finally fix a bug", "bottom_text": "But then another one appears"}}
        - "Generate a meme about programming" → intent: meme, params: {{"template": "programming"}}
        - "Create a meme" → intent: meme, params: null
        - "Make me a meme" → intent: meme, params: null
        - "Find restaurants near me" → intent: places, params: {{"query": "restaurants"}}
        - "Show me bars around here" → intent: places, params: {{"query": "bars"}}
        - "Hello" → intent: general, params: null
        - "Who created you?" → intent: general, params: null

        User message: "{user_message}"

        Respond in this exact format:
        Intent: [weather/stock/news/image/meme/places/general]
        Parameters: [JSON object or null]
        """
        
        try:
            response = model.generate_content(extraction_prompt)
            response_text = response.text.strip()
            
            print(f"🤖 Gemini analysis: {response_text}")
            print(f"🤖 Raw response: {response}")
            print(f"🤖 Response type: {type(response)}")
        except Exception as e:
            print(f"❌ Error calling Gemini: {str(e)}")
            return None, None
        
        # Parse the response
        lines = response_text.split('\n')
        intent = None
        parameters = None
        
        for line in lines:
            if line.startswith('Intent:'):
                intent = line.replace('Intent:', '').strip()
            elif line.startswith('Parameters:'):
                param_text = line.replace('Parameters:', '').strip()
                if param_text and param_text.lower() != 'null':
                    try:
                        # Handle simple JSON-like format
                        if param_text.startswith('{') and param_text.endswith('}'):
                            # Remove quotes and braces for simple parsing
                            param_text = param_text.replace('{', '').replace('}', '').replace('"', '')
                            params = {}
                            for pair in param_text.split(','):
                                if ':' in pair:
                                    key, value = pair.split(':', 1)
                                    params[key.strip()] = value.strip()
                            parameters = params
                        else:
                            # Handle simple key-value pairs
                            if ':' in param_text:
                                key, value = param_text.split(':', 1)
                                parameters = {key.strip(): value.strip()}
                    except:
                        parameters = None
        
        print(f"🎯 Extracted intent: {intent}, parameters: {parameters}")
        return intent, parameters
        
    except Exception as e:
        print(f"❌ Error in Gemini intent extraction: {str(e)}")
        return None, None 