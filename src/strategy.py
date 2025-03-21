from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum


class Position(Enum):
    """Enum representing possible position states."""
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"


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
        # TODO: Consider adding these into the class
        # self.position_size = 0.0
        # self.entry_price = 0.0
        # self.stop_loss = 0.0
        # self.take_profit = 0.0
    
    @abstractmethod
    def update(self, data: Dict[str, Any]) -> None:
        """
        Process new market data and update the strategy state.
        
        Args:
            data: Dictionary containing market data
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
        pass
    
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
        pass
    
    def adjust_take_profit(self, new_take_profit: float) -> None:
        """
        Adjust the take profit level for the current position.
        
        Args:
            new_take_profit: New take profit price
        """
        pass
    
