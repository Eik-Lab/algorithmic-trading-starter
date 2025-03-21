from typing import Dict, Any, Tuple, Optional, List
import numpy as np
from src.strategy import Strategy, Position, Order


class SMAStrategy(Strategy):
    """
    A Simple Moving Average (SMA) crossover strategy.
    
    This strategy generates trading signals based on the crossover of two
    simple moving averages of different periods (fast and slow).
    """
    
    def __init__(self, name: str, fast_period: int = 10, slow_period: int = 30, 
                 position_size: float = 100.0, stop_loss_pct: Optional[float] = None,
                 take_profit_pct: Optional[float] = None):
        """
        Initialize the SMA strategy.
        
        Args:
            name: A unique identifier for the strategy
            fast_period: Period for the fast moving average
            slow_period: Period for the slow moving average
            position_size: Default position size as percentage of available capital
            stop_loss_pct: Optional stop loss percentage
            take_profit_pct: Optional take profit percentage
        """
        super().__init__(name)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.default_position_size = position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        
        # Initialize price history
        self.price_history: List[float] = []
        
        # Initialize moving averages
        self.fast_ma: Optional[float] = None
        self.slow_ma: Optional[float] = None
        
        # Previous moving averages for crossover detection
        self.prev_fast_ma: Optional[float] = None
        self.prev_slow_ma: Optional[float] = None
    
    def update(self, data: Dict[str, Any]) -> None:
        """
        Process new market data and update the strategy state.
        
        Args:
            data: Dictionary containing market data with 'price' key
        """
        if 'price' in data:
            # Store previous moving averages for crossover detection
            self.prev_fast_ma = self.fast_ma
            self.prev_slow_ma = self.slow_ma
            
            # Add new price to history
            self.price_history.append(data['price'])
            
            # Keep only necessary price history
            if len(self.price_history) > self.slow_period:
                self.price_history = self.price_history[-self.slow_period:]
            
            # Calculate moving averages if we have enough data
            if len(self.price_history) >= self.fast_period:
                self.fast_ma = sum(self.price_history[-self.fast_period:]) / self.fast_period
            
            if len(self.price_history) >= self.slow_period:
                self.slow_ma = sum(self.price_history[-self.slow_period:]) / self.slow_period
            
            # Generate trading signal based on moving average crossover
            if self.fast_ma is not None and self.slow_ma is not None:
                current_price = data['price']
                
                # Check for crossover and generate signals
                if self.prev_fast_ma is not None and self.prev_slow_ma is not None:
                    # Bullish crossover (fast MA crosses above slow MA)
                    if self.prev_fast_ma <= self.prev_slow_ma and self.fast_ma > self.slow_ma:
                        if self.position != Position.LONG:
                            # Close any existing position
                            if self.position != Position.NEUTRAL:
                                self.close()
                            
                            # Calculate stop loss and take profit levels if specified
                            stop_loss = None
                            if self.stop_loss_pct is not None:
                                stop_loss = current_price * (1 - self.stop_loss_pct / 100)
                            
                            take_profit = None
                            if self.take_profit_pct is not None:
                                take_profit = current_price * (1 + self.take_profit_pct / 100)
                            
                            # Enter long position
                            self.long(self.default_position_size, current_price, stop_loss, take_profit)
                    
                    # Bearish crossover (fast MA crosses below slow MA)
                    elif self.prev_fast_ma >= self.prev_slow_ma and self.fast_ma < self.slow_ma:
                        if self.position != Position.SHORT:
                            # Close any existing position
                            if self.position != Position.NEUTRAL:
                                self.close()
                            
                            # Calculate stop loss and take profit levels if specified
                            stop_loss = None
                            if self.stop_loss_pct is not None:
                                stop_loss = current_price * (1 + self.stop_loss_pct / 100)
                            
                            take_profit = None
                            if self.take_profit_pct is not None:
                                take_profit = current_price * (1 - self.take_profit_pct / 100)
                            
                            # Enter short position
                            self.short(self.default_position_size, current_price, stop_loss, take_profit)
    
    def generate_signal(self, data: Dict[str, Any]) -> Tuple[Position, float]:
        """
        Analyze market data and determine whether to go long, short, or stay neutral.
        
        Args:
            data: Dictionary containing market data
            
        Returns:
            A tuple containing the position signal (LONG, SHORT, or NEUTRAL) and the signal strength (0.0 to 1.0)
        """
        # Need both moving averages to generate a signal
        if self.fast_ma is None or self.slow_ma is None:
            return Position.NEUTRAL, 0.0
        
        # Calculate signal strength based on the difference between moving averages
        ma_diff = self.fast_ma - self.slow_ma
        ma_avg = (self.fast_ma + self.slow_ma) / 2
        signal_strength = min(abs(ma_diff / ma_avg), 1.0)
        
        # Generate signal based on moving average relationship
        if self.fast_ma > self.slow_ma:
            return Position.LONG, signal_strength
        elif self.fast_ma < self.slow_ma:
            return Position.SHORT, signal_strength
        else:
            return Position.NEUTRAL, 0.0
    
    def calculate_position_size(self, signal_strength: float) -> float:
        """
        Calculate the position size based on signal strength.
        
        Args:
            signal_strength: A value between 0.0 and 1.0 indicating the strength of the signal
            
        Returns:
            The position size to use (as a percentage of available capital)
        """
        # Scale position size based on signal strength
        return self.default_position_size * signal_strength
    
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
        previous_position = self.position
        previous_size = self.position_size
        previous_price = self.entry_price
        
        self.position = Position.NEUTRAL
        self.position_size = 0.0
        self.entry_price = 0.0
        self.stop_loss = None
        self.take_profit = None
        
        print(f"CLOSED {previous_position.value}: Size={previous_size}, Entry={previous_price}")

