# ProxyForge 错误日志说明

## 📋 错误日志格式

ProxyForge 现在提供详细的错误日志,帮助你快速定位问题。

---

## 🔍 错误类型

### 1. 超时错误 (TimeoutException)

**日志示例:**
```
✗ 第 1/3 次请求失败 [超时]
   URL: https://data.similarweb.com/api/v1/data?domain=google.com
   代理: http://123.45.67.89:8080
   错误: Read timeout
```

**原因:**
- 代理响应太慢
- 目标服务器响应慢
- 网络不稳定

**解决方案:**
- 增加 `timeout` 参数值
- 等待自动重试(会切换代理)

---

### 2. 连接错误 (ConnectError)

**日志示例:**
```
✗ 第 1/3 次请求失败 [连接错误]
   URL: https://data.similarweb.com/api/v1/data?domain=google.com
   代理: http://123.45.67.89:8080
   错误: Connection refused
```

**原因:**
- 代理服务器不可用
- 代理端口关闭
- 网络连接问题

**解决方案:**
- 自动切换到下一个代理
- 检查网络连接

---

### 3. 代理错误 (ProxyError)

**日志示例:**
```
✗ 第 1/3 次请求失败 [代理错误]
   URL: https://data.similarweb.com/api/v1/data?domain=google.com
   代理: http://123.45.67.89:8080
   错误: Proxy tunnel failed
```

**原因:**
- 代理服务器配置错误
- 代理需要认证但未提供
- 代理不支持目标协议

**解决方案:**
- 自动切换代理
- 检查代理配置

---

### 4. HTTP 状态错误 (HTTPStatusError)

**日志示例:**
```
✗ 第 1/3 次请求失败 [HTTP错误]
   URL: https://data.similarweb.com/api/v1/data?domain=google.com
   代理: http://123.45.67.89:8080
   状态码: 403
   错误: Forbidden
```

**常见状态码:**
- `403 Forbidden`: 被目标服务器拒绝(可能检测到代理)
- `429 Too Many Requests`: 请求过于频繁
- `500 Internal Server Error`: 服务器内部错误
- `502 Bad Gateway`: 代理网关错误
- `503 Service Unavailable`: 服务不可用

**解决方案:**
- `403`: 切换代理,添加更真实的 headers
- `429`: 降低请求频率
- `5xx`: 等待后重试

---

### 5. 其他错误

**日志示例:**
```
✗ 第 1/3 次请求失败 [SSLError]
   URL: https://data.similarweb.com/api/v1/data?domain=google.com
   代理: http://123.45.67.89:8080
   错误: SSL handshake failed
```

---

## ✅ 成功日志

**日志示例:**
```
✓ 请求成功: https://data.similarweb.com/api/v1/data?domain=google.com
  状态码: 200
  代理: http://123.45.67.89:8080
```

---

## ❌ 最终失败日志

当所有重试都失败时:

```
❌ 所有重试均失败
   URL: https://data.similarweb.com/api/v1/data?domain=google.com
   尝试次数: 3
   错误类型: 超时
   错误信息: Read timeout
```

---

## 📊 完整请求流程日志示例

### 场景 1: 第一次成功

```
2025-12-30 14:00:00 | INFO | 使用代理发送请求: http://123.45.67.89:8080 -> https://data.similarweb.com/api/v1/data?domain=google.com
2025-12-30 14:00:02 | INFO | ✓ 请求成功: https://data.similarweb.com/api/v1/data?domain=google.com, 状态码: 200, 代理: http://123.45.67.89:8080
```

### 场景 2: 第一次失败,第二次成功

```
2025-12-30 14:00:00 | INFO | 使用代理发送请求: http://123.45.67.89:8080 -> https://data.similarweb.com/api/v1/data?domain=google.com
2025-12-30 14:00:10 | WARNING | ✗ 第 1/3 次请求失败 [超时]
   URL: https://data.similarweb.com/api/v1/data?domain=google.com
   代理: http://123.45.67.89:8080
   错误: Read timeout
2025-12-30 14:00:10 | DEBUG | 已标记代理失效: http://123.45.67.89:8080
2025-12-30 14:00:10 | INFO | 使用代理发送请求: http://98.76.54.32:3128 -> https://data.similarweb.com/api/v1/data?domain=google.com
2025-12-30 14:00:12 | INFO | ✓ 请求成功: https://data.similarweb.com/api/v1/data?domain=google.com, 状态码: 200, 代理: http://98.76.54.32:3128
```

### 场景 3: 所有重试都失败

```
2025-12-30 14:00:00 | INFO | 使用代理发送请求: http://123.45.67.89:8080 -> https://data.similarweb.com/api/v1/data?domain=google.com
2025-12-30 14:00:10 | WARNING | ✗ 第 1/3 次请求失败 [超时]
   URL: https://data.similarweb.com/api/v1/data?domain=google.com
   代理: http://123.45.67.89:8080
   错误: Read timeout
2025-12-30 14:00:10 | DEBUG | 已标记代理失效: http://123.45.67.89:8080

2025-12-30 14:00:10 | INFO | 使用代理发送请求: http://98.76.54.32:3128 -> https://data.similarweb.com/api/v1/data?domain=google.com
2025-12-30 14:00:20 | WARNING | ✗ 第 2/3 次请求失败 [连接错误]
   URL: https://data.similarweb.com/api/v1/data?domain=google.com
   代理: http://98.76.54.32:3128
   错误: Connection refused
2025-12-30 14:00:20 | DEBUG | 已标记代理失效: http://98.76.54.32:3128

2025-12-30 14:00:20 | INFO | 使用代理发送请求: http://11.22.33.44:8888 -> https://data.similarweb.com/api/v1/data?domain=google.com
2025-12-30 14:00:25 | WARNING | ✗ 第 3/3 次请求失败 [HTTP错误]
   URL: https://data.similarweb.com/api/v1/data?domain=google.com
   代理: http://11.22.33.44:8888
   状态码: 403
   错误: Forbidden
2025-12-30 14:00:25 | DEBUG | 已标记代理失效: http://11.22.33.44:8888

2025-12-30 14:00:25 | ERROR | ❌ 所有重试均失败
   URL: https://data.similarweb.com/api/v1/data?domain=google.com
   尝试次数: 3
   错误类型: HTTP状态错误
   错误信息: Forbidden
   最后状态码: 403
```

---

## 🛠️ 调试技巧

### 1. 查看实时日志

```bash
# 启动服务时查看日志
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 或查看日志文件
tail -f logs/proxyforge.log
```

### 2. 调整日志级别

编辑 `.env`:

```env
# 查看更详细的日志(包括 DEBUG)
LOG_LEVEL=DEBUG

# 只看重要信息
LOG_LEVEL=INFO

# 只看错误
LOG_LEVEL=ERROR
```

### 3. 根据错误类型优化

| 错误类型 | 优化建议 |
|---------|---------|
| 超时 | 增加 `timeout` 或 `PROXY_VALIDATION_TIMEOUT` |
| 连接错误 | 增加代理池大小 `PROXY_POOL_SIZE` |
| HTTP 403 | 改进 headers,使其更像真实浏览器 |
| HTTP 429 | 降低请求频率,增加延迟 |

---

## 💡 最佳实践

1. **合理设置重试次数**
   ```json
   {
     "max_retries": 3  // 推荐 3-5 次
   }
   ```

2. **设置合适的超时**
   ```json
   {
     "timeout": 30  // 根据目标网站调整
   }
   ```

3. **监控错误率**
   - 如果错误率 > 50%,考虑增加代理池大小
   - 如果频繁出现 403,检查 headers 配置

4. **定期查看日志**
   ```bash
   # 查看最近的错误
   grep "ERROR" logs/proxyforge.log | tail -20
   
   # 统计错误类型
   grep "请求失败" logs/proxyforge.log | grep -oP '\[.*?\]' | sort | uniq -c
   ```

---

## 📞 常见问题

### Q: 为什么总是超时?

A: 可能原因:
1. 免费代理质量差 → 增加 `PROXY_POOL_SIZE`
2. 超时设置太短 → 增加 `timeout` 参数
3. 目标网站响应慢 → 这是正常的,等待重试

### Q: 为什么总是 403?

A: 可能原因:
1. Headers 不够真实 → 参考浏览器的完整 headers
2. 代理被识别 → 使用更高质量的代理
3. IP 被封禁 → 切换代理或降低请求频率

### Q: 如何提高成功率?

A: 建议:
1. 增加代理池大小: `PROXY_POOL_SIZE=200`
2. 增加重试次数: `max_retries: 5`
3. 使用完整的浏览器 headers
4. 降低请求频率

---

## 🎯 总结

ProxyForge 的详细错误日志帮助你:

✅ 快速定位问题  
✅ 了解失败原因  
✅ 优化配置参数  
✅ 提高请求成功率  

查看日志文件: `logs/proxyforge.log`
