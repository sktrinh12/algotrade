from strategies.tools.tools import symbol_type
from strategies.tools.common import YahooDataBacktesting, BacktestingBroker, Trader, datetime, argparse
from param_helper import STRATEGIES, build_params


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Trading Bot with various Strategies')
    parser.add_argument('--trade', action='store_true', help='Enable live trading')

    parser.add_argument('--symbol', type=symbol_type, default='AAPL', help='Specify ticker symbol')
    parser.add_argument('--window', type=int, default=22, help='Specify window size')
    parser.add_argument('--short_window', type=int, default=9, help='Specify short window size')
    parser.add_argument('--long_window', type=int, default=21, help='Specify long window size')
    parser.add_argument('--risk_tolerance', type=float, default=0.02, help='Specify risk tolerance for bracket order')
    parser.add_argument('--cash_at_risk', type=float, default=0.1, help='Specify cash at risk or amount of capital that could be lost if the investment performs poorly')
    parser.add_argument('--num_std_dev', type=float, default=2.0, help='Specify standard deviation')
    parser.add_argument('--strategy', required=True, type=str,\
                        default=STRATEGIES[0], choices=STRATEGIES,\
                        help=f'Specify a strategy: {", ".join(STRATEGIES)}')

    args = parser.parse_args()

    params = build_params(args)
    if args.trade:
        print("Live trading is enabled.")
        broker = Alpaca(ALPACA_CONFIG)
        strategy = SimpleMACrossover(
                    name=strat_name,
                    broker=broker,
                    parameters = params
        )
        bot = Trader()
        bot.add_strategy(strategy)
        bot.run_all()
    else:
        start = datetime(2023, 1, 1)
        end = datetime(2023, 5, 1)
        data_source = YahooDataBacktesting(
            datetime_start=start,
            datetime_end=end,
        )
        broker = BacktestingBroker(data_source=data_source)
        strat_name = f'{args.symbol}_{args.strategy}'
        if args.strategy == STRATEGIES[0]: # Simple Moving Avg Crossover
            from strategies.SimpleMACrossover import SimpleMACrossover
            strategy = SimpleMACrossover(
                  name=strat_name,
                  broker=broker,
                  parameters=params
            )
        elif args.strategy == STRATEGIES[1]: # BollingerBands
            from strategies.BollingerBands import BollingerBandsBot
            strategy = BollingerBandsBot(
                  name=strat_name,
                  broker=broker,
                  parameters=params
            )
        elif args.strategy == STRATEGIES[2]: # MeanRevision
            from strategies.MeanRevision import MeanRevision
            strategy = MeanRevision(
                  name=strat_name,
                  broker=broker,
                  parameters=params
            )
        elif args.strategy == STRATEGIES[3]: # SentimentAnalysis
            from strategies.SentimentAnalysis import SentimentAnalysis
            strategy = SentimentAnalysis(
                  name=strat_name,
                  broker=broker,
                  parameters=params
            )
        elif args.strategy == STRATEGIES[4]: # AroonCrossover
            from strategies.AroonCrossover import AroonCrossover
            strategy = AroonCrossover(
                  name=strat_name,
                  broker=broker,
                  parameters=params
            )
        elif args.strategy == STRATEGIES[5]: # EmaCrossover
            from strategies.EmaCrossover import EmaCrossover
            strategy = EmaCrossover(
                  name=strat_name,
                  broker=broker,
                  parameters=params
            )
        elif args.strategy == STRATEGIES[6]: # VolatilityATR
            from strategies.VolatilityATR import VolatilityATR
            strategy = VolatilityATR(
                  name=strat_name,
                  broker=broker,
                  parameters=params
            )



        trader = Trader(logfile="", backtest=True)
        trader.add_strategy(strategy)
        results = trader.run_all(show_plot=True,
                                 show_tearsheet=True,
                                 save_tearsheet=False)
        assert results
