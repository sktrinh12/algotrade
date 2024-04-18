from .tools.common import Strategy, np, pd
from .tools.tools import position_sizing


class VolatilityTrendATR(Strategy):

    parameters = {
        "symbol": "",
        'window': 0,
        'atr_prev_candles_num' : 0,
        "number_of_lots": 0
    }

    def get_trend_direction(self, prices: np.array):
        atr = self.atr(prices, self.parameters['timeperiod_atr'])
        current_atr = atr.iloc[-1]
        atr_prev_candles_num = atr.iloc[-self.parameters['atr_prev_candles_num']]
        return 1 if current_atr > atr_prev_candles_num else -1 if current_atr < atr_prev_candles_num else 0

    def on_candle(self, candle):
        symbol = self.parameters['symbol']
        prices = self.history(symbol, 'close', self.parameters['timeperiod_atr'], skip_last=False)
        trend_direction = self.get_trend_direction(prices)
        print(f"Trend Direction: {trend_direction}")

        if trend_direction == 1:
            self.buy_signal(symbol)
        elif trend_direction == -1:
            self.sell_signal(symbol)

    def buy_signal(self, symbol):
        position = self.get_position(symbol)
        if position is None:
            cash = self.wallet.balance
            quantity = self.calculate_quantity(cash, symbol)
            self.buy_symbol(symbol, quantity)

    def sell_signal(self, symbol):
        position = self.get_position(symbol)
        if position is not None:
            self.sell_position(symbol)

    def calculate_quantity(self, cash, symbol):
        price = self.price
        return position_sizing(cash, price, self.parameters['number_of_lots'])
