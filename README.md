# algotrade

### Trading Strategies and Optimal Parameter Values

This repository contains implementations of various trading strategies, each designed to generate buy or sell signals based on specific market conditions. The optimal parameter values for each strategy have been carefully tuned to maximize profit potential while minimizing risk.

#### Mean Reversion

- Parameters: `window=100, risk_tolerance=0.04, z_threshold=1.5`
- Description: Identifies assets that have deviated significantly from their historical mean prices, anticipating a reversion to the mean.

#### Aroon Crossover

- Parameters: `window=50, risk_tolerance=0.04`
- Description: Utilizes the Aroon indicator to identify trend changes and generate buy or sell signals accordingly.

#### Simple Moving Average Crossover

- Parameters: `window=90, risk_tolerance=0.02, short_window=14, long_window=50`
- Description: Generates signals based on the crossover of short-term and long-term moving averages, indicating potential changes in trend direction.

#### RSI Crossover

- Parameters: `window=120, risk_tolerance=0.1, upper_threshold=70, lower_threshold=30, rsi_period=14`
- Description: Uses the Relative Strength Index (RSI) to identify overbought and oversold conditions, generating buy or sell signals accordingly.

#### Exponential Moving Average Crossover

- Parameters: `short_window=10, long_window=50, risk_tolerance=0.01`
- Description: Similar to the Simple Moving Average Crossover strategy, but utilizes exponential moving averages for smoother signal generation.

#### Bollinger Bands

- Parameters: `window=100, risk_tolerance=0.04, std=1.5`
- Description: Uses Bollinger Bands to identify potential buying or selling opportunities based on price volatility.

#### Volatility ATR

- Parameters: `window=5, atr_multiplier=2.5, risk_tolerance=0.03`
- Description: Utilizes the Average True Range (ATR) indicator to determine market volatility and adjust risk parameters accordingly.

### Usage

In order to run the trading strategy:

```
python main.py --symbol MSFT --strategy mean-reversion --window 100 --cash_at_risk 0.30 --risk_tolerance 0.04
```

In order to run the same trading strategy unit test (pass symbol as an environmental variable):

```
SYMBOL=MSFT python tests/test_MeanReversion.py
```
