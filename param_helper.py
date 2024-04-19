STRATEGY_INDICES = {
    'simple-mac-crossover': 0,
    'bollinger-bands': 1,
    'mean-reversion': 2,
    'sentiment': 3,
    'aroon-crossover': 4,
    'ema-crossover': 5,
    'volatility-atr': 6,
    'rsi-crossover': 7
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
    for k,v in parameters.items():
        print(f'{k}:{v}')
    return parameters

