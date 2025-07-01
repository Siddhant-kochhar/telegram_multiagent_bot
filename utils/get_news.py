import requests
import os
from dotenv import load_dotenv

load_dotenv()
news_api_key = os.getenv('NEWS_API_KEY', 'None')




def detect_news_request(message):
    news_keywords = ['news', 'headlines', 'breaking', 'latest', 'updates', 'current events']
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in news_keywords)

def extract_news_query(message):
    # Extract what kind of news user wants
    message_lower = message.lower()
    
    # If asking for specific topic
    if 'about' in message_lower:
        parts = message_lower.split('about')
        if len(parts) > 1:
            return parts[1].strip()
    
    # Look for specific topics
    topics = ['technology', 'sports', 'business', 'health', 'science', 'entertainment']
    for topic in topics:
        if topic in message_lower:
            return topic
    
    return "latest"  # Default to latest news

def get_news(query="latest", country="in"):
    try:
        if news_api_key == 'None':
            return "News API key not configured."
            
        if query == "latest":
            # Get top headlines
            url = f"https://newsapi.org/v2/top-headlines?country={country}&apiKey={news_api_key}"
        else:
            # Search for specific news
            url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&language=en&apiKey={news_api_key}"
        
        response = requests.get(url)
        data = response.json()
        
        # Check for API errors
        if response.status_code != 200:
            if "error" in data:
                return f"News API error: {data['error']}"
            return "Sorry, I couldn't fetch news at the moment. Please try again later."
        
        if data.get('articles'):
            articles = data['articles'][:5]  # Get top 5 articles
            
            if query == "latest":
                news_text = "📰 Latest Headlines:\n\n"
            else:
                news_text = f"📰 News about '{query.title()}':\n\n"
            
            for i, article in enumerate(articles, 1):
                title = article.get('title', 'No title')
                source = article.get('source', {}).get('name', 'Unknown source')
                description = article.get('description', 'No description')
                
                # Truncate description if too long
                if description and len(description) > 100:
                    description = description[:100] + "..."
                
                news_text += f"{i}. {title}\n"
                news_text += f"   📰 Source: {source}\n"
                if description and description != "No description":
                    news_text += f"   📝 {description}\n"
                news_text += "\n"
            
            return news_text
        else:
            return f"Sorry, I couldn't find news about '{query}'. Please try a different topic."
    
    except Exception as e:
        return f"News service error: {str(e)}"