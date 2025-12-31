"""代理获取模块 - 集成 pyfreeproxy"""

import asyncio
from typing import List, Set
from freeproxy.modules import BuildProxiedSession, ProxyInfo
from app.models import ProxyModel, ProxyProtocol
from app.utils import log


class ProxyFetcher:
    """代理获取器"""
    
    # 支持的代理源
    PROXY_SOURCES = [
        # 'ProxiflyProxiedSession', 
        # 'FreeproxylistProxiedSession', 
        'IhuanProxiedSession', 
        'IP89ProxiedSession', 
        'IP3366ProxiedSession', 
        'KuaidailiProxiedSession', 
        'KxdailiProxiedSession', 
        # 'ProxydailyProxiedSession', 
        'ProxydbProxiedSession', 
        'ProxyhubProxiedSession', 
        'ProxylistProxiedSession', 
        'QiyunipProxiedSession', 
        # 'SpysoneProxiedSession', 
        'Tomcat1235ProxiedSession', 
        # 'DatabayProxiedSession', 
        # 'FineProxyProxiedSession', 
        'IPLocateProxiedSession', 
        'JiliuipProxiedSession', 
        'TheSpeedXProxiedSession', 
        'GeonodeProxiedSession', 
        'FreeProxyDBProxiedSession', 
        'ProxyScrapeProxiedSession'
    ]
    
    def __init__(self):
        self.fetched_proxies: Set[str] = set()
        self._source_index = 0  # 用于轮换代理源
    
    async def fetch_proxies(self, count: int = 50) -> List[ProxyModel]:
        """
        获取代理列表
        
        Args:
            count: 需要获取的代理数量
            
        Returns:
            代理列表
        """
        log.info(f"开始获取代理,目标数量: {count}")
        proxies = []
        
        try:
            # 使用线程池执行同步的 pyfreeproxy 调用
            loop = asyncio.get_event_loop()
            
            # 计算需要使用的代理源数量（最多使用5个源，但会轮换）
            sources_to_use = min(5, len(self.PROXY_SOURCES))
            
            # 使用轮换策略选择代理源
            selected_sources = []
            for i in range(sources_to_use):
                source_idx = (self._source_index + i) % len(self.PROXY_SOURCES)
                selected_sources.append(self.PROXY_SOURCES[source_idx])
            
            # 更新索引，下次从不同位置开始
            self._source_index = (self._source_index + sources_to_use) % len(self.PROXY_SOURCES)
            
            log.info(f"本次使用代理源: {', '.join(selected_sources)}")
            
            # 从选中的源获取代理
            for source in selected_sources:
                try:
                    source_proxies = await loop.run_in_executor(
                        None,
                        self._fetch_from_source,
                        source
                    )
                    proxies.extend(source_proxies)
                    
                    if len(proxies) >= count:
                        break
                        
                except Exception as e:
                    log.warning(f"从 {source} 获取代理失败: {e}")
                    continue
            
            # 去重并限制数量
            unique_proxies = []
            seen = set()
            for proxy in proxies:
                if proxy.proxy_url not in seen:
                    seen.add(proxy.proxy_url)
                    unique_proxies.append(proxy)
                    if len(unique_proxies) >= count:
                        break
            
            log.info(f"成功获取 {len(unique_proxies)} 个代理")
            return unique_proxies
            
        except Exception as e:
            log.error(f"获取代理失败: {e}")
            return []
    
    def _fetch_from_source(self, source: str) -> List[ProxyModel]:
        """
        从指定源获取代理
        
        Args:
            source: 代理源名称
            
        Returns:
            代理列表
        """
        proxies = []
        
        try:
            log.info(f"从 {source} 获取代理...")
            
            # 创建代理会话
            session = BuildProxiedSession({
                "max_pages": 1,  # 每个源只抓取1页
                "type": source,
                "disable_print": True,  # 禁用打印
            })
            
            # 获取代理列表
            proxy_infos: List[ProxyInfo] = session.refreshproxies()
            
            # 转换为 ProxyModel
            for proxy_info in proxy_infos:
                try:
                    proxy = self._convert_proxy_info(proxy_info, source)
                    if proxy:
                        proxies.append(proxy)
                except Exception as e:
                    log.debug(f"转换代理失败: {e}")
                    continue
            
            log.info(f"从 {source} 获取到 {len(proxies)} 个代理")
            
        except Exception as e:
            log.error(f"从 {source} 获取代理异常: {e}")
        
        return proxies
    
    def _convert_proxy_info(self, proxy_info: ProxyInfo, source: str) -> ProxyModel:
        """
        将 ProxyInfo 转换为 ProxyModel
        
        Args:
            proxy_info: pyfreeproxy 的 ProxyInfo 对象
            source: 代理来源
            
        Returns:
            ProxyModel
        """
        try:
            # 解析协议
            protocol_str = proxy_info.protocol.lower()
            if protocol_str == "http":
                protocol = ProxyProtocol.HTTP
            elif protocol_str == "https":
                protocol = ProxyProtocol.HTTPS
            elif protocol_str == "socks4":
                protocol = ProxyProtocol.SOCKS4
            elif protocol_str == "socks5":
                protocol = ProxyProtocol.SOCKS5
            else:
                protocol = ProxyProtocol.HTTP
            
            # 创建代理模型
            proxy = ProxyModel(
                host=proxy_info.ip,
                port=int(proxy_info.port),
                protocol=protocol,
                country=proxy_info.country_code,
                anonymity=proxy_info.anonymity,
                speed=proxy_info.delay / 1000.0 if proxy_info.delay else None,  # 转换为秒
                source=source,  # 设置代理来源
            )
            
            return proxy
            
        except Exception as e:
            log.error(f"转换 ProxyInfo 失败: {e}")
            return None
