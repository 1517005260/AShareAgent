#!/usr/bin/env python3
"""
系统初始化脚本
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.models import DatabaseManager, AgentModel
from backend.models.auth_models import UserAuthService
from src.utils.dual_logger import init_dual_logging_system, get_dual_logger


def init_database():
    """初始化数据库，创建所有表结构"""
    print("🗄️  初始化数据库...")
    
    # 确保数据目录存在
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    
    # 确保日志目录存在
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # 创建数据库管理器实例
    db_path = str(data_dir / "ashare_agent.db")
    print(f"   数据库路径: {db_path}")
    
    try:
        # 初始化数据库
        db_manager = DatabaseManager(db_path)
        
        # 初始化双写日志系统
        system_logger = init_dual_logging_system(db_manager)
        system_logger.info("系统初始化开始")
        
        # 验证数据库表是否创建成功
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            # 验证system_logs表是否存在
            table_names = [table[0] for table in tables]
            if 'system_logs' in table_names:
                print("   ✅ system_logs表创建成功，双写日志系统可用")
                system_logger.info("system_logs表验证成功，双写日志系统已启用")
            else:
                print("   ⚠️  system_logs表未找到，只使用文件日志")
                
        print(f"   ✅ 成功创建 {len(tables)} 个数据表")
        system_logger.info(f"数据库初始化完成，共创建 {len(tables)} 个数据表")
        
        # 将数据库管理器存储为全局变量，供其他函数使用
        global global_db_manager
        global_db_manager = db_manager
        
        return True
        
    except Exception as e:
        print(f"   ❌ 数据库初始化失败: {e}")
        return False


def create_user_directly(db_manager, username, email, password, full_name, phone=None):
    """直接在数据库中创建用户，绕过密码长度验证"""
    auth_service = UserAuthService(db_manager)
    
    # 检查用户是否已存在
    if auth_service.get_user_by_username(username):
        return None
    
    if auth_service.get_user_by_email(email):
        return None
        
    # 直接创建用户记录
    password_hash = auth_service.get_password_hash(password)
    now = datetime.now()
    
    query = """
    INSERT INTO users (username, email, password_hash, full_name, phone, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    params = (username, email, password_hash, full_name, phone, now, now)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        user_id = cursor.lastrowid
        conn.commit()
        
        return user_id


def init_users():
    """初始化用户：创建管理员和示例用户"""
    print("👥 初始化用户...")
    
    db_manager = global_db_manager
    auth_service = UserAuthService(db_manager)
    user_logger = get_dual_logger('user_management')
    
    # 定义用户数据
    users_data = [
        {
            "username": "admin",
            "email": "admin@example.com",
            "password": "123456",
            "full_name": "系统管理员",
            "phone": "13800138000",
            "role": "admin",
            "is_superuser": True,
            "description": "系统管理员，拥有所有权限"
        },
        {
            "username": "premium_user", 
            "email": "premium@example.com",
            "password": "123456",
            "full_name": "高级用户",
            "phone": "13800138001",
            "role": "premium_user",
            "is_superuser": False,
            "description": "高级用户，拥有高级分析和回测权限"
        },
        {
            "username": "regular_user",
            "email": "regular@example.com", 
            "password": "123456",
            "full_name": "普通用户",
            "phone": "13800138002",
            "role": "regular_user",
            "is_superuser": False,
            "description": "普通用户，拥有基础功能权限"
        }
    ]
    
    created_users = []
    
    for user_data in users_data:
        try:
            # 检查用户是否已存在
            existing_user = auth_service.get_user_by_username(user_data["username"])
            if existing_user:
                print(f"   ⚠️  用户 {user_data['username']} 已存在，跳过创建")
                continue
            
            # 直接创建用户
            user_id = create_user_directly(
                db_manager,
                user_data["username"],
                user_data["email"],
                user_data["password"],
                user_data["full_name"],
                user_data["phone"]
            )
            
            if user_id:
                print(f"   ✅ 创建用户: {user_data['username']} ({user_data['full_name']})")
                user_logger.info(f"创建用户成功: {user_data['username']} ({user_data['full_name']})", 
                               user_id=user_id, resource_id=str(user_id))
                
                # 如果是超级用户，设置标记
                if user_data["is_superuser"]:
                    with db_manager.get_connection() as conn:
                        conn.execute("UPDATE users SET is_superuser = 1 WHERE id = ?", (user_id,))
                        conn.commit()
                    print(f"      👑 设置为超级管理员")
                
                # 分配角色
                success = auth_service.assign_role_to_user(user_id, user_data["role"])
                if success:
                    print(f"      🎭 分配角色: {user_data['role']}")
                
                created_users.append(user_data)
            else:
                print(f"   ❌ 创建用户 {user_data['username']} 失败")
                
        except Exception as e:
            print(f"   ❌ 创建用户 {user_data['username']} 失败: {e}")
    
    return created_users


def init_agents():
    """初始化Agent配置"""
    print("🤖 初始化Agent...")
    
    # 尝试使用全局数据库管理器，如果不存在则创建新的
    try:
        db_manager = global_db_manager
    except NameError:
        # 如果global_db_manager未定义，创建新的数据库管理器
        data_dir = project_root / "data"
        db_path = str(data_dir / "ashare_agent.db")
        db_manager = DatabaseManager(db_path)
        
        # 初始化双写日志系统（如果需要）
        try:
            from src.utils.dual_logger import logger_manager
            logger_manager.set_database_manager(db_manager)
        except:
            pass  # 忽略日志系统初始化失败
    
    agent_model = AgentModel(db_manager)
    agent_logger = get_dual_logger('agent_management')
    
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
    
    created_agents = 0
    
    # 检查并创建Agent
    for agent_config in default_agents:
        existing_agent = agent_model.get_agent_by_name(agent_config["name"])
        
        if existing_agent:
            print(f"   ⚠️  Agent '{agent_config['display_name']}' 已存在，跳过创建")
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
            print(f"   ✅ 创建Agent: {agent_config['display_name']}")
            agent_logger.info(f"创建Agent成功: {agent_config['display_name']} ({agent_config['name']})", 
                           resource_id=agent_config['name'])
            created_agents += 1
        else:
            print(f"   ❌ 创建Agent失败: {agent_config['display_name']}")
            agent_logger.error(f"创建Agent失败: {agent_config['display_name']} ({agent_config['name']})", 
                            resource_id=agent_config['name'])
    
    # 显示Agent统计
    agents = agent_model.get_all_agents()
    print(f"   📊 数据库中共有 {len(agents)} 个Agent (新增 {created_agents} 个)")
    
    return len(agents)


def init_system_config():
    """初始化系统配置"""
    print("⚙️  初始化系统配置...")
    
    db_manager = global_db_manager
    config_logger = get_dual_logger('system_config')
    
    default_configs = [
        {
            "config_key": "system.name",
            "config_value": "A股投资智能分析系统",
            "config_type": "string",
            "description": "系统名称",
            "category": "system"
        },
        {
            "config_key": "system.version",
            "config_value": "1.0.0",
            "config_type": "string",
            "description": "系统版本",
            "category": "system"
        },
        {
            "config_key": "auth.token_expire_minutes",
            "config_value": "30",
            "config_type": "number",
            "description": "JWT令牌过期时间（分钟）",
            "category": "auth"
        },
        {
            "config_key": "analysis.max_concurrent_tasks",
            "config_value": "5",
            "config_type": "number",
            "description": "最大并发分析任务数",
            "category": "analysis"
        },
        {
            "config_key": "analysis.default_news_count",
            "config_value": "10",
            "config_type": "number",
            "description": "默认新闻数量",
            "category": "analysis"
        },
        {
            "config_key": "portfolio.max_portfolios_per_user",
            "config_value": "10",
            "config_type": "number",
            "description": "每个用户最大投资组合数",
            "category": "portfolio"
        }
    ]
    
    created_configs = 0
    
    for config in default_configs:
        # 检查配置是否已存在
        check_query = "SELECT 1 FROM system_config WHERE config_key = ?"
        existing = db_manager.execute_query(check_query, (config["config_key"],))
        if existing:
            print(f"   ⚠️  配置 {config['config_key']} 已存在，跳过创建")
            continue
        
        try:
            insert_query = """
            INSERT INTO system_config (config_key, config_value, config_type, description, category)
            VALUES (?, ?, ?, ?, ?)
            """
            with db_manager.get_connection() as conn:
                conn.execute(insert_query, (
                    config["config_key"],
                    config["config_value"],
                    config["config_type"],
                    config["description"],
                    config["category"]
                ))
                conn.commit()
            print(f"   ✅ 创建配置: {config['config_key']}")
            created_configs += 1
        except Exception as e:
            print(f"   ❌ 创建配置 {config['config_key']} 失败: {e}")
    
    print(f"   📊 系统配置初始化完成 (新增 {created_configs} 个)")
    return created_configs


def verify_initialization():
    """验证初始化结果"""
    print("🔍 验证初始化结果...")
    
    db_manager = DatabaseManager()
    auth_service = UserAuthService(db_manager)
    agent_model = AgentModel(db_manager)
    
    # 验证用户
    test_users = ["admin", "premium_user", "regular_user"]
    valid_users = 0
    
    for username in test_users:
        user = auth_service.get_user_by_username(username)
        if user:
            roles = auth_service.get_user_roles(user.id)
            permissions = auth_service.get_user_permissions(user.id)
            valid_users += 1
            print(f"   👤 {username}: {len(roles)} 角色, {len(permissions)} 权限")
        else:
            print(f"   ❌ 用户 {username} 不存在")
    
    # 验证Agent
    agents = agent_model.get_all_agents()
    active_agents = len([a for a in agents if a['status'] == 'active'])
    print(f"   🤖 Agent: {len(agents)} 总数, {active_agents} 活跃")
    
    # 验证系统配置
    config_query = "SELECT COUNT(*) as count FROM system_config"
    config_result = db_manager.execute_query(config_query)
    config_count = config_result[0]['count'] if config_result else 0
    print(f"   ⚙️  系统配置: {config_count} 项")
    
    return valid_users, len(agents), config_count


def display_summary(created_users, agent_count, config_count):
    """显示初始化总结"""
    print("\n" + "=" * 60)
    print("🎉 系统初始化完成！")
    print("=" * 60)
    
    if created_users:
        print("\n📋 用户账户信息:")
        for user in created_users:
            print(f"   {user['description']}")
            print(f"   用户名: {user['username']} | 密码: {user['password']}")
            print(f"   邮箱: {user['email']} | 角色: {user['role']}")
            print()
    
    print("📊 初始化统计:")
    print(f"   用户数量: {len(created_users) if created_users else 0}")
    print(f"   Agent数量: {agent_count}")
    print(f"   系统配置: {config_count}")
    
    print("\n⚠️  重要提醒:")
    print("   1. 默认密码为 123456，生产环境请立即修改")
    print("   2. 系统已就绪，可以启动后端和前端服务")
    print("   3. 首次使用建议先熟悉系统功能")


def main():
    """主初始化函数"""
    print("=" * 60)
    print("🚀 AShare Agent 系统初始化")
    print("=" * 60)
    
    try:
        # 1. 初始化数据库
        if not init_database():
            print("❌ 数据库初始化失败，停止执行")
            return False
        
        # 2. 初始化用户
        created_users = init_users()
        
        # 3. 初始化Agent
        agent_count = init_agents()
        
        # 4. 初始化系统配置
        config_count = init_system_config()
        
        # 5. 验证初始化结果
        verify_initialization()
        
        # 6. 显示总结
        display_summary(created_users, agent_count, config_count)
        
        return True
        
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)