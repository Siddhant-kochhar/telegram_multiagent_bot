# Syro Bot - Render Deployment Guide

## 🚀 Deployment Instructions

### 1. Render Configuration

**Service Settings:**
- **Name:** `telegram_multiagent_bot`
- **Language:** Python 3
- **Branch:** `siddhant_dev`
- **Region:** Oregon (US West)
- **Instance Type:** Free (or Starter for better performance)

**Build & Start Commands:**
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`

### 2. Environment Variables

Add these environment variables in Render dashboard:

```
TELEGRAM_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
MONGODB_URL=your_mongodb_atlas_connection_string
GOOGLE_PLACES_API_KEY=your_google_places_api_key
HUGGINGFACE_TOKEN=your_huggingface_token
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
UPSTASH_REDIS_REST_URL=your_upstash_redis_url
UPSTASH_REDIS_REST_TOKEN=your_upstash_redis_token
PORT=8000
PYTHON_VERSION=3.9.18
```

### 3. Deployment Steps

1. **Connect Repository:** Link your GitHub repository to Render
2. **Configure Service:** Use the settings above
3. **Add Environment Variables:** Copy from your local `.env` file
4. **Deploy:** Render will automatically build and deploy

### 4. Health Checks

The service includes health check endpoints:
- **Health Check:** `https://your-app.onrender.com/health`
- **Root:** `https://your-app.onrender.com/`

### 5. Telegram Webhook

After deployment, set your Telegram webhook:
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-app.onrender.com/webhook"}'
```

### 6. Monitoring

- Check logs in Render dashboard
- Use health endpoint for monitoring
- Monitor MongoDB Atlas connection

### 7. Free Tier Limitations

**Free Tier:**
- Spins down after 15 minutes of inactivity
- May have cold start delays
- 512 MB RAM, 0.1 CPU

**Recommended for Production:**
- Starter tier ($7/month) or higher
- Better performance and uptime
- No sleep mode

### 8. File Structure

```
telegram_multiagent_bot/
├── Dockerfile
├── render.yaml
├── start.sh
├── requirements.txt
├── main.py
├── .dockerignore
├── .gitignore
├── utils/
├── prompts/
└── DEPLOYMENT.md
```

### 9. Troubleshooting

**Common Issues:**
- Ensure all environment variables are set
- Check MongoDB Atlas IP whitelist (add 0.0.0.0/0 for Render)
- Verify Telegram webhook URL
- Check logs for startup errors

**Debug Commands:**
```bash
# Check service health
curl https://your-app.onrender.com/health

# Test webhook
curl -X POST https://your-app.onrender.com/webhook \
     -H "Content-Type: application/json" \
     -d '{"test": true}'
```

## 🎉 Your Syro bot is ready for production!
