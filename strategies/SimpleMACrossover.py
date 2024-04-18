from .tools.common import Strategy, Trader, np, pd
from .tools.tools import position_sizing, symbol_type

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
        self.signal = None
        self.last_price = 0
        self.sleeptime = "1D"


    def get_trend_signal(self, prices: np.array):
        data = pd.DataFrame({'close': prices})
        data['short_ma'] = data['close'].rolling(self.parameters['short_window']).mean()
        data['long_ma'] = data['close'].rolling(self.parameters['long_window']).mean()
        data['Signal'] = np.where(np.logical_and(data['short_ma'] > data['long_ma'],
                                                data['short_ma'].shift(1) < data['long_ma'].shift(1)),
                                 "BUY", None)
        data['Signal'] = np.where(np.logical_and(data['short_ma'] < data['long_ma'],
                                                data['short_ma'].shift(1) > data['long_ma'].shift(1)),
                                 "SELL", data['Signal'])
        last_data = data.iloc[-1]
        self.signal = last_data['Signal']
        self.last_price = last_data['close']
        print(f"{'':<4}{self.signal}")

    def on_trading_iteration(self):
        bars = self.get_historical_prices(self.parameters['symbol'], self.parameters['window'], "day")

        self.get_trend_signal(bars.df['close'])
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
