from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Tuple


@dataclass
class Candle:
    open: float
    high: float
    low: float
    close: float
    timestamp: datetime


class MarketData:
    """Genera velas sintéticas para XAUUSD. Es suficiente para probar la lógica del sistema
    sin depender de un broker o datos reales. Puedes cambiarlo por una API real más adelante.
    """

    def __init__(self, seed: int = 42, candle_count: int = 220):
        self.seed = seed
        self.candle_count = candle_count
        self.candles = self._generate_candles()

    def _generate_candles(self) -> List[Candle]:
        rng = random.Random(self.seed)
        base = 2335.0
        candles: List[Candle] = []
        current_time = datetime.now(timezone.utc) - timedelta(minutes=self.candle_count * 5)

        last_close = base
        for _ in range(self.candle_count):
            drift = rng.uniform(-1.2, 1.8)
            move = rng.uniform(-0.8, 0.8)
            open_price = last_close
            close_price = open_price + drift + move * 0.5
            high = max(open_price, close_price) + rng.uniform(0.2, 1.1)
            low = min(open_price, close_price) - rng.uniform(0.2, 1.1)

            candles.append(Candle(
                open=open_price,
                high=high,
                low=low,
                close=close_price,
                timestamp=current_time,
            ))
            last_close = close_price
            current_time += timedelta(minutes=5)

        return candles

    def get_series(self) -> List[float]:
        return [c.close for c in self.candles]

    def get_last_candle(self) -> Candle:
        return self.candles[-1]

    def get_recent_candles(self, count: int = 20) -> List[Candle]:
        return self.candles[-count:]

    def get_pivots(self, window: int = 20) -> Tuple[float, float]:
        lows = [c.low for c in self.candles[-window:]]
        highs = [c.high for c in self.candles[-window:]]
        return min(lows), max(highs)

    def generate_fake_news_block(self) -> bool:
        return False
