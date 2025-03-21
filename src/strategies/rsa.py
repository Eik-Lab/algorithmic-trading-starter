import numpy as np
from typing import Dict, Any, Tuple, Optional
from strategy import Strategy, Position


class RSAStrategy(Strategy):
    """
    A stupid simple Relative Strength Analysis (RSA) strategy.
    
    This strategy compares the price of an asset to a moving average
    and generates signals based on the relative strength.
    """
    
    def __init__(self, name: str, window_size: int = 14):
        """
        Initialize the RSA strategy.
        
        Args:
            name: A unique identifier for the strategy
            window_size: The lookback period for calculating moving average
        """
        super().__init__(name)
        self.window_size = window_size
        self.prices = []
    
    def update(self, data: Dict[str, Any]) -> None:
        """
        Process new market data and update the strategy state.
        
        Args:
            data: Dictionary containing market data with 'price' key
        """
        if 'price' not in data:
            print("Warning: Missing price data for RSA strategy")
            return
        
        # Store price data
        self.prices.append(data['price'])
        
        # Keep only the most recent window_size prices
        if len(self.prices) > self.window_size:
            self.prices = self.prices[-self.window_size:]
        
        # Execute the strategy if we have enough data
        if len(self.prices) >= self.window_size:
            self.execute_strategy(data)
    
    def generate_signal(self, data: Dict[str, Any]) -> Tuple[Position, float]:
        """
        Generate trading signals based on relative strength analysis.
        
        Args:
            data: Dictionary containing market data
            
        Returns:
            A tuple containing the position signal and signal strength
        """
        if len(self.prices) < self.window_size:
            return Position.NEUTRAL, 0.0
        
        current_price = data['price']
        moving_avg = np.mean(self.prices)
        
        # Calculate relative strength (how far price is from moving average)
        relative_strength = (current_price / moving_avg) - 1
        
        # Calculate signal strength (normalized between 0 and 1)
        signal_strength = min(abs(relative_strength) * 10, 1.0)
        
        # Generate position signal based on stupid simple logic
        if current_price > moving_avg * 1.02:  # Price is 2% above MA
            return Position.LONG, signal_strength
        elif current_price < moving_avg * 0.98:  # Price is 2% below MA
            return Position.SHORT, signal_strength
        else:
            return Position.NEUTRAL, 0.0
    
    def calculate_position_size(self, signal_strength: float) -> float:
        """
        Calculate position size based on signal strength.
        
        Args:
            signal_strength: A value between 0.0 and 1.0 indicating signal strength
            
        Returns:
            The position size to use
        """
        # Simple position sizing: stronger signals get larger positions
        base_size = 1.0
        return base_size * signal_strength
    
    def short(self, size: float, entry_price: float, 
              stop_loss: Optional[float] = None, 
              take_profit: Optional[float] = None) -> None:
        """
        Enter a short position.
        
        Args:
            size: Position size
            entry_price: Entry price
            stop_loss: Optional stop loss price
            take_profit: Optional take profit price
        """
        self.position = Position.SHORT
        self.position_size = size
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        print(f"SHORT: Size={size}, Entry={entry_price}, SL={stop_loss}, TP={take_profit}")
    
    def close(self) -> None:
        """Close the current position."""
        old_position = self.position
        self.position = Position.NEUTRAL
        self.position_size = 0.0
        print(f"CLOSED: Previous position={old_position.value}")

