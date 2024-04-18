from .tools.common import Strategy, np, pd
from .tools.tools import position_sizing


class VolatilityATR(Strategy):
    """
    Volatility refers to the variation in the price of an asset over time. The more volatile an asset is, the greater the amplitude of its price movements. The True Range is a fundamental measure for calculating the ATR. It represents the maximum amplitude among the following three values:

    1) The difference between the daily high and low prices.

    2) The difference between the daily high price and the previous day's closing price.

    3) The difference between the daily low price and the previous day's closing price.

    Once we have the True Range values for each day, we can calculate the ATR by taking a moving average of these values. The ATR is commonly calculated with a 14-day period.
    """

    parameters = {
        "symbol": "",
        "window": 0,
        "cash_at_risk": 0.0,
        "risk_tolerance": 0.0,
    }

    def initialize(self):
        self.atr_multiplier = 1.1
        self.signal = None
        self.last_price = 0.0

    def calculate_true_range(self, df: pd.DataFrame) -> pd.Series:
        high_low_diff = df['high'] - df['low']
        high_close_diff = np.abs(df['high'] - df['close'].shift(1))
        low_close_diff = np.abs(df['low'] - df['close'].shift(1))
        true_range = pd.concat([high_low_diff, high_close_diff, low_close_diff], axis=1).max(axis=1)
        return true_range

    def calculate_average_true_range(self, df: pd.DataFrame) -> float:
        true_range = self.calculate_true_range(df)
        atr = true_range.rolling(window=self.parameters['window']).mean()
        return atr.iloc[-1]

    def get_atr_signal(self, prices: pd.DataFrame) -> pd.DataFrame:
        atr = self.calculate_average_true_range(prices)
        atr_stop_loss = atr * self.atr_multiplier

        # Generate signals based on ATR stop loss
        signals = []
        for i in range(len(prices)):
            if i == 0:
                signals.append("HOLD")  # Default signal for the first row
            else:
                if prices['close'].iloc[i] > prices['close'].iloc[i-1] + atr_stop_loss:
                    signals.append("BUY")
                elif prices['close'].iloc[i] < prices['close'].iloc[i-1] - atr_stop_loss:
                    signals.append("SELL")
                else:
                    signals.append("HOLD")

        # Add the signals to the DataFrame
        prices['Signal'] = signals
        self.signal = signals[-1]  # Update the current signal
        print(f'signal: {self.signal}')
        return prices

    def on_trading_iteration(self):
        bars = self.get_historical_prices(self.parameters['symbol'], self.parameters['window'], "day")
        data = self.get_atr_signal(bars.df)
        self.last_price = bars.df['close'].iloc[-1]

        cash = self.get_cash()
        quantity = position_sizing(cash, self.last_price, self.parameters['cash_at_risk'])

        if self.signal == 'BUY':
            if cash > 0 and quantity > 0:
                # Calculate take-profit and stop-loss prices based on risk tolerance
                take_profit_price = self.last_price * (1 + self.parameters['risk_tolerance'])
                stop_loss_price = self.last_price * (1 - self.parameters['risk_tolerance'])

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
        elif self.signal == "SELL":
            pos = self.get_position(self.parameters['symbol'])
            if pos is not None:
                self.sell_all()
