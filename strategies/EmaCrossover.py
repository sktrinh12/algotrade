from .tools.common import Strategy, np, pd
from .tools.tools import position_sizing, set_vars


class EmaCrossoverCalc():

    def __init__(self, params):
        self.short_window = params['short_window']
        self.long_window = params['long_window']

    def get_data(self, prices: np.array) -> pd.DataFrame:
        ema_x = prices.ewm(span=self.short_window, adjust=False).mean()
        ema_y = prices.ewm(span=self.long_window, adjust=False).mean()

        # The 'span' parameter specifies the number of periods over which the exponential decay factor is applied.
        # A larger span will give more weight to recent observations, while a smaller span will give more weight to older observations.

        # The 'adjust' parameter determines whether to divide by the decaying adjustment factor.
        # Setting it to True scales the result by the decaying adjustment factor to account for the varying number of observations in each window.
        crossover_signal = np.where(ema_x > ema_y, 'BUY', np.where(ema_x < ema_y, 'SELL', 'HOLD'))
        return pd.DataFrame({
            'Price': prices,
            'Signal': crossover_signal
        })

class EmaCrossover(Strategy):

    parameters = {
        "symbol": "",
        'window': 0,
        'short_window' : 0,
        'long_window' : 0,
        "cash_at_risk": 0.0,
        "risk_tolerance": 0.0,
    }

    def initialize(self):
        self.strategy = EmaCrossoverCalc(
            params = {
                'short_window': self.parameters['short_window'],
                'long_window': self.parameters['long_window']
            }
        )

    def on_trading_iteration(self):
        bars = self.get_historical_prices(self.parameters['symbol'],
                                          self.parameters['window'], "day")
        prices = bars.df['close']
        data = self.strategy.get_data(prices)
        signal, last_price = set_vars(data, 'Signal')
        print(f"{'':<4}{signal}")

        cash = self.get_cash()
        quantity = position_sizing(cash, last_price, self.parameters['cash_at_risk'])
        if signal == 'BUY':
            if cash > 0 and quantity > 0:
                # Calculate take-profit and stop-loss prices based on risk tolerance
                take_profit_price = last_price * (1 + self.parameters['risk_tolerance'])
                stop_loss_price = last_price * (1 - self.parameters['risk_tolerance'])

                # Create a bracket order with take-profit and stop-loss prices
                order = self.create_order(
                    self.parameters['symbol'],
                    quantity,
                    side="buy",
                    type="bracket",
                    take_profit_price=take_profit_price,
                    stop_loss_price=stop_loss_price
                )
                self.submit_order(order)
            else:
                print(f"Error: cash: {cash}, quantity: {quantity}")
        elif signal == 'SELL':
            pos = self.get_position(self.parameters['symbol'])
            if pos is not None:
                self.sell_all()
