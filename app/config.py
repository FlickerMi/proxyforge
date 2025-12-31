"""配置管理模块"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # 代理池配置
    proxy_pool_size: int = 100
    proxy_update_interval: int = 3600  # 秒
    proxy_validation_timeout: int = 10  # 秒
    proxy_validation_url: str = "https://httpbin.org/ip"
    
    # 请求配置
    request_timeout: int = 30  # 秒
    request_max_retries: int = 3  # 已弃用,保留向后兼容
    request_max_retries_per_proxy: int = 3  # 单个代理重试次数
    request_max_proxy_switches: int = 5  # 最大切换代理次数
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/proxyforge.log"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 全局配置实例
settings = Settings()
