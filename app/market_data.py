from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

import requests


class NewsService:
    """Servicio de noticias macro para XAUUSD.

    Intenta usar TradingEconomics si existe API key; si no, devuelve un evento de demo
    de forma local para que el sistema pueda probarse sin depender de un servicio externo.
    """

    def __init__(self, config):
        self.config = config
        self.api_key = os.getenv("TRADINGECONOMICS_API_KEY")
        self.base_url = os.getenv("TRADINGECONOMICS_URL", "https://api.tradingeconomics.com")

    def get_news(self) -> List[Dict[str, Any]]:
        if self.api_key:
            try:
                payload = {
                    "c": "us",
                    "f": "json",
                    "token": self.api_key,
                }
                response = requests.get(
                    f"{self.base_url}/calendar",
                    params=payload,
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()
                if isinstance(data, list):
                    return self._normalize_news(data)
            except Exception:
                pass

        return self._demo_news()

    def _normalize_news(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []
        for item in data[:10]:
            name = str(item.get("name") or item.get("event") or "").strip()
            if not name:
                continue
            normalized.append({
                "event": name,
                "country": item.get("country") or "United States",
                "impact": str(item.get("impact") or "medium").lower(),
                "time_utc": item.get("time") or item.get("date") or datetime.now(timezone.utc).isoformat(),
                "actual": item.get("actual"),
                "forecast": item.get("forecast"),
                "previous": item.get("previous"),
            })
        return normalized

    def _demo_news(self) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        event_time = (now + timedelta(minutes=35)).strftime("%Y-%m-%dT%H:%M:%SZ")
        return [{
            "event": "CPI",
            "country": "United States",
            "impact": "high",
            "time_utc": event_time,
            "actual": None,
            "forecast": "3.1",
            "previous": "3.2",
        }]

    def should_block_trading(self, current_time: datetime, event: Dict[str, Any]) -> Tuple[bool, str]:
        event_time_raw = event.get("time_utc") or event.get("date")
        if not event_time_raw:
            return False, "Sin fecha del evento"

        try:
            if event_time_raw.endswith("Z"):
                event_time = datetime.fromisoformat(event_time_raw.replace("Z", "+00:00"))
            else:
                event_time = datetime.fromisoformat(event_time_raw)
        except ValueError:
            return False, "Formato de fecha no válido"

        minutes_to_event = (event_time - current_time).total_seconds() / 60.0
        impact = str(event.get("impact") or "").lower()

        if impact == "high" and abs(minutes_to_event) <= self.config.high_impact_block_minutes:
            return True, f"Bloqueado por evento de alto impacto: {event.get('event')}"

        if impact == "medium" and abs(minutes_to_event) <= self.config.medium_impact_block_minutes:
            return True, f"Bloqueado por evento de impacto medio: {event.get('event')}"

        return False, "No hay bloqueo por noticias"

    def classify_event(self, event_name: str) -> str:
        name = (event_name or "").lower()
        for keyword in self.config.high_impact_events:
            if keyword.lower() in name:
                return "high"
        return "medium"
