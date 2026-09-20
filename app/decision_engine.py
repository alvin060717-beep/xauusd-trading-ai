from __future__ import annotations

from typing import Tuple


class RiskEngine:
    """Motor de riesgo. El risk engine es el último filtro antes de operar."""

    def __init__(self, config):
        self.config = config

    def validate_trade(self, signal_decision: str, news_blocked: bool, rr_ratio: float = 2.0) -> Tuple[bool, str]:
        if news_blocked:
            return False, "Bloqueado por noticias de impacto macro"

        if signal_decision == "NO_TRADE":
            return False, "No hay señal técnica válida"

        if rr_ratio < self.config.min_rr_ratio:
            return False, f"Ratio riesgo/beneficio insuficiente: {rr_ratio} < {self.config.min_rr_ratio}"

        return True, "Riesgo aceptado"
