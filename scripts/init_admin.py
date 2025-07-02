#!/usr/bin/env python3
"""
初始化默认管理员用户脚本
仅在数据库中没有管理员用户时创建默认管理员
"""
import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from backend.models.auth_models import UserAuthService, UserCreate
from backend.dependencies import get_database_manager

def init_default_admin():
    """初始化默认管理员用户"""
    try:
        db_manager = get_database_manager()
        auth_service = UserAuthService(db_manager)
        
        # 检查是否已经有管理员用户
        admin_query = """
        SELECT COUNT(*) as count 
        FROM users u
        JOIN user_roles ur ON u.id = ur.user_id
        JOIN roles r ON ur.role_id = r.id
        WHERE r.name = 'admin' AND u.is_active = 1
        """
        result = db_manager.execute_query(admin_query)
        admin_count = result[0]['count'] if result else 0
        
        if admin_count > 0:
            print(f"✅ 数据库中已存在 {admin_count} 个管理员用户，跳过初始化")
            return True
        
        print("🔧 数据库中没有管理员用户，创建默认管理员...")
        
        # 创建默认管理员用户
        admin_user = UserCreate(
            username="admin",
            email="admin@system.local",
            password="Admin123!@#",  # 强密码
            full_name="系统管理员"
        )
        
        # 创建用户
        created_user = auth_service.create_user(admin_user)
        print(f"✅ 创建管理员用户: {created_user.username} (ID: {created_user.id})")
        
        # 移除默认的 regular_user 角色
        auth_service.remove_role_from_user(created_user.id, "regular_user")
        
        # 分配管理员角色
        success = auth_service.assign_role_to_user(created_user.id, "admin")
        if success:
            print("✅ 已分配管理员角色")
        else:
            print("❌ 分配管理员角色失败")
            return False
        
        print("\n🎉 默认管理员用户创建成功！")
        print("📋 登录信息:")
        print(f"   用户名: admin")
        print(f"   密码: Admin123!@#")
        print(f"   邮箱: admin@system.local")
        print("\n⚠️  请在生产环境中立即更改默认密码！")
        
        return True
        
    except Exception as e:
        print(f"❌ 初始化管理员用户失败: {e}")
        return False

if __name__ == "__main__":
    success = init_default_admin()
    if not success:
        sys.exit(1)