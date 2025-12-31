"""代理池管理模块"""

import asyncio
import uuid
from datetime import datetime
from typing import List, Optional, Dict
from app.models import ProxyModel, ProxyStatsModel
from app.core.proxy_fetcher import ProxyFetcher
from app.core.proxy_validator import ProxyValidator
from app.config import settings
from app.utils import log


class ProxyPool:
    """代理池管理器"""
    
    def __init__(self):
        self.proxies: Dict[str, ProxyModel] = {}
        self.fetcher = ProxyFetcher()
        self.validator = ProxyValidator()
        self.update_interval = settings.proxy_update_interval
        self.pool_size = settings.proxy_pool_size
        self.last_update: Optional[datetime] = None
        self._update_task: Optional[asyncio.Task] = None
        self._refill_threshold = int(self.pool_size * 0.5)  # 当代理数低于50%时触发补充
    
    async def start(self):
        """启动代理池"""
        log.info("启动代理池管理器")
        
        # 快速启动策略:先获取少量代理,快速启动服务
        # 只需要 10 个有效代理即可启动,获取 50 个原始代理(预期有效率 20%)
        quick_start_count = 10  # 快速启动只需要 10 个有效代理
        log.info(f"快速启动模式:先获取 {quick_start_count} 个有效代理")
        
        # 快速启动时使用较小的倍数和单次尝试
        await self.update_pool(target_count=quick_start_count, max_attempts=1, fetch_multiplier=5)
        
        # 启动后台任务
        # 1. 持续补充代理到目标数量
        self._update_task = asyncio.create_task(self._background_tasks())
    
    async def _background_tasks(self):
        """后台任务:持续补充代理 + 定时更新"""
        # 首先补充到目标数量
        await asyncio.sleep(2)  # 等待服务完全启动
        log.info("后台任务:开始补充代理到目标数量")
        await self.update_pool()
        
        # 然后进入定时更新循环
        while True:
            try:
                await asyncio.sleep(self.update_interval)
                log.info("定时更新代理池: 开始重新验证现有代理")
                
                # 先验证现有代理有效性
                await self.validate_pool()
                
                # 再补充新代理
                await self.update_pool()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"后台任务失败: {e}")
    
    async def stop(self):
        """停止代理池"""
        log.info("停止代理池管理器")
        
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
    
    
    async def update_pool(self, target_count: int = None, max_attempts: int = 3, fetch_multiplier: int = 5):
        """
        更新代理池
        
        Args:
            target_count: 目标代理数量,默认使用配置的 pool_size
            max_attempts: 最大尝试轮数,默认 3 轮
            fetch_multiplier: 获取倍数,默认 5 倍(考虑到 20% 有效率)
        """
        try:
            target = target_count or self.pool_size
            log.info(f"开始更新代理池,目标: {target} 个有效代理")
            
            # 先清理失效代理
            self._cleanup_invalid_proxies()
            
            # 计算需要获取的代理数量
            current_valid = len(self.get_valid_proxies())
            needed = max(target - current_valid, 0)
            
            if needed == 0:
                log.info(f"代理池已满,当前有效代理数: {current_valid}/{target}")
                return
            
            log.info(f"当前有效代理: {current_valid}/{target}, 需要补充: {needed} 个")
            
            # 由于免费代理质量较低,获取更多代理以确保有足够的有效代理
            # 使用可配置的倍数
            fetch_count = needed * fetch_multiplier
            
            for attempt in range(1, max_attempts + 1):
                log.info(f"第 {attempt}/{max_attempts} 轮获取代理,目标: {fetch_count} 个")
                
                # 获取新代理
                new_proxies = await self.fetcher.fetch_proxies(fetch_count)
                
                if not new_proxies:
                    log.warning(f"第 {attempt} 轮未获取到新代理")
                    continue
                
                # 验证代理
                valid_proxies = await self.validator.get_valid_proxies(new_proxies)
                
                # 添加到代理池
                added_count = 0
                for proxy in valid_proxies:
                    proxy.id = str(uuid.uuid4())
                    proxy.last_checked = datetime.now()
                    self.proxies[proxy.id] = proxy
                    added_count += 1
                
                log.info(f"第 {attempt} 轮添加了 {added_count} 个有效代理")
                
                # 检查是否达到目标
                current_valid = len(self.get_valid_proxies())
                if current_valid >= target:
                    log.info(f"已达到目标代理数,当前有效代理: {current_valid}/{target}")
                    break
                
                # 如果还未达到目标,减少下一轮的获取数量
                remaining = target - current_valid
                fetch_count = remaining * fetch_multiplier
            
            # 清理失效代理
            self._cleanup_invalid_proxies()
            
            self.last_update = datetime.now()
            final_count = len(self.get_valid_proxies())
            log.info(f"代理池更新完成,当前有效代理数: {final_count}/{target}")
            
            if final_count < target:
                log.warning(f"警告: 有效代理数({final_count})未达到目标({target}),免费代理质量较低")
            
        except Exception as e:
            log.error(f"更新代理池失败: {e}")
            
    async def validate_pool(self):
        """重新验证池中的所有代理"""
        proxies = list(self.proxies.values())
        if not proxies:
            log.info("代理池为空,跳过验证")
            return
            
        log.info(f"开始重新验证池中 {len(proxies)} 个代理")
        
        # 验证所有代理(包括失效的,检查是否恢复)
        await self.validator.validate_proxies(proxies)
        
        # 统计验证后的有效代理数
        valid_count = len(self.get_valid_proxies())
        log.info(f"验证完成,当前有效代理数: {valid_count}/{self.pool_size}")
    
    def _cleanup_invalid_proxies(self):
        """清理失效代理"""
        invalid_ids = [pid for pid, proxy in self.proxies.items() if not proxy.is_valid]
        
        for pid in invalid_ids:
            del self.proxies[pid]
        
        if invalid_ids:
            log.info(f"清理了 {len(invalid_ids)} 个失效代理")
    
    def get_proxy(self, proxy_id: str) -> Optional[ProxyModel]:
        """
        获取指定代理
        
        Args:
            proxy_id: 代理 ID
            
        Returns:
            代理模型
        """
        return self.proxies.get(proxy_id)
    
    def get_random_proxy(self) -> Optional[ProxyModel]:
        """
        获取随机代理
        
        Returns:
            代理模型
        """
        valid_proxies = self.get_valid_proxies()
        
        if not valid_proxies:
            log.warning("代理池中没有可用代理")
            return None
        
        # 检查代理数量是否低于阈值,触发后台补充
        if len(valid_proxies) < self._refill_threshold:
            log.warning(f"代理数量不足({len(valid_proxies)}/{self.pool_size}),触发后台补充任务")
            # 创建后台任务补充代理,不阻塞当前请求
            asyncio.create_task(self.update_pool())
        
        # 按速度排序,选择最快的代理
        sorted_proxies = sorted(valid_proxies, key=lambda p: p.speed or 999)
        return sorted_proxies[0] if sorted_proxies else None
    
    def get_all_proxies(self) -> List[ProxyModel]:
        """
        获取所有代理
        
        Returns:
            代理列表
        """
        return list(self.proxies.values())
    
    def get_valid_proxies(self) -> List[ProxyModel]:
        """
        获取有效代理列表
        
        Returns:
            有效代理列表
        """
        return [p for p in self.proxies.values() if p.is_valid]
    
    def remove_proxy(self, proxy_id: str) -> bool:
        """
        移除代理
        
        Args:
            proxy_id: 代理 ID
            
        Returns:
            是否成功
        """
        if proxy_id in self.proxies:
            del self.proxies[proxy_id]
            log.info(f"移除代理: {proxy_id}")
            return True
        return False
    
    def mark_proxy_invalid(self, proxy_id: str):
        """
        标记代理为失效
        
        Args:
            proxy_id: 代理 ID
        """
        if proxy_id in self.proxies:
            self.proxies[proxy_id].is_valid = False
            log.info(f"标记代理失效: {proxy_id}")
    
    def get_stats(self) -> ProxyStatsModel:
        """
        获取代理池统计信息
        
        Returns:
            统计信息
        """
        all_proxies = self.get_all_proxies()
        valid_proxies = self.get_valid_proxies()
        
        avg_speed = None
        if valid_proxies:
            speeds = [p.speed for p in valid_proxies if p.speed]
            avg_speed = sum(speeds) / len(speeds) if speeds else None
        
        return ProxyStatsModel(
            total_proxies=len(all_proxies),
            valid_proxies=len(valid_proxies),
            invalid_proxies=len(all_proxies) - len(valid_proxies),
            last_update=self.last_update,
            avg_speed=avg_speed,
        )


# 全局代理池实例
proxy_pool = ProxyPool()
