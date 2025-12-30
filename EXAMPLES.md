# ProxyForge 使用示例 - SimilarWeb API

## 示例 1: 使用 curl 命令

### 基础请求

```bash
curl -X POST http://localhost:8000/api/request \
  -H "Content-Type: application/json" \
  -d @example_similarweb.json
```

### 完整命令(单行)

```bash
curl -X POST http://localhost:8000/api/request -H "Content-Type: application/json" -d "{\"url\":\"https://data.similarweb.com/api/v1/data?domain=google.com\",\"method\":\"GET\",\"headers\":{\"Accept\":\"application/json, text/plain, */*\",\"Accept-Language\":\"zh-CN,zh;q=0.9,en;q=0.8\",\"Accept-Encoding\":\"gzip, deflate, br\",\"Cache-Control\":\"no-cache\",\"Pragma\":\"no-cache\",\"User-Agent\":\"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0\",\"sec-ch-ua\":\"\\\"Not/A)Brand\\\";v=\\\"8\\\", \\\"Chromium\\\";v=\\\"126\\\", \\\"Google Chrome\\\";v=\\\"126\\\"\",\"sec-ch-ua-mobile\":\"?0\",\"sec-ch-ua-platform\":\"\\\"macOS\\\"\",\"Sec-Fetch-Dest\":\"empty\",\"Sec-Fetch-Mode\":\"cors\",\"Sec-Fetch-Site\":\"same-site\",\"Origin\":\"https://www.similarweb.com\",\"Referer\":\"https://www.similarweb.com/website/google.com/\"},\"timeout\":30,\"max_retries\":3}"
```

---

## 示例 2: 使用 Python requests

```python
import requests
import json

# ProxyForge API 地址
PROXYFORGE_URL = "http://localhost:8000/api/request"

# 构造请求数据
payload = {
    "url": "https://data.similarweb.com/api/v1/data?domain=google.com",
    "method": "GET",
    "headers": {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Origin": "https://www.similarweb.com",
        "Referer": "https://www.similarweb.com/website/google.com/"
    },
    "timeout": 30,
    "max_retries": 3
}

# 发送请求到 ProxyForge
response = requests.post(PROXYFORGE_URL, json=payload)

# 解析响应
if response.status_code == 200:
    result = response.json()
    
    if result['success']:
        data = result['data']
        print(f"✓ 请求成功!")
        print(f"状态码: {data['status_code']}")
        print(f"使用代理: {data['proxy_used']}")
        print(f"耗时: {data['elapsed']}秒")
        print(f"\n响应内容:")
        print(data['content'])
    else:
        print(f"✗ 请求失败: {result['message']}")
else:
    print(f"✗ API 调用失败: {response.status_code}")
```

---

## 示例 3: 使用 JavaScript/Node.js

```javascript
const fetch = require('node-fetch');

async function fetchViaSimilarWeb(domain) {
    const proxyforgeUrl = 'http://localhost:8000/api/request';
    
    const payload = {
        url: `https://data.similarweb.com/api/v1/data?domain=${domain}`,
        method: 'GET',
        headers: {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0',
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Origin': 'https://www.similarweb.com',
            'Referer': `https://www.similarweb.com/website/${domain}/`
        },
        timeout: 30,
        max_retries: 3
    };
    
    try {
        const response = await fetch(proxyforgeUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('✓ 请求成功!');
            console.log('状态码:', result.data.status_code);
            console.log('使用代理:', result.data.proxy_used);
            console.log('耗时:', result.data.elapsed, '秒');
            console.log('\n响应内容:');
            console.log(result.data.content);
            
            // 解析 JSON 响应
            const data = JSON.parse(result.data.content);
            return data;
        } else {
            console.error('✗ 请求失败:', result.message);
            return null;
        }
    } catch (error) {
        console.error('✗ 错误:', error.message);
        return null;
    }
}

// 使用示例
fetchViaSimilarWeb('google.com')
    .then(data => {
        if (data) {
            console.log('\n解析后的数据:', data);
        }
    });
```

---

## 示例 4: 批量查询多个域名

```python
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

PROXYFORGE_URL = "http://localhost:8000/api/request"

def fetch_domain_data(domain):
    """通过 ProxyForge 获取域名数据"""
    payload = {
        "url": f"https://data.similarweb.com/api/v1/data?domain={domain}",
        "method": "GET",
        "headers": {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "Origin": "https://www.similarweb.com",
            "Referer": f"https://www.similarweb.com/website/{domain}/"
        },
        "timeout": 30,
        "max_retries": 3
    }
    
    try:
        response = requests.post(PROXYFORGE_URL, json=payload, timeout=60)
        result = response.json()
        
        if result['success']:
            return {
                'domain': domain,
                'success': True,
                'data': json.loads(result['data']['content']),
                'proxy': result['data']['proxy_used']
            }
        else:
            return {
                'domain': domain,
                'success': False,
                'error': result['message']
            }
    except Exception as e:
        return {
            'domain': domain,
            'success': False,
            'error': str(e)
        }

# 批量查询
domains = ['google.com', 'facebook.com', 'twitter.com', 'youtube.com']

print(f"开始批量查询 {len(domains)} 个域名...\n")

# 使用线程池并发请求
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(fetch_domain_data, domain): domain for domain in domains}
    
    for future in as_completed(futures):
        result = future.result()
        
        if result['success']:
            print(f"✓ {result['domain']}")
            print(f"  代理: {result['proxy']}")
            print(f"  数据: {result['data']}\n")
        else:
            print(f"✗ {result['domain']}")
            print(f"  错误: {result['error']}\n")
```

---

## 响应示例

成功响应:

```json
{
  "success": true,
  "message": "请求成功",
  "data": {
    "status_code": 200,
    "headers": {
      "content-type": "application/json",
      "date": "Mon, 30 Dec 2024 05:50:00 GMT"
    },
    "content": "{\"domain\":\"google.com\",\"rank\":1,\"traffic\":...}",
    "encoding": "utf-8",
    "elapsed": 2.345,
    "proxy_used": "http://123.45.67.89:8080"
  }
}
```

失败响应:

```json
{
  "detail": "请求失败,已重试 3 次: Connection timeout"
}
```

---

## 注意事项

1. **超时设置**: SimilarWeb API 可能响应较慢,建议设置 `timeout: 30` 或更长
2. **重试次数**: 建议设置 `max_retries: 3`,失败会自动切换代理重试
3. **Headers**: 必须包含 `Origin` 和 `Referer`,否则可能被拒绝
4. **域名参数**: 记得在 `Referer` 中替换实际的域名
5. **并发限制**: 批量请求时建议控制并发数,避免过载

---

## 快速测试

```bash
# 使用提供的示例文件测试
curl -X POST http://localhost:8000/api/request \
  -H "Content-Type: application/json" \
  -d @example_similarweb.json

# 或者直接在命令行测试
curl -X POST http://localhost:8000/api/request \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://data.similarweb.com/api/v1/data?domain=google.com",
    "method": "GET",
    "headers": {
      "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
      "Origin": "https://www.similarweb.com",
      "Referer": "https://www.similarweb.com/website/google.com/"
    }
  }'
```
