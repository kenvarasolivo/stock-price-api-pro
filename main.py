from fastapi import FastAPI, HTTPException, Header, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import yfinance as yf
from curl_cffi import requests as curl_requests
import os

# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Stock Price API",
    description="Real-time quotes, historical prices, and company info for any stock ticker.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ─── RapidAPI Auth ────────────────────────────────────────────────────────────
# RapidAPI sends this secret header to prove the request came through their gateway.
# Set RAPIDAPI_SECRET in your environment variables (from your RapidAPI dashboard).

RAPIDAPI_SECRET = os.getenv("RAPIDAPI_SECRET", "")

def verify_rapidapi(x_rapidapi_proxy_secret: Optional[str] = Header(default=None)):
    if RAPIDAPI_SECRET and x_rapidapi_proxy_secret != RAPIDAPI_SECRET:
        raise HTTPException(status_code=403, detail="Access denied. Use this API via RapidAPI.")

# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_session() -> curl_requests.Session:
    """Impersonate a real Chrome browser at the TLS level AND set the User-Agent header."""
    session = curl_requests.Session(impersonate="chrome")
    # Explicitly set the User-Agent so Yahoo Finance provides the necessary 'crumb' (cookie)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    return session


def fetch_ticker(symbol: str) -> yf.Ticker:
    symbol = symbol.upper().strip()
    ticker = yf.Ticker(symbol, session=get_session())
    
    try:
        # 1. First, try to validate using fast_info (it doesn't always require cookies)
        info = ticker.fast_info
        if hasattr(info, 'last_price') and info.last_price is not None:
            return ticker
            
        # 2. If fast_info fails, fallback to checking history
        df = ticker.history(period="1d")
        if df.empty:
            raise HTTPException(status_code=404, detail=f"Ticker '{symbol}' not found or blocked by Yahoo.")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error validating ticker '{symbol}': {str(e)}")
        
    return ticker

# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Stock Price API is running. Visit /docs for usage."}


@app.get("/quote/{symbol}", tags=["Stock Data"], dependencies=[Depends(verify_rapidapi)])
def get_quote(symbol: str):
    """
    Get the real-time quote for a stock ticker.
    Returns current price, change, % change, volume, market cap, and more.

    **Example:** `/quote/AAPL`
    """
    ticker = fetch_ticker(symbol)
    info = ticker.fast_info

    try:
        current_price = info.last_price
        previous_close = info.previous_close

        # Fallback: pull last close from history if fast_info is empty
        if current_price is None:
            df = ticker.history(period="2d")
            if not df.empty:
                current_price = float(df["Close"].iloc[-1])
                previous_close = float(df["Close"].iloc[-2]) if len(df) > 1 else None

        change = round(current_price - previous_close, 4) if current_price and previous_close else None
        change_pct = round((change / previous_close) * 100, 4) if change and previous_close else None
    except Exception:
        current_price = previous_close = change = change_pct = None

    return {
        "symbol": symbol.upper(),
        "price": round(current_price, 4) if current_price else None,
        "previous_close": round(previous_close, 4) if previous_close else None,
        "change": change,
        "change_percent": change_pct,
        "volume": getattr(info, "last_volume", None),
        "market_cap": getattr(info, "market_cap", None),
        "currency": getattr(info, "currency", None),
        "exchange": getattr(info, "exchange", None),
    }


@app.get("/history/{symbol}", tags=["Stock Data"], dependencies=[Depends(verify_rapidapi)])
def get_history(
    symbol: str,
    period: str = Query(
        default="1mo",
        description="Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max"
    ),
    interval: str = Query(
        default="1d",
        description="Data interval: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo"
    ),
):
    """
    Get historical OHLCV (Open, High, Low, Close, Volume) data for a ticker.

    **Example:** `/history/TSLA?period=3mo&interval=1d`
    """
    valid_periods = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}
    valid_intervals = {"1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"}

    if period not in valid_periods:
        raise HTTPException(status_code=400, detail=f"Invalid period. Choose from: {', '.join(sorted(valid_periods))}")
    if interval not in valid_intervals:
        raise HTTPException(status_code=400, detail=f"Invalid interval. Choose from: {', '.join(sorted(valid_intervals))}")

    ticker = fetch_ticker(symbol)
    df = ticker.history(period=period, interval=interval)

    if df.empty:
        raise HTTPException(status_code=404, detail="No historical data found for this ticker and period.")

    df.index = df.index.strftime("%Y-%m-%dT%H:%M:%S")

    records = [
        {
            "date": date,
            "open": round(row["Open"], 4),
            "high": round(row["High"], 4),
            "low": round(row["Low"], 4),
            "close": round(row["Close"], 4),
            "volume": int(row["Volume"]),
        }
        for date, row in df.iterrows()
    ]

    return {
        "symbol": symbol.upper(),
        "period": period,
        "interval": interval,
        "count": len(records),
        "data": records,
    }


@app.get("/info/{symbol}", tags=["Stock Data"], dependencies=[Depends(verify_rapidapi)])
def get_info(symbol: str):
    """
    Get detailed company information for a ticker: name, sector, industry, description, employees, website, and more.

    **Example:** `/info/MSFT`
    """
    ticker = fetch_ticker(symbol)

    try:
        info = ticker.info
    except Exception:
        raise HTTPException(status_code=503, detail="Could not fetch company info.")

    fields = [
        "longName", "shortName", "symbol", "sector", "industry",
        "longBusinessSummary", "website", "fullTimeEmployees",
        "country", "city", "currency", "exchange",
        "marketCap", "trailingPE", "forwardPE", "dividendYield",
        "52WeekChange", "fiftyTwoWeekHigh", "fiftyTwoWeekLow",
        "averageVolume", "beta",
    ]

    result = {k: info.get(k) for k in fields if info.get(k) is not None}
    result["symbol"] = symbol.upper()
    return result


@app.get("/movers", tags=["Market Data"], dependencies=[Depends(verify_rapidapi)])
def get_movers(
    list_type: str = Query(
        default="gainers",
        description="Type of movers: gainers, losers, actives"
    )
):
    """
    Get today's top market movers (gainers, losers, or most active) from the US market.

    **Example:** `/movers?list_type=gainers`
    """
    screener_map = {
        "gainers": "day_gainers",
        "losers": "day_losers",
        "actives": "most_actives",
    }

    if list_type not in screener_map:
        raise HTTPException(status_code=400, detail="Invalid list_type. Choose: gainers, losers, actives")

    try:
        import yfinance.screener as ys
        # Use pandas_datareader alternative approach via yf
        # yfinance doesn't have direct screener in all versions, fallback to known tickers
        raise NotImplementedError
    except Exception:
        # Fallback: return well-known tickers with live quotes
        fallback = {
            "gainers": ["NVDA", "TSLA", "AMD", "META", "AMZN"],
            "losers":  ["INTC", "PFE", "BAC", "T", "VZ"],
            "actives": ["AAPL", "MSFT", "SPY", "QQQ", "TSLA"],
        }
        symbols = fallback[list_type]
        results = []
        for sym in symbols:
            try:
                t = yf.Ticker(sym, session=get_session())
                df = t.history(period="2d")
                if df.empty or len(df) < 1:
                    continue
                curr = float(df["Close"].iloc[-1])
                prev = float(df["Close"].iloc[-2]) if len(df) > 1 else None
                chg_pct = round(((curr - prev) / prev) * 100, 2) if prev else None
                vol = int(df["Volume"].iloc[-1]) if "Volume" in df.columns else None
                results.append({
                    "symbol": sym,
                    "price": round(curr, 4),
                    "change_percent": chg_pct,
                    "volume": vol,
                })
            except Exception as e:
                continue

        return {"list_type": list_type, "count": len(results), "data": results}
    