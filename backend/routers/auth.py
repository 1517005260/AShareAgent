"""
用户认证和权限管理API路由
"""
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials

from backend.models.api_models import ApiResponse
from backend.models.auth_models import (
    UserCreate, UserUpdate, UserPasswordUpdate, LoginRequest, 
    Token, UserResponse, UserInDB, Role, Permission
)
from backend.services.auth_service import (
    get_auth_service, get_current_user, get_current_active_user, 
    require_permission, require_admin, AuthService
)


router = APIRouter(prefix="/api/auth", tags=["认证管理"])


@router.post("/register", response_model=ApiResponse[UserResponse])
async def register_user(
    user_data: UserCreate,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户注册
    
    - **username**: 用户名，唯一
    - **email**: 邮箱地址，唯一
    - **password**: 密码，至少8位
    - **full_name**: 全名（可选）
    - **phone**: 电话号码（可选）
    """
    try:
        user = await auth_service.register_user(user_data)
        return ApiResponse(
            success=True,
            message="用户注册成功",
            data=user
        )
    except HTTPException as e:
        return ApiResponse(
            success=False,
            message=e.detail,
            data=None
        )


@router.post("/login", response_model=ApiResponse[Token])
async def login(
    login_data: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户登录
    
    - **username**: 用户名
    - **password**: 密码
    """
    try:
        # 获取客户端信息
        user_agent = request.headers.get("User-Agent", "")
        ip_address = request.client.host if request.client else "unknown"
        
        token = await auth_service.login(login_data, user_agent, ip_address)
        return ApiResponse(
            success=True,
            message="登录成功",
            data=token
        )
    except HTTPException as e:
        return ApiResponse(
            success=False,
            message=e.detail,
            data=None
        )


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_current_user_info(
    current_user: UserInDB = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """获取当前用户信息"""
    user_response = auth_service.user_auth.get_user_response(current_user)
    return ApiResponse(
        success=True,
        message="获取用户信息成功",
        data=user_response
    )


@router.put("/me", response_model=ApiResponse[UserResponse])
async def update_current_user(
    user_update: UserUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """更新当前用户信息"""
    try:
        updated_user = await auth_service.update_user_profile(current_user.id, user_update)
        return ApiResponse(
            success=True,
            message="用户信息更新成功",
            data=updated_user
        )
    except HTTPException as e:
        return ApiResponse(
            success=False,
            message=e.detail,
            data=None
        )


@router.post("/change-password", response_model=ApiResponse[bool])
async def change_password(
    password_update: UserPasswordUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """修改当前用户密码"""
    try:
        success = await auth_service.change_password(current_user.id, password_update)
        return ApiResponse(
            success=success,
            message="密码修改成功" if success else "密码修改失败",
            data=success
        )
    except HTTPException as e:
        return ApiResponse(
            success=False,
            message=e.detail,
            data=False
        )


@router.get("/users", response_model=ApiResponse[Dict[str, Any]])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    _: UserInDB = Depends(require_permission("user:read")),
    auth_service: AuthService = Depends(get_auth_service)
):
    """获取用户列表（需要user:read权限）"""
    try:
        result = await auth_service.list_users(skip, limit)
        return ApiResponse(
            success=True,
            message="获取用户列表成功",
            data=result
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"获取用户列表失败: {str(e)}",
            data=None
        )


@router.get("/users/{user_id}", response_model=ApiResponse[UserResponse])
async def get_user_by_id(
    user_id: int,
    _: UserInDB = Depends(require_permission("user:read")),
    auth_service: AuthService = Depends(get_auth_service)
):
    """根据ID获取用户信息（需要user:read权限）"""
    try:
        user = await auth_service.get_user_by_id(user_id)
        return ApiResponse(
            success=True,
            message="获取用户信息成功",
            data=user
        )
    except HTTPException as e:
        return ApiResponse(
            success=False,
            message=e.detail,
            data=None
        )


@router.post("/users/{user_id}/roles/{role_name}", response_model=ApiResponse[bool])
async def assign_user_role(
    user_id: int,
    role_name: str,
    current_user: UserInDB = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """为用户分配角色（管理员权限）"""
    try:
        success = await auth_service.assign_user_role(user_id, role_name, current_user.id)
        return ApiResponse(
            success=success,
            message=f"角色分配{'成功' if success else '失败'}",
            data=success
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"角色分配失败: {str(e)}",
            data=False
        )


@router.delete("/users/{user_id}/roles/{role_name}", response_model=ApiResponse[bool])
async def remove_user_role(
    user_id: int,
    role_name: str,
    current_user: UserInDB = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """移除用户角色（管理员权限）"""
    try:
        success = await auth_service.remove_user_role(user_id, role_name, current_user.id)
        return ApiResponse(
            success=success,
            message=f"角色移除{'成功' if success else '失败'}",
            data=success
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"角色移除失败: {str(e)}",
            data=False
        )


@router.get("/roles", response_model=ApiResponse[List[Role]])
async def list_roles(
    _: UserInDB = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """获取角色列表（管理员权限）"""
    try:
        roles = auth_service.user_auth.list_roles()
        return ApiResponse(
            success=True,
            message="获取角色列表成功",
            data=roles
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"获取角色列表失败: {str(e)}",
            data=[]
        )


@router.get("/permissions", response_model=ApiResponse[List[Permission]])
async def list_permissions(
    _: UserInDB = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """获取权限列表（管理员权限）"""
    try:
        permissions = auth_service.user_auth.list_permissions()
        return ApiResponse(
            success=True,
            message="获取权限列表成功",
            data=permissions
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"获取权限列表失败: {str(e)}",
            data=[]
        )


@router.get("/logs/me", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_my_logs(
    limit: int = 50,
    current_user: UserInDB = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """获取当前用户的操作日志"""
    try:
        logs = await auth_service.get_user_logs(current_user.id, limit)
        return ApiResponse(
            success=True,
            message="获取操作日志成功",
            data=logs
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"获取操作日志失败: {str(e)}",
            data=[]
        )


@router.get("/logs/{user_id}", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_user_logs(
    user_id: int,
    limit: int = 50,
    _: UserInDB = Depends(require_permission("system:logs")),
    auth_service: AuthService = Depends(get_auth_service)
):
    """获取指定用户的操作日志（需要system:logs权限）"""
    try:
        logs = await auth_service.get_user_logs(user_id, limit)
        return ApiResponse(
            success=True,
            message="获取操作日志成功",
            data=logs
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"获取操作日志失败: {str(e)}",
            data=[]
        )


@router.get("/stats", response_model=ApiResponse[Dict[str, Any]])
async def get_system_stats(
    _: UserInDB = Depends(require_permission("system:monitor")),
    auth_service: AuthService = Depends(get_auth_service)
):
    """获取系统统计信息（需要system:monitor权限）"""
    try:
        stats = await auth_service.get_system_stats()
        return ApiResponse(
            success=True,
            message="获取系统统计成功",
            data=stats
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"获取系统统计失败: {str(e)}",
            data={}
        )