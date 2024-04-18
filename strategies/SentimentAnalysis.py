from .tools.common import Strategy, np, pd
from datetime import timedelta
from .tools.tools import position_sizing, symbol_type
from .tools.finbert_utils import estimate_sentiment
from .tools.config import ALPACA_CONFIG
from alpaca_trade_api import REST

class SentimentAnalysis(Strategy):

    parameters = {
        "symbol": "",
        "window": 0,
        "cash_at_risk": 0.0,
        "risk_tolerance": 0.0,
    }

    def initialize(self):
        self.sleeptime = "1H"
        self.last_trade = None
        self.probability_threshold = 0.9
        self.api = REST(base_url=ALPACA_CONFIG['BASE_URL'],\
                        key_id=ALPACA_CONFIG['API_KEY'],\
                        secret_key=ALPACA_CONFIG['API_SECRET'])

    def get_dates(self):
        today = self.get_datetime()
        three_days_prior = today - timedelta(days=3)
        return today.strftime('%Y-%m-%d'), three_days_prior.strftime('%Y-%m-%d')

    def get_sentiment(self):
        today, three_days_prior = self.get_dates()
        news = self.api.get_news(symbol=self.parameters['symbol'], start=three_days_prior, end=today)
        news = [ev.__dict__["_raw"]["headline"] for ev in news]
        probability, sentiment = estimate_sentiment(news)
        print(f'sentiment: {sentiment}; probability: {probability:.2f}')
        return probability, sentiment

    def on_trading_iteration(self):
        probability, sentiment = self.get_sentiment()

        cash = self.get_cash()
        last_price = self.get_last_price(self.parameters['symbol'])
        quantity = position_sizing(cash, last_price, self.parameters['cash_at_risk'])
        if cash > last_price:
            take_profit_price = last_price * (1 + self.parameters['risk_tolerance'])
            stop_loss_price = last_price * (1 - self.parameters['risk_tolerance'])
            if sentiment == "positive" and probability > self.probability_threshold:
                if self.last_trade == "SELL":
                    self.sell_all()
                order = self.create_order(
                    self.parameters['symbol'],
                    quantity,
                    side="buy",
                    type="bracket",
                    take_profit_price=take_profit_price,
                    stop_loss_price=stop_loss_price
                )
                self.submit_order(order)
                self.last_trade = "BUY"
            elif sentiment == "negative" and probability > self.probability_threshold:
                if self.last_trade == "BUY":
                    self.sell_all()
                order = self.create_order(
                    self.parameters['symbol'],
                    quantity,
                    side="sell",
                    type="bracket",
                    take_profit_price=take_profit_price,
                    stop_loss_price=stop_loss_price
                )
                self.submit_order(order)
                self.last_trade = "SELL"
