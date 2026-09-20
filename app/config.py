from dataclasses import dataclass, field
import os
from typing import List


@dataclass
class Config:
    symbol: str = "XAUUSD"
    max_risk_per_trade: float = 0.005
    min_rr_ratio: float = 2.0
    high_impact_block_minutes: int = 60
    medium_impact_block_minutes: int = 30
    high_impact_events: List[str] = field(default_factory=lambda: [
        "fomc",
        "federal funds rate",
        "cpi",
        "core cpi",
        "pce",
        "core pce",
        "non-farm payrolls",
        "nfp",
        "powell",
        "fed",
        "interest rate",
        "unemployment",
        "inflation",
        "jobless claims",
    ])

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            symbol=os.getenv("XAUUSD_SYMBOL", "XAUUSD"),
            max_risk_per_trade=float(os.getenv("MAX_RISK_PER_TRADE", "0.005")),
            min_rr_ratio=float(os.getenv("MIN_RR_RATIO", "2.0")),
            high_impact_block_minutes=int(os.getenv("HIGH_IMPACT_BLOCK_MINUTES", "60")),
            medium_impact_block_minutes=int(os.getenv("MEDIUM_IMPACT_BLOCK_MINUTES", "30")),
        )
