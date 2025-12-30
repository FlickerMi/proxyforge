# ProxyForge 代理池策略配置指南

## 🎯 策略选择

ProxyForge 现在使用**混合策略**,这是生产环境的最佳实践。

### 当前策略:快速启动 + 后台补充 ⭐ (推荐)

```
启动阶段 (极速):
  1. 快速获取 10 个有效代理 (约 3-5 秒)
  2. 获取 50 个原始代理,验证得到 10+ 个有效代理
  3. 服务立即可用 ✓
  
后台阶段:
  4. 等待 2 秒,确保服务稳定
  5. 后台持续补充到 100 个代理
  6. 定时更新(默认每小时)
```

**优势**:
- ✅ 启动极快(3-5秒即可使用)
- ✅ 用户体验好(不需要等待)
- ✅ 代理数量充足(后台补充到目标)
- ✅ 持续更新(保持代理池新鲜)

---

## 📊 不同场景的配置建议

### 1. 开发/测试环境

**目标**: 快速启动,资源占用少

```env
# .env 配置
PROXY_POOL_SIZE=20              # 小池子即可
PROXY_UPDATE_INTERVAL=7200      # 2小时更新一次
PROXY_VALIDATION_TIMEOUT=5      # 快速验证
```

**特点**:
- 启动时间: ~5 秒
- 内存占用: 低
- 适合: 本地开发、功能测试

---

### 2. 生产环境 - 低流量

**目标**: 平衡性能和资源

```env
# .env 配置
PROXY_POOL_SIZE=50              # 中等池子
PROXY_UPDATE_INTERVAL=3600      # 1小时更新
PROXY_VALIDATION_TIMEOUT=10     # 标准验证
```

**特点**:
- 启动时间: ~10 秒
- 代理数量: 50 个
- 适合: 小型应用、个人项目

---

### 3. 生产环境 - 高流量 ⭐

**目标**: 高可用性,充足代理

```env
# .env 配置
PROXY_POOL_SIZE=200             # 大池子
PROXY_UPDATE_INTERVAL=1800      # 30分钟更新
PROXY_VALIDATION_TIMEOUT=10     # 标准验证
REQUEST_MAX_RETRIES=5           # 增加重试次数
```

**特点**:
- 启动时间: ~10 秒(快速启动30个)
- 最终代理: 200 个(后台补充)
- 适合: 高并发应用、爬虫服务

---

### 4. 极速模式(仅快速启动)

如果你只想快速启动,不需要大量代理:

**修改代码** (`app/core/proxy_pool.py`):

```python
async def start(self):
    """启动代理池"""
    log.info("启动代理池管理器")
    
    # 极速模式:只获取少量代理,不后台补充
    quick_start_count = 10  # 只要10个代理
    await self.update_pool(target_count=quick_start_count, max_attempts=1)
    
    # 启动定时更新(不补充到目标数量)
    self._update_task = asyncio.create_task(self._periodic_update())

async def _periodic_update(self):
    """定时更新,但不补充到目标数量"""
    while True:
        try:
            await asyncio.sleep(self.update_interval)
            # 只更新现有代理,不增加数量
            await self.update_pool(target_count=10, max_attempts=1)
        except asyncio.CancelledError:
            break
```

---

## 🔧 高级配置

### 调整快速启动数量

编辑 `app/core/proxy_pool.py` 第 32 行:

```python
# 默认: 10 个有效代理 (推荐,启动最快)
quick_start_count = 10

# 更多代理: 20 个有效代理 (稍慢但更稳定)
quick_start_count = 20

# 极速模式: 5 个有效代理 (最快启动)
quick_start_count = 5
```

### 调整后台补充延迟

编辑 `app/core/proxy_pool.py` 第 42 行:

```python
# 默认: 等待 2 秒
await asyncio.sleep(2)

# 立即补充: 0 秒
await asyncio.sleep(0)

# 延迟补充: 10 秒
await asyncio.sleep(10)
```

---

## 📈 性能对比

| 策略 | 启动时间 | 初始代理数 | 最终代理数 | 内存占用 | 适用场景 |
|------|---------|-----------|-----------|---------|---------|
| **混合策略(当前)** | 3-5秒 | 10 | 100 | 中 | ⭐ 生产推荐 |
| 全量启动 | 60-120秒 | 100 | 100 | 中 | 对启动时间不敏感 |
| 按需获取 | 2-5秒 | 10 | 10-50 | 低 | 开发测试 |
| 极速模式 | 2-3秒 | 5 | 5 | 低 | 快速演示 |

---

## 💡 最佳实践建议

### 1. 生产环境配置

```env
# 推荐配置
PROXY_POOL_SIZE=100
PROXY_UPDATE_INTERVAL=3600
PROXY_VALIDATION_TIMEOUT=10
REQUEST_MAX_RETRIES=3
```

**原因**:
- 100个代理足够应对大部分场景
- 1小时更新保持代理新鲜度
- 快速启动不影响用户体验

### 2. 监控代理池状态

定期检查代理池健康度:

```bash
# 查看代理池统计
curl http://localhost:8000/api/proxy/stats

# 预期输出
{
  "total_proxies": 100,
  "valid_proxies": 95,
  "invalid_proxies": 5,
  "avg_speed": 3.5
}
```

**告警阈值**:
- `valid_proxies < 20`: 需要手动更新
- `avg_speed > 10`: 代理质量差,考虑增加验证频率

### 3. 手动触发更新

如果发现代理不足:

```bash
# 手动更新代理池
curl -X POST http://localhost:8000/api/proxy/update
```

---

## 🎓 总结

**对于大多数场景,当前的混合策略是最佳选择**:

✅ **快速启动**: 5-10秒即可使用  
✅ **后台补充**: 不影响用户体验  
✅ **持续更新**: 保持代理池健康  
✅ **灵活配置**: 可根据需求调整

**特殊场景**:
- 开发测试: 减小 `PROXY_POOL_SIZE` 到 20
- 高并发: 增大 `PROXY_POOL_SIZE` 到 200
- 资源受限: 使用极速模式

根据实际使用情况调整配置,找到最适合你的平衡点!
