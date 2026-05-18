# 📈 Stock Price API — Render + RapidAPI Deployment Guide

A FastAPI-powered stock data API using **yfinance** (no paid data subscription needed).

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/quote/{symbol}` | Real-time price, change, volume, market cap |
| GET | `/history/{symbol}` | Historical OHLCV data (period + interval) |
| GET | `/info/{symbol}` | Company info, sector, PE ratio, 52-week range |
| GET | `/movers` | Top gainers / losers / most active |

---

## Run Locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Visit http://localhost:8000/docs for the interactive Swagger UI.

---

## Step 1 — Deploy to Render

1. Push this folder to a **GitHub repo** (public or private)

2. Go to https://render.com → **New → Web Service**

3. Connect your GitHub repo

4. Render will auto-detect the `render.yaml` — confirm these settings:
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

5. Under **Environment Variables**, add:
   - `RAPIDAPI_SECRET` → leave blank for now (you'll get this from RapidAPI later)

6. Click **Create Web Service**

7. Wait ~2 minutes. You'll get a public URL like:
   ```
   https://stock-price-api.onrender.com
   ```

8. Test it:
   ```bash
   curl https://stock-price-api.onrender.com/
   ```

> ⚠️ **Render Free Tier Note:** The service spins down after 15 minutes of inactivity.
> The first request after sleep takes ~30 seconds (cold start).
> Fix this with UptimeRobot — see Step 2.

---

## Step 2 — Keep It Awake with UptimeRobot

Render's free tier sleeps after 15 min of no traffic. UptimeRobot pings it every 5 minutes for free, keeping it always on.

1. Go to https://uptimerobot.com → **Create a free account**

2. Click **Add New Monitor**

3. Set:
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** Stock API
   - **URL:** `https://your-app.onrender.com/` ← your Render URL
   - **Monitoring Interval:** every **5 minutes**

4. Click **Create Monitor**

That's it — UptimeRobot pings your `/` health check endpoint every 5 minutes, preventing Render from sleeping it.

---

## Step 3 — List on RapidAPI

1. Go to https://rapidapi.com/provider → create a provider account

2. Click **Add New API → Specify an existing API**

3. Fill in:
   - **Base URL:** `https://your-app.onrender.com`
   - **Name:** Stock Price API
   - **Category:** Finance

4. Add endpoints in the RapidAPI dashboard:

   | Method | Path | Description |
   |--------|------|-------------|
   | GET | `/quote/{symbol}` | Real-time stock quote |
   | GET | `/history/{symbol}` | Historical OHLCV prices |
   | GET | `/info/{symbol}` | Company details |
   | GET | `/movers` | Top gainers / losers / actives |

5. In **Settings → Security**, copy the **Proxy Secret**

6. Back on Render, go to **Environment → Environment Variables** and set:
   ```
   RAPIDAPI_SECRET = <paste your RapidAPI proxy secret here>
   ```
   Render will redeploy automatically.

7. Go to **Monetization** on RapidAPI and set your pricing tiers (see suggestion below)

8. **Publish!**

---

## Suggested Pricing Tiers

| Plan | Requests/month | Price |
|------|----------------|-------|
| Free | 100 | $0 |
| Basic | 5,000 | $9.99 |
| Pro | 50,000 | $29.99 |
| Ultra | 500,000 | $99.99 |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `RAPIDAPI_SECRET` | From RapidAPI → Settings → Security. Validates requests came through RapidAPI. Leave blank to disable (local dev only). |

---

## Example Requests

```bash
# Real-time quote
curl https://your-app.onrender.com/quote/AAPL \
  -H "X-RapidAPI-Proxy-Secret: YOUR_SECRET"

# 3 months of daily history
curl "https://your-app.onrender.com/history/TSLA?period=3mo&interval=1d" \
  -H "X-RapidAPI-Proxy-Secret: YOUR_SECRET"

# Company info
curl https://your-app.onrender.com/info/MSFT \
  -H "X-RapidAPI-Proxy-Secret: YOUR_SECRET"

# Top gainers
curl "https://your-app.onrender.com/movers?list_type=gainers" \
  -H "X-RapidAPI-Proxy-Secret: YOUR_SECRET"
```

---

## Files Overview

```
stock-api/
├── main.py           # FastAPI app
├── requirements.txt  # Python dependencies
├── render.yaml       # Render deployment config
└── README.md         # This file
```
