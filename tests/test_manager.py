import json
import unittest
import importlib.util
import sys
from pathlib import Path

# Load metanet_manager module directly to avoid importing optional deps
MANAGER_PATH = Path(__file__).resolve().parents[1] / 'STR_ONE' / 'str_one' / 'metanet_manager.py'
spec = importlib.util.spec_from_file_location('metanet_manager', MANAGER_PATH)
metanet_manager = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = metanet_manager
spec.loader.exec_module(metanet_manager)

receive_signal = metanet_manager.receive_signal
compute_global_signal = metanet_manager.compute_global_signal
reset_signals = metanet_manager.reset_signals

class TestMetaNetManager(unittest.TestCase):
    def tearDown(self):
        reset_signals()

    def test_weighted_signal(self):
        reset_signals()
        receive_signal('bot_01', {'asset': 'BTCUSD', 'score': 0.5, 'signal': 'buy', 'confidence': 1.0})
        receive_signal('bot_02', {'asset': 'BTCUSD', 'score': -0.2, 'signal': 'sell', 'confidence': 0.5})
        receive_signal('bot_03', {'asset': 'BTCUSD', 'score': 0.1, 'signal': 'buy', 'confidence': 1.0})

        result = json.loads(compute_global_signal())
        expected = {'weighted_score': 0.2, 'aggregated_signal': 'buy'}
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
