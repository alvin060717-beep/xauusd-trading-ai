from __future__ import annotations

from typing import Dict, List, Tuple


class SignalEngine:
    """Motor técnico para XAUUSD.

    Evalúa: tendencia, estructura, FVG, liquidez y momentum.
    """

    def __init__(self):
        self.min_confidence = 7

    def analyze(self, market_data) -> Dict:
        candles = market_data.get_recent_candles(50)
        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]

        ema_20 = self._ema(closes, 20)
        ema_50 = self._ema(closes, 50)
        ema_200 = self._ema(closes, 200)
        vwap = self._vwap(candles)
        atr = self._atr(candles, 14)

        last_close = closes[-1]
        prev_close = closes[-2]
        last_high = highs[-1]
        last_low = lows[-1]
        recent_high = max(highs[-10:])
        recent_low = min(lows[-10:])

        score = 0
        reasons = []

        # Trend
        if last_close > ema_20 > ema_50:
            score += 2
            reasons.append("Tendencia alcista: precio por encima de EMA20 y EMA50")
        elif last_close < ema_20 < ema_50:
            score -= 2
            reasons.append("Tendencia bajista: precio por debajo de EMA20 y EMA50")
        else:
            reasons.append("Sin tendencia clara por EMAs")

        if last_close > ema_200:
            score += 1
            reasons.append("Precio por encima de EMA200")
        elif last_close < ema_200:
            score -= 1
            reasons.append("Precio por debajo de EMA200")

        # Momentum
        if last_close > vwap:
            score += 1
            reasons.append("Precio por encima del VWAP")
        else:
            score -= 1
            reasons.append("Precio por debajo del VWAP")

        # Liquidity sweep / recent extremes
        if last_low < recent_low and last_close > recent_low:
            score += 2
            reasons.append("Sweep de liquidez bajista recuperado")
        elif last_high > recent_high and last_close < recent_high:
            score -= 2
            reasons.append("Sweep de liquidez alcista rechazado")

        # FVG rough logic
        fvg = self._detect_fvg(candles)
        if fvg == "bullish":
            score += 2
            reasons.append("FVG alcista identificado")
        elif fvg == "bearish":
            score -= 2
            reasons.append("FVG bajista identificado")

        # Structure / breakout
        if last_close > prev_close and last_high > recent_high * 0.998:
            score += 1
            reasons.append("Estructura alcista con nuevo máximo local")
        elif last_close < prev_close and last_low < recent_low * 1.002:
            score -= 1
            reasons.append("Estructura bajista con nuevo mínimo local")

        # Volatility filter
        if atr <= 0:
            atr = 1
        if atr > 4:
            score -= 1
            reasons.append("Volatilidad alta, operar con cuidado")

        direction = "NO_TRADE"
        if score >= 4:
            direction = "BUY"
        elif score <= -4:
            direction = "SELL"

        return {
            "decision": direction,
            "score": score,
            "reasons": reasons,
            "ema_20": ema_20,
            "ema_50": ema_50,
            "ema_200": ema_200,
            "vwap": vwap,
            "atr": atr,
            "fvg": fvg,
            "latest_close": last_close,
            "latest_high": last_high,
            "latest_low": last_low,
        }

    def _ema(self, values: List[float], period: int) -> float:
        if not values:
            return 0.0
        multiplier = 2 / (period + 1)
        ema = values[0]
        for value in values[1:]:
            ema = (value - ema) * multiplier + ema
        return ema

    def _vwap(self, candles) -> float:
        total_price_volume = 0.0
        total_volume = 0.0
        for candle in candles:
            typical_price = (candle.high + candle.low + candle.close) / 3.0
            volume = 1.0
            total_price_volume += typical_price * volume
            total_volume += volume
        return total_price_volume / total_volume if total_volume else 0.0

    def _atr(self, candles, period: int) -> float:
        if len(candles) < 2:
            return 0.0
        true_ranges = []
        for i in range(1, len(candles)):
            prev = candles[i - 1]
            current = candles[i]
            tr = max(
                current.high - current.low,
                abs(current.high - prev.close),
                abs(current.low - prev.close),
            )
            true_ranges.append(tr)
        if len(true_ranges) < period:
            return sum(true_ranges) / len(true_ranges) if true_ranges else 0.0
        return sum(true_ranges[-period:]) / period

    def _detect_fvg(self, candles) -> str:
        if len(candles) < 3:
            return "none"

        a = candles[-3]
        b = candles[-2]
        c = candles[-1]

        bullish_gap = a.low > c.high and b.close > a.low
        bearish_gap = a.high < c.low and b.close < a.high

        if bullish_gap:
            return "bullish"
        if bearish_gap:
            return "bearish"
        return "none"
