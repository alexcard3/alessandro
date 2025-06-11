"""Collection of simple trading bots used by MetaNetManager."""

__all__ = [
    'TrendFollowingBot',
    'apply_strategy',
    'generate_signal',
    'BreakoutStrategyBot',
    'apply_breakout_strategy',
    'generate_breakout_signal',
    'MeanReversionBot',
    'apply_mean_reversion_strategy',
    'generate_mean_reversion_signal',
    'BTC4H5MBot',
    'apply_btc4h5m_strategy',
    'generate_btc4h5m_signal',
]

from .trend_following import TrendFollowingBot, apply_strategy, generate_signal
from .breakout_strategy import (
    BreakoutStrategyBot,
    apply_strategy as apply_breakout_strategy,
    generate_signal as generate_breakout_signal,
)
from .mean_reversion import (
    MeanReversionBot,
    apply_strategy as apply_mean_reversion_strategy,
    generate_signal as generate_mean_reversion_signal,
)
from .btc4h5m import (
    BTC4H5MBot,
    apply_strategy as apply_btc4h5m_strategy,
    generate_signal as generate_btc4h5m_signal,
)
