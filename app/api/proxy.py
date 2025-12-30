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
