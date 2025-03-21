import argparse
import asyncio
import os
from strategies.rsa import RSAStrategy



def main():
    """Main function to run the application."""
    parser = argparse.ArgumentParser(description='Algorithmic Trading Starter')
    parser.add_argument('--mode', type=str, choices=['backtest', 'live'], default='backtest',
                        help='Trading mode: backtest or live')
    parser.add_argument('--strategy', type=str, default='rsa',
                        help='Strategy to use (default: rsa)')
    parser.add_argument('--window-size', type=int, default=20,
                        help='Window size for the strategy (default: 20)')
    parser.add_argument('--symbol', type=str, default='SPY',
                        help='Symbol to trade (default: SPY)')
    parser.add_argument('--days', type=int, default=1000,
                        help='Number of days for backtest (default: 1000)')
    parser.add_argument('--volatility', type=float, default=0.015,
                        help='Volatility for sample data (default: 0.015)')
    parser.add_argument('--trend', type=float, default=0.0005,
                        help='Trend factor for sample data (default: 0.0005)')
    parser.add_argument('--capital', type=float, default=10000.0,
                        help='Initial capital (default: 10000.0)')
    
    args = parser.parse_args()
    
    # Set strategy parameters
    strategy_params = {
        'window_size': args.window_size
    }
    
    if args.mode == 'backtest':
        # Import backtest module
        from backtest import generate_sample_data, backtest_strategy, print_performance_summary, plot_backtest_results
        
        print(f"Algorithmic Trading Starter - {args.strategy.upper()} Strategy Backtest")
        
        # Generate sample data
        print("Generating sample price data...")
        data = generate_sample_data(days=args.days, volatility=args.volatility, trend=args.trend)
        
        # Run backtest
        print(f"Running backtest with {args.strategy.upper()} strategy (window size: {strategy_params['window_size']})...")
        trader = backtest_strategy(data, RSAStrategy, strategy_params, initial_capital=args.capital)
        
        # Print performance summary
        print_performance_summary(trader)
        
        # Plot results
        print("Plotting results...")
        plot_backtest_results(data, trader, save_path='backtest_results.png')
        
        print("Backtest completed. Results saved to 'backtest_results.png'")
        
    elif args.mode == 'live':
        # Import live trading module
        from live_trading import main as live_main
        
        # Check if API keys are set
        api_key = os.environ.get('ALPACA_API_KEY')
        api_secret = os.environ.get('ALPACA_API_SECRET')
        
        if not api_key or not api_secret:
            print("Error: Alpaca API credentials not found in environment variables.")
            print("Please set ALPACA_API_KEY and ALPACA_API_SECRET environment variables.")
            return
        
        # Set strategy parameters as environment variables for live_trading.py
        os.environ['STRATEGY'] = args.strategy
        os.environ['WINDOW_SIZE'] = str(args.window_size)
        
        print(f"Starting live trading with {args.strategy.upper()} strategy...")
        
        # Create and run the event loop
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(live_main())
        except KeyboardInterrupt:
            print("Keyboard interrupt received, shutting down...")
        finally:
            loop.close()


if __name__ == "__main__":
    main()

