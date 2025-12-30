# 状态码过滤功能使用示例

## 功能说明

ProxyForge 现在支持配置哪些 HTTP 状态码应该触发代理切换和重试。

## 默认行为

**默认情况下,不会基于状态码进行重试判断。**

只有当你明确指定 `retry_on_status_codes` 参数时,才会在遇到指定状态码时切换代理重试。

### 推荐配置

对于需要状态码过滤的场景,推荐使用以下配置:
- **403** - Forbidden (被拒绝,可能代理被识别)
- **429** - Too Many Requests (请求过于频繁)
- **502** - Bad Gateway (网关错误)
- **503** - Service Unavailable (服务不可用)

## 使用示例

### 示例 1: 不进行状态码判断 (默认)

```bash
curl -X POST http://localhost:8000/api/request \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/api",
    "method": "GET"
  }'
```

默认不会基于状态码重试,只在连接失败、超时等异常时重试。

---

### 示例 2: 启用状态码重试 - 只在 403 时重试

```bash
curl -X POST http://localhost:8000/api/request \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/api",
    "method": "GET",
    "retry_on_status_codes": [403]
  }'
```

---

### 示例 3: 多个状态码

在 403, 429, 500, 502, 503 时重试:

```bash
curl -X POST http://localhost:8000/api/request \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/api",
    "method": "GET",
    "retry_on_status_codes": [403, 429, 500, 502, 503]
  }'
```

---

### 示例 4: Python 示例

```python
import requests

payload = {
    "url": "https://data.similarweb.com/api/v1/data?domain=google.com",
    "method": "GET",
    "headers": {
        "User-Agent": "Mozilla/5.0...",
        "Origin": "https://www.similarweb.com",
        "Referer": "https://www.similarweb.com/website/google.com/"
    },
    # 自定义重试状态码
    "retry_on_status_codes": [403, 429],
    "max_retries": 5
}

response = requests.post("http://localhost:8000/api/request", json=payload)
result = response.json()

if result['success']:
    print("成功!", result['data']['status_code'])
else:
    print("失败:", result['message'])
```

---

## 日志示例

### 遇到需要重试的状态码

```
2025-12-30 16:00:00 | INFO | 使用代理发送请求: http://123.45.67.89:8080 -> https://example.com/api
2025-12-30 16:00:02 | WARNING | ✗ 第 1/3 次请求失败 [状态码需要重试]
   URL: https://example.com/api
   代理: http://123.45.67.89:8080
   状态码: 403
   说明: 该状态码在重试列表中 [403, 429, 502, 503]
2025-12-30 16:00:02 | DEBUG | 已标记代理失效: http://123.45.67.89:8080

2025-12-30 16:00:02 | INFO | 使用代理发送请求: http://98.76.54.32:3128 -> https://example.com/api
2025-12-30 16:00:04 | INFO | ✓ 请求成功: https://example.com/api, 状态码: 200, 代理: http://98.76.54.32:3128
```

---

## 常见状态码说明

| 状态码 | 含义 | 是否建议重试 | 说明 |
|--------|------|-------------|------|
| **403** | Forbidden | ✅ 是 | 可能是代理被识别,换代理通常能解决 |
| **429** | Too Many Requests | ✅ 是 | 请求过于频繁,换代理可以绕过限制 |
| **500** | Internal Server Error | ⚠️ 可选 | 服务器错误,重试可能有用 |
| **502** | Bad Gateway | ✅ 是 | 网关错误,通常是代理问题 |
| **503** | Service Unavailable | ✅ 是 | 服务不可用,可能是临时问题 |
| **401** | Unauthorized | ❌ 否 | 认证问题,换代理无用 |
| **404** | Not Found | ❌ 否 | 资源不存在,换代理无用 |
| **200** | OK | ❌ 否 | 成功,不需要重试 |

---

## 最佳实践

### 1. 针对不同网站调整

```python
# 对于严格的网站
"retry_on_status_codes": [403, 429, 502, 503]

# 对于一般网站
"retry_on_status_codes": [403, 502, 503]

# 对于宽松的网站
"retry_on_status_codes": [502, 503]
```

### 2. 配合重试次数

```python
{
    "retry_on_status_codes": [403, 429],
    "max_retries": 5  # 增加重试次数
}
```

### 3. 监控日志

观察哪些状态码频繁出现,调整配置:

```bash
# 查看状态码分布
grep "状态码:" logs/proxyforge.log | grep -oP '\d{3}' | sort | uniq -c
```

---

## 完整示例: SimilarWeb API

```json
{
  "url": "https://data.similarweb.com/api/v1/data?domain=google.com",
  "method": "GET",
  "headers": {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Origin": "https://www.similarweb.com",
    "Referer": "https://www.similarweb.com/website/google.com/"
  },
  "timeout": 30,
  "max_retries": 5,
  "retry_on_status_codes": [403, 429, 502, 503]
}
```

---

## 注意事项

1. **状态码 vs 异常**: 
   - 状态码重试: 服务器返回了响应,但状态码不理想
   - 异常重试: 连接失败、超时等,总是会重试

2. **重试次数**: 
   - 每次重试都会切换代理
   - 建议设置 `max_retries` 为 3-5

3. **性能考虑**:
   - 过多的重试状态码会增加请求时间
   - 根据实际情况调整

4. **默认行为**:
   - 默认: 不进行状态码判断 (`None`)
   - 启用: 明确指定状态码列表,如 `[403, 429]`
   - 空数组 `[]`: 也表示不判断
