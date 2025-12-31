"""代理验证模块"""

import asyncio
import time
from typing import List
import httpx
from app.models import ProxyModel
from app.config import settings
from app.utils import log


class ProxyValidator:
    """代理验证器"""
    
    def __init__(self):
        self.validation_url = settings.proxy_validation_url
        self.timeout = settings.proxy_validation_timeout
    
    async def validate_proxy(self, proxy: ProxyModel) -> ProxyModel:
        """
        验证单个代理
        
        Args:
            proxy: 代理模型
            
        Returns:
            更新后的代理模型
        """
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient(
                proxies=proxy.to_dict(),
                timeout=self.timeout,
                verify=False,
            ) as client:
                response = await client.get(self.validation_url)
                
                if response.status_code == 200:
                    proxy.is_valid = True
                    proxy.speed = time.time() - start_time
                    log.debug(f"代理验证成功: {proxy.proxy_url}, 速度: {proxy.speed:.2f}s")
                else:
                    proxy.is_valid = False
                    log.debug(f"代理验证失败: {proxy.proxy_url}, 状态码: {response.status_code}")
                    
        except Exception as e:
            proxy.is_valid = False
            log.debug(f"代理验证异常: {proxy.proxy_url}, 错误: {e}")
        
        return proxy
    
    async def validate_proxies(self, proxies: List[ProxyModel], concurrency: int = 10) -> List[ProxyModel]:
        """
        批量验证代理
        
        Args:
            proxies: 代理列表
            concurrency: 并发数
            
        Returns:
            验证后的代理列表
        """
        log.info(f"开始验证 {len(proxies)} 个代理,并发数: {concurrency}")
        
        # 使用信号量控制并发
        semaphore = asyncio.Semaphore(concurrency)
        
        async def validate_with_semaphore(proxy: ProxyModel) -> ProxyModel:
            async with semaphore:
                return await self.validate_proxy(proxy)
        
        # 并发验证
        tasks = [validate_with_semaphore(proxy) for proxy in proxies]
        validated_proxies = await asyncio.gather(*tasks)
        
        # 统计结果
        valid_count = sum(1 for p in validated_proxies if p.is_valid)
        
        # 统计各来源的有效代理数
        source_stats = {}
        for p in validated_proxies:
            if p.is_valid and p.source:
                source_stats[p.source] = source_stats.get(p.source, 0) + 1
        
        # 格式化来源统计信息
        source_info = ", ".join([f"{src}: {cnt}" for src, cnt in source_stats.items()]) if source_stats else "无"
        
        log.info(f"代理验证完成,有效: {valid_count}/{len(proxies)}, 来源分布: {source_info}")
        
        return validated_proxies
    
    async def get_valid_proxies(self, proxies: List[ProxyModel], concurrency: int = 10) -> List[ProxyModel]:
        """
        获取有效代理列表
        
        Args:
            proxies: 代理列表
            concurrency: 并发数
            
        Returns:
            有效代理列表
        """
        validated_proxies = await self.validate_proxies(proxies, concurrency)
        return [p for p in validated_proxies if p.is_valid]
