"""
用户认证和权限管理数据模型
实现完整的RBAC权限控制系统
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, validator
from passlib.context import CryptContext
import secrets
from jose import jwt, JWTError
from src.database.models import DatabaseManager


# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT配置
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    """用户创建模型"""
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度不能少于8位')
        return v


class UserUpdate(BaseModel):
    """用户更新模型"""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserPasswordUpdate(BaseModel):
    """用户密码更新模型"""
    old_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('新密码长度不能少于8位')
        return v


class UserInDB(UserBase):
    """数据库中的用户模型"""
    id: int
    password_hash: str
    is_superuser: bool = False
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    login_count: int = 0


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    is_superuser: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None
    login_count: int = 0
    roles: List[str] = []
    permissions: List[str] = []


class TokenData(BaseModel):
    """Token数据模型"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    permissions: List[str] = []


class Token(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str
    expires_at: datetime
    user: UserResponse


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str


class Role(BaseModel):
    """角色模型"""
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime


class Permission(BaseModel):
    """权限模型"""
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    resource: str
    action: str


class RoleCreate(BaseModel):
    """角色创建模型"""
    name: str
    display_name: str
    description: Optional[str] = None


class UserAuthService:
    """用户认证服务"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            permissions: List[str] = payload.get("permissions", [])
            if username is None:
                return None
            token_data = TokenData(
                username=username, 
                user_id=user_id, 
                permissions=permissions
            )
            return token_data
        except JWTError:
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """认证用户"""
        user = self.get_user_by_username(username)
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user
    
    def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """根据用户名获取用户"""
        query = "SELECT * FROM users WHERE username = ? AND is_active = 1"
        result = self.db.execute_query(query, (username,))
        if result:
            user_data = result[0]
            return UserInDB(**dict(user_data))
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[UserInDB]:
        """根据ID获取用户"""
        query = "SELECT * FROM users WHERE id = ? AND is_active = 1"
        result = self.db.execute_query(query, (user_id,))
        if result:
            user_data = result[0]
            return UserInDB(**dict(user_data))
        return None
    
    def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """根据邮箱获取用户"""
        query = "SELECT * FROM users WHERE email = ? AND is_active = 1"
        result = self.db.execute_query(query, (email,))
        if result:
            user_data = result[0]
            return UserInDB(**dict(user_data))
        return None
    
    def create_user(self, user: UserCreate) -> UserInDB:
        """创建用户"""
        # 检查用户名和邮箱是否已存在
        if self.get_user_by_username(user.username):
            raise ValueError("用户名已存在")
        if self.get_user_by_email(user.email):
            raise ValueError("邮箱已存在")
        
        password_hash = self.get_password_hash(user.password)
        now = datetime.now()
        
        query = """
        INSERT INTO users (username, email, password_hash, full_name, phone, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            user.username, user.email, password_hash, 
            user.full_name, user.phone, now, now
        )
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            user_id = cursor.lastrowid
            conn.commit()
            
            # 为新用户分配默认角色
            self.assign_role_to_user(user_id, "regular_user")
            
            return self.get_user_by_id(user_id)
    
    def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[UserInDB]:
        """更新用户信息"""
        current_user = self.get_user_by_id(user_id)
        if not current_user:
            return None
        
        # 检查邮箱是否被其他用户使用
        if user_update.email:
            existing_user = self.get_user_by_email(user_update.email)
            if existing_user and existing_user.id != user_id:
                raise ValueError("邮箱已被其他用户使用")
        
        update_fields = []
        params = []
        
        if user_update.full_name is not None:
            update_fields.append("full_name = ?")
            params.append(user_update.full_name)
        
        if user_update.phone is not None:
            update_fields.append("phone = ?")
            params.append(user_update.phone)
        
        if user_update.email is not None:
            update_fields.append("email = ?")
            params.append(user_update.email)
        
        if user_update.is_active is not None:
            update_fields.append("is_active = ?")
            params.append(user_update.is_active)
        
        if not update_fields:
            return current_user
        
        update_fields.append("updated_at = ?")
        params.append(datetime.now())
        params.append(user_id)
        
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        
        with self.db.get_connection() as conn:
            conn.execute(query, params)
            conn.commit()
            
        return self.get_user_by_id(user_id)
    
    def update_password(self, user_id: int, password_update: UserPasswordUpdate) -> bool:
        """更新用户密码"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        if not self.verify_password(password_update.old_password, user.password_hash):
            raise ValueError("原密码错误")
        
        new_password_hash = self.get_password_hash(password_update.new_password)
        
        query = "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?"
        with self.db.get_connection() as conn:
            conn.execute(query, (new_password_hash, datetime.now(), user_id))
            conn.commit()
            
        return True
    
    def update_login_info(self, user_id: int):
        """更新登录信息"""
        query = """
        UPDATE users 
        SET last_login = ?, login_count = login_count + 1, updated_at = ?
        WHERE id = ?
        """
        now = datetime.now()
        with self.db.get_connection() as conn:
            conn.execute(query, (now, now, user_id))
            conn.commit()
    
    def get_user_roles(self, user_id: int) -> List[str]:
        """获取用户角色"""
        query = """
        SELECT r.name FROM roles r
        JOIN user_roles ur ON r.id = ur.role_id
        WHERE ur.user_id = ? AND r.is_active = 1
        """
        result = self.db.execute_query(query, (user_id,))
        return [row['name'] for row in result]
    
    def get_user_permissions(self, user_id: int) -> List[str]:
        """获取用户权限"""
        query = """
        SELECT DISTINCT p.name FROM permissions p
        JOIN role_permissions rp ON p.id = rp.permission_id
        JOIN user_roles ur ON rp.role_id = ur.role_id
        WHERE ur.user_id = ?
        """
        result = self.db.execute_query(query, (user_id,))
        return [row['name'] for row in result]
    
    def assign_role_to_user(self, user_id: int, role_name: str) -> bool:
        """为用户分配角色"""
        # 获取角色ID
        role_query = "SELECT id FROM roles WHERE name = ? AND is_active = 1"
        role_result = self.db.execute_query(role_query, (role_name,))
        if not role_result:
            return False
        
        role_id = role_result[0]['id']
        
        # 检查用户是否已有该角色
        check_query = "SELECT 1 FROM user_roles WHERE user_id = ? AND role_id = ?"
        if self.db.execute_query(check_query, (user_id, role_id)):
            return True  # 已有该角色
        
        # 分配角色
        assign_query = "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)"
        with self.db.get_connection() as conn:
            conn.execute(assign_query, (user_id, role_id))
            conn.commit()
            
        return True
    
    def remove_role_from_user(self, user_id: int, role_name: str) -> bool:
        """移除用户角色"""
        query = """
        DELETE FROM user_roles 
        WHERE user_id = ? AND role_id = (
            SELECT id FROM roles WHERE name = ?
        )
        """
        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (user_id, role_name))
            conn.commit()
            return cursor.rowcount > 0
    
    def has_permission(self, user_id: int, permission: str) -> bool:
        """检查用户是否有指定权限"""
        permissions = self.get_user_permissions(user_id)
        return permission in permissions
    
    def get_user_response(self, user: UserInDB) -> UserResponse:
        """获取用户响应模型"""
        roles = self.get_user_roles(user.id)
        permissions = self.get_user_permissions(user.id)
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            last_login=user.last_login,
            login_count=user.login_count,
            roles=roles,
            permissions=permissions
        )
    
    def list_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """获取用户列表"""
        query = """
        SELECT * FROM users 
        WHERE is_active = 1 
        ORDER BY created_at DESC 
        LIMIT ? OFFSET ?
        """
        result = self.db.execute_query(query, (limit, skip))
        users = []
        for user_data in result:
            user = UserInDB(**dict(user_data))
            users.append(self.get_user_response(user))
        return users
    
    def get_total_users_count(self) -> int:
        """获取用户总数"""
        query = "SELECT COUNT(*) as count FROM users WHERE is_active = 1"
        result = self.db.execute_query(query)
        return result[0]['count'] if result else 0
    
    def list_roles(self) -> List[Role]:
        """获取角色列表"""
        query = "SELECT * FROM roles WHERE is_active = 1 ORDER BY name"
        result = self.db.execute_query(query)
        return [Role(**dict(row)) for row in result]
    
    def list_permissions(self) -> List[Permission]:
        """获取权限列表"""
        query = "SELECT * FROM permissions ORDER BY resource, action"
        result = self.db.execute_query(query)
        return [Permission(**dict(row)) for row in result]