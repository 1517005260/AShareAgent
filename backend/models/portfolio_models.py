"""
投资组合管理数据模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator
from decimal import Decimal


class PortfolioBase(BaseModel):
    """投资组合基础模型"""
    name: str
    description: Optional[str] = None
    initial_capital: float
    
    @validator('initial_capital')
    def validate_initial_capital(cls, v):
        if v <= 0:
            raise ValueError('初始资金必须大于0')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('组合名称长度不能少于2个字符')
        return v.strip()


class PortfolioCreate(PortfolioBase):
    """创建投资组合模型"""
    pass


class PortfolioUpdate(BaseModel):
    """更新投资组合模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError('组合名称长度不能少于2个字符')
        return v.strip() if v else v


class PortfolioResponse(PortfolioBase):
    """投资组合响应模型"""
    id: int
    user_id: int
    current_value: Optional[float] = None
    cash_balance: Optional[float] = None
    total_return: Optional[float] = None
    return_rate: Optional[float] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class HoldingBase(BaseModel):
    """持仓基础模型"""
    ticker: str
    quantity: int
    avg_cost: float
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('持仓数量必须大于0')
        return v
    
    @validator('avg_cost')
    def validate_avg_cost(cls, v):
        if v <= 0:
            raise ValueError('平均成本必须大于0')
        return v


class HoldingResponse(HoldingBase):
    """持仓响应模型"""
    id: int
    portfolio_id: int
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_rate: Optional[float] = None
    last_updated: datetime


class TransactionBase(BaseModel):
    """交易基础模型"""
    ticker: str
    transaction_type: str  # buy/sell
    quantity: int
    price: float
    commission: float = 0.0
    notes: Optional[str] = None
    
    @validator('transaction_type')
    def validate_transaction_type(cls, v):
        if v not in ['buy', 'sell']:
            raise ValueError('交易类型必须是buy或sell')
        return v
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('交易数量必须大于0')
        return v
    
    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('交易价格必须大于0')
        return v
    
    @validator('commission')
    def validate_commission(cls, v):
        if v < 0:
            raise ValueError('手续费不能为负数')
        return v


class TransactionCreate(TransactionBase):
    """创建交易记录模型"""
    pass


class TransactionResponse(TransactionBase):
    """交易响应模型"""
    id: int
    portfolio_id: int
    total_amount: float
    transaction_date: datetime


class PortfolioSummary(BaseModel):
    """投资组合摘要"""
    portfolio: PortfolioResponse
    holdings: List[HoldingResponse]
    total_positions: int
    total_market_value: float
    total_cost: float
    total_unrealized_pnl: float
    total_unrealized_pnl_rate: float
    cash_balance: float
    total_value: float


class PortfolioPerformance(BaseModel):
    """投资组合绩效"""
    portfolio_id: int
    total_return: float
    return_rate: float
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    volatility: Optional[float] = None
    win_rate: Optional[float] = None
    profit_loss_ratio: Optional[float] = None
    start_date: datetime
    end_date: datetime
    

class PortfolioService:
    """投资组合服务"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def create_portfolio(self, user_id: int, portfolio_data: PortfolioCreate) -> PortfolioResponse:
        """创建投资组合"""
        now = datetime.now()
        
        query = """
        INSERT INTO user_portfolios (user_id, name, description, initial_capital, 
                                   current_value, cash_balance, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (
                user_id,
                portfolio_data.name,
                portfolio_data.description,
                portfolio_data.initial_capital,
                portfolio_data.initial_capital,  # 初始当前价值等于初始资金
                portfolio_data.initial_capital,  # 初始现金余额等于初始资金
                now,
                now
            ))
            portfolio_id = cursor.lastrowid
            conn.commit()
        
        return self.get_portfolio_by_id(user_id, portfolio_id)
    
    def get_portfolio_by_id(self, user_id: int, portfolio_id: int) -> Optional[PortfolioResponse]:
        """根据ID获取投资组合"""
        query = """
        SELECT * FROM user_portfolios 
        WHERE id = ? AND user_id = ? AND is_active = 1
        """
        result = self.db.execute_query(query, (portfolio_id, user_id))
        
        if result:
            portfolio_data = dict(result[0])
            # 计算收益率
            if portfolio_data['current_value'] and portfolio_data['initial_capital']:
                portfolio_data['total_return'] = portfolio_data['current_value'] - portfolio_data['initial_capital']
                portfolio_data['return_rate'] = (portfolio_data['total_return'] / portfolio_data['initial_capital']) * 100
            
            return PortfolioResponse(**portfolio_data)
        return None
    
    def list_user_portfolios(self, user_id: int) -> List[PortfolioResponse]:
        """获取用户的投资组合列表"""
        query = """
        SELECT * FROM user_portfolios 
        WHERE user_id = ? AND is_active = 1 
        ORDER BY created_at DESC
        """
        result = self.db.execute_query(query, (user_id,))
        
        portfolios = []
        for row in result:
            portfolio_data = dict(row)
            # 计算收益率
            if portfolio_data['current_value'] and portfolio_data['initial_capital']:
                portfolio_data['total_return'] = portfolio_data['current_value'] - portfolio_data['initial_capital']
                portfolio_data['return_rate'] = (portfolio_data['total_return'] / portfolio_data['initial_capital']) * 100
            
            portfolios.append(PortfolioResponse(**portfolio_data))
        
        return portfolios
    
    def update_portfolio(self, user_id: int, portfolio_id: int, update_data: PortfolioUpdate) -> Optional[PortfolioResponse]:
        """更新投资组合"""
        current_portfolio = self.get_portfolio_by_id(user_id, portfolio_id)
        if not current_portfolio:
            return None
        
        update_fields = []
        params = []
        
        if update_data.name is not None:
            update_fields.append("name = ?")
            params.append(update_data.name)
        
        if update_data.description is not None:
            update_fields.append("description = ?")
            params.append(update_data.description)
        
        if update_data.is_active is not None:
            update_fields.append("is_active = ?")
            params.append(update_data.is_active)
        
        if not update_fields:
            return current_portfolio
        
        update_fields.append("updated_at = ?")
        params.append(datetime.now())
        params.append(portfolio_id)
        params.append(user_id)
        
        query = f"""
        UPDATE user_portfolios 
        SET {', '.join(update_fields)}
        WHERE id = ? AND user_id = ?
        """
        
        with self.db.get_connection() as conn:
            conn.execute(query, params)
            conn.commit()
        
        return self.get_portfolio_by_id(user_id, portfolio_id)
    
    def add_transaction(self, user_id: int, portfolio_id: int, transaction: TransactionCreate) -> TransactionResponse:
        """添加交易记录"""
        # 验证组合所有权
        portfolio = self.get_portfolio_by_id(user_id, portfolio_id)
        if not portfolio:
            raise ValueError("投资组合不存在或无权限访问")
        
        total_amount = transaction.quantity * transaction.price + transaction.commission
        now = datetime.now()
        
        # 开始事务
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 插入交易记录
            transaction_query = """
            INSERT INTO user_transactions (portfolio_id, ticker, transaction_type, 
                                         quantity, price, commission, total_amount, notes, transaction_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(transaction_query, (
                portfolio_id,
                transaction.ticker,
                transaction.transaction_type,
                transaction.quantity,
                transaction.price,
                transaction.commission,
                total_amount,
                transaction.notes,
                now
            ))
            transaction_id = cursor.lastrowid
            
            # 更新持仓
            self._update_holdings(cursor, portfolio_id, transaction)
            
            # 更新现金余额
            if transaction.transaction_type == 'buy':
                cash_change = -total_amount
            else:  # sell
                cash_change = total_amount - transaction.commission
            
            cursor.execute("""
                UPDATE user_portfolios 
                SET cash_balance = cash_balance + ?, updated_at = ?
                WHERE id = ?
            """, (cash_change, now, portfolio_id))
            
            conn.commit()
        
        # 获取创建的交易记录
        return self.get_transaction_by_id(transaction_id)
    
    def _update_holdings(self, cursor, portfolio_id: int, transaction: TransactionCreate):
        """更新持仓信息"""
        # 检查是否已有持仓
        cursor.execute("""
            SELECT * FROM user_holdings 
            WHERE portfolio_id = ? AND ticker = ?
        """, (portfolio_id, transaction.ticker))
        
        existing_holding = cursor.fetchone()
        
        if transaction.transaction_type == 'buy':
            if existing_holding:
                # 更新现有持仓
                old_quantity = existing_holding['quantity']
                old_avg_cost = existing_holding['avg_cost']
                new_quantity = old_quantity + transaction.quantity
                new_avg_cost = ((old_quantity * old_avg_cost) + 
                               (transaction.quantity * transaction.price)) / new_quantity
                
                cursor.execute("""
                    UPDATE user_holdings 
                    SET quantity = ?, avg_cost = ?, last_updated = ?
                    WHERE portfolio_id = ? AND ticker = ?
                """, (new_quantity, new_avg_cost, datetime.now(), portfolio_id, transaction.ticker))
            else:
                # 创建新持仓
                cursor.execute("""
                    INSERT INTO user_holdings (portfolio_id, ticker, quantity, avg_cost, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                """, (portfolio_id, transaction.ticker, transaction.quantity, transaction.price, datetime.now()))
        
        else:  # sell
            if existing_holding:
                new_quantity = existing_holding['quantity'] - transaction.quantity
                if new_quantity < 0:
                    raise ValueError(f"卖出数量超过持仓数量，当前持仓: {existing_holding['quantity']}")
                elif new_quantity == 0:
                    # 清空持仓
                    cursor.execute("""
                        DELETE FROM user_holdings 
                        WHERE portfolio_id = ? AND ticker = ?
                    """, (portfolio_id, transaction.ticker))
                else:
                    # 更新持仓数量
                    cursor.execute("""
                        UPDATE user_holdings 
                        SET quantity = ?, last_updated = ?
                        WHERE portfolio_id = ? AND ticker = ?
                    """, (new_quantity, datetime.now(), portfolio_id, transaction.ticker))
            else:
                raise ValueError(f"没有{transaction.ticker}的持仓，无法卖出")
    
    def get_transaction_by_id(self, transaction_id: int) -> Optional[TransactionResponse]:
        """根据ID获取交易记录"""
        query = "SELECT * FROM user_transactions WHERE id = ?"
        result = self.db.execute_query(query, (transaction_id,))
        
        if result:
            return TransactionResponse(**dict(result[0]))
        return None
    
    def get_portfolio_holdings(self, user_id: int, portfolio_id: int) -> List[HoldingResponse]:
        """获取投资组合持仓"""
        # 验证组合所有权
        portfolio = self.get_portfolio_by_id(user_id, portfolio_id)
        if not portfolio:
            return []
        
        query = """
        SELECT h.*, 
               COALESCE(h.current_price, h.avg_cost) as current_price,
               (h.quantity * COALESCE(h.current_price, h.avg_cost)) as market_value,
               ((COALESCE(h.current_price, h.avg_cost) - h.avg_cost) * h.quantity) as unrealized_pnl,
               (((COALESCE(h.current_price, h.avg_cost) - h.avg_cost) / h.avg_cost) * 100) as unrealized_pnl_rate
        FROM user_holdings h
        WHERE h.portfolio_id = ?
        ORDER BY h.last_updated DESC
        """
        result = self.db.execute_query(query, (portfolio_id,))
        
        holdings = []
        for row in result:
            holding_data = dict(row)
            holdings.append(HoldingResponse(**holding_data))
        
        return holdings
    
    def get_portfolio_transactions(self, user_id: int, portfolio_id: int, 
                                 limit: int = 50, offset: int = 0) -> List[TransactionResponse]:
        """获取投资组合交易记录"""
        # 验证组合所有权
        portfolio = self.get_portfolio_by_id(user_id, portfolio_id)
        if not portfolio:
            return []
        
        query = """
        SELECT * FROM user_transactions 
        WHERE portfolio_id = ?
        ORDER BY transaction_date DESC
        LIMIT ? OFFSET ?
        """
        result = self.db.execute_query(query, (portfolio_id, limit, offset))
        
        transactions = []
        for row in result:
            transactions.append(TransactionResponse(**dict(row)))
        
        return transactions
    
    def get_portfolio_summary(self, user_id: int, portfolio_id: int) -> Optional[PortfolioSummary]:
        """获取投资组合摘要"""
        portfolio = self.get_portfolio_by_id(user_id, portfolio_id)
        if not portfolio:
            return None
        
        holdings = self.get_portfolio_holdings(user_id, portfolio_id)
        
        total_market_value = sum(h.market_value or 0 for h in holdings)
        total_cost = sum(h.quantity * h.avg_cost for h in holdings)
        total_unrealized_pnl = sum(h.unrealized_pnl or 0 for h in holdings)
        total_unrealized_pnl_rate = (total_unrealized_pnl / total_cost * 100) if total_cost > 0 else 0
        
        return PortfolioSummary(
            portfolio=portfolio,
            holdings=holdings,
            total_positions=len(holdings),
            total_market_value=total_market_value,
            total_cost=total_cost,
            total_unrealized_pnl=total_unrealized_pnl,
            total_unrealized_pnl_rate=total_unrealized_pnl_rate,
            cash_balance=portfolio.cash_balance or 0,
            total_value=total_market_value + (portfolio.cash_balance or 0)
        )