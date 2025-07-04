"""
双写日志中间件 - 自动记录API请求到文件和数据库
"""
import time
import json
from typing import Callable, Optional
from fastapi import Request, Response
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.dual_logger import get_dual_logger
from backend.services.auth_service import decode_access_token


class DualLoggingMiddleware(BaseHTTPMiddleware):
    """双写日志中间件 - 记录API调用到文件和数据库"""
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/docs", "/openapi.json", "/favicon.ico"]
        self.api_logger = get_dual_logger('api_requests')
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并记录日志"""
        # 检查是否应该排除此路径
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # 记录开始时间
        start_time = time.time()
        
        # 提取用户信息
        user_id, user_info = self._extract_user_info(request)
        
        # 记录请求开始
        request_data = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", ""),
            "user_id": user_id
        }
        
        # 执行请求
        try:
            response = await call_next(request)
            
            # 计算响应时间
            process_time = time.time() - start_time
            
            # 记录成功的API调用
            self._log_api_call(
                request_data=request_data,
                response_status=response.status_code,
                process_time=process_time,
                user_id=user_id,
                success=True
            )
            
            return response
            
        except Exception as e:
            # 计算响应时间
            process_time = time.time() - start_time
            
            # 记录失败的API调用
            self._log_api_call(
                request_data=request_data,
                response_status=500,
                process_time=process_time,
                user_id=user_id,
                success=False,
                error=str(e)
            )
            
            raise e
    
    def _extract_user_info(self, request: Request) -> tuple[Optional[int], Optional[dict]]:
        """从请求中提取用户信息"""
        try:
            # 从Authorization头中提取token
            authorization = request.headers.get("authorization")
            if not authorization:
                return None, None
            
            scheme, token = get_authorization_scheme_param(authorization)
            if scheme.lower() != "bearer":
                return None, None
            
            # 解码token获取用户信息
            payload = decode_access_token(token)
            if payload:
                user_id = payload.get("user_id")
                return user_id, payload
            
        except Exception:
            pass
        
        return None, None
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # 返回直接连接的IP
        if hasattr(request.client, 'host'):
            return request.client.host
        
        return "unknown"
    
    def _log_api_call(self, request_data: dict, response_status: int, 
                      process_time: float, user_id: Optional[int], 
                      success: bool, error: Optional[str] = None):
        """记录API调用日志"""
        try:
            # 创建具有用户上下文的日志记录器
            if user_id:
                user_logger = self.api_logger.set_user_context(
                    user_id=user_id,
                    ip_address=request_data.get("client_ip"),
                    user_agent=request_data.get("user_agent")
                )
            else:
                user_logger = self.api_logger
            
            # 构建日志消息
            log_message = f"{request_data['method']} {request_data['path']} - {response_status} - {process_time:.3f}s"
            
            # 根据状态码选择日志级别
            if success and 200 <= response_status < 400:
                log_level = "info"
            elif 400 <= response_status < 500:
                log_level = "warning"
            else:
                log_level = "error"
            
            # 构建额外信息
            extra_data = {
                "resource_id": request_data['path'],
                "ip_address": request_data.get("client_ip"),
                "user_agent": request_data.get("user_agent"),
                "response_time": process_time,
                "status_code": response_status
            }
            
            if error:
                extra_data["error"] = error
                log_message += f" - Error: {error}"
            
            # 记录日志
            getattr(user_logger, log_level)(log_message, **extra_data)
            
        except Exception as e:
            # 日志记录失败时不应该影响正常请求，只是静默失败
            pass


def setup_dual_logging_middleware(app):
    """设置双写日志中间件"""
    app.add_middleware(
        DualLoggingMiddleware,
        exclude_paths=[
            "/docs", 
            "/openapi.json", 
            "/favicon.ico",
            "/redoc",
            "/health"  # 健康检查端点通常不需要记录
        ]
    )