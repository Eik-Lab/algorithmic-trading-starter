import asyncio
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Alpaca API imports
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.live import StockDataStream

from trader import Trader
from strategy import Strategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlpacaTrader:
    """
    Live trading implementation using Alpaca API.
    
    This class handles the connection to Alpaca, data streaming,
    and order execution based on strategy signals.
    """
    
    def __init__(
        self, 
        api_key: str, 
        api_secret: str, 
        paper_trading: bool = True,
        symbols: List[str] = ["SPY"],
        timeframe: TimeFrame = TimeFrame.Day,
        initial_capital: float = 10000.0
    ):
        """
        Initialize the Alpaca trader.
        
        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            paper_trading: Whether to use paper trading
            symbols: List of symbols to trade
            timeframe: Timeframe for data
            initial_capital: Initial capital for the trader
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.paper_trading = paper_trading
        self.symbols = symbols
        self.timeframe = timeframe
        
        # Initialize Alpaca clients
        self.trading_client = TradingClient(api_key, api_secret, paper=paper_trading)
        self.data_client = StockHistoricalDataClient(api_key, api_secret)
        self.data_stream = StockDataStream(api_key, api_secret)
        
        # Initialize our trader
        self.trader = Trader(initial_capital=initial_capital)
        
        # Store latest prices
        self.latest_prices = {}
        
        # Flag to control the trading loop
        self.is_running = False
        
        logger.info(f"AlpacaTrader initialized with symbols: {symbols}")
    
    async def start(self):
        """Start the trading system."""
        self.is_running = True
        
        # Subscribe to data stream
        await self._setup_data_stream()
        
        # Load historical data for initialization
        await self._load_historical_data()
        
        # Start the main trading loop
        await self._trading_loop()
    
    async def stop(self):
        """Stop the trading system."""
        self.is_running = False
        await self.data_stream.stop_ws()
        logger.info("Trading system stopped")
    
    def add_strategy(self, strategy: Strategy):
        """
        Add a trading strategy.
        
        Args:
            strategy: Strategy to add
        """
        self.trader.add_strategy(strategy)
        logger.info(f"Added strategy: {strategy.name}")
    
    async def _setup_data_stream(self):
        """Set up the data stream for real-time updates."""
        # Subscribe to trade updates
        self.data_stream.subscribe_trades(self._handle_trade_update, *self.symbols)
        
        # Subscribe to bar updates (if needed)
        # self.data_stream.subscribe_bars(self._handle_bar_update, *self.symbols)
        
        # Start the websocket connection
        await self.data_stream.run()
        
        logger.info(f"Data stream set up for symbols: {self.symbols}")
    
    async def _load_historical_data(self):
        """Load historical data to initialize strategies."""
        end = datetime.now()
        start = end - timedelta(days=30)  # Get 30 days of data
        
        for symbol in self.symbols:
            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=self.timeframe,
                start=start,
                end=end
            )
            
            bars = self.data_client.get_stock_bars(request_params)
            
            # Convert to DataFrame for easier processing
            if symbol in bars:
                df = pd.DataFrame([bar.dict() for bar in bars[symbol]])
                
                # Initialize strategies with historical data
                for _, row in df.iterrows():
                    market_data = {
                        'symbol': symbol,
                        'price': row['close'],
                        'date': row['timestamp']
                    }
                    self.trader.update(market_data)
                
                # Store the latest price
                if not df.empty:
                    self.latest_prices[symbol] = df.iloc[-1]['close']
                    
                logger.info(f"Loaded {len(df)} historical bars for {symbol}")
    
    def _handle_trade_update(self, trade):
        """
        Handle real-time trade updates.
        
        Args:
            trade: Trade data from Alpaca
        """
        symbol = trade.symbol
        price = trade.price
        timestamp = trade.timestamp
        
        # Update latest price
        self.latest_prices[symbol] = price
        
        # Create market data dictionary
        market_data = {
            'symbol': symbol,
            'price': price,
            'date': timestamp
        }
        
        # Update trader with new data
        self.trader.update(market_data)
        
        # Check if we need to execute any orders
        self._check_and_execute_orders(symbol)
    
    def _check_and_execute_orders(self, symbol: str):
        """
        Check if we need to execute any orders based on strategy signals.
        
        Args:
            symbol: Symbol to check
        """
        for strategy_name, position_info in self.trader.positions.items():
            # Skip if this strategy doesn't have an active position change
            if not hasattr(self.trader.strategies[strategy_name], 'order_pending'):
                continue
                
            if self.trader.strategies[strategy_name].order_pending:
                # Get the order details
                order = self.trader.strategies[strategy_name].pending_order
                
                # Execute the order
                self._execute_order(symbol, order.direction, order.quantity)
                
                # Reset the pending order flag
                self.trader.strategies[strategy_name].order_pending = False
                self.trader.strategies[strategy_name].pending_order = None
    
    def _execute_order(self, symbol: str, direction, quantity: float):
        """
        Execute an order with Alpaca.
        
        Args:
            symbol: Symbol to trade
            direction: Order direction (LONG, SHORT, NEUTRAL)
            quantity: Order quantity
        """
        # Determine order side
        if direction.value == 'long':
            side = OrderSide.BUY
        elif direction.value == 'short':
            side = OrderSide.SELL
        elif direction.value == 'neutral':
            # Close position - need to determine current position first
            position = self.trading_client.get_open_position(symbol)
            if position.side == 'long':
                side = OrderSide.SELL
            else:
                side = OrderSide.BUY
        
        # Create order request
        order_request = MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=side,
            time_in_force=TimeInForce.DAY
        )
        
        # Submit order
        try:
            order = self.trading_client.submit_order(order_request)
            logger.info(f"Order submitted: {order.id} - {symbol} {side} {quantity}")
        except Exception as e:
            logger.error(f"Order execution failed: {e}")
    
    async def _trading_loop(self):
        """Main trading loop that runs periodically."""
        while self.is_running:
            # Check account status
            account = self.trading_client.get_account()
            logger.info(f"Account status: ${float(account.equity):.2f} equity, ${float(account.buying_power):.2f} buying power")
            
            # Wait for next iteration
            await asyncio.sleep(60)  # Check every minute


async def main():
    """Main function to run the live trading system."""
    # Replace with your Alpaca API credentials
    API_KEY = "PKFZ8LQ6OIIT9C86KM87"
    API_SECRET = "vqCzwadxt8kTGXVB7aQcS19MsTi6kF4wOPVT1ZQM"
    
    # Initialize the Alpaca trader
    trader = AlpacaTrader(
        api_key=API_KEY,
        api_secret=API_SECRET,
        paper_trading=True,  # Use paper trading
        symbols=["SPY"],     # Trade SPY
        timeframe=TimeFrame.Day
    )
    
    # Add a strategy
    from strategies.rsa import RSAStrategy
    strategy = RSAStrategy(name="RSA_Live", window_size=20)
    trader.add_strategy(strategy)
    
    try:
        # Start the trading system
        await trader.start()
    except KeyboardInterrupt:
        # Handle graceful shutdown
        logger.info("Keyboard interrupt received, shutting down...")
    finally:
        # Stop the trading system
        await trader.stop()


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())

