"""Mean Reversion strategy module using RSI and Bollinger Bands.

Provides a helper function to compute a MetaNet-compatible signal and a bot
class to dispatch it to ``MetaNetManager``.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Compute the Relative Strength Index of ``series``."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def apply_strategy(df: pd.DataFrame, rsi_period: int = 5) -> pd.DataFrame:
    """Calculate RSI and Bollinger Band signals on ``df``."""
    df = df.copy()
    df["rsi"] = rsi(df["close"], period=rsi_period)
    df["ma20"] = df["close"].rolling(window=20).mean()
    df["std"] = df["close"].rolling(window=20).std()
    df["lower_bb"] = df["ma20"] - 2 * df["std"]
    df["upper_bb"] = df["ma20"] + 2 * df["std"]
    df["signal"] = np.where(
        (df["rsi"] < 30) & (df["close"] < df["lower_bb"]),
        1,
        np.where(
            (df["rsi"] > 70) & (df["close"] > df["upper_bb"]),
            -1,
            0,
        ),
    )
    return df


def generate_signal(df: pd.DataFrame, asset: str = "BTCUSD", rsi_period: int = 5) -> Dict[str, object]:
    """Generate a signal dictionary from ``df`` for ``MetaNetManager``."""
    result = apply_strategy(df, rsi_period)
    last = result.iloc[-1]
    if last["signal"] == 1:
        score = float(last["ma20"] - last["close"])
    elif last["signal"] == -1:
        score = float(last["close"] - last["ma20"])
    else:
        score = 0.0
    width = float(max(last["upper_bb"] - last["lower_bb"], 1e-8))
    confidence = float(min(abs(score) / width, 1.0))
    signal = "buy" if last["signal"] == 1 else "sell" if last["signal"] == -1 else "hold"
    return {
        "asset": asset,
        "score": score,
        "signal": signal,
        "confidence": confidence,
    }


class MeanReversionBot:
    """Bot wrapper around the mean reversion strategy."""

    def __init__(self, bot_id: str, manager, asset: str = "BTCUSD", rsi_period: int = 5) -> None:
        self.bot_id = bot_id
        self.manager = manager
        self.asset = asset
        self.rsi_period = rsi_period

    def on_new_data(self, df: pd.DataFrame) -> None:
        """Create a signal from ``df`` and forward it to ``MetaNetManager``."""
        signal = generate_signal(df, self.asset, self.rsi_period)
        self.manager.receive_signal(self.bot_id, signal)
