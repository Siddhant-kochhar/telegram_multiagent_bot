# 🤖 Ballu - Intelligent Telegram Bot

> **Created by Siddhant Kochhar & Shreya Sharma**

Ballu is an intelligent AI assistant built as a Telegram bot that combines the power of Google Gemini AI with function calling capabilities. It can provide weather updates, stock prices, news, and engage in natural conversations with a friendly personality.

## ✨ Features

### 🌟 Core Capabilities
- **Intelligent Intent Recognition**: Uses Google Gemini AI to understand user intent and extract parameters
- **Function Calling**: Automatically calls appropriate functions based on user requests
- **Natural Language Processing**: Converses naturally with Ballu's friendly personality
- **User Management**: Tracks users and chat history in MongoDB
- **Welcome Experience**: Personalized welcome messages and images for new users

### 🔧 Available Functions
- **🌤️ Weather Updates**: Get current weather for any city worldwide
- **📊 Stock Information**: Real-time stock prices and market data
- **📰 News Updates**: Latest news and topic-specific articles
- **💬 General Chat**: Natural conversations with AI personality

### 🎯 Smart Features
- **Context Awareness**: Remembers conversation history and user preferences
- **Error Handling**: Robust error handling with detailed logging
- **API Integration**: Seamless integration with multiple external APIs
- **Database Storage**: MongoDB for user tracking and chat history

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MongoDB (local or cloud)
- Telegram Bot Token
- API Keys for external services

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Siddhant-kochhar/telegram_multiagent_bot.git
   cd telegram_multiagent_bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   TELEGRAM_TOKEN=your_telegram_bot_token
   WEATHER_API_KEY=your_weather_api_key
   STOCK_API_KEY=your_stock_api_key
   NEWS_API_KEY=your_news_api_key
   GEMINI_API_KEY=your_gemini_api_key
   MONGODB_URL=your_mongodb_connection_string
   ```

4. **Run the application**
   ```bash
   make run
   # or
   python main.py
   ```

## 🔑 API Keys Required

### 1. Telegram Bot Token
- Create a bot via [@BotFather](https://t.me/botfather) on Telegram
- Get your bot token and add it to `.env`

### 2. Google Gemini API Key
- Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
- Create an API key for Gemini
- Add to `.env` as `GEMINI_API_KEY`

### 3. Weather API Key
- Sign up at [OpenWeatherMap](https://openweathermap.org/api)
- Get your API key
- Add to `.env` as `WEATHER_API_KEY`

### 4. Stock API Key
- Sign up at [Alpha Vantage](https://www.alphavantage.co/)
- Get your API key
- Add to `.env` as `STOCK_API_KEY`

### 5. News API Key
- Sign up at [NewsAPI](https://newsapi.org/)
- Get your API key
- Add to `.env` as `NEWS_API_KEY`

### 6. MongoDB Connection
- Use MongoDB Atlas (cloud) or local MongoDB
- Add connection string to `.env` as `MONGODB_URL`

## 📱 Usage Examples

### Weather Queries
```
User: "What's the weather in Mumbai?"
Ballu: "🌤️ Here's the current weather in Mumbai..."

User: "How's the weather in New York?"
Ballu: "🌤️ Current conditions in New York..."
```

### Stock Queries
```
User: "Stock price of AAPL"
Ballu: "📊 Apple Inc. (AAPL) is currently trading at..."

User: "What's TSLA trading at?"
Ballu: "📊 Tesla Inc. (TSLA) current price..."
```

### News Queries
```
User: "Latest news"
Ballu: "📰 Here are the latest headlines..."

User: "Technology news"
Ballu: "📰 Latest technology news and updates..."
```

### General Chat
```
User: "Hello Ballu!"
Ballu: "👋 Hi there! I'm Ballu, your friendly AI assistant..."
```

## 🏗️ Project Structure

```
telegram_multiagent_bot/
├── main.py                 # Main FastAPI application
├── requirements.txt        # Python dependencies
├── Makefile               # Build and run commands
├── .env                   # Environment variables (create this)
├── welcome.jpeg           # Welcome image for new users
├── prompts/
│   ├── __init__.py
│   └── ballu_prompts.py   # AI prompts and personality
└── utils/
    ├── __init__.py
    ├── database.py        # MongoDB operations
    ├── get_weather.py     # Weather API integration
    ├── get_stock.py       # Stock API integration
    └── get_news.py        # News API integration
```

## 🔧 Available Commands

```bash
# Run the application
make run

# Install dependencies
make install

# Run with development server
make dev

# Check application health
curl http://localhost:8000/
```

## 🌐 API Endpoints

### Health Check
- `GET /` - Application status and statistics

### Webhook
- `POST /webhook` - Telegram webhook endpoint

### User Statistics
- `GET /user/{user_id}` - Get user chat history and statistics

### Function Testing
- `POST /test-function` - Test function calling manually

## 🚀 Deployment

### Local Development
```bash
make run
```

### Production Deployment
1. Set up a server with Python 3.8+
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables
4. Set up MongoDB
5. Configure Telegram webhook
6. Run with production server (Gunicorn, uvicorn, etc.)

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## 🛠️ Configuration

### Telegram Webhook Setup
After deploying, set your webhook URL:
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_DOMAIN>/webhook
```

### Environment Variables
All configuration is done through environment variables in the `.env` file. See the API Keys section above for required variables.

## 📊 Database Schema

### Users Collection
```json
{
  "user_id": 123456789,
  "first_name": "John",
  "username": "john_doe",
  "created_at": "2024-01-01T00:00:00Z",
  "last_active": "2024-01-01T12:00:00Z",
  "total_messages": 25,
  "preferences": {}
}
```

### Chat History Collection
```json
{
  "user_id": 123456789,
  "user_message": "Weather in Mumbai",
  "bot_response": "🌤️ Current weather in Mumbai...",
  "message_type": "weather",
  "function_used": "get_weather",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is created by Siddhant Kochhar and Shreya Sharma as a final year undergraduate project.

## 🙏 Acknowledgments

- Google Gemini AI for intelligent conversation capabilities
- Telegram Bot API for messaging platform
- MongoDB for data storage
- Various API providers (OpenWeatherMap, Alpha Vantage, NewsAPI)

## 📞 Support

For questions or issues:
- Create an issue on GitHub
- Contact the creators: Siddhant Kochhar & Shreya Sharma

---

**Made with ❤️ by Siddhant Kochhar & Shreya Sharma**