STRATEGY_INDICES = {
    'simple-mac-crossover': 0,
    'bollinger-bands': 1,
    'mean-reversion': 2,
    'sentiment': 3,
    'aroon-crossover': 4,
    'ema-crossover': 5,
    'volatility-atr': 6
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
    print(parameters)
    return parameters

