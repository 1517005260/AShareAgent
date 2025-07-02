#!/usr/bin/env python3
"""
初始化Agent数据脚本
为数据库添加初始的Agent配置数据
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database.models import DatabaseManager, AgentModel


def init_default_agents():
    """初始化默认的Agent数据"""
    
    # 创建数据库管理器
    db_manager = DatabaseManager()
    agent_model = AgentModel(db_manager)
    
    # 默认Agent配置
    default_agents = [
        {
            "name": "technical_analyst",
            "display_name": "技术分析师",
            "description": "负责股票技术指标分析，包括趋势、均线、成交量等技术面分析",
            "agent_type": "analysis",
            "status": "active",
            "config": {
                "indicators": ["MA", "MACD", "RSI", "BB", "ADX"],
                "timeframes": ["daily", "weekly"],
                "signal_threshold": 0.6
            }
        },
        {
            "name": "fundamentals_analyst",
            "display_name": "基本面分析师",
            "description": "负责公司财务数据分析，包括盈利能力、财务健康状况等基本面分析",
            "agent_type": "analysis",
            "status": "active",
            "config": {
                "metrics": ["ROE", "PE", "PB", "EPS", "Revenue"],
                "analysis_depth": "detailed",
                "industry_comparison": True
            }
        },
        {
            "name": "sentiment_analyst",
            "display_name": "情感分析师",
            "description": "负责市场情绪和新闻舆情分析，提供投资者情绪指标",
            "agent_type": "sentiment",
            "status": "active",
            "config": {
                "news_sources": ["financial_news", "social_media"],
                "sentiment_model": "llm_based",
                "confidence_threshold": 0.7
            }
        },
        {
            "name": "valuation_analyst",
            "display_name": "估值分析师",
            "description": "负责股票内在价值评估，包括DCF模型、相对估值等",
            "agent_type": "analysis",
            "status": "active",
            "config": {
                "models": ["DCF", "owner_earnings", "relative_valuation"],
                "discount_rate": 0.1,
                "growth_assumptions": "conservative"
            }
        },
        {
            "name": "risk_manager",
            "display_name": "风险管理师",
            "description": "负责投资风险评估和控制，包括VaR、波动率等风险指标分析",
            "agent_type": "risk",
            "status": "active",
            "config": {
                "risk_metrics": ["VaR", "volatility", "max_drawdown", "beta"],
                "confidence_level": 0.95,
                "stress_test": True
            }
        },
        {
            "name": "macro_analyst",
            "display_name": "宏观分析师",
            "description": "负责宏观经济环境分析，评估政策、经济数据对股票的影响",
            "agent_type": "macro",
            "status": "active",
            "config": {
                "macro_factors": ["monetary_policy", "fiscal_policy", "economic_indicators"],
                "geographic_scope": "China",
                "update_frequency": "daily"
            }
        },
        {
            "name": "portfolio_manager",
            "display_name": "投资组合管理师",
            "description": "负责整合各分析师意见，制定最终投资决策和仓位管理",
            "agent_type": "trading",
            "status": "active",
            "config": {
                "decision_weights": {
                    "technical": 0.2,
                    "fundamental": 0.3,
                    "sentiment": 0.15,
                    "valuation": 0.25,
                    "risk": 0.1
                },
                "position_sizing": "kelly_criterion",
                "max_position": 0.1
            }
        },
        {
            "name": "researcher_bull",
            "display_name": "多方研究员",
            "description": "专注于寻找和分析股票的积极因素，提供看涨观点",
            "agent_type": "analysis",
            "status": "active",
            "config": {
                "research_focus": "growth_opportunities",
                "bias": "optimistic",
                "confidence_adjustment": 1.0
            }
        },
        {
            "name": "researcher_bear",
            "display_name": "空方研究员",
            "description": "专注于识别和分析股票的风险因素，提供看跌观点",
            "agent_type": "analysis",
            "status": "active",
            "config": {
                "research_focus": "risk_factors",
                "bias": "pessimistic",
                "confidence_adjustment": 1.0
            }
        },
        {
            "name": "debate_moderator",
            "display_name": "辩论主持人",
            "description": "主持多空双方辩论，综合评估不同观点，形成平衡的投资建议",
            "agent_type": "analysis",
            "status": "active",
            "config": {
                "debate_rounds": 3,
                "objectivity_weight": 0.8,
                "llm_arbitration": True
            }
        }
    ]
    
    print("开始初始化Agent数据...")
    
    # 检查并创建Agent
    for agent_config in default_agents:
        existing_agent = agent_model.get_agent_by_name(agent_config["name"])
        
        if existing_agent:
            print(f"Agent '{agent_config['name']}' 已存在，跳过创建")
            continue
        
        # 创建新Agent
        success = agent_model.create_agent(
            name=agent_config["name"],
            display_name=agent_config["display_name"],
            description=agent_config["description"],
            agent_type=agent_config["agent_type"],
            status=agent_config["status"],
            config=agent_config["config"]
        )
        
        if success:
            print(f"✅ 成功创建Agent: {agent_config['display_name']} ({agent_config['name']})")
        else:
            print(f"❌ 创建Agent失败: {agent_config['display_name']} ({agent_config['name']})")
    
    print("\nAgent初始化完成!")
    
    # 显示创建的Agent列表
    agents = agent_model.get_all_agents()
    print(f"\n当前数据库中共有 {len(agents)} 个Agent:")
    for agent in agents:
        print(f"- {agent['display_name']} ({agent['name']}) - {agent['status']}")


if __name__ == "__main__":
    try:
        init_default_agents()
    except Exception as e:
        print(f"初始化失败: {str(e)}")
        sys.exit(1)