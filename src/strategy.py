from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass


class Position(Enum):
    """Enum representing possible position states."""
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"


@dataclass
class Order:
    """Class representing a trading order."""
    price: float
    quantity: float
    direction: Position


class Strategy(ABC):
    """
    Base class for algorithmic trading strategies.
    
    This class provides a framework for implementing trading strategies
    with common methods for position management and signal generation.
    """
    
    def __init__(self, name: str):
        """
        Initialize a new strategy.
        
        Args:
            name: A unique identifier for the strategy
        """
        self.name = name
        self.position = Position.NEUTRAL
        self.position_size = 0.0
        self.entry_price = 0.0
        self.stop_loss = 0.0
        self.take_profit = 0.0
        
        # For live trading order management
        self.order_pending = False
        self.pending_order = None
    
    @abstractmethod
    def update(self, data: Dict[str, Any]) -> None:
        """
        Process new market data and update the strategy state.
        
        Args:
            data: Dictionary containing market data
        """
        pass
    
    @abstractmethod
    def generate_signal(self, data: Dict[str, Any]) -> Tuple[Position, float]:
        """
        Analyze market data and determine whether to go long, short, or stay neutral.
        
        Args:
            data: Dictionary containing market data
            
        Returns:
            A tuple containing the position signal (LONG, SHORT, or NEUTRAL) and the signal strength (0.0 to 1.0)
        """
        pass
    
    def execute_strategy(self, data: Dict[str, Any]) -> Optional[Order]:
        """
        This method provides a blanket implementation. Feel free to override.
        Execute the strategy based on the current market data.
        
        This method calls generate_signal() to determine the position,
        then executes an action based on the signal.
        
        Args:
            data: Dictionary containing market data
            
        Returns:
            An Order object if a trade is executed, None otherwise
        """
        signal, strength = self.generate_signal(data)
        # Should probably throw an error? 
        current_price = data.get('price', 0.0)
        
        # Determine position size based on signal strength
        size = self.calculate_position_size(strength)
        
        if signal == Position.LONG and self.position != Position.LONG:
            if self.position == Position.SHORT:
                self.close()
            self.long(size, current_price)
            order = Order(price=current_price, quantity=size, direction=Position.LONG)
            self.order_pending = True
            self.pending_order = order
            return order
            
        elif signal == Position.SHORT and self.position != Position.SHORT:
            if self.position == Position.LONG:
                self.close()
            self.short(size, current_price)
            order = Order(price=current_price, quantity=size, direction=Position.SHORT)
            self.order_pending = True
            self.pending_order = order
            return order
            
        elif signal == Position.NEUTRAL and self.position != Position.NEUTRAL:
            self.close()
            order = Order(price=current_price, quantity=self.position_size, direction=Position.NEUTRAL)
            self.order_pending = True
            self.pending_order = order
            return order
            
        return None
    
    def calculate_position_size(self, signal_strength: float) -> float:
        """
        Calculate the position size based on signal strength.
        
        Args:
            signal_strength: A value between 0.0 and 1.0 indicating the strength of the signal
            
        Returns:
            The position size to use
        """
        pass
    
    def long(self, size: float, entry_price: float, 
             stop_loss: Optional[float] = None, 
             take_profit: Optional[float] = None) -> None:
        """
        Enter a long position.
        
        Args:
            size: Position size
            entry_price: Entry price
            stop_loss: Optional stop loss price
            take_profit: Optional take profit price
        """
        self.position = Position.LONG
        self.position_size = size
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        print(f"LONG: Size={size}, Entry={entry_price}, SL={stop_loss}, TP={take_profit}")
    
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
        pass
           
    def close(self) -> None:
        """Close the current position."""
        pass
    
    def adjust_stop_loss(self, new_stop_loss: float) -> None:
        """
        Adjust the stop loss level for the current position.
        
        Args:
            new_stop_loss: New stop loss price
        """
        self.stop_loss = new_stop_loss
        print(f"ADJUSTED SL: New stop loss = {new_stop_loss}")
    
    def adjust_take_profit(self, new_take_profit: float) -> None:
        """
        Adjust the take profit level for the current position.
        
        Args:
            new_take_profit: New take profit price
        """
        self.take_profit = new_take_profit
        print(f"ADJUSTED TP: New take profit = {new_take_profit}")
    
    def is_in_position(self) -> bool:
        """Check if the strategy is currently in a position."""
        return self.position != Position.NEUTRAL
    
    def get_position(self) -> Position:
        """Get the current position state."""
        return self.position
    
