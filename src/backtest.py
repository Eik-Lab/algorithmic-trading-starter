import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from trader import Trader
from typing import Type, Dict, Any, Optional


def generate_sample_data(days=100, volatility=0.01, trend=0.001):
    """
    Generate sample price data for testing.
    
    Args:
        days: Number of days to generate
        volatility: Daily price volatility
        trend: Trend factor (positive for uptrend, negative for downtrend)
        
    Returns:
        DataFrame with date and price columns
    """
    np.random.seed(42)  # For reproducibility
    
    # Generate random price movements
    returns = np.random.normal(trend, volatility, days)
    
    # Calculate price series starting at 100
    price = 100
    prices = [price]
    
    for ret in returns:
        price *= (1 + ret)
        prices.append(price)
    
    # Create date range
    dates = pd.date_range(start='2023-01-01', periods=days+1)
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'price': prices
    })
    
    return df


def load_data_from_csv(file_path: str) -> pd.DataFrame:
    """
    Load historical price data from a CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        DataFrame with price data
    """
    df = pd.read_csv(file_path)
    
    # Ensure the DataFrame has the required columns
    required_columns = ['date', 'price']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"CSV file must contain a '{col}' column")
    
    # Convert date column to datetime
    df['date'] = pd.to_datetime(df['date'])
    
    return df


def backtest_strategy(data: pd.DataFrame, strategy_class: Type, strategy_params: Optional[Dict[str, Any]] = None, initial_capital: float = 10000):
    """
    Backtest a trading strategy on historical data.
    
    Args:
        data: DataFrame with price data
        strategy_class: Strategy class to test
        strategy_params: Dictionary of parameters for the strategy
        initial_capital: Initial capital for the backtest
        
    Returns:
        Trader instance with backtest results
    """
    if strategy_params is None:
        strategy_params = {}
    
    # Initialize trader and strategy
    trader = Trader(initial_capital=initial_capital)
    strategy = strategy_class(name=f"{strategy_class.__name__}_Backtest", **strategy_params)
    trader.add_strategy(strategy)
    
    # Run backtest
    for _, row in data.iterrows():
        market_data = {
            'price': row['price'],
            'date': row['date']
        }
        trader.update(market_data)
    
    # Close any open positions at the end
    for strategy_name in trader.positions:
        if trader.positions[strategy_name]['active']:
            trader._close_position(strategy_name, data.iloc[-1]['price'])
    
    return trader


def plot_backtest_results(data: pd.DataFrame, trader: Trader, save_path: Optional[str] = None):
    """
    Plot the backtest results.
    
    Args:
        data: DataFrame with price data
        trader: Trader instance with backtest results
        save_path: Optional path to save the plot
    """
    # Extract trade data
    trades = pd.DataFrame(trader.trade_history)
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})
    
    # Plot price chart
    ax1.plot(data['date'], data['price'], label='Price')
    
    # Plot entry and exit points
    long_entries = []
    short_entries = []
    exits = []
    
    for i, trade in enumerate(trader.trade_history):
        if trade['action'] == 'open_long':
            entry = ax1.scatter(data['date'][i], trade['price'], color='green', marker='^', s=100)
            long_entries.append(entry)
        elif trade['action'] == 'open_short':
            entry = ax1.scatter(data['date'][i], trade['price'], color='red', marker='v', s=100)
            short_entries.append(entry)
        elif trade['action'] == 'close':
            exit_point = ax1.scatter(data['date'][i], trade['price'], color='black', marker='o', s=50)
            exits.append(exit_point)
    
    # Add legend with trade signals
    legend_elements = [
        plt.Line2D([0], [0], color='blue', lw=2, label='Price'),
        plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='green', markersize=10, label='Long Entry'),
        plt.Line2D([0], [0], marker='v', color='w', markerfacecolor='red', markersize=10, label='Short Entry'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='black', markersize=8, label='Exit')
    ]
    
    ax1.set_title('Price Chart with Trade Signals')
    ax1.set_ylabel('Price')
    ax1.legend(handles=legend_elements, loc='upper left')
    ax1.grid(True)
    
    # Plot equity curve
    equity = [trader.initial_capital]
    for trade in trader.trade_history:
        if trade['action'] == 'close':
            equity.append(equity[-1] + trade.get('net_pnl', 0))
    
    # Extend equity array to match data length
    while len(equity) < len(data):
        equity.append(equity[-1])
    
    ax2.plot(data['date'][:len(equity)], equity, label='Equity Curve', color='purple')
    ax2.set_title('Equity Curve')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Capital')
    ax2.legend(loc='upper left')
    ax2.grid(True)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
    
    plt.show()


def print_performance_summary(trader: Trader):
    """
    Print a summary of the backtest performance.
    
    Args:
        trader: Trader instance with backtest results
    """
    summary = trader.get_performance_summary()
    
    print("\n===== PERFORMANCE SUMMARY =====")
    print(f"Initial Capital: ${summary['initial_capital']:.2f}")
    print(f"Final Capital: ${summary['current_capital']:.2f}")
    print(f"Total Return: {summary['total_return']:.2f}%")
    print(f"Total Trades: {summary['total_trades']}")
    print(f"Winning Trades: {summary['winning_trades']} ({summary['win_rate']:.2f}%)")
    print(f"Losing Trades: {summary['losing_trades']}")
    print(f"Profit Factor: {summary['profit_factor']:.2f}")
    print(f"Total Commission: ${summary['total_commission']:.2f}")
    print("================================\n")


if __name__ == "__main__":
    from strategies.rsa import RSAStrategy
    
    print("Algorithmic Trading Starter - RSA Strategy Backtest")
    
    # Generate sample data
    print("Generating sample price data...")
    data = generate_sample_data(days=1000, volatility=0.015, trend=0.0005)
    
    # Set strategy parameters
    strategy_params = {
        'window_size': 20  # 20-day moving average
    }
    
    # Run backtest
    print(f"Running backtest with RSA strategy (window size: {strategy_params['window_size']})...")
    trader = backtest_strategy(data, RSAStrategy, strategy_params)
    
    # Print performance summary
    print_performance_summary(trader)
    
    # Plot results
    print("Plotting results...")
    plot_backtest_results(data, trader, save_path='backtest_results.png')
    
    print("Backtest completed. Results saved to 'backtest_results.png'")

