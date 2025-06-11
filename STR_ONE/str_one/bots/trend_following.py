"""Trend Following strategy module.

Implements a simple moving average crossover approach and exposes a helper
function to generate a MetaNet-compatible signal dictionary.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict


def apply_strategy(df: pd.DataFrame, short_window: int = 20, long_window: int = 50) -> pd.DataFrame:
    """Calculate moving average cross signals on ``df``.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with a ``close`` column.
    short_window : int, optional
        Period for the short moving average.
    long_window : int, optional
        Period for the long moving average.

    Returns
    -------
    pandas.DataFrame
        DataFrame with ``ma_short``, ``ma_long`` and ``signal`` columns.
    """
    df = df.copy()
    df["ma_short"] = df["close"].rolling(window=short_window).mean()
    df["ma_long"] = df["close"].rolling(window=long_window).mean()
    df["signal"] = 0
    df.loc[short_window:, "signal"] = np.where(
        df["ma_short"][short_window:] > df["ma_long"][short_window:], 1, -1
    )
    return df


def generate_signal(df: pd.DataFrame, asset: str = "BTCUSD", short_window: int = 20, long_window: int = 50) -> Dict[str, object]:
    """Generate a signal dictionary for ``MetaNetManager`` from ``df``.

    Parameters
    ----------
    df : pandas.DataFrame
        Price data with a ``close`` column.
    asset : str, optional
        Asset identifier included in the resulting dictionary.
    short_window : int, optional
        Short moving average window.
    long_window : int, optional
        Long moving average window.

    Returns
    -------
    Dict[str, object]
        Dictionary with ``asset``, ``score``, ``signal`` and ``confidence``.
    """
    result = apply_strategy(df, short_window, long_window)
    last_row = result.iloc[-1]
    score = float(last_row["ma_short"] - last_row["ma_long"])
    signal = "buy" if last_row["signal"] > 0 else "sell"
    confidence = float(min(abs(score) / max(last_row["ma_long"], 1.0), 1.0))
    return {
        "asset": asset,
        "score": score,
        "signal": signal,
        "confidence": confidence,
    }

class TrendFollowingBot:
    """Simple bot wrapping the trend following strategy."""

    def __init__(self, bot_id: str, manager, asset: str = "BTCUSD", short_window: int = 20, long_window: int = 50) -> None:
        self.bot_id = bot_id
        self.manager = manager
        self.asset = asset
        self.short_window = short_window
        self.long_window = long_window

    def on_new_data(self, df: pd.DataFrame) -> None:
        """Generate a signal from ``df`` and send it to ``MetaNetManager``."""
        signal = generate_signal(df, self.asset, self.short_window, self.long_window)
        self.manager.receive_signal(self.bot_id, signal)
