from .tools.common import Strategy, np, pd
from .tools.tools import position_sizing

class MeanRevision(Strategy):

    parameters = {
        "symbol": "",
        "window": 0,
        "cash_at_risk": 0.0,
        "risk_tolerance": 0.0,
    }

    def initialize(self):
        self.z_threshold = 1.5
        self.sleeptime = "1D"
        self.signal = None
        self.last_price = 0.0
        print(f"symbol: {self.parameters['symbol']}")


    def get_mean_reversion_signal(self, prices: np.array) -> pd.DataFrame:
        rolling_mean = prices.rolling(window=self.parameters['window']).mean()
        rolling_std = prices.rolling(window=self.parameters['window']).std()

        # Calculate the Z-score
        z_score = (prices - rolling_mean) / rolling_std

        # Define the trading signals
        signal = np.where(z_score < -self.z_threshold, "BUY", np.where(z_score > self.z_threshold, "SELL", "HOLD"))

        data = pd.DataFrame({'Price': prices, 'Signal': signal})
        self.last_price = data['Price'].iloc[-1]
        self.signal = data['Signal'].iloc[-1]
        return data


    def on_trading_iteration(self):
        bars = self.get_historical_prices(self.parameters['symbol'], self.parameters['window'], "day")
        prices = bars.df['close']
        signal = self.get_mean_reversion_signal(prices)
        print(f"signal: {self.signal}")

        cash = self.get_cash()
        quantity = position_sizing(cash, self.last_price, self.parameters['cash_at_risk'])
        print(f"Last Price: {self.last_price}, Quantity: {quantity}")

        if self.signal == 'BUY':
            if cash > 0 and quantity > 0:
                # Calculate take-profit and stop-loss prices based on risk tolerance
                take_profit_price = self.last_price * (1 + self.parameters['risk_tolerance'])
                stop_loss_price = self.last_price * (1 - self.parameters['risk_tolerance'])

                # Create a bracket order with take-profit and stop-loss prices
                order = self.create_order(
                    self.parameters['symbol'],
                    quantity,
                    "buy",
                    type="bracket",
                    take_profit_price=take_profit_price,
                    stop_loss_price=stop_loss_price
                )
                self.submit_order(order)
            else:
                print(f"Error: cash: {cash}, quantity: {quantity}")
        elif self.signal == "SELL":
            pos = self.get_position(self.parameters['symbol'])
            if pos is not None:
                self.sell_all()
