"""
初始化认证系统
创建默认管理员用户和系统配置
"""
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.database.models import DatabaseManager
from backend.models.auth_models import UserAuthService, UserCreate


def init_default_admin():
    """初始化默认管理员用户"""
    db_manager = DatabaseManager()
    auth_service = UserAuthService(db_manager)
    
    # 检查是否已有管理员用户
    admin_user = auth_service.get_user_by_username("admin")
    if admin_user:
        print("管理员用户已存在，跳过创建")
        return admin_user
    
    # 创建默认管理员用户
    admin_data = UserCreate(
        username="admin",
        email="admin@ashareagent.com",
        password="admin123456",
        full_name="系统管理员"
    )
    
    try:
        admin_user = auth_service.create_user(admin_data)
        print(f"创建管理员用户成功: {admin_user.username}")
        
        # 将用户设置为超级管理员
        query = "UPDATE users SET is_superuser = 1 WHERE id = ?"
        with db_manager.get_connection() as conn:
            conn.execute(query, (admin_user.id,))
            conn.commit()
        
        # 分配管理员角色
        auth_service.assign_role_to_user(admin_user.id, "admin")
        print("分配管理员角色成功")
        
        return admin_user
    except Exception as e:
        print(f"创建管理员用户失败: {e}")
        return None


def init_test_users():
    """初始化测试用户"""
    db_manager = DatabaseManager()
    auth_service = UserAuthService(db_manager)
    
    test_users = [
        {
            "username": "premium_user",
            "email": "premium@test.com",
            "password": "test123456",
            "full_name": "高级用户测试",
            "role": "premium_user"
        },
        {
            "username": "regular_user",
            "email": "regular@test.com", 
            "password": "test123456",
            "full_name": "普通用户测试",
            "role": "regular_user"
        }
    ]
    
    for user_data in test_users:
        # 检查用户是否已存在
        existing_user = auth_service.get_user_by_username(user_data["username"])
        if existing_user:
            print(f"测试用户 {user_data['username']} 已存在，跳过创建")
            continue
        
        try:
            user_create = UserCreate(
                username=user_data["username"],
                email=user_data["email"],
                password=user_data["password"],
                full_name=user_data["full_name"]
            )
            
            user = auth_service.create_user(user_create)
            print(f"创建测试用户成功: {user.username}")
            
            # 移除默认角色，分配指定角色
            auth_service.remove_role_from_user(user.id, "regular_user")
            auth_service.assign_role_to_user(user.id, user_data["role"])
            print(f"分配角色 {user_data['role']} 成功")
            
        except Exception as e:
            print(f"创建测试用户 {user_data['username']} 失败: {e}")


def init_system_config():
    """初始化系统配置"""
    db_manager = DatabaseManager()
    
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
    
    for config in default_configs:
        # 检查配置是否已存在
        check_query = "SELECT 1 FROM system_config WHERE config_key = ?"
        existing = db_manager.execute_query(check_query, (config["config_key"],))
        if existing:
            print(f"配置 {config['config_key']} 已存在，跳过创建")
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
            print(f"创建系统配置成功: {config['config_key']}")
        except Exception as e:
            print(f"创建系统配置 {config['config_key']} 失败: {e}")


def main():
    """主函数"""
    print("开始初始化认证系统...")
    
    # 初始化数据库（确保所有表都已创建）
    print("初始化数据库...")
    db_manager = DatabaseManager()
    print("数据库初始化完成")
    
    # 创建默认管理员
    print("\n创建默认管理员用户...")
    admin_user = init_default_admin()
    
    # 创建测试用户
    print("\n创建测试用户...")
    init_test_users()
    
    # 初始化系统配置
    print("\n初始化系统配置...")
    init_system_config()
    
    print("\n认证系统初始化完成!")
    print("默认管理员账户: admin / admin123456")
    print("测试账户:")
    print("  高级用户: premium_user / test123456")
    print("  普通用户: regular_user / test123456")


if __name__ == "__main__":
    main()