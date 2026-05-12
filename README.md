# crypto-momentum-backtest-
Configurable SMA crossover momentum backtest engine for crypto markets. Fetches live OHLCV data from Binance API, calculates Sharpe ratio, max drawdown, and equity curve with transaction cost modelling.
# Crypto Momentum Backtest Engine

A clean, configurable backtesting framework for SMA crossover momentum strategies on crypto OHLCV data. Fetches historical candles directly from the Binance public API — no data files needed.

## Strategy Logic

- **Entry:** Go long when the short-term SMA crosses above the long-term SMA
- **Exit:** Close position when short-term SMA crosses below long-term SMA
- Applies a realistic transaction cost model (configurable taker fee per side)
- Compares strategy performance against buy-and-hold benchmark

## Output

```
==========================================
  BACKTEST RESULTS
==========================================
  Symbol                 BTCUSDT
  Period                 2024-05-10 → 2025-05-09
  Strategy Return        +34.17%
  Buy & Hold             +41.82%
  Sharpe Ratio           1.243
  Max Drawdown           -18.34%
  Round Trips            14
  Final Equity           $13,417.00
==========================================
```

## Setup

```bash
pip install requests pandas numpy
python momentum_backtest.py
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `SYMBOL` | BTCUSDT | Trading pair |
| `INTERVAL` | 1d | Candle timeframe |
| `LOOKBACK` | 365 | Number of candles |
| `SHORT_WINDOW` | 20 | Fast SMA period |
| `LONG_WINDOW` | 50 | Slow SMA period |
| `INITIAL_CAPITAL` | $10,000 | Starting capital |
| `TAKER_FEE` | 0.06% | Per-side transaction cost |

## Extending

- Swap in different signal logic (RSI, Bollinger, momentum score)
- Add walk-forward validation by splitting into train/test windows
- Add position sizing rules (fixed fractional, Kelly criterion)
- Export equity curve to CSV for further analysis
