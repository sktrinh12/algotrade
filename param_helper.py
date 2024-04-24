STRATEGY_INDICES = {
    'simple-ma-crossover': ['SimpleMACrossover' , 0],
    'bollinger-bands': ['BollingerBands', 1],
    'mean-reversion':['MeanReversion', 2],
    'sentiment':['SentimentAnalysis', 3],
    'aroon-crossover':['AroonCrossover', 4],
    'ema-crossover':['EmaCrossover', 5],
    'volatility-atr':['VolatilityATR', 6],
    'rsi-crossover':['RsiCrossover', 7]
}

STRATEGIES = list(STRATEGY_INDICES.keys())

def build_params(args):
    parameters={
    "symbol": args.symbol,
    "window":args.window,
    "cash_at_risk":args.cash_at_risk,
    "risk_tolerance":args.risk_tolerance
    }
    if args.strategy == STRATEGIES[0] or args.strategy == STRATEGIES[5]:
        parameters.update({'long_window': args.long_window,
                           'short_window': args.short_window
                           })
    elif args.strategy == STRATEGIES[1]:
        parameters['num_std_dev'] = args.num_std_dev
    elif args.strategy == STRATEGIES[7]:
        parameters['rsi_period'] = args.rsi_period
        parameters['upper_threshold'] = args.upper_threshold
        parameters['lower_threshold'] = args.lower_threshold
    return parameters

