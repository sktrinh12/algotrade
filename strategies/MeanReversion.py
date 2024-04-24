from .tools.common import Strategy, np, pd
from .tools.tools import position_sizing, set_vars, prnt_params


class MeanReversionCalc():

    def __init__(self, params):
        self.window = params['window']
        self.z_threshold = params['z_threshold']

    def get_data(self, prices: np.array) -> pd.DataFrame:
        rolling_mean = prices.rolling(window=self.window).mean()
        rolling_std = prices.rolling(window=self.window).std()

        # Calculate the Z-score
        z_score = (prices - rolling_mean) / rolling_std

        # Define the trading signals
        signal = np.where(z_score < -self.z_threshold, "BUY", np.where(z_score > self.z_threshold, "SELL", "HOLD"))

        return pd.DataFrame({'Price': prices, 'Signal': signal})


class MeanReversion(Strategy):

    parameters = {
        "symbol": "",
        "window": 0,
        "cash_at_risk": 0.0,
        "risk_tolerance": 0.0,
        "z_threshold": 1.5
    }

    def initialize(self):
        self.sleeptime = "1D"
        self.strategy = MeanReversionCalc(
            params = {
                'window': self.parameters['window'],
                'z_threshold': self.parameters['z_threshold']
            }
        )
        prnt_params(self.parameters)

    def on_trading_iteration(self):
        bars = self.get_historical_prices(self.parameters['symbol'], self.parameters['window'], "day")
        prices = bars.df['close']
        data = self.strategy.get_data(prices)
        signal, last_price = set_vars(data, 'Signal')
        print(f"{'':<4}{signal}")

        cash = self.get_cash()
        quantity = position_sizing(cash, last_price, self.parameters['cash_at_risk'])
        print(f"Last Price: {last_price}, Quantity: {quantity}")

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
        elif signal == "SELL":
            pos = self.get_position(self.parameters['symbol'])
            if pos is not None:
                self.sell_all()
