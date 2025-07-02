"""
API使用统计中间件
"""
import time
import json
from datetime import datetime
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.dependencies import get_database_manager
from backend.services.auth_service import get_auth_service


class APIStatsMiddleware(BaseHTTPMiddleware):
    """API统计中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并记录统计信息"""
        # 记录开始时间
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        url = str(request.url)
        endpoint = request.url.path
        user_agent = request.headers.get("user-agent", "")
        ip_address = self._get_client_ip(request)
        request_size = self._get_request_size(request)
        
        # 获取用户ID（如果已认证）
        user_id = None
        try:
            # 从Authorization header获取用户信息
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                auth_service = get_auth_service()
                token_data = auth_service.user_auth.verify_token(token)
                if token_data:
                    user_id = token_data.user_id
        except Exception:
            # 认证失败不影响统计记录
            pass
        
        # 执行请求
        response = await call_next(request)
        
        # 计算响应时间
        response_time = (time.time() - start_time) * 1000  # 转换为毫秒
        
        # 获取响应信息
        status_code = response.status_code
        response_size = self._get_response_size(response)
        
        # 异步记录统计信息（不影响响应）
        try:
            await self._record_api_stats(
                user_id=user_id,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time=response_time,
                request_size=request_size,
                response_size=response_size,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except Exception as e:
            # 统计记录失败不影响正常响应
            print(f"记录API统计失败: {e}")
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 尝试从各种header获取真实IP
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # 回退到直接连接IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _get_request_size(self, request: Request) -> int:
        """获取请求大小（估算）"""
        try:
            content_length = request.headers.get("content-length")
            if content_length:
                return int(content_length)
            
            # 如果没有content-length，估算header大小
            header_size = sum(len(k) + len(v) + 4 for k, v in request.headers.items())  # +4 for ": " and "\r\n"
            return header_size + len(str(request.url))
        except:
            return 0
    
    def _get_response_size(self, response: Response) -> int:
        """获取响应大小（估算）"""
        try:
            content_length = response.headers.get("content-length")
            if content_length:
                return int(content_length)
            
            # 估算header大小
            header_size = sum(len(k) + len(v) + 4 for k, v in response.headers.items())
            return header_size
        except:
            return 0
    
    async def _record_api_stats(self, user_id: int = None, endpoint: str = "", 
                               method: str = "", status_code: int = 0,
                               response_time: float = 0, request_size: int = 0,
                               response_size: int = 0, ip_address: str = "",
                               user_agent: str = ""):
        """记录API统计信息到数据库"""
        try:
            # 跳过一些不需要统计的端点
            skip_endpoints = ["/docs", "/openapi.json", "/redoc", "/favicon.ico"]
            if any(endpoint.startswith(skip) for skip in skip_endpoints):
                return
            
            # 只统计API端点
            if not endpoint.startswith("/api/"):
                return
            
            # 只记录已认证用户的统计信息
            if user_id is None:
                return
            
            db_manager = get_database_manager()
            
            query = """
            INSERT INTO api_usage_stats 
            (user_id, endpoint, method, status_code, response_time, 
             request_size, response_size, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            with db_manager.get_connection() as conn:
                conn.execute(query, (
                    user_id,
                    endpoint,
                    method,
                    status_code,
                    response_time,
                    request_size,
                    response_size,
                    datetime.now()
                ))
                conn.commit()
                
        except Exception as e:
            # 记录失败不抛出异常，避免影响正常业务
            print(f"记录API统计到数据库失败: {e}")


def add_stats_middleware(app):
    """添加统计中间件到应用"""
    app.add_middleware(APIStatsMiddleware)