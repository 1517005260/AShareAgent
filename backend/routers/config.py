"""
系统配置管理API路由
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from backend.models.api_models import ApiResponse
from backend.models.auth_models import UserInDB
from backend.models.config_models import (
    ConfigCreate, ConfigUpdate, ConfigResponse, ConfigService, ConfigValue
)
from backend.services.auth_service import get_current_active_user, require_permission, require_admin
from backend.dependencies import get_database_manager
from src.database.models import DatabaseManager
import logging

logger = logging.getLogger("config_router")

# 创建路由器
router = APIRouter(prefix="/api/config", tags=["系统配置管理"])


def get_config_service(db_manager: DatabaseManager = Depends(get_database_manager)) -> ConfigService:
    """获取配置服务实例"""
    return ConfigService(db_manager)


@router.post("/", response_model=ApiResponse[ConfigResponse])
async def create_config(
    config_data: ConfigCreate,
    current_user: UserInDB = Depends(require_permission("system:config")),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    创建系统配置
    
    - **config_key**: 配置键（必填，唯一）
    - **config_value**: 配置值（必填）
    - **config_type**: 配置类型，string/number/boolean/json（默认string）
    - **description**: 配置描述（可选）
    - **category**: 配置分类（默认general）
    - **is_sensitive**: 是否敏感信息（默认false）
    """
    try:
        # 验证配置值类型
        if not config_service.validate_config_value(config_data.config_type, config_data.config_value):
            return ApiResponse(
                success=False,
                message=f"配置值格式不符合类型 {config_data.config_type}",
                data=None
            )
        
        config = config_service.create_config(config_data)
        
        return ApiResponse(
            success=True,
            message="系统配置创建成功",
            data=config
        )
        
    except ValueError as e:
        return ApiResponse(
            success=False,
            message=str(e),
            data=None
        )
    except Exception as e:
        logger.error(f"创建系统配置失败: {e}")
        return ApiResponse(
            success=False,
            message=f"创建系统配置失败: {str(e)}",
            data=None
        )


@router.get("/", response_model=ApiResponse[List[ConfigResponse]])
async def list_configs(
    category: Optional[str] = Query(None, description="配置分类过滤"),
    include_sensitive: bool = Query(False, description="是否包含敏感配置"),
    current_user: UserInDB = Depends(get_current_active_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """获取系统配置列表"""
    try:
        # 非管理员用户不能查看敏感配置
        if include_sensitive:
            # 检查用户是否有系统配置权限
            from backend.services.auth_service import get_auth_service
            auth_service = get_auth_service()
            if not auth_service.user_auth.has_permission(current_user.id, "system:config"):
                include_sensitive = False
        
        configs = config_service.list_configs(category, include_sensitive)
        
        return ApiResponse(
            success=True,
            message="获取配置列表成功",
            data=configs
        )
        
    except Exception as e:
        logger.error(f"获取配置列表失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取配置列表失败: {str(e)}",
            data=[]
        )


@router.get("/categories", response_model=ApiResponse[List[str]])
async def get_config_categories(
    current_user: UserInDB = Depends(get_current_active_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """获取配置分类列表"""
    try:
        categories = config_service.get_categories()
        
        return ApiResponse(
            success=True,
            message="获取配置分类成功",
            data=categories
        )
        
    except Exception as e:
        logger.error(f"获取配置分类失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取配置分类失败: {str(e)}",
            data=[]
        )


@router.get("/category/{category_name}", response_model=ApiResponse[Dict[str, ConfigValue]])
async def get_configs_by_category(
    category_name: str,
    include_sensitive: bool = Query(False, description="是否包含敏感配置"),
    current_user: UserInDB = Depends(get_current_active_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """根据分类获取配置（类型化值）"""
    try:
        # 非管理员用户不能查看敏感配置
        if include_sensitive:
            from backend.services.auth_service import get_auth_service
            auth_service = get_auth_service()
            if not auth_service.user_auth.has_permission(current_user.id, "system:config"):
                include_sensitive = False
        
        configs = config_service.get_config_by_category(category_name, include_sensitive)
        
        return ApiResponse(
            success=True,
            message=f"获取分类 {category_name} 配置成功",
            data=configs
        )
        
    except Exception as e:
        logger.error(f"获取分类配置失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取分类配置失败: {str(e)}",
            data={}
        )


@router.get("/{config_key}", response_model=ApiResponse[ConfigResponse])
async def get_config(
    config_key: str,
    current_user: UserInDB = Depends(get_current_active_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """根据键获取配置"""
    try:
        config = config_service.get_config_by_key(config_key)
        
        if not config:
            return ApiResponse(
                success=False,
                message=f"配置 '{config_key}' 不存在",
                data=None
            )
        
        # 检查敏感配置权限
        if config.is_sensitive:
            from backend.services.auth_service import get_auth_service
            auth_service = get_auth_service()
            if not auth_service.user_auth.has_permission(current_user.id, "system:config"):
                return ApiResponse(
                    success=False,
                    message="无权限访问敏感配置",
                    data=None
                )
        
        return ApiResponse(
            success=True,
            message="获取配置成功",
            data=config
        )
        
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取配置失败: {str(e)}",
            data=None
        )


@router.put("/{config_key}", response_model=ApiResponse[ConfigResponse])
async def update_config(
    config_key: str,
    update_data: ConfigUpdate,
    current_user: UserInDB = Depends(require_permission("system:config")),
    config_service: ConfigService = Depends(get_config_service)
):
    """更新系统配置"""
    try:
        # 如果更新配置值，验证类型
        if update_data.config_value is not None:
            current_config = config_service.get_config_by_key(config_key)
            if current_config and not config_service.validate_config_value(
                current_config.config_type, update_data.config_value
            ):
                return ApiResponse(
                    success=False,
                    message=f"配置值格式不符合类型 {current_config.config_type}",
                    data=None
                )
        
        updated_config = config_service.update_config(config_key, update_data)
        
        if not updated_config:
            return ApiResponse(
                success=False,
                message=f"配置 '{config_key}' 不存在",
                data=None
            )
        
        return ApiResponse(
            success=True,
            message="配置更新成功",
            data=updated_config
        )
        
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        return ApiResponse(
            success=False,
            message=f"更新配置失败: {str(e)}",
            data=None
        )


@router.delete("/{config_key}", response_model=ApiResponse[bool])
async def delete_config(
    config_key: str,
    current_user: UserInDB = Depends(require_permission("system:config")),
    config_service: ConfigService = Depends(get_config_service)
):
    """删除系统配置"""
    try:
        success = config_service.delete_config(config_key)
        
        return ApiResponse(
            success=success,
            message="配置删除成功" if success else "配置不存在",
            data=success
        )
        
    except Exception as e:
        logger.error(f"删除配置失败: {e}")
        return ApiResponse(
            success=False,
            message=f"删除配置失败: {str(e)}",
            data=False
        )


@router.get("/value/{config_key}", response_model=ApiResponse[Any])
async def get_config_value(
    config_key: str,
    current_user: UserInDB = Depends(get_current_active_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """获取配置的类型化值"""
    try:
        config = config_service.get_config_by_key(config_key)
        
        if not config:
            return ApiResponse(
                success=False,
                message=f"配置 '{config_key}' 不存在",
                data=None
            )
        
        # 检查敏感配置权限
        if config.is_sensitive:
            from backend.services.auth_service import get_auth_service
            auth_service = get_auth_service()
            if not auth_service.user_auth.has_permission(current_user.id, "system:config"):
                return ApiResponse(
                    success=False,
                    message="无权限访问敏感配置",
                    data=None
                )
        
        typed_value = config_service.get_typed_config_value(config_key)
        
        return ApiResponse(
            success=True,
            message="获取配置值成功",
            data=typed_value
        )
        
    except Exception as e:
        logger.error(f"获取配置值失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取配置值失败: {str(e)}",
            data=None
        )


@router.post("/import", response_model=ApiResponse[Dict[str, Any]])
async def import_configs(
    import_data: Dict[str, Any],
    overwrite: bool = Query(False, description="是否覆盖现有配置"),
    current_user: UserInDB = Depends(require_admin),
    config_service: ConfigService = Depends(get_config_service)
):
    """导入配置（管理员权限）"""
    try:
        results = config_service.import_configs(import_data, overwrite)
        
        return ApiResponse(
            success=True,
            message="配置导入完成",
            data=results
        )
        
    except Exception as e:
        logger.error(f"导入配置失败: {e}")
        return ApiResponse(
            success=False,
            message=f"导入配置失败: {str(e)}",
            data={}
        )


@router.get("/export/{category}", response_model=ApiResponse[Dict[str, Any]])
async def export_configs(
    category: str,
    current_user: UserInDB = Depends(require_admin),
    config_service: ConfigService = Depends(get_config_service)
):
    """导出配置（管理员权限）"""
    try:
        export_data = config_service.export_configs(category if category != "all" else None)
        
        return ApiResponse(
            success=True,
            message="配置导出成功",
            data=export_data
        )
        
    except Exception as e:
        logger.error(f"导出配置失败: {e}")
        return ApiResponse(
            success=False,
            message=f"导出配置失败: {str(e)}",
            data={}
        )


@router.get("/system/info", response_model=ApiResponse[Dict[str, Any]])
async def get_system_info(
    current_user: UserInDB = Depends(get_current_active_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """获取系统信息和配置概览"""
    try:
        system_info = config_service.get_system_info()
        
        return ApiResponse(
            success=True,
            message="获取系统信息成功",
            data=system_info
        )
        
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取系统信息失败: {str(e)}",
            data={}
        )