from typing import Any, Dict
import strategy


class Trader:
    """
    Trader class responsible for executing trades based on strategy signals.
    
    This class handles the interaction between trading strategies and the market,
    managing execution, position tracking, and performance monitoring. It serves
    as the central component that coordinates multiple strategies, tracks their
    positions, and maintains the overall portfolio.
    
    The Trader maintains a record of all trades, calculates performance metrics,
    and handles the accounting aspects of trading including commissions, P&L
    calculation, and capital management. It can work with both backtesting and
    live trading implementations.
    """
    
    def __init__(self, initial_capital: float = 10000.0):
        """
        Initialize a new trader.
        
        Args:
            initial_capital: Starting capital for the trader
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.strategies: Dict[str, strategy.Strategy] = {}
        self.positions: Dict[str, Any] = {}
        self.trade_history = []
        self.commission_rate = 0.001  # 0.1% commission by default
        
    def add_strategy(self, strategy: strategy.Strategy):
        """
        Add a trading strategy to the trader.
        
        Args:
            strategy: A Strategy object to be managed by this trader
        """
        self.strategies[strategy.name] = strategy
        self.positions[strategy.name] = {
            'active': False,
            'type': None,
            'size': 0.0,
            'entry_price': 0.0,
            'current_price': 0.0,
            'pnl': 0.0,
            'stop_loss': None,
            'take_profit': None
        }
        print(f"Added strategy: {strategy.name}")
        
    def remove_strategy(self, strategy_name: str):
        """
        Remove a trading strategy from the trader.
        
        Args:
            strategy_name: Name of the strategy to remove
        """
        if strategy_name in self.strategies:
            # Close any open positions for this strategy
            if self.positions[strategy_name]['active']:
                self._close_position(strategy_name)
                
            del self.strategies[strategy_name]
            del self.positions[strategy_name]
            print(f"Removed strategy: {strategy_name}")
        else:
            print(f"Strategy not found: {strategy_name}")
            
    def update(self, data):
        """
        Process new market data and update all strategies.
        
        Args:
            data: Dictionary containing market data
        """
        current_price = data.get('price', 0.0)
        
        # Update all strategies with new data
        for name, strategy in self.strategies.items():
            strategy.update(data)
            
            # Check if strategy position state has changed
            position = strategy.get_position()
            position_info = self.positions[name]
            
            # Handle position changes
            if position.value == 'long' and not position_info['active']:
                self._open_long(name, strategy.position_size, current_price, 
                               strategy.stop_loss, strategy.take_profit)
                
            elif position.value == 'short' and not position_info['active']:
                self._open_short(name, strategy.position_size, current_price,
                                strategy.stop_loss, strategy.take_profit)
                
            elif position.value == 'neutral' and position_info['active']:
                self._close_position(name, current_price)
                
            # Update position info if active
            if position_info['active']:
                position_info['current_price'] = current_price
                
                # Calculate current P&L
                if position_info['type'] == 'long':
                    position_info['pnl'] = (current_price - position_info['entry_price']) * position_info['size']
                else:  # short
                    position_info['pnl'] = (position_info['entry_price'] - current_price) * position_info['size']
                
                # Check stop loss and take profit
                self._check_exit_conditions(name, current_price)
    
    def _open_long(self, strategy_name, size, price, stop_loss=None, take_profit=None):
        """
        Open a long position for a strategy.
        
        Args:
            strategy_name: Name of the strategy
            size: Position size
            price: Entry price
            stop_loss: Optional stop loss price
            take_profit: Optional take profit price
        """
        position = self.positions[strategy_name]
        position['active'] = True
        position['type'] = 'long'
        position['size'] = size
        position['entry_price'] = price
        position['current_price'] = price
        position['stop_loss'] = stop_loss
        position['take_profit'] = take_profit
        
        # Record the trade
        trade = {
            'strategy': strategy_name,
            'action': 'open_long',
            'size': size,
            'price': price,
            'timestamp': None,  # Would use actual timestamp in real implementation
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }
        self.trade_history.append(trade)
        
        print(f"OPENED LONG: Strategy={strategy_name}, Size={size}, Price={price}")
    
    def _open_short(self, strategy_name, size, price, stop_loss=None, take_profit=None):
        """
        Open a short position for a strategy.
        
        Args:
            strategy_name: Name of the strategy
            size: Position size
            price: Entry price
            stop_loss: Optional stop loss price
            take_profit: Optional take profit price
        """
        position = self.positions[strategy_name]
        position['active'] = True
        position['type'] = 'short'
        position['size'] = size
        position['entry_price'] = price
        position['current_price'] = price
        position['stop_loss'] = stop_loss
        position['take_profit'] = take_profit
        
        # Record the trade
        trade = {
            'strategy': strategy_name,
            'action': 'open_short',
            'size': size,
            'price': price,
            'timestamp': None,  # Would use actual timestamp in real implementation
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }
        self.trade_history.append(trade)
        
        print(f"OPENED SHORT: Strategy={strategy_name}, Size={size}, Price={price}")
    
    def _close_position(self, strategy_name, price=None):
        """
        Close a position for a strategy.
        
        Args:
            strategy_name: Name of the strategy
            price: Optional closing price (uses current price if not provided)
        """
        position = self.positions[strategy_name]
        
        if not position['active']:
            return
            
        if price is None:
            price = position['current_price']
            
        # Calculate P&L
        if position['type'] == 'long':
            pnl = (price - position['entry_price']) * position['size']
        else:  # short
            pnl = (position['entry_price'] - price) * position['size']
            
        # Apply commission
        commission = price * position['size'] * self.commission_rate
        net_pnl = pnl - commission
        
        # Update capital
        self.capital += net_pnl
        
        # Record the trade
        trade = {
            'strategy': strategy_name,
            'action': 'close',
            'size': position['size'],
            'price': price,
            'pnl': pnl,
            'commission': commission,
            'net_pnl': net_pnl,
            'timestamp': None  # Would use actual timestamp in real implementation
        }
        self.trade_history.append(trade)
        
        print(f"CLOSED: Strategy={strategy_name}, Price={price}, PnL={net_pnl:.2f}")
        
        # Reset position
        position['active'] = False
        position['type'] = None
        position['size'] = 0.0
        position['entry_price'] = 0.0
        position['current_price'] = 0.0
        position['pnl'] = 0.0
        position['stop_loss'] = None
        position['take_profit'] = None
    
    def _check_exit_conditions(self, strategy_name, current_price):
        """
        Check if stop loss or take profit conditions are met.
        
        Args:
            strategy_name: Name of the strategy
            current_price: Current market price
        """
        position = self.positions[strategy_name]
        
        if not position['active']:
            return
            
        # Check stop loss
        if position['stop_loss'] is not None:
            if (position['type'] == 'long' and current_price <= position['stop_loss']) or \
               (position['type'] == 'short' and current_price >= position['stop_loss']):
                print(f"STOP LOSS TRIGGERED: Strategy={strategy_name}, Price={current_price}")
                self._close_position(strategy_name, current_price)
                return
                
        # Check take profit
        if position['take_profit'] is not None:
            if (position['type'] == 'long' and current_price >= position['take_profit']) or \
               (position['type'] == 'short' and current_price <= position['take_profit']):
                print(f"TAKE PROFIT TRIGGERED: Strategy={strategy_name}, Price={current_price}")
                self._close_position(strategy_name, current_price)
                return
    
    def get_performance_summary(self):
        """
        Generate a performance summary for all strategies.
        
        Returns:
            Dictionary containing performance metrics
        """
        total_trades = len([t for t in self.trade_history if t['action'] == 'close'])
        winning_trades = len([t for t in self.trade_history if t['action'] == 'close' and t.get('net_pnl', 0) > 0])
        losing_trades = len([t for t in self.trade_history if t['action'] == 'close' and t.get('net_pnl', 0) <= 0])
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        total_profit = sum([t.get('net_pnl', 0) for t in self.trade_history if t['action'] == 'close' and t.get('net_pnl', 0) > 0])
        total_loss = sum([t.get('net_pnl', 0) for t in self.trade_history if t['action'] == 'close' and t.get('net_pnl', 0) <= 0])
        
        profit_factor = abs(total_profit / total_loss) if total_loss != 0 else float('inf')
        
        return {
            'initial_capital': self.initial_capital,
            'current_capital': self.capital,
            'total_return': (self.capital - self.initial_capital) / self.initial_capital * 100,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate * 100,
            'profit_factor': profit_factor,
            'total_commission': sum([t.get('commission', 0) for t in self.trade_history if t['action'] == 'close'])
        }
