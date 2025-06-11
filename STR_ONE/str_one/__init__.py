"""STR_ONE package."""

__all__ = [
    'StrOneApp',
    'MetaNetManager',
    'receive_signal',
    'compute_global_signal',
    'reset_signals',
    'get_signals_state',
    'TrendFollowingBot',
    'BreakoutStrategyBot',
    'MeanReversionBot',
    'BTC4H5MBot',
]

from .main import StrOneApp
from .metanet_manager import (
    MetaNetManager,
    compute_global_signal,
    get_signals_state,
    receive_signal,
    reset_signals,
)
from .bots.trend_following import TrendFollowingBot
from .bots.breakout_strategy import BreakoutStrategyBot
from .bots.mean_reversion import MeanReversionBot
from .bots.btc4h5m import BTC4H5MBot
