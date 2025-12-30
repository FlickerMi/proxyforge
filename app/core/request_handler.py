"""请求处理模块"""

import httpx
from typing import Optional
from app.models import RequestModel, ResponseModel, ProxyModel
from app.config import settings
from app.utils import log


class RequestHandler:
    """请求处理器"""
    
    def __init__(self):
        self.timeout = settings.request_timeout
        self.max_retries = settings.request_max_retries
    
    async def send_request(
        self, 
        request: RequestModel, 
        proxy: Optional[ProxyModel] = None
    ) -> ResponseModel:
        """
        发送 HTTP 请求
        
        Args:
            request: 请求模型
            proxy: 代理模型(可选)
            
        Returns:
            响应模型
            
        Raises:
            Exception: 请求失败
        """
        timeout = request.timeout or self.timeout
        
        # 构建请求参数
        kwargs = {
            "method": request.method.value,
            "url": request.url,
            "timeout": timeout,
            "follow_redirects": request.allow_redirects,
        }
        
        if request.headers:
            kwargs["headers"] = request.headers
        
        if request.params:
            kwargs["params"] = request.params
        
        if request.data:
            kwargs["data"] = request.data
        
        if request.json:
            kwargs["json"] = request.json
        
        # 配置代理
        client_kwargs = {"verify": False}
        if proxy:
            client_kwargs["proxies"] = proxy.to_dict()
            log.info(f"使用代理发送请求: {proxy.proxy_url} -> {request.url}")
        else:
            log.info(f"直接发送请求: {request.url}")
        
        # 发送请求
        async with httpx.AsyncClient(**client_kwargs) as client:
            response = await client.request(**kwargs)
        
        # 构建响应
        return ResponseModel(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.text,
            encoding=response.encoding,
            elapsed=response.elapsed.total_seconds(),
            proxy_used=proxy.proxy_url if proxy else None,
        )
    
    async def send_request_with_retry(
        self, 
        request: RequestModel,
        get_proxy_func,
        mark_invalid_func
    ) -> ResponseModel:
        """
        发送请求并自动重试
        
        Args:
            request: 请求模型
            get_proxy_func: 获取代理的函数
            mark_invalid_func: 标记代理失效的函数
            
        Returns:
            响应模型
            
        Raises:
            Exception: 所有重试都失败
        """
        max_retries = request.max_retries or self.max_retries
        retry_status_codes = request.retry_on_status_codes  # 直接使用用户指定的值,None 表示不判断
        last_error = None
        last_error_type = None
        last_status_code = None
        
        for attempt in range(max_retries):
            proxy = None
            try:
                # 获取代理
                proxy = get_proxy_func()
                
                if not proxy:
                    log.warning(f"第 {attempt + 1}/{max_retries} 次尝试: 没有可用代理")
                    # 如果没有代理,尝试直接请求
                    return await self.send_request(request, None)
                
                # 发送请求
                response = await self.send_request(request, proxy)
                
                # 检查状态码是否需要重试 (仅当用户明确指定时)
                if retry_status_codes and response.status_code in retry_status_codes:
                    last_status_code = response.status_code
                    last_error_type = "需要重试的状态码"
                    last_error = f"HTTP {response.status_code}"
                    
                    log.warning(
                        f"✗ 第 {attempt + 1}/{max_retries} 次请求失败 [状态码需要重试]\n"
                        f"   URL: {request.url}\n"
                        f"   代理: {proxy.proxy_url if proxy else '无'}\n"
                        f"   状态码: {response.status_code}\n"
                        f"   说明: 该状态码在重试列表中 {retry_status_codes}"
                    )
                    
                    # 标记代理失效
                    if proxy:
                        mark_invalid_func(proxy.id)
                        log.debug(f"已标记代理失效: {proxy.proxy_url}")
                    
                    # 如果还有重试机会,继续
                    if attempt < max_retries - 1:
                        continue
                    else:
                        # 最后一次重试也失败了,抛出异常
                        raise Exception(f"HTTP {response.status_code}: 所有重试均返回需要重试的状态码")
                
                # 状态码正常或未配置状态码过滤,返回响应
                log.info(f"✓ 请求成功: {request.url}, 状态码: {response.status_code}, 代理: {proxy.proxy_url}")
                return response
                
            except httpx.TimeoutException as e:
                last_error = e
                last_error_type = "超时"
                log.warning(
                    f"✗ 第 {attempt + 1}/{max_retries} 次请求失败 [超时]\n"
                    f"   URL: {request.url}\n"
                    f"   代理: {proxy.proxy_url if proxy else '无'}\n"
                    f"   错误: {str(e)}"
                )
                
            except httpx.ConnectError as e:
                last_error = e
                last_error_type = "连接错误"
                log.warning(
                    f"✗ 第 {attempt + 1}/{max_retries} 次请求失败 [连接错误]\n"
                    f"   URL: {request.url}\n"
                    f"   代理: {proxy.proxy_url if proxy else '无'}\n"
                    f"   错误: {str(e)}"
                )
                
            except httpx.ProxyError as e:
                last_error = e
                last_error_type = "代理错误"
                log.warning(
                    f"✗ 第 {attempt + 1}/{max_retries} 次请求失败 [代理错误]\n"
                    f"   URL: {request.url}\n"
                    f"   代理: {proxy.proxy_url if proxy else '无'}\n"
                    f"   错误: {str(e)}"
                )
                
            except httpx.HTTPStatusError as e:
                last_error = e
                last_error_type = "HTTP状态错误"
                last_status_code = e.response.status_code
                log.warning(
                    f"✗ 第 {attempt + 1}/{max_retries} 次请求失败 [HTTP错误]\n"
                    f"   URL: {request.url}\n"
                    f"   代理: {proxy.proxy_url if proxy else '无'}\n"
                    f"   状态码: {e.response.status_code}\n"
                    f"   错误: {str(e)}"
                )
                
            except Exception as e:
                last_error = e
                last_error_type = type(e).__name__
                log.warning(
                    f"✗ 第 {attempt + 1}/{max_retries} 次请求失败 [{last_error_type}]\n"
                    f"   URL: {request.url}\n"
                    f"   代理: {proxy.proxy_url if proxy else '无'}\n"
                    f"   错误: {str(e)}"
                )
            
            # 标记代理失效
            if proxy:
                mark_invalid_func(proxy.id)
                log.debug(f"已标记代理失效: {proxy.proxy_url}")
            
            # 如果还有重试机会,继续
            if attempt < max_retries - 1:
                continue
        
        # 所有重试都失败,构造详细错误信息
        error_details = {
            "url": request.url,
            "attempts": max_retries,
            "error_type": last_error_type,
            "error_message": str(last_error),
        }
        
        if last_status_code:
            error_details["status_code"] = last_status_code
        
        error_msg = (
            f"请求失败,已重试 {max_retries} 次\n"
            f"错误类型: {last_error_type}\n"
            f"错误信息: {last_error}"
        )
        
        if last_status_code:
            error_msg += f"\n状态码: {last_status_code}"
        
        log.error(
            f"❌ 所有重试均失败\n"
            f"   URL: {request.url}\n"
            f"   尝试次数: {max_retries}\n"
            f"   错误类型: {last_error_type}\n"
            f"   错误信息: {last_error}\n"
            + (f"   最后状态码: {last_status_code}\n" if last_status_code else "")
        )
        
        raise Exception(error_msg)


# 全局请求处理器实例
request_handler = RequestHandler()
