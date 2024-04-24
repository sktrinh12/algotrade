from .tools.common import Strategy, Trader, np, pd
from .tools.tools import position_sizing, set_vars, prnt_params

class SimpleMACrossoverCalc:

    def __init__(self, params):
        self.short_window = params['short_window']
        self.long_window = params['long_window']
        self.data = None

    def get_data(self, prices: np.array) -> pd.DataFrame:
        data = pd.DataFrame({'Price': prices})
        data['short_ma'] = data['Price'].rolling(self.short_window).mean()
        data['long_ma'] = data['Price'].rolling(self.long_window).mean()
        # Buy condition: short moving average crosses above long moving average
        buy_condition = (data['short_ma'] > data['long_ma'])
        # Sell condition: short moving average crosses below long moving average
        sell_condition = (buy_condition) & (buy_condition.shift(1) == False)
        hold_condition = ~(buy_condition | sell_condition)

        sell_condition = (data['short_ma'] < data['long_ma']) & (data['short_ma'].shift(1) >= data['long_ma'].shift(1))

        # Hold condition: neither buy nor sell condition is met
        hold_condition = ~(buy_condition | sell_condition)
        data['Signal'] = ''
        data.loc[buy_condition, 'Signal'] = 'BUY'
        data.loc[sell_condition, 'Signal'] = 'SELL'
        data.loc[hold_condition, 'Signal'] = 'HOLD'
        self.data = data
        return data



class SimpleMACrossover(Strategy):
    parameters = {
        'symbol': '',
        "window": 0,
        'short_window' : 0,
        'long_window' : 0,
        'risk_tolerance' : 0.0,
        'cash_at_risk': 0.0,
    }

    def initialize(self):
        self.sleeptime = "1D"
        self.strategy = SimpleMACrossoverCalc(
            params = {
                'short_window': self.parameters['short_window'],
                'long_window': self.parameters['long_window']
            }
        )
        prnt_params(self.parameters)

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
