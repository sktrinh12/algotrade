from .tools.common import Strategy, np, pd
from .tools.tools import position_sizing, set_vars, prnt_params


class BollingerBandsCalc():

    def __init__(self, params):
        self.num_std_dev = params['num_std_dev']
        self.window = params['window']

    def get_data(self, prices: np.array) -> pd.DataFrame:
        last_price = prices.iloc[-1]
        rolling_mean = prices.rolling(window=self.window).mean()
        rolling_std = prices.rolling(window=self.window).std()
        upper_band = rolling_mean + (rolling_std * self.num_std_dev)
        lower_band = rolling_mean - (rolling_std * self.num_std_dev)
        signal = np.where(
                last_price > upper_band,
                'SELL',
                np.where(last_price < lower_band,
                         'BUY','HOLD'
                         )
        )

        return pd.DataFrame({'Price': prices,
                             'RollingMean': rolling_mean,
                             'RollingStd': rolling_std,
                             'UpperBand': upper_band,
                             'LowerBand': lower_band,
                             'Signal': signal,
                            })


class BollingerBands(Strategy):

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
        self.strategy = BollingerBandsCalc(
            params = {
                'num_std_dev': self.parameters['num_std_dev'],
                'window': self.parameters['window']
            }
        )
        prnt_params(self.parameters)


    def on_trading_iteration(self):
        bars = self.get_historical_prices(self.parameters['symbol'], self.parameters['window'], "day")
        prices = bars.df['close']

        if len(prices) < self.parameters['window']:
            return

        data = self.strategy.get_data(prices)
        signal, last_price = set_vars(data, 'Signal')
        last_lower_band = data['UpperBand'].iloc[-1]
        last_upper_band = data['LowerBand'].iloc[-1]

        cash = self.get_cash()
        quantity = position_sizing(cash, last_price, self.parameters['cash_at_risk'])
        print(f"{'':<4}Last Price: {last_price}, Quantity: {quantity}, UB: {last_upper_band}, LB: {last_lower_band}")

        if signal == 'SELL':
            pos = self.get_position(self.parameters['symbol'])
            if pos is not None:
                self.sell_all()
        elif (signal == 'BUY') and (cash > 0) and (quantity > 0):
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
