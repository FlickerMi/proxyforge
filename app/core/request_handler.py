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
        发送请求并自动重试(双层重试机制)
        
        Args:
            request: 请求模型
            get_proxy_func: 获取代理的函数
            mark_invalid_func: 标记代理失效的函数
            
        Returns:
            响应模型
            
        Raises:
            Exception: 所有重试都失败
        """
        # 处理向后兼容性: 如果只设置了 max_retries, 将其作为 max_proxy_switches
        if request.max_retries is not None and request.max_proxy_switches == 5:
            max_proxy_switches = request.max_retries
        else:
            max_proxy_switches = request.max_proxy_switches or settings.request_max_proxy_switches
        
        max_retries_per_proxy = request.max_retries_per_proxy or settings.request_max_retries_per_proxy
        retry_status_codes = request.retry_on_status_codes
        
        last_error = None
        last_error_type = None
        last_status_code = None
        total_attempts = 0
        
        log.info(
            f"开始请求 {request.url}\n"
            f"   重试策略: 最多尝试 {max_proxy_switches} 个代理, 每个代理重试 {max_retries_per_proxy} 次\n"
            f"   最大尝试次数: {max_proxy_switches * max_retries_per_proxy}"
        )
        
        # 外层循环: 切换不同的代理
        for proxy_index in range(max_proxy_switches):
            proxy = None
            
            try:
                # 获取代理
                proxy = get_proxy_func()
                
                if not proxy:
                    log.warning(f"代理 {proxy_index + 1}/{max_proxy_switches}: 没有可用代理")
                    # 如果没有代理,尝试直接请求
                    try:
                        return await self.send_request(request, None)
                    except Exception as e:
                        last_error = e
                        last_error_type = "无代理直接请求失败"
                        if proxy_index < max_proxy_switches - 1:
                            continue
                        else:
                            break
                
                log.info(f"代理 {proxy_index + 1}/{max_proxy_switches}: 使用 {proxy.proxy_url}")
                
                # 内层循环: 对当前代理进行重试
                proxy_failed = False
                for retry_index in range(max_retries_per_proxy):
                    total_attempts += 1
                    
                    try:
                        # 发送请求
                        response = await self.send_request(request, proxy)
                        
                        # 检查状态码是否需要重试 (仅当用户明确指定时)
                        if retry_status_codes and response.status_code in retry_status_codes:
                            last_status_code = response.status_code
                            last_error_type = "需要重试的状态码"
                            last_error = f"HTTP {response.status_code}"
                            
                            log.warning(
                                f"✗ 代理 {proxy_index + 1}/{max_proxy_switches}, "
                                f"重试 {retry_index + 1}/{max_retries_per_proxy} [状态码需要重试]\n"
                                f"   URL: {request.url}\n"
                                f"   代理: {proxy.proxy_url}\n"
                                f"   状态码: {response.status_code}\n"
                                f"   说明: 该状态码在重试列表中 {retry_status_codes}"
                            )
                            
                            # 如果是当前代理的最后一次重试,标记代理失效并切换代理
                            if retry_index >= max_retries_per_proxy - 1:
                                mark_invalid_func(proxy.id)
                                log.debug(f"已标记代理失效: {proxy.proxy_url}")
                                proxy_failed = True
                                break
                            else:
                                # 继续用当前代理重试
                                continue
                        
                        # 状态码正常或未配置状态码过滤,返回响应
                        log.info(
                            f"✓ 请求成功 (总尝试 {total_attempts} 次)\n"
                            f"   URL: {request.url}\n"
                            f"   代理: {proxy.proxy_url}\n"
                            f"   状态码: {response.status_code}"
                        )
                        return response
                        
                    except httpx.TimeoutException as e:
                        last_error = e
                        last_error_type = "超时"
                        log.warning(
                            f"✗ 代理 {proxy_index + 1}/{max_proxy_switches}, "
                            f"重试 {retry_index + 1}/{max_retries_per_proxy} [超时]\n"
                            f"   URL: {request.url}\n"
                            f"   代理: {proxy.proxy_url}\n"
                            f"   错误: {str(e)}"
                        )
                        
                    except httpx.ConnectError as e:
                        last_error = e
                        last_error_type = "连接错误"
                        log.warning(
                            f"✗ 代理 {proxy_index + 1}/{max_proxy_switches}, "
                            f"重试 {retry_index + 1}/{max_retries_per_proxy} [连接错误]\n"
                            f"   URL: {request.url}\n"
                            f"   代理: {proxy.proxy_url}\n"
                            f"   错误: {str(e)}"
                        )
                        
                    except httpx.ProxyError as e:
                        last_error = e
                        last_error_type = "代理错误"
                        log.warning(
                            f"✗ 代理 {proxy_index + 1}/{max_proxy_switches}, "
                            f"重试 {retry_index + 1}/{max_retries_per_proxy} [代理错误]\n"
                            f"   URL: {request.url}\n"
                            f"   代理: {proxy.proxy_url}\n"
                            f"   错误: {str(e)}"
                        )
                        
                    except httpx.HTTPStatusError as e:
                        last_error = e
                        last_error_type = "HTTP状态错误"
                        last_status_code = e.response.status_code
                        log.warning(
                            f"✗ 代理 {proxy_index + 1}/{max_proxy_switches}, "
                            f"重试 {retry_index + 1}/{max_retries_per_proxy} [HTTP错误]\n"
                            f"   URL: {request.url}\n"
                            f"   代理: {proxy.proxy_url}\n"
                            f"   状态码: {e.response.status_code}\n"
                            f"   错误: {str(e)}"
                        )
                        
                    except Exception as e:
                        last_error = e
                        last_error_type = type(e).__name__
                        log.warning(
                            f"✗ 代理 {proxy_index + 1}/{max_proxy_switches}, "
                            f"重试 {retry_index + 1}/{max_retries_per_proxy} [{last_error_type}]\n"
                            f"   URL: {request.url}\n"
                            f"   代理: {proxy.proxy_url}\n"
                            f"   错误: {str(e)}"
                        )
                    
                    # 如果是当前代理的最后一次重试,标记失效
                    if retry_index >= max_retries_per_proxy - 1:
                        proxy_failed = True
                
                # 当前代理的所有重试都失败,标记代理失效
                if proxy_failed and proxy:
                    mark_invalid_func(proxy.id)
                    log.info(f"代理 {proxy_index + 1}/{max_proxy_switches}: {proxy.proxy_url} 所有重试失败,已标记失效")
                    
            except Exception as e:
                last_error = e
                last_error_type = type(e).__name__
                log.error(f"代理 {proxy_index + 1}/{max_proxy_switches}: 发生异常 - {e}")
        
        # 所有代理和重试都失败,构造详细错误信息
        error_msg = (
            f"请求失败,已尝试 {max_proxy_switches} 个代理,共 {total_attempts} 次请求\n"
            f"错误类型: {last_error_type}\n"
            f"错误信息: {last_error}"
        )
        
        if last_status_code:
            error_msg += f"\n最后状态码: {last_status_code}"
        
        log.error(
            f"❌ 所有重试均失败\n"
            f"   URL: {request.url}\n"
            f"   尝试代理数: {max_proxy_switches}\n"
            f"   总尝试次数: {total_attempts}\n"
            f"   错误类型: {last_error_type}\n"
            f"   错误信息: {last_error}\n"
            + (f"   最后状态码: {last_status_code}\n" if last_status_code else "")
        )
        
        raise Exception(error_msg)


# 全局请求处理器实例
request_handler = RequestHandler()
