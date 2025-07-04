"""
用户认证和权限管理业务逻辑服务
"""
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from backend.models.auth_models import (
    UserAuthService, UserCreate, UserUpdate, UserPasswordUpdate,
    LoginRequest, Token, UserResponse, UserInDB, TokenData
)
from src.database.models import DatabaseManager

logger = logging.getLogger(__name__)
security = HTTPBearer()


class AuthService:
    """认证服务主类"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.user_auth = UserAuthService(db_manager)
    
    async def register_user(self, user_data: UserCreate) -> UserResponse:
        """注册新用户"""
        try:
            user = self.user_auth.create_user(user_data)
            self.log_action(
                user_id=user.id,
                action="user_register",
                resource="user",
                resource_id=str(user.id),
                details={"username": user.username, "email": user.email}
            )
            return self.user_auth.get_user_response(user)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"用户注册失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="用户注册失败"
            )
    
    async def login(self, login_data: LoginRequest, user_agent: str = None, ip_address: str = None) -> Token:
        """用户登录"""
        user = self.user_auth.authenticate_user(login_data.username, login_data.password)
        if not user:
            # 记录登录失败
            self.log_action(
                action="login_failed",
                resource="auth",
                details={"username": login_data.username},
                ip_address=ip_address,
                user_agent=user_agent
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户账户已被禁用"
            )
        
        # 获取用户权限
        permissions = self.user_auth.get_user_permissions(user.id)
        
        # 创建访问令牌
        access_token_expires = timedelta(minutes=1440)  # 24小时过期
        access_token = self.user_auth.create_access_token(
            data={
                "sub": user.username,
                "user_id": user.id,
                "permissions": permissions
            },
            expires_delta=access_token_expires
        )
        
        # 更新登录信息
        self.user_auth.update_login_info(user.id)
        
        # 记录登录成功
        self.log_action(
            user_id=user.id,
            action="login_success",
            resource="auth",
            details={"username": user.username},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        expires_at = datetime.utcnow() + access_token_expires
        user_response = self.user_auth.get_user_response(user)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_at=expires_at,
            user=user_response
        )
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
        """获取当前用户"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        token_data = self.user_auth.verify_token(credentials.credentials)
        if token_data is None:
            raise credentials_exception
        
        user = self.user_auth.get_user_by_username(token_data.username)
        if user is None:
            raise credentials_exception
        
        return user
    
    async def get_current_active_user(self, current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
        """获取当前活跃用户"""
        if not current_user.is_active:
            raise HTTPException(status_code=400, detail="用户账户已被禁用")
        return current_user
    
    def require_permission(self, permission: str):
        """权限检查装饰器"""
        async def permission_checker(current_user: UserInDB = Depends(self.get_current_active_user)) -> UserInDB:
            if not self.user_auth.has_permission(current_user.id, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要权限: {permission}"
                )
            return current_user
        return permission_checker
    
    def require_role(self, role: str):
        """角色检查装饰器"""
        async def role_checker(current_user: UserInDB = Depends(self.get_current_active_user)) -> UserInDB:
            user_roles = self.user_auth.get_user_roles(current_user.id)
            if role not in user_roles and not current_user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要角色: {role}"
                )
            return current_user
        return role_checker
    
    async def update_user_profile(self, user_id: int, user_update: UserUpdate) -> UserResponse:
        """更新用户资料"""
        try:
            updated_user = self.user_auth.update_user(user_id, user_update)
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            
            self.log_action(
                user_id=user_id,
                action="user_update",
                resource="user",
                resource_id=str(user_id),
                details=user_update.dict(exclude_unset=True)
            )
            
            return self.user_auth.get_user_response(updated_user)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    async def change_password(self, user_id: int, password_update: UserPasswordUpdate) -> bool:
        """修改密码"""
        try:
            success = self.user_auth.update_password(user_id, password_update)
            if success:
                self.log_action(
                    user_id=user_id,
                    action="password_change",
                    resource="user",
                    resource_id=str(user_id)
                )
            return success
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    async def get_user_by_id(self, user_id: int) -> UserResponse:
        """根据ID获取用户"""
        user = self.user_auth.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return self.user_auth.get_user_response(user)
    
    async def list_users(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """获取用户列表"""
        users = self.user_auth.list_users(skip, limit)
        total = self.user_auth.get_total_users_count()
        
        return {
            "users": users,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    async def assign_user_role(self, user_id: int, role_name: str, assigned_by: int) -> bool:
        """为用户分配角色"""
        success = self.user_auth.assign_role_to_user(user_id, role_name)
        if success:
            self.log_action(
                user_id=assigned_by,
                action="role_assign",
                resource="user",
                resource_id=str(user_id),
                details={"role": role_name}
            )
        return success
    
    async def remove_user_role(self, user_id: int, role_name: str, removed_by: int) -> bool:
        """移除用户角色"""
        success = self.user_auth.remove_role_from_user(user_id, role_name)
        if success:
            self.log_action(
                user_id=removed_by,
                action="role_remove",
                resource="user",
                resource_id=str(user_id),
                details={"role": role_name}
            )
        return success
    
    def log_action(self, action: str, resource: str = None, resource_id: str = None, 
                   user_id: int = None, details: Dict[str, Any] = None, 
                   ip_address: str = None, user_agent: str = None):
        """记录操作日志"""
        try:
            query = """
            INSERT INTO system_logs (user_id, action, resource, resource_id, details, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            details_json = json.dumps(details) if details else None
            
            with self.db.get_connection() as conn:
                conn.execute(query, (
                    user_id, action, resource, resource_id, 
                    details_json, ip_address, user_agent
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"记录操作日志失败: {e}")
    
    async def get_user_logs(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """获取用户操作日志"""
        query = """
        SELECT * FROM system_logs 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
        """
        result = self.db.execute_query(query, (user_id, limit))
        logs = []
        for row in result:
            log_data = dict(row)
            if log_data.get('details'):
                log_data['details'] = json.loads(log_data['details'])
            logs.append(log_data)
        return logs
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        stats = {}
        
        # 用户统计
        user_stats_query = """
        SELECT 
            COUNT(*) as total_users,
            COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_users,
            COUNT(CASE WHEN last_login >= datetime('now', '-30 days') THEN 1 END) as monthly_active_users,
            COUNT(CASE WHEN created_at >= datetime('now', '-7 days') THEN 1 END) as new_users_this_week
        FROM users
        """
        user_result = self.db.execute_query(user_stats_query)
        if user_result:
            stats['users'] = dict(user_result[0])
        
        # 分析任务统计
        task_stats_query = """
        SELECT 
            COUNT(*) as total_tasks,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
            COUNT(CASE WHEN status = 'running' THEN 1 END) as running_tasks,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tasks,
            COUNT(CASE WHEN created_at >= datetime('now', '-24 hours') THEN 1 END) as tasks_today
        FROM user_analysis_tasks
        """
        task_result = self.db.execute_query(task_stats_query)
        if task_result:
            stats['analysis_tasks'] = dict(task_result[0])
        
        # API调用统计
        api_stats_query = """
        SELECT 
            COUNT(*) as total_calls,
            COUNT(CASE WHEN created_at >= datetime('now', '-24 hours') THEN 1 END) as calls_today,
            AVG(response_time) as avg_response_time,
            COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_calls
        FROM api_usage_stats
        WHERE created_at >= datetime('now', '-7 days')
        """
        api_result = self.db.execute_query(api_stats_query)
        if api_result:
            stats['api_usage'] = dict(api_result[0])
        
        return stats


# 全局认证服务实例
auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """获取认证服务实例"""
    global auth_service
    if auth_service is None:
        from backend.dependencies import get_database_manager
        db_manager = get_database_manager()
        auth_service = AuthService(db_manager)
    return auth_service


# 依赖注入函数
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
    """获取当前用户依赖"""
    auth_svc = get_auth_service()
    return await auth_svc.get_current_user(credentials)


async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """获取当前活跃用户依赖"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户账户已被禁用")
    return current_user


def require_permission(permission: str):
    """权限检查依赖"""
    async def permission_checker(current_user: UserInDB = Depends(get_current_active_user)) -> UserInDB:
        auth_svc = get_auth_service()
        if not auth_svc.user_auth.has_permission(current_user.id, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要权限: {permission}"
            )
        return current_user
    return permission_checker


def require_admin(current_user: UserInDB = Depends(get_current_active_user)) -> UserInDB:
    """管理员权限检查"""
    auth_svc = get_auth_service()
    user_roles = auth_svc.user_auth.get_user_roles(current_user.id)
    if 'admin' not in user_roles and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


def decode_access_token(token: str) -> Optional[dict]:
    """解码访问令牌 - 用于中间件"""
    from backend.models.auth_models import SECRET_KEY, ALGORITHM
    from jose import jwt, JWTError
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None