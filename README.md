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
