import os
import re
import time
import json
import uuid
from datetime import datetime, timedelta
from typing import Literal, Optional
import requests
import yfinance as yf
from fastapi import APIRouter, Request, Response, Body, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
from bson import ObjectId
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from tavily import TavilyClient
from serpapi.google_search import GoogleSearch
from finnhub import Client as FinnhubClient
from dotenv import load_dotenv

# Router definition
chatbot_router = APIRouter(prefix="/chat", tags=["chat"])
templates = Jinja2Templates(directory="templates")

load_dotenv()

# MongoDB Setup
uri = os.getenv("MONGODB_URI")
client = MongoClient(uri) 
db = client["financial_sight"] 
collection = db["conversation_logs"] 

# API Keys
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
MARKETAUX_API_KEY = os.getenv("MARKETAUX_API_KEY")
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Clients
finnhub_client = FinnhubClient(api_key=FINNHUB_API_KEY) if FINNHUB_API_KEY else None
tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

# Tool Definitions
def tavily_search(
        query: str,
        max_results: int = 5,
        topic: Literal["general", "news", "finance"] = "general",
        include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )

def serpapi_news_search(query: str, max_results: int = 5):
    """Search Google News via SerpAPI (SAFE, compact)"""

    params = {
        "engine": "google_news",
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "num": max_results,
        "sort": "date"
    }

    results = GoogleSearch(params).get_dict().get("news_results", [])

    cleaned = []
    for r in results[:max_results]:
        cleaned.append({
            "title": r.get("title", ""),
            "source": r.get("source", ""),
            "url": r.get("link", ""),
            "published": r.get("date", "")
        })

    return cleaned
def marketaux_stock_news(symbol: str, limit: int = 5):
    """Fetch news from MarketMuse"""
    try:
        url = "https://api.marketaux.com/v1/news/all"
        params = {
            "symbols": symbol,
            "filter_entities": "true",
            "language": "en",
            "limit": limit,
            "api_token": MARKETAUX_API_KEY
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        return [
            {
                "title": n.get("title"),
                "summary": n.get("description"),
                "source": n.get("source"),
                "url": n.get("url"),
                "published": n.get("published_at")
            }
            for n in data.get("data", [])
        ]

    except Exception as e:
        return {"error": str(e)}
def finnhub_stocks_news(symbol: str, limit: int = 5):
    """Fetch latest stock-specific news from Finnhub"""

    try:
        today = datetime.utcnow().date()
        past = today - timedelta(days=7)

        news = finnhub_client.company_news(
            symbol,
            _from=past.strftime("%Y-%m-%d"),
            to=today.strftime("%Y-%m-%d")
        )

        return [
            {
                "title": n.get("headline", ""),
                "source": n.get("source", "Finnhub"),
                "url": n.get("url", ""),
                "published": n.get("datetime", ""),
                "summary": n.get("summary", "")
            }
            for n in news
        ][:limit]

    except Exception as e:
        print("Finnhub error:", e)
        return []


def alphavantage_stock_quote(symbol: str):
    """Fetch real-time stock data from Alpha Vantage"""
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHAVANTAGE_API_KEY}"
        data = requests.get(url, timeout=10).json()

        q = data.get("Global Quote", {})

        # 🚨 CRITICAL CHECK
        if not q or "05. price" not in q:
            return {"error": f"No real-time data available for {symbol} from Alpha Vantage"}

        return {
            "symbol": symbol,
            "price": q.get("05. price"),
            "high": q.get("03. high"),
            "low": q.get("04. low"),
            "volume": q.get("06. volume"),
        }

    except Exception as e:
        return {"error": str(e)}
def yfinance_stock_summary(symbol: str):
    """Fetch stock summary using yfinance"""
    try:
        info = yf.Ticker(symbol).info
        return {
            "symbol": symbol,
            "longName": info.get("longName"),
            "currentPrice": info.get("currentPrice"),
            "dayHigh": info.get("dayHigh"),
            "dayLow": info.get("dayLow"),
            "marketCap": info.get("marketCap"),
            "website": info.get("website"),
        }
    except:
        return {}


mapping = {"airtel": "BHARTIARTL.NS", "jio": "RELIANCE.NS", "reliance": "RELIANCE.NS", "google": "GOOGL", "amazon": "AMZN", "apple": "AAPL", "tesla": "TSLA", "microsoft": "MSFT","tatamotors":"TMCV.NS","hdfc":"HDFCBANK.NS"}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json"
}
def resolve_stock_symbol(query: str, retries: int = 3):
    """Resolve company name to stock symbol"""
    q = query.lower().strip()

    if q in mapping:
        return mapping[q]

    # 2️⃣ Yahoo Finance search
    url = "https://query1.finance.yahoo.com/v1/finance/search"
    params = {"q": query, "quotesCount": 5, "newsCount": 0}

    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=5)

            if r.status_code != 200:
                raise ValueError("Yahoo Finance unavailable")

            data = r.json()

            # Prefer NSE if available
            for qte in data.get("quotes", []):
                if qte.get("symbol", "").endswith(".NS"):
                    return qte["symbol"]

            # Otherwise any equity
            for qte in data.get("quotes", []):
                if qte.get("symbol") and qte.get("quoteType") in ("EQUITY", "ETF"):
                    return qte["symbol"]

            raise ValueError(f"'{query}' is not a publicly listed stock")

        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(0.5)


# Agent Factory
def get_agent(model_name: str = "groq:qwen/qwen3-32b"):
    
    # Handle Groq Compound model specifically
    if "groq" in model_name and "compound" in model_name:
        return create_agent(
            model=model_name,
             # No tools for this specific mode as per user request
            checkpointer=InMemorySaver(),
            system_prompt="You are a Financial Agent that solves user queries and provides  real-time relevant responses based on what the user asks alwys include the important links and details."
        )

    elif "gpt-5.2" in model_name:
        # Map pseudo-model 'gpt-5.2' to a real high-performance model
        real_model = "gpt-5.2" 
        return create_agent(
            model=real_model,
            tools =[
                resolve_stock_symbol,
                tavily_search,
                serpapi_news_search,
                yfinance_stock_summary,
                alphavantage_stock_quote
            ],
            checkpointer=InMemorySaver(),
            system_prompt="""
You are a Financial Agent designed to answer user queries accurately and in real-time.
Rules:
- Always use tool for to do anything.
- Always provide relevant and up-to-date information based on the user's question.
- Include important links, sources, and details wherever possible.
- Use 'resolve_stock_symbol' first for company names to get accurate stock data.
- For stock-related queries, fetch the latest quotes and summaries.
- For general financial news, prioritize reliability and recency.
- Never hallucinate data; if information is unavailable, clearly state that.
- Summarize key points concisely for easy understanding.
"""
        )
    
    return create_agent(
    model=model_name,
    tools=[
        resolve_stock_symbol,
        # marketaux_stock_news,
        # finnhub_stocks_news,
        alphavantage_stock_quote,
        yfinance_stock_summary,
        tavily_search,
        serpapi_news_search
    ],
    checkpointer=InMemorySaver(),
    system_prompt="""You are a Financial Assistant giving real-time stock data and news.
Rules:
1. Always identify stock symbols using 'resolve_stock_symbol' first do not use any other assumptions.
2. Fetch stock data via 'yfinance_stock_summary' (India) or 'alphavantage_stock_quote' (US).
3. Search content via 'tavily_search' or 'serpapi_news_search'.
4. Provide accurate, cited answers with links. Do not hallucinate."""
)

    

# Default agent
agent = get_agent()

def get_history(session_id: str, email: str, limit: int = None):
    if collection is None: return []
    # Filter by both session_id and user email
    query = collection.find({"session_id": session_id, "user_email": email}).sort("timestamp", -1)
    if limit: query = query.limit(limit)
    history = list(query)
    msgs = []
    for h in reversed(history):
        msgs.append({"role": "user", "content": h["user_input"]})
        msgs.append({"role": "assistant", "content": h["response"]})
    return msgs

@chatbot_router.post("/new_chat")
async def new_chat(request: Request):
    user = request.session.get("user")
    if not user: raise HTTPException(status_code=401, detail="Unauthorized")
    
    new_session_id = str(uuid.uuid4())
    resp = JSONResponse(content={"session_id": new_session_id})
    resp.set_cookie(key="session_id", value=new_session_id, httponly=True)
    return resp

@chatbot_router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/auth")
        
    session_id = request.cookies.get("session_id")
    response = templates.TemplateResponse("chatbot.html", {"request": request, "user": user})
    if not session_id:
        session_id = str(uuid.uuid4())
        response.set_cookie(key="session_id", value=session_id, httponly=True)
    return response

@chatbot_router.get("/sessions")
async def get_sessions(request: Request):
    user = request.session.get("user")
    if not user: return JSONResponse(content={"error": "Unauthorized"}, status_code=401)
    
    if collection is None: return []
    email = user.get("email")
    pipeline = [
        {"$match": {"user_email": email}},
        {"$sort": {"timestamp": 1}}, 
        {"$group": {
            "_id": "$session_id", 
            "first_message": {"$first": "$user_input"}, 
            "last_timestamp": {"$last": "$timestamp"}
        }}, 
        {"$sort": {"last_timestamp": -1}}
    ]
    return list(collection.aggregate(pipeline))

@chatbot_router.get("/history/{target_session_id}")
async def history_session(request: Request, target_session_id: str):
    user = request.session.get("user")
    if not user: return JSONResponse(content={"error": "Unauthorized"}, status_code=401)
    return get_history(target_session_id, user.get("email"))

@chatbot_router.get("/delete_session/{target_session_id}")
async def delete_session(request: Request, target_session_id: str):
    user = request.session.get("user")
    if not user: raise HTTPException(status_code=401, detail="Unauthorized")
    
    if collection is None: raise HTTPException(status_code=500, detail="DB error")
    collection.delete_many({"session_id": target_session_id, "user_email": user.get("email")})
    return {"success": True}
    
@chatbot_router.post("/chat")
async def chat_api(request: Request, payload: dict = Body(...)):
    user_input = payload.get("message")
    requested_model = payload.get("model", "groq:qwen/qwen3-32b")
    session_id = request.cookies.get("session_id")
    
    if not user_input:
        raise HTTPException(status_code=400, detail="No message provided")
    
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    email = user.get("email")
    history = get_history(session_id, email, limit=3)
    
    # --- DEBUG LOGGING START ---
    # print(f"\n[DEBUG] Session ID: {session_id}")
    # print(f"[DEBUG] User Email: {email}")
    # print(f"[DEBUG] History Loaded: {len(history)} items")
    total_hist_len = 0
    if history:
        for i, h in enumerate(history):
            content = h.get('content', '')
            c_len = len(content)
            total_hist_len += c_len
    #         print(f"[DEBUG] Hist #{i} ({h.get('role', 'unknown')}) [Len: {c_len}]: {content[:50]}...")
    # print(f"[DEBUG] Total History Char Limit: {total_hist_len}")
    # print(f"[DEBUG] Current Input [Len: {len(user_input)}]: {user_input[:50]}...")
    # --- DEBUG LOGGING END ---

    messages = history + [{"role": "user", "content": user_input}]

    # Determine Agent
    current_agent = get_agent(requested_model)

    try:
        response = current_agent.invoke(
            {"messages": messages}, 
            {"configurable": {"thread_id": f"{email}_{session_id}"}}
        )
        final_answer = response["messages"][-1].content
        
        msg_id = None
        if collection is not None:
            collection.insert_one({
                "session_id": session_id, 
                "user_email": email, 
                "timestamp": datetime.utcnow(), 
                "user_input": user_input, 
                "response": final_answer,
                "model": requested_model
            })
            
        return {"content": final_answer}

    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

