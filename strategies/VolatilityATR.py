from .tools.common import Strategy, np, pd
from .tools.tools import position_sizing, set_vars


class VolatilityATRCalc():

    """
    Volatility refers to the variation in the price of an asset over time. The more volatile an asset is, the greater the amplitude of its price movements. The True Range is a fundamental measure for calculating the ATR. It represents the maximum amplitude among the following three values:

    1) The difference between the daily high and low prices.

    2) The difference between the daily high price and the previous day's closing price.

    3) The difference between the daily low price and the previous day's closing price.

    Once we have the True Range values for each day, we can calculate the ATR by taking a moving average of these values. The ATR is commonly calculated with a 14-day period.
    """

    def __init__(self, params):
        self.window = params['window']
        self.atr_multiplier = params['atr_multiplier']

    def calculate_true_range(self, df: pd.DataFrame) -> pd.Series:
        high_low_diff = df['high'] - df['low']
        high_close_diff = np.abs(df['high'] - df['close'].shift(1))
        low_close_diff = np.abs(df['low'] - df['close'].shift(1))
        true_range = pd.concat([high_low_diff, high_close_diff, low_close_diff], axis=1).max(axis=1)
        return true_range

    def calculate_average_true_range(self, df: pd.DataFrame) -> float:
        true_range = self.calculate_true_range(df)
        atr = true_range.rolling(window=self.window).mean()
        return atr.iloc[-1]

    def get_data(self, df: pd.DataFrame) -> pd.DataFrame:
        atr = self.calculate_average_true_range(df)
        atr_stop_loss = atr * self.atr_multiplier

        # Generate signals based on ATR stop loss
        signals = np.where(
                    df['close'].diff() > atr_stop_loss,
                    "BUY",
                    np.where(df['close'].diff() < -atr_stop_loss,
                             "SELL",
                             "HOLD"
                    )
        )
        signals[0] = "HOLD"  # Set default signal for the first row
        df_copy = df.copy()
        df_copy['Signal'] = signals
        return df_copy

class VolatilityATR(Strategy):

    parameters = {
        "symbol": "",
        "window": 0,
        "cash_at_risk": 0.0,
        "risk_tolerance": 0.0,
        "atr_multiplier": 0.0,
    }

    def initialize(self):
        self.strategy = VolatilityATRCalc(
            params = {
                'window': self.parameters['window'],
                'atr_multiplier': self.parameters['atr_multiplier']
            }
        )


    def on_trading_iteration(self):
        bars = self.get_historical_prices(self.parameters['symbol'], self.parameters['window'], "day")
        data = self.strategy.get_data(bars.df)
        signal, last_price = set_vars(data, 'Signal')

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
        elif signal == "SELL":
            pos = self.get_position(self.parameters['symbol'])
            if pos is not None:
                self.sell_all()
