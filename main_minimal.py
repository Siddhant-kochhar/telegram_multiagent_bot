from fastapi import FastAPI, Request
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(title="Syro - Minimal Test", version="1.0.0")

@app.get("/")
def home():
    return {"message": "Bot is alive!", "status": "healthy"}

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": "2025-08-25"}

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        print("📩 Incoming Telegram update:", data)
        return {"ok": True, "message": "Webhook received"}
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        return {"ok": False, "error": str(e)}

@app.post("/webhook/webhook")
async def webhook_double(request: Request):
    """Alternative webhook endpoint for double /webhook path"""
    return await webhook(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
