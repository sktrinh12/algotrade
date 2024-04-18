"""
    checkout:
        - strategy specific docs here : https://algobulls.github.io/pyalgotrading/strategies/bollinger_bands/
        - generalised docs in detail here : https://algobulls.github.io/pyalgotrading/strategies/strategy_guides/common_strategy_guide/
"""

from .tools.common import Strategy, np, pd
from .tools.tools import position_sizing, symbol_type


class BollingerBandsBot(Strategy):
    parameters = {
        'symbol': '',
        "window": 0,
        "cash_at_risk": 0.0,
        "num_std_dev": 0.0,
        "risk_tolerance": 0.0
    }

    def initialize(self):
        self.last_price = 0.0
        self.last_upper_band = None
        self.last_lower_band = None
        print(f"symbol: {self.parameters['symbol']}")

    def calculate_bollinger_bands(self, prices: np.array) -> pd.DataFrame:
        rolling_mean = prices.rolling(window=self.parameters['window']).mean()
        rolling_std = prices.rolling(window=self.parameters['window']).std()
        upper_band = rolling_mean + (rolling_std * self.parameters['num_std_dev'])
        lower_band = rolling_mean - (rolling_std * self.parameters['num_std_dev'])

        data = pd.DataFrame({'Price': prices,
                             'RollingMean': rolling_mean,
                             'RollingStd': rolling_std,
                             'UpperBand': upper_band,
                             'LowerBand': lower_band
                            })
        self.last_price = data['Price'].iloc[-1]

        self.last_upper_band = data['UpperBand'].iloc[-1]
        self.last_lower_band = data['LowerBand'].iloc[-1]
        return data


    def on_trading_iteration(self):
        bars = self.get_historical_prices(self.parameters['symbol'], self.parameters['window'], "day")
        prices = bars.df['close']

        if len(prices) < self.parameters['window']:
            return

        data = self.calculate_bollinger_bands(prices)

        cash = self.get_cash()
        quantity = position_sizing(cash, self.last_price, self.parameters['cash_at_risk'])
        print(f"Last Price: {self.last_price}, Quantity: {quantity}, UB: {self.last_upper_band}, LB: {self.last_lower_band}")

        if self.last_upper_band is None or self.last_lower_band is None or quantity <= 0:
            return

        if self.last_price > self.last_upper_band:
            pos = self.get_position(self.parameters['symbol'])
            if pos is not None:
                self.sell_all()
        elif (self.last_price < self.last_lower_band) and (cash > 0) and (quantity > 0):
            take_profit_price = self.last_price * (1 + self.parameters['risk_tolerance'])
            stop_loss_price = self.last_price * (1 - self.parameters['risk_tolerance'])
            order = self.create_order(
                    self.parameters['symbol'],
                    quantity,
                    side="buy",
                    type="bracket",
                    take_profit_price=take_profit_price,
                    stop_loss_price=stop_loss_price
                )
            self.submit_order(order)
