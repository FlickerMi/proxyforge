"""代理查询 API"""

from fastapi import APIRouter, HTTPException
from typing import List
from app.models import ProxyModel, ProxyStatsModel, ApiResponse
from app.core.proxy_pool import proxy_pool
from app.utils import log

router = APIRouter(prefix="/api/proxy", tags=["代理管理"])


@router.get("/list", response_model=ApiResponse, summary="获取代理列表")
async def get_proxy_list(
    valid_only: bool = True,
    limit: int = 100
) -> ApiResponse:
    """
    获取代理列表
    
    Args:
        valid_only: 是否只返回有效代理
        limit: 返回数量限制
        
    Returns:
        代理列表
    """
    try:
        if valid_only:
            proxies = proxy_pool.get_valid_proxies()
        else:
            proxies = proxy_pool.get_all_proxies()
        
        # 限制返回数量
        proxies = proxies[:limit]
        
        return ApiResponse(
            success=True,
            message=f"获取到 {len(proxies)} 个代理",
            data=[proxy.model_dump() for proxy in proxies]
        )
    except Exception as e:
        log.error(f"获取代理列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/random", response_model=ApiResponse, summary="获取随机代理")
async def get_random_proxy() -> ApiResponse:
    """
    获取随机代理(速度最快的)
    
    Returns:
        代理信息
    """
    try:
        proxy = proxy_pool.get_random_proxy()
        
        if not proxy:
            return ApiResponse(
                success=False,
                message="没有可用代理",
                data=None
            )
        
        return ApiResponse(
            success=True,
            message="获取代理成功",
            data=proxy.model_dump()
        )
    except Exception as e:
        log.error(f"获取随机代理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=ApiResponse, summary="获取代理池统计")
async def get_proxy_stats() -> ApiResponse:
    """
    获取代理池统计信息
    
    Returns:
        统计信息
    """
    try:
        stats = proxy_pool.get_stats()
        
        return ApiResponse(
            success=True,
            message="获取统计信息成功",
            data=stats.model_dump()
        )
    except Exception as e:
        log.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{proxy_id}", response_model=ApiResponse, summary="删除代理")
async def delete_proxy(proxy_id: str) -> ApiResponse:
    """
    删除指定代理
    
    Args:
        proxy_id: 代理 ID
        
    Returns:
        操作结果
    """
    try:
        success = proxy_pool.remove_proxy(proxy_id)
        
        if success:
            return ApiResponse(
                success=True,
                message=f"删除代理成功: {proxy_id}",
                data=None
            )
        else:
            return ApiResponse(
                success=False,
                message=f"代理不存在: {proxy_id}",
                data=None
            )
    except Exception as e:
        log.error(f"删除代理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update", response_model=ApiResponse, summary="手动更新代理池")
async def update_proxy_pool() -> ApiResponse:
    """
    手动触发代理池更新
    
    Returns:
        操作结果
    """
    try:
        await proxy_pool.update_pool()
        stats = proxy_pool.get_stats()
        
        return ApiResponse(
            success=True,
            message="代理池更新成功",
            data=stats.model_dump()
        )
    except Exception as e:
        log.error(f"更新代理池失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-sources", response_model=ApiResponse, summary="测试所有代理源")
async def test_proxy_sources() -> ApiResponse:
    """
    测试所有配置的代理源,返回每个源能获取到的代理数量
    
    Returns:
        每个代理源及其获取到的代理数量
        
    Example Response:
        {
            "success": true,
            "message": "测试完成,共测试 23 个代理源",
            "data": {
                "sources": [
                    {"source": "IhuanProxiedSession", "count": 15, "status": "success"},
                    {"source": "IP89ProxiedSession", "count": 0, "status": "failed", "error": "连接超时"},
                    ...
                ],
                "total_sources": 23,
                "successful_sources": 18,
                "total_proxies": 234
            }
        }
    """
    try:
        from app.core.proxy_fetcher import ProxyFetcher
        import asyncio
        
        log.info("开始测试所有代理源...")
        fetcher = ProxyFetcher()
        
        results = []
        total_proxies = 0
        successful_sources = 0
        
        # 测试每个代理源
        for source in fetcher.PROXY_SOURCES:
            try:
                log.info(f"测试代理源: {source}")
                
                # 使用线程池执行同步调用
                loop = asyncio.get_event_loop()
                proxies = await loop.run_in_executor(
                    None,
                    fetcher._fetch_from_source,
                    source
                )
                
                count = len(proxies)
                total_proxies += count
                
                if count > 0:
                    successful_sources += 1
                    results.append({
                        "source": source,
                        "count": count,
                        "status": "success"
                    })
                    log.info(f"✓ {source}: 获取到 {count} 个代理")
                else:
                    results.append({
                        "source": source,
                        "count": 0,
                        "status": "no_proxies"
                    })
                    log.warning(f"✗ {source}: 未获取到代理")
                    
            except Exception as e:
                results.append({
                    "source": source,
                    "count": 0,
                    "status": "failed",
                    "error": str(e)
                })
                log.error(f"✗ {source}: 测试失败 - {e}")
        
        # 按获取数量降序排序
        results.sort(key=lambda x: x["count"], reverse=True)
        
        return ApiResponse(
            success=True,
            message=f"测试完成,共测试 {len(fetcher.PROXY_SOURCES)} 个代理源",
            data={
                "sources": results,
                "total_sources": len(fetcher.PROXY_SOURCES),
                "successful_sources": successful_sources,
                "total_proxies": total_proxies
            }
        )
        
    except Exception as e:
        log.error(f"测试代理源失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
