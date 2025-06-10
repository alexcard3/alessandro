"""MetaNet manager module.

This module manages up to 99 subordinate trading bots, collects their signals
and computes a weighted global signal for the MetaNet head bot.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class BotSignal:
    """Container for a bot signal."""

    asset: str
    score: float
    signal: str
    confidence: float
    weight: float = 1.0


class MetaNetManager:
    """Manage the collection and aggregation of bot signals."""

    def __init__(self) -> None:
        # Initialize slots for 99 bots (bot_01 .. bot_99)
        self.bot_ids: List[str] = [f"bot_{i:02d}" for i in range(1, 100)]
        self.signals: Dict[str, Optional[BotSignal]] = {
            bot_id: None for bot_id in self.bot_ids
        }
        logger.debug("Initialized manager with %d bots", len(self.bot_ids))

    def reset_signals(self) -> None:
        """Resetta tutti i segnali ricevuti, riportandoli a ``None``."""
        for bot_id in self.bot_ids:
            self.signals[bot_id] = None
        logger.info("Reset dei segnali effettuato.")

    def get_signals_state(self) -> Dict[str, Optional[BotSignal]]:
        """Restituisce lo stato attuale dei segnali ricevuti."""
        return self.signals

    def receive_signal(self, bot_id: str, signal_dict: Dict[str, object]) -> None:
        """Store the signal from a bot.

        Parameters
        ----------
        bot_id: str
            Identifier of the sending bot (e.g. ``"bot_01"``).
        signal_dict: Dict[str, object]
            Dictionary containing ``asset``, ``score``, ``signal`` and
            ``confidence`` keys.
        """
        if bot_id not in self.signals:
            logger.warning("Unknown bot_id: %s", bot_id)
            return

        try:
            signal = BotSignal(
                asset=str(signal_dict["asset"]),
                score=float(signal_dict.get("score", 0.0)),
                signal=str(signal_dict.get("signal", "hold")),
                confidence=float(signal_dict.get("confidence", 1.0)),
            )
        except KeyError as exc:
            logger.error("Missing key in signal from %s: %s", bot_id, exc)
            return

        self.signals[bot_id] = signal
        logger.info("Received signal from %s: %s", bot_id, signal_dict)

    def compute_global_signal(self) -> Dict[str, object]:
        """Compute the weighted average score and aggregated decision.

        Returns
        -------
        Dict[str, object]
            Dictionary with ``weighted_score`` and ``aggregated_signal``.
        """
        total_weight = 0.0
        weighted_score = 0.0
        decision_votes = {"buy": 0.0, "sell": 0.0, "hold": 0.0}

        for bot_id, signal in self.signals.items():
            if signal is None:
                continue
            w = signal.weight * signal.confidence
            total_weight += w
            weighted_score += signal.score * w
            decision_votes[signal.signal] = decision_votes.get(signal.signal, 0.0) + w

        if total_weight == 0.0:
            result = {"weighted_score": 0.0, "aggregated_signal": "hold"}
        else:
            avg_score = weighted_score / total_weight
            agg_signal = max(decision_votes, key=decision_votes.get)
            result = {
                "weighted_score": round(avg_score, 4),
                "aggregated_signal": agg_signal,
            }

        logger.info("Computed global signal: %s", result)
        return result


# Module-level manager instance
_manager = MetaNetManager()


def receive_signal(bot_id: str, signal_dict: Dict[str, object]) -> None:
    """Public API to send a signal to the module-level manager."""
    _manager.receive_signal(bot_id, signal_dict)


def compute_global_signal() -> str:
    """Return the aggregated signal as a JSON string."""
    result = _manager.compute_global_signal()
    return json.dumps(result)


def reset_signals() -> None:
    """Public API to reset all signals in the manager."""
    _manager.reset_signals()


def get_signals_state() -> Dict[str, Optional[BotSignal]]:
    """Public API to obtain the current internal state of signals."""
    return _manager.get_signals_state()
