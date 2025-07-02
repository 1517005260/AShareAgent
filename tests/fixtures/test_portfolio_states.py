"""
测试用的投资组合状态数据

提供不同场景下的投资组合状态，用于测试组合管理逻辑
"""

from datetime import datetime, timedelta

# 初始状态 - 全现金
INITIAL_STATE = {
    "messages": [],
    "data": {
        "stock_symbol": "000001",
        "portfolio": {
            "cash": 100000.0,
            "stock": 0,
            "total_value": 100000.0,
            "positions": []
        },
        "current_price": 12.50,
        "last_transaction": None
    },
    "metadata": {
        "show_reasoning": False,
        "current_agent_name": "portfolio_manager",
        "analysis_timestamp": datetime.now().isoformat(),
        "market_session": "regular"
    }
}

# 持有股票状态
HOLDING_STOCKS_STATE = {
    "messages": [],
    "data": {
        "stock_symbol": "000001", 
        "portfolio": {
            "cash": 25000.0,
            "stock": 6000,  # 6000股
            "total_value": 100000.0,  # 25000现金 + 75000股票价值
            "positions": [
                {
                    "symbol": "000001",
                    "shares": 6000,
                    "avg_cost": 12.50,
                    "current_price": 12.50,
                    "unrealized_pnl": 0.0,
                    "position_value": 75000.0
                }
            ]
        },
        "current_price": 12.50,
        "last_transaction": {
            "type": "buy",
            "shares": 6000,
            "price": 12.50,
            "timestamp": (datetime.now() - timedelta(days=5)).isoformat()
        }
    },
    "metadata": {
        "show_reasoning": False,
        "current_agent_name": "portfolio_manager",
        "analysis_timestamp": datetime.now().isoformat(),
        "market_session": "regular"
    }
}

# 盈利状态
PROFITABLE_STATE = {
    "messages": [],
    "data": {
        "stock_symbol": "000001",
        "portfolio": {
            "cash": 25000.0,
            "stock": 6000,
            "total_value": 107980.0,  # 25000现金 + 82980股票价值(涨到13.83)
            "positions": [
                {
                    "symbol": "000001",
                    "shares": 6000,
                    "avg_cost": 12.50,
                    "current_price": 13.83,
                    "unrealized_pnl": 7980.0,  # (13.83-12.50)*6000=7980
                    "position_value": 82980.0
                }
            ]
        },
        "current_price": 13.83,
        "last_transaction": {
            "type": "buy",
            "shares": 6000,
            "price": 12.50,
            "timestamp": (datetime.now() - timedelta(days=10)).isoformat()
        }
    },
    "metadata": {
        "show_reasoning": False,
        "current_agent_name": "portfolio_manager",
        "analysis_timestamp": datetime.now().isoformat(),
        "market_session": "regular"
    }
}

# 亏损状态
LOSING_STATE = {
    "messages": [],
    "data": {
        "stock_symbol": "000001",
        "portfolio": {
            "cash": 25000.0,
            "stock": 6000,
            "total_value": 92000.0,  # 25000现金 + 67000股票价值(跌到11.17)
            "positions": [
                {
                    "symbol": "000001",
                    "shares": 6000,
                    "avg_cost": 12.50,
                    "current_price": 11.17,
                    "unrealized_pnl": -8000.0,  # (11.17-12.50)*6000
                    "position_value": 67000.0
                }
            ]
        },
        "current_price": 11.17,
        "last_transaction": {
            "type": "buy",
            "shares": 6000,
            "price": 12.50,
            "timestamp": (datetime.now() - timedelta(days=7)).isoformat()
        }
    },
    "metadata": {
        "show_reasoning": False,
        "current_agent_name": "portfolio_manager",
        "analysis_timestamp": datetime.now().isoformat(),
        "market_session": "regular"
    }
}

# 高风险状态 - 重仓单一股票
HIGH_RISK_STATE = {
    "messages": [],
    "data": {
        "stock_symbol": "000001",
        "portfolio": {
            "cash": 5000.0,
            "stock": 7600,  # 95%资金投入股票
            "total_value": 100000.0,
            "positions": [
                {
                    "symbol": "000001",
                    "shares": 7600,
                    "avg_cost": 12.50,
                    "current_price": 12.50,
                    "unrealized_pnl": 0.0,
                    "position_value": 95000.0
                }
            ]
        },
        "current_price": 12.50,
        "last_transaction": {
            "type": "buy",
            "shares": 7600,
            "price": 12.50,
            "timestamp": (datetime.now() - timedelta(days=1)).isoformat()
        }
    },
    "metadata": {
        "show_reasoning": False,
        "current_agent_name": "portfolio_manager",
        "analysis_timestamp": datetime.now().isoformat(),
        "market_session": "regular"
    }
}

# 测试场景配置
TEST_SCENARIOS = {
    "initial": INITIAL_STATE,
    "holding": HOLDING_STOCKS_STATE,
    "profitable": PROFITABLE_STATE,
    "losing": LOSING_STATE,
    "high_risk": HIGH_RISK_STATE
}

# 决策测试用例
DECISION_TEST_CASES = [
    {
        "name": "强烈买入信号",
        "analyst_signals": {
            "technical": {"signal": "bullish", "confidence": 0.9},
            "fundamental": {"signal": "bullish", "confidence": 0.85},
            "sentiment": {"signal": "bullish", "confidence": 0.8},
            "valuation": {"signal": "bullish", "confidence": 0.75}
        },
        "expected_action": "buy",
        "portfolio_state": "initial"
    },
    {
        "name": "强烈卖出信号",
        "analyst_signals": {
            "technical": {"signal": "bearish", "confidence": 0.9},
            "fundamental": {"signal": "bearish", "confidence": 0.85},
            "sentiment": {"signal": "bearish", "confidence": 0.8},
            "valuation": {"signal": "bearish", "confidence": 0.8}
        },
        "expected_action": "sell",
        "portfolio_state": "holding"
    },
    {
        "name": "混合信号",
        "analyst_signals": {
            "technical": {"signal": "bullish", "confidence": 0.6},
            "fundamental": {"signal": "bearish", "confidence": 0.7},
            "sentiment": {"signal": "neutral", "confidence": 0.5},
            "valuation": {"signal": "bearish", "confidence": 0.8}
        },
        "expected_action": "hold",
        "portfolio_state": "holding"
    },
    {
        "name": "止损场景",
        "analyst_signals": {
            "technical": {"signal": "bearish", "confidence": 0.8},
            "fundamental": {"signal": "bearish", "confidence": 0.75},
            "sentiment": {"signal": "bearish", "confidence": 0.7},
            "valuation": {"signal": "neutral", "confidence": 0.5}
        },
        "expected_action": "sell", 
        "portfolio_state": "losing"
    },
    {
        "name": "止盈场景",
        "analyst_signals": {
            "technical": {"signal": "neutral", "confidence": 0.5},
            "fundamental": {"signal": "bullish", "confidence": 0.6},
            "sentiment": {"signal": "neutral", "confidence": 0.5},
            "valuation": {"signal": "bearish", "confidence": 0.8}  # 估值过高
        },
        "expected_action": "sell",
        "portfolio_state": "profitable"
    }
]