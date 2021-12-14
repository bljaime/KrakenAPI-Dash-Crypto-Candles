import pandas as pd
import krakenex
import currencies
from unittest import TestCase

class TestPair(TestCase):

    def test_calculate_vwap(self):

        data = {'price': [42882.6, 42882.5, 42882.6, 42886.4, 42882.6, 42882.5, 42882.5, 42882.6, 42882.5,
                          42882.5, 42863.5, 42863.5, 42863.5, 42863.5, 42863.5, 42863.4, 42863.4, 42863.4],
                'volume': [6.891900e-04, 4.500000e-04, 4.364200e-04, 1.304900e-01, 9.174280e-03, 4.700000e-03,
                           1.560000e-03, 3.378900e-04, 3.148960e-03, 5.870863e-02, 4.521540e-03, 7.536000e-03,
                           1.005370e-03, 4.666000e-04, 1.302500e-04, 1.010000e-03, 3.045640e-03, 1.666028e-02]}

        df1 = pd.DataFrame(data)

        api = krakenex.API()
        pair1 = currencies.Pair('BTC/USD', '1m', 60, api)

        assert round(pair1.calculate_vwap(df1), 2) == round(42881.90495, 2)
