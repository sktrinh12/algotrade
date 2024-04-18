import unittest
import numpy as np
import pandas as pd
from datetime import datetime
from lumibot.backtesting import YahooDataBacktesting, BacktestingBroker
from strategies.EmaCrossover import EmaCrossover

class TestEmaCrossover(unittest.TestCase):
    def setUp(self):
        # Initialize the EMACrossover strategy with test parameters

        start = datetime(2023, 1, 1)
        end = datetime(2023, 6, 1)
        data_source = YahooDataBacktesting(
            datetime_start=start,
            datetime_end=end,
        )
        broker = BacktestingBroker(data_source=data_source)
        params = {
            'symbol':'NVDA',
            'short_window':5,
            'long_window':9,
            'cash_at_risk':0.1,
            'risk_tolerance':0.02
        }
        self.strategy = EmaCrossover(parameters = params,
                                     broker=broker)

    def test_get_ema_crossover_signal(self):
        df = pd.read_csv('logs/nvda_expected_signals.csv')
        prices = df.Close

        # Calculate expected crossover signals based on the test prices
        expected_signals = df['Signal'].tolist()
        print(expected_signals)
        print('-'*10)

        # Call the method to get crossover signals
        df_test = self.strategy.get_ema_crossover_signal(prices)
        signals = df_test['Signal']
        print(signals)

        # Check if the generated signals match the expected signals
        self.assertEqual(signals, expected_signals)

if __name__ == "__main__":
    unittest.main()
