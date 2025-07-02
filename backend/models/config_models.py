"""
系统配置管理数据模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, validator
import json


class ConfigBase(BaseModel):
    """配置基础模型"""
    config_key: str
    config_value: str
    config_type: str = "string"  # string, number, boolean, json
    description: Optional[str] = None
    category: str = "general"
    is_sensitive: bool = False
    
    @validator('config_type')
    def validate_config_type(cls, v):
        allowed_types = ['string', 'number', 'boolean', 'json']
        if v not in allowed_types:
            raise ValueError(f'配置类型必须是: {", ".join(allowed_types)}')
        return v
    
    @validator('config_key')
    def validate_config_key(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('配置键长度不能少于2个字符')
        return v.strip()


class ConfigCreate(ConfigBase):
    """创建配置模型"""
    pass


class ConfigUpdate(BaseModel):
    """更新配置模型"""
    config_value: Optional[str] = None
    description: Optional[str] = None
    is_sensitive: Optional[bool] = None


class ConfigResponse(ConfigBase):
    """配置响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime


class ConfigValue(BaseModel):
    """配置值模型（类型化）"""
    key: str
    value: Union[str, int, float, bool, Dict, List]
    type: str
    description: Optional[str] = None


class ConfigService:
    """系统配置服务"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def create_config(self, config_data: ConfigCreate) -> ConfigResponse:
        """创建系统配置"""
        # 检查配置键是否已存在
        existing = self.get_config_by_key(config_data.config_key)
        if existing:
            raise ValueError(f"配置键 '{config_data.config_key}' 已存在")
        
        now = datetime.now()
        query = """
        INSERT INTO system_config (config_key, config_value, config_type, description, 
                                  is_sensitive, category, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (
                config_data.config_key,
                config_data.config_value,
                config_data.config_type,
                config_data.description,
                config_data.is_sensitive,
                config_data.category,
                now,
                now
            ))
            config_id = cursor.lastrowid
            conn.commit()
        
        return self.get_config_by_id(config_id)
    
    def get_config_by_id(self, config_id: int) -> Optional[ConfigResponse]:
        """根据ID获取配置"""
        query = "SELECT * FROM system_config WHERE id = ?"
        result = self.db.execute_query(query, (config_id,))
        
        if result:
            return ConfigResponse(**dict(result[0]))
        return None
    
    def get_config_by_key(self, config_key: str) -> Optional[ConfigResponse]:
        """根据键获取配置"""
        query = "SELECT * FROM system_config WHERE config_key = ?"
        result = self.db.execute_query(query, (config_key,))
        
        if result:
            return ConfigResponse(**dict(result[0]))
        return None
    
    def list_configs(self, category: str = None, include_sensitive: bool = False) -> List[ConfigResponse]:
        """获取配置列表"""
        where_conditions = []
        params = []
        
        if category:
            where_conditions.append("category = ?")
            params.append(category)
        
        if not include_sensitive:
            where_conditions.append("is_sensitive = 0")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        query = f"""
        SELECT * FROM system_config 
        WHERE {where_clause}
        ORDER BY category, config_key
        """
        
        result = self.db.execute_query(query, params)
        return [ConfigResponse(**dict(row)) for row in result]
    
    def update_config(self, config_key: str, update_data: ConfigUpdate) -> Optional[ConfigResponse]:
        """更新配置"""
        current_config = self.get_config_by_key(config_key)
        if not current_config:
            return None
        
        update_fields = []
        params = []
        
        if update_data.config_value is not None:
            update_fields.append("config_value = ?")
            params.append(update_data.config_value)
        
        if update_data.description is not None:
            update_fields.append("description = ?")
            params.append(update_data.description)
        
        if update_data.is_sensitive is not None:
            update_fields.append("is_sensitive = ?")
            params.append(update_data.is_sensitive)
        
        if not update_fields:
            return current_config
        
        update_fields.append("updated_at = ?")
        params.append(datetime.now())
        params.append(config_key)
        
        query = f"""
        UPDATE system_config 
        SET {', '.join(update_fields)}
        WHERE config_key = ?
        """
        
        with self.db.get_connection() as conn:
            conn.execute(query, params)
            conn.commit()
        
        return self.get_config_by_key(config_key)
    
    def delete_config(self, config_key: str) -> bool:
        """删除配置"""
        query = "DELETE FROM system_config WHERE config_key = ?"
        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (config_key,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_typed_config_value(self, config_key: str, default_value: Any = None) -> Any:
        """获取类型化的配置值"""
        config = self.get_config_by_key(config_key)
        if not config:
            return default_value
        
        try:
            if config.config_type == "string":
                return config.config_value
            elif config.config_type == "number":
                # 尝试转换为int，如果失败则转换为float
                try:
                    return int(config.config_value)
                except ValueError:
                    return float(config.config_value)
            elif config.config_type == "boolean":
                return config.config_value.lower() in ('true', '1', 'yes', 'on')
            elif config.config_type == "json":
                return json.loads(config.config_value)
            else:
                return config.config_value
        except (ValueError, json.JSONDecodeError):
            return default_value
    
    def set_config_value(self, config_key: str, value: Any) -> bool:
        """设置配置值（自动类型转换）"""
        config = self.get_config_by_key(config_key)
        if not config:
            return False
        
        try:
            if config.config_type == "json":
                config_value = json.dumps(value, ensure_ascii=False)
            else:
                config_value = str(value)
            
            update_data = ConfigUpdate(config_value=config_value)
            updated_config = self.update_config(config_key, update_data)
            return updated_config is not None
        except Exception:
            return False
    
    def get_config_by_category(self, category: str, include_sensitive: bool = False) -> Dict[str, ConfigValue]:
        """根据分类获取配置"""
        configs = self.list_configs(category, include_sensitive)
        result = {}
        
        for config in configs:
            typed_value = self.get_typed_config_value(config.config_key)
            result[config.config_key] = ConfigValue(
                key=config.config_key,
                value=typed_value,
                type=config.config_type,
                description=config.description
            )
        
        return result
    
    def get_categories(self) -> List[str]:
        """获取所有配置分类"""
        query = "SELECT DISTINCT category FROM system_config ORDER BY category"
        result = self.db.execute_query(query)
        return [row['category'] for row in result]
    
    def export_configs(self, category: str = None) -> Dict[str, Any]:
        """导出配置（用于备份）"""
        configs = self.list_configs(category, include_sensitive=True)
        export_data = {
            "export_time": datetime.now().isoformat(),
            "category": category,
            "configs": []
        }
        
        for config in configs:
            config_data = {
                "config_key": config.config_key,
                "config_value": config.config_value,
                "config_type": config.config_type,
                "description": config.description,
                "category": config.category,
                "is_sensitive": config.is_sensitive
            }
            export_data["configs"].append(config_data)
        
        return export_data
    
    def import_configs(self, import_data: Dict[str, Any], overwrite: bool = False) -> Dict[str, Any]:
        """导入配置"""
        results = {
            "imported": 0,
            "skipped": 0,
            "errors": []
        }
        
        for config_data in import_data.get("configs", []):
            try:
                config_create = ConfigCreate(**config_data)
                
                if not overwrite and self.get_config_by_key(config_create.config_key):
                    results["skipped"] += 1
                    continue
                
                if overwrite:
                    # 删除现有配置
                    self.delete_config(config_create.config_key)
                
                self.create_config(config_create)
                results["imported"] += 1
                
            except Exception as e:
                results["errors"].append(f"导入配置 {config_data.get('config_key', 'unknown')} 失败: {str(e)}")
        
        return results
    
    def validate_config_value(self, config_type: str, config_value: str) -> bool:
        """验证配置值的类型"""
        try:
            if config_type == "string":
                return True
            elif config_type == "number":
                float(config_value)
                return True
            elif config_type == "boolean":
                return config_value.lower() in ('true', 'false', '1', '0', 'yes', 'no', 'on', 'off')
            elif config_type == "json":
                json.loads(config_value)
                return True
            return False
        except (ValueError, json.JSONDecodeError):
            return False
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        configs = self.get_config_by_category("system", include_sensitive=False)
        
        # 获取统计信息
        stats_query = """
        SELECT 
            COUNT(*) as total_configs,
            COUNT(CASE WHEN is_sensitive = 1 THEN 1 END) as sensitive_configs,
            COUNT(DISTINCT category) as total_categories
        FROM system_config
        """
        stats_result = self.db.execute_query(stats_query)
        stats = dict(stats_result[0]) if stats_result else {}
        
        return {
            "system_configs": configs,
            "config_statistics": stats,
            "categories": self.get_categories()
        }