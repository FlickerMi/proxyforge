"""数据模型定义"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ProxyProtocol(str, Enum):
    """代理协议类型"""
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


class ProxyModel(BaseModel):
    """代理信息模型"""
    id: Optional[str] = None
    host: str
    port: int
    protocol: ProxyProtocol = ProxyProtocol.HTTP
    username: Optional[str] = None
    password: Optional[str] = None
    country: Optional[str] = None
    anonymity: Optional[str] = None
    speed: Optional[float] = None  # 响应时间(秒)
    last_checked: Optional[datetime] = None
    is_valid: bool = True
    
    @property
    def proxy_url(self) -> str:
        """获取代理 URL"""
        if self.username and self.password:
            return f"{self.protocol.value}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol.value}://{self.host}:{self.port}"
    
    def to_dict(self) -> Dict[str, str]:
        """转换为 httpx 使用的代理字典"""
        return {
            "http://": self.proxy_url,
            "https://": self.proxy_url,
        }


class HttpMethod(str, Enum):
    """HTTP 方法"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class RequestModel(BaseModel):
    """代理请求模型"""
    url: str = Field(..., description="目标 URL")
    method: HttpMethod = Field(HttpMethod.GET, description="HTTP 方法")
    headers: Optional[Dict[str, str]] = Field(None, description="请求头")
    params: Optional[Dict[str, Any]] = Field(None, description="查询参数")
    data: Optional[Dict[str, Any]] = Field(None, description="表单数据")
    json: Optional[Dict[str, Any]] = Field(None, description="JSON 数据")
    timeout: Optional[int] = Field(30, description="超时时间(秒)")
    allow_redirects: bool = Field(True, description="是否允许重定向")
    max_retries: Optional[int] = Field(3, description="最大重试次数")
    retry_on_status_codes: Optional[List[int]] = Field(
        None, 
        description="触发重试的 HTTP 状态码列表,默认为 None (不基于状态码重试),可设置如 [403, 429, 502, 503]"
    )


class ResponseModel(BaseModel):
    """响应模型"""
    status_code: int
    headers: Dict[str, str]
    content: str
    encoding: Optional[str] = None
    elapsed: float  # 请求耗时(秒)
    proxy_used: Optional[str] = None  # 使用的代理


class ProxyStatsModel(BaseModel):
    """代理池统计模型"""
    total_proxies: int
    valid_proxies: int
    invalid_proxies: int
    last_update: Optional[datetime] = None
    avg_speed: Optional[float] = None


class ApiResponse(BaseModel):
    """统一 API 响应模型"""
    success: bool
    message: str = ""
    data: Optional[Any] = None
