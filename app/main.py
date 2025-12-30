"""FastAPI 应用主入口"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.proxy_pool import proxy_pool
from app.api import proxy, request
from app.utils import log
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    log.info("ProxyForge 启动中...")
    await proxy_pool.start()
    log.info("ProxyForge 启动完成")
    
    yield
    
    # 关闭时
    log.info("ProxyForge 关闭中...")
    await proxy_pool.stop()
    log.info("ProxyForge 已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="ProxyForge",
    description="基于 FastAPI 和 freeproxy 的代理服务",
    version="0.1.0",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(proxy.router)
app.include_router(request.router)


@app.get("/", tags=["根路径"])
async def root():
    """根路径"""
    return {
        "name": "ProxyForge",
        "version": "0.1.0",
        "description": "代理服务 API",
        "docs": "/docs",
    }


@app.get("/health", tags=["健康检查"])
async def health():
    """健康检查"""
    stats = proxy_pool.get_stats()
    return {
        "status": "healthy",
        "proxy_pool": stats.model_dump(),
    }


def main():
    """主函数"""
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
