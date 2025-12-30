"""代理请求 API"""

from fastapi import APIRouter, HTTPException
from app.models import RequestModel, ResponseModel, ApiResponse
from app.core.proxy_pool import proxy_pool
from app.core.request_handler import request_handler
from app.utils import log

router = APIRouter(prefix="/api", tags=["代理请求"])


@router.post("/request", response_model=ApiResponse, summary="通过代理发送请求")
async def send_proxy_request(request: RequestModel) -> ApiResponse:
    """
    通过代理发送 HTTP 请求
    
    接收完整的请求参数,通过代理池中的代理发送请求,并返回响应数据。
    如果请求失败,会自动重试并切换代理。
    
    Args:
        request: 请求参数
            - url: 目标 URL
            - method: HTTP 方法 (GET, POST, PUT, DELETE 等)
            - headers: 请求头 (可选)
            - params: 查询参数 (可选)
            - data: 表单数据 (可选)
            - json: JSON 数据 (可选)
            - timeout: 超时时间,秒 (可选,默认 30)
            - allow_redirects: 是否允许重定向 (可选,默认 True)
            - max_retries: 最大重试次数 (可选,默认 3)
    
    Returns:
        响应数据
            - status_code: HTTP 状态码
            - headers: 响应头
            - content: 响应内容
            - encoding: 编码
            - elapsed: 请求耗时
            - proxy_used: 使用的代理
    
    Example:
        ```json
        {
            "url": "https://httpbin.org/ip",
            "method": "GET"
        }
        ```
        
        ```json
        {
            "url": "https://httpbin.org/post",
            "method": "POST",
            "headers": {
                "User-Agent": "ProxyForge/1.0"
            },
            "json": {
                "key": "value"
            }
        }
        ```
    """
    try:
        log.info(f"收到代理请求: {request.method} {request.url}")
        
        # 通过代理发送请求(带重试)
        response = await request_handler.send_request_with_retry(
            request=request,
            get_proxy_func=proxy_pool.get_random_proxy,
            mark_invalid_func=proxy_pool.mark_proxy_invalid
        )
        
        return ApiResponse(
            success=True,
            message="请求成功",
            data=response.model_dump()
        )
        
    except Exception as e:
        log.error(f"代理请求失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
