"""
    checkout:
        - strategy specific docs here : https://algobulls.github.io/pyalgotrading/strategies/bollinger_bands/
        - generalised docs in detail here : https://algobulls.github.io/pyalgotrading/strategies/strategy_guides/common_strategy_guide/
"""

from .tools.common import Strategy, np, pd, Tuple
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
        print(f"symbol: {self.parameters['symbol']}")

    def calculate_bollinger_bands(self, prices: np.array) -> Tuple[np.array, np.array, np.array]:
        rolling_mean = prices.rolling(window=self.parameters['window']).mean()
        rolling_std = prices.rolling(window=self.parameters['window']).std()
        upper_band = rolling_mean + (rolling_std * self.parameters['num_std_dev'])
        lower_band = rolling_mean - (rolling_std * self.parameters['num_std_dev'])
        return rolling_mean, upper_band, lower_band


    def on_trading_iteration(self):
        bars = self.get_historical_prices(self.parameters['symbol'], self.parameters['window'], "day")
        prices = bars.df['close']

        if len(prices) < self.parameters['window']:
            return

        rolling_mean, upper_band, lower_band = self.calculate_bollinger_bands(prices)

        last_price = prices.iloc[-1]
        last_upper_band = upper_band.iloc[-1]
        last_lower_band = lower_band.iloc[-1]

        cash = self.get_cash()
        quantity = position_sizing(cash, last_price, self.parameters['cash_at_risk'])
        print(f"Last Price: {last_price}, Quantity: {quantity}, UB: {last_upper_band}, LB: {last_lower_band}")

        if np.isnan(last_upper_band) or np.isnan(last_lower_band) or quantity <= 0:
            return

        if last_price > last_upper_band:
            pos = self.get_position(self.parameters['symbol'])
            if pos is not None:
                self.sell_all()
        elif (last_price < last_lower_band) and (cash > 0) and (quantity > 0):
            take_profit_price = last_price * (1 + self.parameters['risk_tolerance'])
            stop_loss_price = last_price * (1 - self.parameters['risk_tolerance'])
            order = self.create_order(
                    self.parameters['symbol'],
                    quantity,
                    side="buy",
                    type="bracket",
                    take_profit_price=take_profit_price,
                    stop_loss_price=stop_loss_price
                )
            self.submit_order(order)