from lumibot.brokers import Alpaca
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from datetime import datetime, timedelta
from alpaca_trade_api import REST
from finbert_utils import estimate_sentiment
import pandas as pd
import numpy as np
from config import ALPACA_CONFIG
import argparse

class BotTrader(Strategy):
    def initialize(self, symbol:str="TSLA", cash_at_risk:float=.5):
        self.symbol = symbol
        self.sleeptime = "1H"
        self.last_trade = None
        self.cash_at_risk = cash_at_risk
        self.api = REST(base_url=ALPACA_CONFIG['ENDPOINT'],\
                        key_id=ALPACA_CONFIG['API_KEY'],\
                        secret_key=ALPACA_CONFIG['API_SECRET'])
        self.buy_threshold = 0.6  # Example buy threshold
        self.sell_threshold = 0.4  # Example sell threshold

    def position_sizing(self):
        cash = self.get_cash()
        last_price = self.get_last_price(self.symbol)
        quantity = round(cash * self.cash_at_risk / last_price, 0)
        return cash, last_price, quantity

    def get_dates(self):
        today = self.get_datetime()
        three_days_prior = today - timedelta(days=3)
        return today.strftime('%Y-%m-%d'), three_days_prior.strftime('%Y-%m-%d')

    def get_sentiment(self):
        today, three_days_prior = self.get_dates()
        news = self.api.get_news(symbol=self.symbol, start=three_days_prior, end=today)
        news = [ev.__dict__["_raw"]["headline"] for ev in news]
        probability, sentiment = estimate_sentiment(news)
        return probability, sentiment

    def get_mean_reversion_signal(self):
        # Fetch historical data
        bars = self.get_historical_prices(self.symbol, 200, "day")  # Fetch 200-day historical data
        df = bars.df

        # Calculate moving averages
        df['9-day'] = df['close'].rolling(9).mean()
        df['21-day'] = df['close'].rolling(21).mean()

        # Calculate the standard deviation
        df['std'] = df['close'].rolling(window=20).std()

        # Calculate the Z-score
        df['z_score'] = (df['close'] - df['21-day']) / df['std']

        # Define the trading signals
        df['signal'] = np.where(df['z_score'] < -2, "BUY", np.where(df['z_score'] > 2, "SELL", "HOLD"))

        # Get the latest signal
        latest_signal = df['signal'].iloc[-1]
        print(latest_signal)

        if latest_signal == -1:
            return "SELL"
        elif latest_signal == 1:
            return "BUY"
        else:
            return "HOLD"


    def on_trading_iteration(self):
        # Get sentiment analysis
        sentiment_probability, sentiment = self.get_sentiment()

        # Get mean reversion signal
        mean_reversion_signal = self.get_mean_reversion_signal()

        # Weighting and decision rules
        sentiment_weight = 0.4
        mean_reversion_weight = 0.6

        # Define dynamic thresholds
        buy_threshold = self.buy_threshold
        sell_threshold = self.sell_threshold
        risk_tolerance = 0.05  # 5% risk tolerance

        # Calculate combined score
        if sentiment == 'positive':
            sentiment_score = 1
        elif sentiment == 'negative':
            sentiment_score = -1
        else:
            sentiment_score = 0

        combined_score = (sentiment_weight * sentiment_probability * sentiment_score) + (mean_reversion_weight * (mean_reversion_signal == "BUY"))
        print(f'combined score: {combined_score}')

        # Execute final trading decision based on the combined signal and dynamic thresholds
        if combined_score > buy_threshold:
            # Buy
            cash, last_price, quantity = self.position_sizing()
            if cash > 0:
                # Calculate take-profit and stop-loss prices based on risk tolerance
                take_profit_price = last_price * (1 + risk_tolerance)
                stop_loss_price = last_price * (1 - risk_tolerance)

                # Create a bracket order with take-profit and stop-loss prices
                order = self.create_order(
                    self.symbol,
                    quantity,
                    "buy",
                    type="bracket",
                    take_profit_price=take_profit_price,
                    stop_loss_price=stop_loss_price
                )
                self.submit_order(order)
                self.last_trade = "BUY"
        elif combined_score < sell_threshold:
            # Sell
            pos = self.get_position(self.symbol)
            if pos is not None:
                self.sell_all()
                self.last_trade = "SELL"
        else:
            self.last_trade = "HOLD"


parser = argparse.ArgumentParser(description='Process arguments.')
parser.add_argument('--trade', action='store_true', help='Specify whether to enable trading')
parser.add_argument('--symbol', type=str, default='AAPL', help='Specify ticker symbol')
args = parser.parse_args()

if __name__ == "__main__":
    broker = Alpaca(ALPACA_CONFIG)
    strategy = BotTrader(name='mlstrat',
              broker=broker,
              parameters={"symbol":args.symbol,
                            "cash_at_risk":.5}
              )
    if args.trade:
        print(f"Real trading is enabled.")
        bot = Trader()
        bot.add_strategy(strategy)
        bot.run_all()
    else:
        print("Paper trading.")
        start = datetime(2023, 1, 5)
        end = datetime(2023, 4, 15)
        strategy.backtest(
            YahooDataBacktesting,
            start,
            end
        )
