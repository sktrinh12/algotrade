from .tools.common import Strategy, np, pd
from .tools.tools import position_sizing

class AroonCrossover(Strategy):

    parameters = {
        "symbol": "",
        "window": 0,
        "cash_at_risk": 0.0,
        "risk_tolerance": 0.0,
    }

    def initialize(self):
        self.sleeptime = "1D"
        print(f"symbol: {self.parameters['symbol']}")

    def get_aroon_signal(self, prices: np.array):
        high_max_idx = prices.rolling(window=self.parameters['window']).apply(lambda x: x.argmax(), raw=True)
        low_min_idx = prices.rolling(window=self.parameters['window']).apply(lambda x: x.argmin(), raw=True)

        aroon_up = (self.parameters['window'] - high_max_idx) * 100 / self.parameters['window']
        aroon_down = (self.parameters['window'] - low_min_idx) * 100 / self.parameters['window']

        aroon_signal = np.where(aroon_up > aroon_down, "BUY", np.where(aroon_up < aroon_down, "SELL", "HOLD"))

        return aroon_signal

    def on_trading_iteration(self):
        bars = self.get_historical_prices(self.parameters['symbol'], self.parameters['window'], "day")
        prices = bars.df['close']
        signal = self.get_aroon_signal(prices)
        print(f"signal: {signal[-1]}")

        last_price = prices.iloc[-1]
        cash = self.get_cash()
        quantity = position_sizing(cash, last_price, self.parameters['cash_at_risk'])
        print(f"Last Price: {last_price}, Quantity: {quantity}")

        if signal[-1] == 'BUY':
            if cash > 0 and quantity > 0:
                # Calculate take-profit and stop-loss prices based on risk tolerance
                take_profit_price = last_price * (1 + self.parameters['risk_tolerance'])
                stop_loss_price = last_price * (1 - self.parameters['risk_tolerance'])

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
        elif signal[-1] == "SELL":
            pos = self.get_position(self.parameters['symbol'])
            if pos is not None:
                self.sell_all()
