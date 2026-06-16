import importlib.util
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "META_NET" / "meta_net" / "meta_net_trader.py"
spec = importlib.util.spec_from_file_location("meta_net_trader", TOOL)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
MetaNetTrader = mod.MetaNetTrader


class TestMetaNetTraderDirection(unittest.TestCase):
    def setUp(self):
        self.t = MetaNetTrader(R=1.0, C=1.0, F=0.1, M=0.1)

    def test_all_sell_returns_sell(self):
        self.t.input_segnali({"a": "sell", "b": "sell", "c": "sell"})
        self.assertEqual("sell", self.t.genera_segnale())

    def test_all_buy_returns_buy(self):
        self.t.input_segnali({"a": "buy", "b": "buy", "c": "buy"})
        self.assertEqual("buy", self.t.genera_segnale())

    def test_all_hold_returns_hold(self):
        self.t.input_segnali({"a": "hold", "b": "hold"})
        self.assertEqual("hold", self.t.genera_segnale())

    def test_majority_sell_returns_sell(self):
        self.t.input_segnali({"a": "sell", "b": "sell", "c": "buy"})  # media -1/3
        self.assertEqual("sell", self.t.genera_segnale())

    def test_empty_input_raises(self):
        with self.assertRaises(ValueError):
            self.t.genera_segnale()


if __name__ == "__main__":
    unittest.main()
