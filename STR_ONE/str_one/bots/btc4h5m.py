"""Advanced BTC 4h/5m strategy bot.

This module adapts the standalone `btc4h5m.py` trading script into a
lightweight component compatible with ``MetaNetManager``. It calculates
several technical indicators using the ``ta`` package and forwards a
simplified trading signal to the manager.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pandas as pd
import ta


@dataclass
class StrategyParams:
    """Configuration parameters for the strategy."""

    atr_len: int = 14
    rsi_len: int = 14
    min_atr_pct: float = 0.0005
    rsi_buy: int = 55
    rsi_sell: int = 45


def apply_strategy(df: pd.DataFrame, params: StrategyParams | None = None) -> pd.DataFrame:
    """Compute indicators and trading signals on ``df``."""
    if params is None:
        params = StrategyParams()

    df = df.copy()
    df["atr"] = ta.volatility.average_true_range(df["high"], df["low"], df["close"], params.atr_len)
    df["rsi"] = ta.momentum.rsi(df["close"], params.rsi_len)
    df["ema20"] = ta.trend.ema_indicator(df["close"], 20)
    df["ema50"] = ta.trend.ema_indicator(df["close"], 50)

    df["atr_pct"] = df["atr"] / df["close"]
    trend_up = (df["close"] > df["ema20"]) & (df["ema20"] > df["ema50"])
    trend_down = (df["close"] < df["ema20"]) & (df["ema20"] < df["ema50"])

    cond_long = (df["atr_pct"] > params.min_atr_pct) & (df["rsi"] > params.rsi_buy) & trend_up
    cond_short = (df["atr_pct"] > params.min_atr_pct) & (df["rsi"] < params.rsi_sell) & trend_down

    df["signal"] = 0
    df.loc[cond_long, "signal"] = 1
    df.loc[cond_short, "signal"] = -1

    return df


def generate_signal(
    df: pd.DataFrame,
    asset: str = "BTCUSD",
    params: StrategyParams | None = None,
) -> Dict[str, object]:
    """Return a MetaNet-compatible signal dictionary from ``df``."""
    result = apply_strategy(df, params)
    last = result.iloc[-1]

    sig_map = {1: "buy", -1: "sell", 0: "hold"}
    signal = sig_map[int(last["signal"])]

    score = float(last["rsi"] - 50.0)
    width = float(max(last["atr_pct"], 1e-8))
    confidence = float(min(abs(score) / max(width, 1e-6), 1.0))

    return {
        "asset": asset,
        "score": score,
        "signal": signal,
        "confidence": confidence,
    }


class BTC4H5MBot:
    """Bot wrapper around the improved BTC strategy."""

    def __init__(
        self,
        bot_id: str,
        manager,
        asset: str = "BTCUSD",
        params: StrategyParams | None = None,
    ) -> None:
        self.bot_id = bot_id
        self.manager = manager
        self.asset = asset
        self.params = params or StrategyParams()

    def on_new_data(self, df: pd.DataFrame) -> None:
        """Generate a signal from ``df`` and send it to ``MetaNetManager``."""
        signal = generate_signal(df, self.asset, self.params)
        self.manager.receive_signal(self.bot_id, signal)
