"""
Crypto Momentum Backtest Engine
--------------------------------
A clean, configurable backtesting framework for momentum strategies
on crypto OHLCV data. Pulls historical data from Binance public API.

Strategy logic:
  - Enter LONG when short-term SMA crosses above long-term SMA
  - Exit when short-term SMA crosses below long-term SMA
  - Applies configurable position sizing and transaction cost model

Author: Venkata Shiva Datta Botla
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime


# ── Configuration ─────────────────────────────────────────────────────────────

SYMBOL          = "BTCUSDT"
INTERVAL        = "1d"           # 1m, 5m, 1h, 4h, 1d
LOOKBACK        = 365            # Number of candles to fetch
SHORT_WINDOW    = 20             # Fast SMA period
LONG_WINDOW     = 50             # Slow SMA period
INITIAL_CAPITAL = 10_000.0       # USD
POSITION_SIZE   = 0.95           # Fraction of capital per trade
TAKER_FEE       = 0.0006         # 0.06% per side (Binance taker)


# ── Data Fetcher ───────────────────────────────────────────────────────────────

def fetch_ohlcv(symbol: str, interval: str, limit: int) -> pd.DataFrame:
    """Fetch OHLCV candles from Binance public API."""
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()

    cols = ["open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_vol", "trades", "taker_base",
            "taker_quote", "ignore"]
    df = pd.DataFrame(r.json(), columns=cols)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df.set_index("open_time", inplace=True)
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)
    return df[["close", "volume"]]


# ── Strategy Signals ───────────────────────────────────────────────────────────

def generate_signals(df: pd.DataFrame, short: int, long: int) -> pd.DataFrame:
    """Compute SMAs and generate long/flat signals."""
    df = df.copy()
    df["sma_short"] = df["close"].rolling(short).mean()
    df["sma_long"]  = df["close"].rolling(long).mean()

    df["signal"] = 0
    df.loc[df["sma_short"] > df["sma_long"], "signal"] = 1   # Long
    df["position"] = df["signal"].shift(1).fillna(0)          # Lag by 1 bar
    return df.dropna()


# ── Backtest Engine ────────────────────────────────────────────────────────────

def run_backtest(df: pd.DataFrame) -> pd.DataFrame:
    """Simulate strategy P&L with transaction costs."""
    df = df.copy()

    df["returns"]   = df["close"].pct_change().fillna(0)
    df["trade"]     = df["position"].diff().abs()             # 1 on entry/exit
    df["cost"]      = df["trade"] * TAKER_FEE

    df["strategy_returns"] = (df["position"] * df["returns"]) - df["cost"]
    df["equity"]   = INITIAL_CAPITAL * (1 + df["strategy_returns"]).cumprod()
    df["bnh_equity"] = INITIAL_CAPITAL * (1 + df["returns"]).cumprod()

    return df


# ── Performance Metrics ────────────────────────────────────────────────────────

def compute_metrics(df: pd.DataFrame) -> dict:
    """Calculate key performance statistics."""
    r = df["strategy_returns"]

    total_return   = (df["equity"].iloc[-1] / INITIAL_CAPITAL - 1) * 100
    bnh_return     = (df["bnh_equity"].iloc[-1] / INITIAL_CAPITAL - 1) * 100

    # Annualised Sharpe (assume 365 trading days for crypto)
    sharpe = (r.mean() / r.std()) * np.sqrt(365) if r.std() > 0 else 0

    # Max drawdown
    rolling_max = df["equity"].cummax()
    drawdown     = (df["equity"] - rolling_max) / rolling_max
    max_dd       = drawdown.min() * 100

    # Trade stats
    trades        = df[df["trade"] == 1]
    num_trades    = len(trades) // 2  # Entry + exit = 1 round trip

    return {
        "Symbol"          : SYMBOL,
        "Period"          : f"{df.index[0].date()} → {df.index[-1].date()}",
        "Strategy Return" : f"{total_return:+.2f}%",
        "Buy & Hold"      : f"{bnh_return:+.2f}%",
        "Sharpe Ratio"    : f"{sharpe:.3f}",
        "Max Drawdown"    : f"{max_dd:.2f}%",
        "Round Trips"     : num_trades,
        "Final Equity"    : f"${df['equity'].iloc[-1]:,.2f}",
    }


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print(f"Fetching {LOOKBACK} {INTERVAL} candles for {SYMBOL}...")
    df = fetch_ohlcv(SYMBOL, INTERVAL, LOOKBACK)

    print(f"Generating signals  (SMA{SHORT_WINDOW} / SMA{LONG_WINDOW})...")
    df = generate_signals(df, SHORT_WINDOW, LONG_WINDOW)

    print("Running backtest...\n")
    df = run_backtest(df)

    metrics = compute_metrics(df)

    print("=" * 45)
    print("  BACKTEST RESULTS")
    print("=" * 45)
    for k, v in metrics.items():
        print(f"  {k:<22} {v}")
    print("=" * 45)

    # Show last 5 rows of equity curve
    print("\nEquity curve (last 5 bars):")
    print(df[["close", "position", "strategy_returns", "equity"]].tail())


if __name__ == "__main__":
    main()
