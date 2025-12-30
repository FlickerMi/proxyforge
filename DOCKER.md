# Docker 部署指南

## 🐳 Docker 部署

### 快速开始

#### 方法 1: 使用 docker-compose (推荐)

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 方法 2: 使用 Docker 命令

```bash
# 构建镜像
docker build -t proxyforge:latest .

# 运行容器
docker run -d \
  --name proxyforge \
  -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  -e PROXY_POOL_SIZE=100 \
  -e LOG_LEVEL=INFO \
  proxyforge:latest

# 查看日志
docker logs -f proxyforge

# 停止容器
docker stop proxyforge
docker rm proxyforge
```

---

## 📦 使用预构建镜像

### 从 GitHub Container Registry 拉取

```bash
# 拉取最新镜像
docker pull ghcr.io/YOUR_USERNAME/proxyforge:latest

# 运行
docker run -d \
  --name proxyforge \
  -p 8000:8000 \
  ghcr.io/YOUR_USERNAME/proxyforge:latest
```

---

## ⚙️ 环境变量配置

在 `docker-compose.yml` 中配置或通过 `-e` 参数传递:

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `HOST` | 0.0.0.0 | 服务监听地址 |
| `PORT` | 8000 | 服务端口 |
| `DEBUG` | False | 调试模式 |
| `PROXY_POOL_SIZE` | 100 | 代理池大小 |
| `PROXY_UPDATE_INTERVAL` | 3600 | 更新间隔(秒) |
| `PROXY_VALIDATION_TIMEOUT` | 10 | 验证超时(秒) |
| `REQUEST_TIMEOUT` | 30 | 请求超时(秒) |
| `REQUEST_MAX_RETRIES` | 3 | 最大重试次数 |
| `LOG_LEVEL` | INFO | 日志级别 |

### 示例: 自定义配置

```yaml
# docker-compose.yml
environment:
  - PROXY_POOL_SIZE=200
  - PROXY_UPDATE_INTERVAL=1800
  - LOG_LEVEL=DEBUG
```

---

## 📊 健康检查

容器内置健康检查,每 30 秒检查一次:

```bash
# 查看健康状态
docker inspect --format='{{.State.Health.Status}}' proxyforge

# 查看健康检查日志
docker inspect --format='{{json .State.Health}}' proxyforge | jq
```

---

## 💾 数据持久化

### 日志持久化

```yaml
volumes:
  - ./logs:/app/logs
```

日志文件会保存在宿主机的 `./logs` 目录。

---

## 🔧 高级配置

### 使用自定义 .env 文件

```bash
# 创建 .env 文件
cp .env.example .env

# 编辑配置
nano .env

# 使用 docker-compose
docker-compose --env-file .env up -d
```

### 多实例部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  proxyforge-1:
    build: .
    ports:
      - "8001:8000"
    environment:
      - PROXY_POOL_SIZE=50
  
  proxyforge-2:
    build: .
    ports:
      - "8002:8000"
    environment:
      - PROXY_POOL_SIZE=50
```

### 使用 Nginx 负载均衡

```nginx
upstream proxyforge {
    server localhost:8001;
    server localhost:8002;
}

server {
    listen 80;
    server_name proxyforge.example.com;

    location / {
        proxy_pass http://proxyforge;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🚀 GitHub Actions 自动构建

### 配置说明

项目包含 `.github/workflows/docker-build.yml`,会在以下情况自动构建镜像:

- ✅ 推送到 `main` 或 `develop` 分支
- ✅ 创建新的 tag (如 `v1.0.0`)
- ✅ 手动触发 (workflow_dispatch)

### 镜像标签策略

| 触发条件 | 生成的标签 |
|---------|-----------|
| 推送到 main | `latest`, `main` |
| 推送到 develop | `develop` |
| Tag `v1.2.3` | `1.2.3`, `1.2`, `1`, `latest` |
| PR | `pr-123` |
| Commit SHA | `main-abc1234` |

### 使用构建的镜像

```bash
# 使用 latest
docker pull ghcr.io/YOUR_USERNAME/proxyforge:latest

# 使用特定版本
docker pull ghcr.io/YOUR_USERNAME/proxyforge:1.0.0

# 使用开发版本
docker pull ghcr.io/YOUR_USERNAME/proxyforge:develop
```

### 配置 GitHub Secrets

GitHub Actions 会自动使用 `GITHUB_TOKEN`,无需额外配置。

如果需要推送到其他 Registry (如 Docker Hub):

1. 在 GitHub 仓库设置中添加 Secrets:
   - `DOCKERHUB_USERNAME`
   - `DOCKERHUB_TOKEN`

2. 修改 `.github/workflows/docker-build.yml`:

```yaml
- name: Log in to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}
```

---

## 🐛 故障排查

### 容器无法启动

```bash
# 查看详细日志
docker logs proxyforge

# 查看容器状态
docker ps -a

# 进入容器调试
docker exec -it proxyforge /bin/bash
```

### 代理池为空

```bash
# 检查网络连接
docker exec proxyforge curl -I https://httpbin.org/ip

# 查看代理池状态
curl http://localhost:8000/api/proxy/stats
```

### 性能问题

```bash
# 查看资源使用
docker stats proxyforge

# 限制资源
docker run -d \
  --name proxyforge \
  --memory="512m" \
  --cpus="1.0" \
  -p 8000:8000 \
  proxyforge:latest
```

---

## 📝 生产环境建议

1. **使用环境变量**: 不要在镜像中硬编码配置
2. **持久化日志**: 挂载日志目录到宿主机
3. **健康检查**: 配置健康检查和自动重启
4. **资源限制**: 设置内存和 CPU 限制
5. **监控**: 集成 Prometheus 或其他监控工具
6. **备份**: 定期备份配置和日志

### 生产环境 docker-compose 示例

```yaml
version: '3.8'

services:
  proxyforge:
    image: ghcr.io/YOUR_USERNAME/proxyforge:latest
    container_name: proxyforge
    restart: always
    ports:
      - "8000:8000"
    environment:
      - PROXY_POOL_SIZE=200
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
      - ./config/.env:/app/.env:ro
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 256M
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health', timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 🔗 相关链接

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
