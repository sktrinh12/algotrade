from .tools.common import Strategy, Trader, np, pd
from .tools.tools import position_sizing, set_vars


class RsiCrossoverCalc():

    def __init__(self, params):
        self.rsi_period = params['rsi_period']
        self.upper_threshold = params['upper_threshold']
        self.lower_threshold = params['lower_threshold']

    def get_data(self, prices: np.array) -> pd.DataFrame:
        data = pd.DataFrame({'Price': prices})
        # Calculate the day-to-day price difference (change)
        data['delta'] = data['Price'].diff(1)
        # Keep positive changes as gains, replace negative changes with 0
        # if the value in the delta is not > 0 then set to 0; fill the NA with 0s
        data['gain'] = (data['delta'].where(data['delta'] > 0, 0)).fillna(0)
        # Keep negative changes as losses (as positive values), replace positive changes with 0
        data['loss'] = (-data['delta'].where(data['delta'] < 0, 0)).fillna(0)
        data['ewm_gain'] = data['gain'].ewm(span=self.rsi_period, min_periods=self.rsi_period).mean()  # Calculate the average gain over the RSI period
        data['ewm_loss'] = data['loss'].ewm(span=self.rsi_period, min_periods=self.rsi_period).mean()  # Calculate the average loss over the RSI period
        data['rs'] = data['ewm_gain'] / data['ewm_loss']  # Compute the Relative Strength (RS) value
        data['RSI'] = 100 - (100 / (1 + data['rs']))  # Calculate the Relative Strength Index (RSI) value
        # When the RSI is above the upper threshold, it suggests that the market is overbought, and it may be a good time to sell.

        # When the RSI is below the lower threshold, it suggests that the market is oversold, and it may be a good time to buy
        data['Signal'] = np.where(
            data['RSI'] > self.upper_threshold,
            'SELL',
            np.where(
                data['RSI'] < self.lower_threshold,
                'BUY',
                'HOLD'
            )
        )
        return data


class RsiCrossover(Strategy):

    parameters = {
        'symbol': '',
        "window": 0,
        'risk_tolerance': 0.0,
        'cash_at_risk': 0.0,
        'upper_threshold': 0,
        'lower_threshold': 0,
    }

    def initialize(self):
        self.sleeptime = "1D"
        self.strategy = RsiCrossoverCalc(
            params = {
                'rsi_period': self.parameters['short_window'],
                'upper_threshold': self.parameters['upper_threshold'],
                'lower_threshold': self.parameters['lower_threshold'],
            }
        )

    def on_trading_iteration(self):
        bars = self.get_historical_prices(self.parameters['symbol'], self.parameters['window'], "day")
        data = self.strategy.get_data(bars.df['close'])
        signal, last_price = set_vars(data, 'Signal')
        print(f"{'':<4}{signal}")

        if signal == 'BUY':
            cash = self.get_cash()
            quantity = position_sizing(cash, last_price, self.parameters['cash_at_risk'])
            if (cash > 0) and (quantity > 0):
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

        elif signal == 'SELL':
            pos = self.get_position(self.parameters['symbol'])
            if pos is not None:
                self.sell_all()
