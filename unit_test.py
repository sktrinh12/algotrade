import unittest
import numpy as np
import pandas as pd
from datetime import datetime
import yfinance as yf
import argparse
import importlib
import os
from param_helper import STRATEGY_INDICES


# Define a function to dynamically import the strategy class
def import_strategy_class(module_name, class_name):
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


class TestStrategy(unittest.TestCase):
    STRATEGY_NAME = 'simple-ma-crossover'
    def setUp(self):
        self.symbol = 'NVDA'
        self.cash = 1000000
        self.start = datetime(2022, 1, 1)
        self.end = datetime(2023, 1, 1)
        self.risk_range = np.arange(0.01, 0.06, 0.01)
        self.cash_at_risk = 0.32
        self.trading_fee = 0.0015
        self.matrix_risk_profit_ma_dict = {}
        self.strategy_name_actual = ''
        self.strategy = None
        self.moving_average_windows = [
            (5, 20),
            (9, 21),
            (14, 50),
            (10, 50),
            (20, 100),
            (50, 200)
        ]

    def test_output(self):
        dff = yf.download(self.symbol, start=self.start, end=self.end)
        # from environment var
        self.strategy_name_actual = STRATEGY_INDICES[self.STRATEGY_NAME][0]
        print(self.strategy_name_actual)
        for win in self.moving_average_windows:
            StrategyClass = import_strategy_class(f'strategies.{self.strategy_name_actual}',
                                  f'{self.strategy_name_actual}Strategy')
            params = {'short_window': win[0],
                      'long_window': win[1]
                      }
            self.strategy = StrategyClass(params)
            self.matrix_risk_profit_ma_dict[f'{win[0]}_{win[1]}'] = {}
            data = self.strategy.get_data(dff['Close'])
            data = pd.merge(dff, data, left_index=True, right_index=True, how="inner")
            data['shifted_open'] = data.Open.shift(-1)
            signal, last_price = self.strategy.set_vars()
            print(f'signal: {signal} | last_price: {last_price}')
            print(data.head(50))

            for risk in self.risk_range:
                in_position = False
                sell_price = None
                sell_prices = []
                sell_dates = []
                buy_price = None
                buy_prices = []
                buy_dates = []
                # quantity = position_sizing(self.cash, last_price, self.cash_at_risk)
                tp = (1 + risk)
                sl = (1 - risk)
                for index, row in data.iterrows():
                    if not in_position and row.Signal == 'BUY':
                        if not pd.isnull(row.shifted_open):
                            buy_price = row.shifted_open
                            self.cash -= buy_price
                            buy_dates.append(index)
                            buy_prices.append(buy_price)
                            in_position = True

                    if in_position:
                        take_profit_price = buy_price * tp
                        stop_loss_price = buy_price * sl

                        if row.Low < stop_loss_price:
                            sell_price = buy_price * sl
                            sell_prices.append(sell_price)
                            sell_dates.append(index)
                            self.cash += sell_price
                            in_position = False
                        elif row.High > take_profit_price:
                            sell_price = buy_price * tp
                            sell_prices.append(sell_price)
                            sell_dates.append(index)
                            self.cash += sell_price
                            in_position = False

                print(f'sell price length: {len(sell_prices)}')
                print(f'buy price length: {len(buy_prices)}')

                # Calculate profits
                profits = pd.Series([(sell - buy) / buy - self.trading_fee for sell, buy in zip(sell_prices, buy_prices)])
                net_profit = (profits + 1).prod()
                # print(f'profit: {net_profit}')

                outer_key = f'{win[0]}_{win[1]}'
                self.matrix_risk_profit_ma_dict[outer_key][f'{risk}'] = net_profit
                self.matrix_risk_profit_ma_dict[outer_key]['cash_remaining'] = self.cash
                self.matrix_risk_profit_ma_dict[outer_key]['cash_%'] = ((self.cash-1e6)/1e6)*100

        # print out results
        sorted_dict = {}
        for window, risk_profit_dict in self.matrix_risk_profit_ma_dict.items():
            sorted_risk_profit_dict = dict(sorted(risk_profit_dict.items(), key=lambda item: item[1], reverse=True))
            sorted_dict[window] = sorted_risk_profit_dict
        for window, risk_profit_dict in sorted_dict.items():
            print(f"Window: {window}")
            for key, val in risk_profit_dict.items():
                if key.startswith('cash'):
                    print(f"  {key}: {val}")
                else:
                    print(f"  Risk: {key}, Profit: {val}")

if __name__ == '__main__':
    TestStrategy.STRATEGY_NAME = os.environ.get('STRATEGY_NAME', TestStrategy.STRATEGY_NAME)
    unittest.main()
