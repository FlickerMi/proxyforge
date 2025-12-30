#!/usr/bin/env python3
"""
ProxyForge - SimilarWeb API 测试脚本
使用 ProxyForge 代理服务访问 SimilarWeb API
"""

import requests
import json
import sys

# ProxyForge API 地址
PROXYFORGE_URL = "http://localhost:8000/api/request"

def fetch_similarweb_data(domain: str):
    """
    通过 ProxyForge 获取 SimilarWeb 数据
    
    Args:
        domain: 要查询的域名,如 'google.com'
    
    Returns:
        dict: 响应数据
    """
    print(f"\n{'='*60}")
    print(f"正在查询域名: {domain}")
    print(f"{'='*60}\n")
    
    # 构造请求数据
    payload = {
        "url": f"https://data.similarweb.com/api/v1/data?domain={domain}",
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
            "Referer": f"https://www.similarweb.com/website/{domain}/"
        },
        "timeout": 30,
        "max_retries": 3
    }
    
    try:
        print("📤 发送请求到 ProxyForge...")
        print(f"   目标 URL: {payload['url']}")
        
        # 发送请求到 ProxyForge
        response = requests.post(PROXYFORGE_URL, json=payload, timeout=60)
        
        # 解析响应
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                data = result['data']
                
                print(f"\n✅ 请求成功!")
                print(f"   HTTP 状态码: {data['status_code']}")
                print(f"   使用代理: {data['proxy_used']}")
                print(f"   请求耗时: {data['elapsed']:.2f} 秒")
                print(f"   响应编码: {data.get('encoding', 'N/A')}")
                
                # 尝试解析 JSON 响应
                try:
                    content = json.loads(data['content'])
                    print(f"\n📊 响应数据:")
                    print(json.dumps(content, indent=2, ensure_ascii=False))
                    return content
                except json.JSONDecodeError:
                    print(f"\n📄 响应内容 (非 JSON):")
                    print(data['content'][:500])  # 只显示前500字符
                    return data['content']
            else:
                print(f"\n❌ 请求失败: {result.get('message', '未知错误')}")
                return None
        else:
            print(f"\n❌ API 调用失败")
            print(f"   状态码: {response.status_code}")
            
            # 尝试解析错误详情
            try:
                error_detail = response.json()
                print(f"   错误详情: {error_detail.get('detail', response.text[:200])}")
            except:
                print(f"   响应: {response.text[:200]}")
            
            return None
            
    except requests.exceptions.Timeout:
        print(f"\n⏱️  请求超时 (60秒)")
        return None
    except requests.exceptions.ConnectionError:
        print(f"\n🔌 连接失败: 请确保 ProxyForge 服务正在运行")
        print(f"   启动命令: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return None
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return None


def main():
    """主函数"""
    # 从命令行参数获取域名,默认为 google.com
    domain = sys.argv[1] if len(sys.argv) > 1 else "google.com"
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                  ProxyForge - SimilarWeb 测试                ║
║                                                              ║
║  通过代理访问 SimilarWeb API 获取网站数据                    ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # 执行查询
    result = fetch_similarweb_data(domain)
    
    if result:
        print(f"\n{'='*60}")
        print("✅ 测试完成!")
        print(f"{'='*60}\n")
    else:
        print(f"\n{'='*60}")
        print("❌ 测试失败")
        print(f"{'='*60}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
