from __future__ import annotations

from datetime import datetime
from typing import Dict


class DecisionEngine:
    def __init__(self, signal_engine, risk_engine, news_service):
        self.signal_engine = signal_engine
        self.risk_engine = risk_engine
        self.news_service = news_service

    def decide(self, market_data, current_time: datetime) -> Dict:
        signal = self.signal_engine.analyze(market_data)
        news_events = self.news_service.get_news()

        blocked = False
        block_reason = ""
        for event in news_events:
            is_blocked, reason = self.news_service.should_block_trading(current_time, event)
            if is_blocked:
                blocked = True
                block_reason = reason
                break

        rr_ratio = 2.0
        risk_ok, risk_reason = self.risk_engine.validate_trade(signal["decision"], blocked, rr_ratio)

        final_decision = "NO_TRADE"
        if risk_ok:
            final_decision = signal["decision"]

        confidence = 0
        if blocked:
            confidence = 0
        else:
            confidence = max(25, min(95, 50 + signal["score"] * 8))

        return {
            "symbol": "XAUUSD",
            "decision": final_decision,
            "confidence": int(confidence),
            "risk_ok": risk_ok,
            "risk_reason": risk_reason if not risk_ok else "",
            "news_blocked": blocked,
            "news_reason": block_reason if blocked else "",
            "signal": signal,
        }
