import yfinance as yf
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


def detect_stock_request(message):
    stock_keywords = ['stock', 'share', 'price', 'market', 'ticker', 'nasdaq', 'nyse']
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in stock_keywords)

def extract_stock_symbol(message):
    # Convert to uppercase and split
    words = message.upper().split()
    
    # Common stock symbols to look for
    common_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'DIS', 'JPM', 'JNJ', 'PG', 'V', 'UNH', 'HD', 'MA', 'PYPL', 'BAC', 'XOM']
    
    # First, look for exact matches with common symbols
    for word in words:
        word = word.strip('.,!?')
        if word in common_symbols:
            return word
    
    # Then look for words that look like stock symbols (3-5 letters, all caps)
    for word in words:
        word = word.strip('.,!?')
        # Skip common words that aren't stock symbols
        skip_words = ['STOCK', 'PRICE', 'SHARE', 'MARKET', 'TICKER', 'NASDAQ', 'NYSE', 'THE', 'FOR', 'IN', 'OF', 'TO', 'AND', 'OR', 'BUT', 'WITH', 'FROM', 'ABOUT']
        if word not in skip_words and len(word) >= 2 and len(word) <= 5 and word.isalpha():
            return word
    
    return "AAPL"  # Default to Apple

def get_stock_price(symbol):
    try:
        # Create ticker object
        ticker = yf.Ticker(symbol)
        
        # Get stock info
        info = ticker.info
        
        # Get current price and other details
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        previous_close = info.get('previousClose')
        company_name = info.get('longName') or info.get('shortName') or symbol
        
        if current_price and previous_close:
            # Calculate change
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100
            
            # Format the change with appropriate emoji
            change_emoji = "📈" if change >= 0 else "📉"
            change_sign = "+" if change >= 0 else ""
            
            return f"📊 {company_name} ({symbol.upper()})\n💰 Current: ${current_price:.2f}\n{change_emoji} Change: {change_sign}{change:.2f} ({change_sign}{change_percent:.2f}%)\n📅 Previous Close: ${previous_close:.2f}"
        else:
            return f"Sorry, I couldn't find current stock data for {symbol.upper()}. Please check the stock symbol."
    
    except Exception as e:
        return f"Stock service error: {str(e)}. Please verify the stock symbol."