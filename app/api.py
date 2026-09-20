from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import Config
from app.decision_engine import DecisionEngine
from app.market_data import MarketData
from app.news_service import NewsService
from app.paper_trading import PaperTrading
from app.risk_engine import RiskEngine
from app.signal_engine import SignalEngine

app = FastAPI(title="XAUUSD Trading AI", version="1.0.0")
config = Config.from_env()
market_data = MarketData()
news_service = NewsService(config)
signal_engine = SignalEngine()
risk_engine = RiskEngine(config)
decision_engine = DecisionEngine(signal_engine, risk_engine, news_service)
paper = PaperTrading()


class CloseTradeRequest(BaseModel):
    exit_price: float = Field(gt=0)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "symbol": config.symbol, "mode": "paper"}


@app.get("/analysis")
def analysis() -> Dict[str, Any]:
    return decision_engine.decide(market_data, datetime.now(timezone.utc))


@app.get("/news")
def news():
    return {"events": news_service.get_news()}


@app.get("/account")
def account():
    return paper.account()


@app.get("/trades")
def trades():
    return {"trades": paper.list_trades()}


@app.post("/paper/open")
def open_paper_trade():
    result = analysis()
    if result["decision"] not in ("BUY", "SELL"):
        raise HTTPException(status_code=409, detail={
            "message": "No se abrió operación: la decisión es NO_TRADE",
            "analysis": result,
        })
    signal = result["signal"]
    entry = signal["latest_close"]
    atr = max(float(signal["atr"]), 0.1)
    if result["decision"] == "BUY":
        stop = entry - atr
        target = entry + atr * config.min_rr_ratio
    else:
        stop = entry + atr
        target = entry - atr * config.min_rr_ratio
    trade = paper.open_trade({
        "symbol": config.symbol,
        "decision": result["decision"],
        "entry": entry,
        "stop_loss": stop,
        "take_profit": target,
    }, config.max_risk_per_trade)
    return {"analysis": result, "trade": trade}


@app.post("/paper/close/{trade_id}")
def close_paper_trade(trade_id: int, request: CloseTradeRequest):
    try:
        return paper.close_trade(trade_id, request.exit_price)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
