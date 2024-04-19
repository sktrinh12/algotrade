from .tools.common import Strategy, Trader, np, pd
from .tools.tools import position_sizing


class RsiCrossover(Strategy):

    parameters = {
        'symbol': '',
        "window": 0,
        'rsi_period': 0,
        'upper_threshold': 0.0,
        'lower_threshold': 0.0,
        'risk_tolerance': 0.0,
        'cash_at_risk': 0.0,
    }

    def initialize(self):
        self.signal = None
        self.last_price = 0
        self.sleeptime = "1D"
        self.df = None

    def calculate_rsi(self, prices: np.array) -> pd.DataFrame:
        # Calculate the day-to-day price difference (change)
        delta = prices.diff()
        # Keep positive changes as gains, replace negative changes with 0
        # if the value in the delta is not > 0 then set to 0; fill the NA with 0s
        gain = (delta.where(delta > 0, 0)).fillna(0)
        # Keep negative changes as losses (as positive values), replace positive changes with 0
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        avg_gain = gain.rolling(self.parameters['rsi_period']).mean()  # Calculate the average gain over the RSI period
        avg_loss = loss.rolling(self.parameters['rsi_period']).mean()  # Calculate the average loss over the RSI period
        rs = avg_gain / avg_loss  # Compute the Relative Strength (RS) value
        data = pd.DataFrame({'Price': prices,
                             'Gain': gain,
                             'Loss': loss,
                             'AvgGain': avg_gain,
                             'AvgLoss': avg_loss,
                             'RS': rs
                            })
        data['RSI'] = 100 - (100 / (1 + rs))  # Calculate the Relative Strength Index (RSI) value
        return data

    def gen_rsi_signal(self, rsi_data: pd.DataFrame) -> pd.DataFrame:
        rsi_data['Signal'] = 'HOLD'
        # When the RSI is above the upper threshold, it suggests that the market is overbought, and it may be a good time to sell.
        rsi_data['Signal'] = np.where(rsi_data['RSI'] > self.parameters['upper_threshold'], 'SELL', rsi_data['Signal'])
        # When the RSI is below the lower threshold, it suggests that the market is oversold, and it may be a good time to buy
        rsi_data['Signal'] = np.where(rsi_data['RSI'] < self.parameters['lower_threshold'], 'BUY', rsi_data['Signal'])
        return rsi_data

    def on_trading_iteration(self):
        bars = self.get_historical_prices(self.parameters['symbol'], self.parameters['window'], "day")
        data = self.calculate_rsi(bars.df['close'])
        data = self.gen_rsi_signal(data)
        self.signal = data['Signal'].iloc[-1]
        self.last_price = bars.df['close'].iloc[-1]
        print(f'signal: {self.signal}')

        if self.signal == 'BUY':
            cash = self.get_cash()
            quantity = position_sizing(cash, self.last_price, self.parameters['cash_at_risk'])
            if (cash > 0) and (quantity > 0):
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

        elif self.signal == 'SELL':
            pos = self.get_position(self.parameters['symbol'])
            if pos is not None:
                self.sell_all()
