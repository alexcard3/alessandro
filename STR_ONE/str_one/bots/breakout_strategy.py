"""Breakout strategy module using Donchian Channels.

Provides utilities to compute breakout signals and a simple bot class to send
signals to ``MetaNetManager``.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict


def apply_strategy(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """Calculate Donchian channel breakout signals on ``df``.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with ``high``, ``low`` and ``close`` columns.
    period : int, optional
        Lookback window for the Donchian channels.

    Returns
    -------
    pandas.DataFrame
        DataFrame with ``upper_band``, ``lower_band`` and ``signal`` columns.
    """
    df = df.copy()
    df["upper_band"] = df["high"].rolling(window=period).max()
    df["lower_band"] = df["low"].rolling(window=period).min()
    df["signal"] = 0
    df["signal"] = np.where(
        df["close"] > df["upper_band"].shift(1),
        1,
        np.where(df["close"] < df["lower_band"].shift(1), -1, 0),
    )
    return df


def generate_signal(df: pd.DataFrame, asset: str = "BTCUSD", period: int = 20) -> Dict[str, object]:
    """Generate a MetaNet-compatible signal dictionary from ``df``.

    Parameters
    ----------
    df : pandas.DataFrame
        Price data with ``high``, ``low`` and ``close`` columns.
    asset : str, optional
        Asset identifier included in the resulting dictionary.
    period : int, optional
        Lookback period for Donchian channels.

    Returns
    -------
    Dict[str, object]
        Dictionary with ``asset``, ``score``, ``signal`` and ``confidence``.
    """
    result = apply_strategy(df, period)
    last = result.iloc[-1]
    if last["signal"] == 1:
        score = float(last["close"] - last["upper_band"])
    elif last["signal"] == -1:
        score = float(last["lower_band"] - last["close"])
    else:
        score = 0.0
    width = float(max(last["upper_band"] - last["lower_band"], 1e-8))
    confidence = float(min(abs(score) / width, 1.0))
    signal = "buy" if last["signal"] == 1 else "sell" if last["signal"] == -1 else "hold"
    return {
        "asset": asset,
        "score": score,
        "signal": signal,
        "confidence": confidence,
    }


class BreakoutStrategyBot:
    """Bot wrapper for the breakout strategy."""

    def __init__(self, bot_id: str, manager, asset: str = "BTCUSD", period: int = 20) -> None:
        self.bot_id = bot_id
        self.manager = manager
        self.asset = asset
        self.period = period

    def on_new_data(self, df: pd.DataFrame) -> None:
        """Generate a signal from ``df`` and send it to ``MetaNetManager``."""
        signal = generate_signal(df, self.asset, self.period)
        self.manager.receive_signal(self.bot_id, signal)
