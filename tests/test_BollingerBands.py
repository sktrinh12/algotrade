import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
import numpy as np
import pandas as pd
from datetime import datetime
import yfinance as yf
from strategies.tools.tools import set_vars
from strategies.BollingerBands import BollingerBandsCalc


class TestBollingerBands(unittest.TestCase):
    SYMBOL = 'AAPL'
    def setUp(self):
        self.cash = 1000000
        self.start = datetime(2022, 1, 1)
        self.end = datetime(2023, 1, 1)
        self.risk_range = np.arange(0.01, 0.06, 0.01)
        self.cash_at_risk = 0.32
        self.trading_fee = 0.0015
        self.matrix_dict = {}
        self.strategy = None
        self.moving_average_windows = [
            5,
            9,
            14,
            21,
            35,
            50,
            100,
            125,
            150
        ]
        self.num_std_dev = np.arange(0.5, 3.5, 0.5)

    def test_output(self):
        dff = yf.download(self.SYMBOL, start=self.start, end=self.end)
        for std in self.num_std_dev:
            for win in self.moving_average_windows:
                self.strategy = BollingerBandsCalc(
                    params = {
                        'window': win,
                        'num_std_dev': std
                    }
                )

                outer_key = f'{std}_{win}'
                self.matrix_dict[outer_key] = {}
                data = self.strategy.get_data(dff['Close'])
                data = pd.merge(dff, data, left_index=True, right_index=True, how="inner")
                data['shifted_open'] = data.Open.shift(-1)
                signal, last_price = set_vars(data, 'Signal')
                print(f'signal: {signal} | last_price: {last_price}')
                print(data.iloc[20:51])

                for risk in self.risk_range:
                    in_position = False
                    sell_price = None
                    sell_prices = []
                    sell_dates = []
                    buy_price = None
                    buy_prices = []
                    buy_dates = []
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

                    self.matrix_dict[outer_key][f'{risk}'] = net_profit
                    self.matrix_dict[outer_key]['cash_remaining'] = self.cash
                    self.matrix_dict[outer_key]['cash_%'] = ((self.cash-1e6)/1e6)*100

        # print out results
        sorted_dict = {}
        optimal_risk = None
        optimal_profit = 0
        optimal_win = None
        optimal_std = None
        for window, risk_profit_dict in self.matrix_dict.items():
            sorted_risk_profit_dict = dict(sorted(risk_profit_dict.items(), key=lambda item: item[1], reverse=True))
            sorted_dict[window] = sorted_risk_profit_dict
        for window, risk_profit_dict in sorted_dict.items():
            print(f"Window: {window}")
            for key, val in risk_profit_dict.items():
                if key.startswith('cash'):
                    print(f"  {key}: {val}")
                else:
                    if optimal_profit < val:
                        optimal_profit = val
                        optimal_risk = key
                        std, win = window.split('_')
                        optimal_win = win
                        optimal_std = std
                    print(f"  Risk: {key}, Profit: {val}")

        padding = " "*4
        print('\n')
        print('='*60)
        print('\n')
        print(f'optimals:\n{padding}Risk: {optimal_risk}\n{padding}Profit:{optimal_profit}\n{padding}Window:{optimal_win}\n{padding}Std:{optimal_std}')

if __name__ == '__main__':
    TestBollingerBands.SYMBOL = os.environ.get('SYMBOL', TestBollingerBands.SYMBOL)
    unittest.main()