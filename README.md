# Algorithmic Trading Starter

A simple framework for algorithmic trading with backtesting and live trading capabilities. This project provides a modular architecture for developing, testing, and deploying trading strategies with minimal setup.

## Features

- Modular strategy implementation with an extensible framework
- Backtesting with historical data and performance metrics
- Live trading integration with Alpaca API (both paper and real trading)
- Performance analysis and visualization tools
- Multiple built-in strategy examples (SMA, RSA)
- Asynchronous data streaming for real-time market data

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Eik-Lab/algorithmic-trading-starter.git
cd algorithmic-trading-starter
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Alpaca API credentials (for live trading):
```bash
export ALPACA_API_KEY="your_api_key"
export ALPACA_API_SECRET="your_api_secret"
```

## Usage

### Backtesting

Run a backtest with default parameters (RSA strategy on SPY):
```bash
python src/main.py --mode backtest
```

Customize your backtest:
```bash
python src/main.py --mode backtest --strategy sma --window-size 50 --symbol AAPL --days 500 --capital 100000
```

### Live Trading

Run live trading with paper account:
```bash
python src/main.py --mode live --strategy rsa --window-size 20
```

Available command-line arguments:
- `--mode`: Trading mode ('backtest' or 'live')
- `--strategy`: Strategy to use ('rsa' or 'sma')
- `--window-size`: Window size for the strategy
- `--symbol`: Symbol to trade (default: 'SPY')
- `--days`: Number of days for backtest
- `--capital`: Initial capital amount

## Project Structure

```
algorithmic-trading-starter/
├── src/
│   ├── main.py              # Main entry point
│   ├── trader.py            # Core trader implementation
│   ├── strategy.py          # Base strategy class
│   ├── backtest.py          # Backtesting engine
│   ├── live_trading.py      # Live trading with Alpaca
│   └── strategies/          # Strategy implementations
│       ├── rsa.py           # Relative Strength Analysis
│       └── sma.py           # Simple Moving Average
├── requirements.txt         # Dependencies
└── README.md                # Documentation
```

## Implementing Custom Strategies

Create a new strategy by extending the base `Strategy` class:

```python
from strategy import Strategy, Position

class MyCustomStrategy(Strategy):
    def __init__(self, name="custom_strategy", window_size=20):
        super().__init__(name)
        self.window_size = window_size
        # Initialize your strategy parameters
        
    def update(self, data):
        # Implement your strategy logic here
        # Use self.enter_long(), self.enter_short(), or self.exit_position()
        # to generate trading signals
        pass
```

## Performance Metrics

The backtesting engine provides the following performance metrics:
- Total return
- Win rate
- Profit factor
- Maximum drawdown
- Sharpe ratio
- Number of trades

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

