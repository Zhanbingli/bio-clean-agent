# 部署指南

本文档提供Bio Clean Agent的多种部署方式。

## 目录

1. [本地开发部署](#本地开发部署)
2. [Docker部署](#docker部署)
3. [生产环境部署](#生产环境部署)
4. [云平台部署](#云平台部署)
5. [安全配置](#安全配置)
6. [监控和维护](#监控和维护)

---

## 本地开发部署

### 使用一键安装脚本

最简单的方式是使用提供的安装脚本:

```bash
# 下载项目
git clone https://github.com/yourusername/bio-clean-agent.git
cd bio-clean-agent

# 运行安装脚本
chmod +x install.sh
./install.sh

# 激活虚拟环境
source .venv/bin/activate

# 启动服务
python start_web.py
```

### 手动安装

如果你更喜欢手动控制:

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -e .[all]

# 生成配置文件
cat > .env <<EOF
PHI_HASH_SALT=$(python3 -c "import secrets; print(secrets.token_hex(32))")
ALLOWED_ORIGINS=http://localhost:8080
LOG_LEVEL=DEBUG
EOF

# 启动服务
python start_web.py
```

---

## Docker部署

### 快速启动

使用Docker Compose一键启动所有服务:

```bash
# 创建环境变量文件
cp .env.example .env
# 编辑.env文件，设置必要的配置

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f web

# 停止服务
docker-compose down
```

### 仅运行Web服务

如果你不需要数据库和Redis:

```bash
# 构建镜像
docker build -t bio-clean-agent .

# 运行容器
docker run -d \
  -p 8080:8080 \
  -e ALLOWED_ORIGINS=http://localhost:8080 \
  -e PHI_HASH_SALT=your-secure-salt \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/outputs:/app/outputs \
  --name bio-clean \
  bio-clean-agent

# 查看日志
docker logs -f bio-clean
```

### 自定义Docker配置

创建自定义的docker-compose配置:

```yaml
# docker-compose.override.yml
version: '3.8'

services:
  web:
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - MAX_FILE_SIZE_MB=500
    volumes:
      - ./custom-data:/app/data
```

运行时会自动合并override文件:

```bash
docker-compose up -d
```

---

## 生产环境部署

### 架构概览

```
Internet
    ↓
[Load Balancer]
    ↓
[Nginx/Traefik] (SSL终端, 反向代理)
    ↓
[Bio Clean Agent] (多个实例)
    ↓
[PostgreSQL] + [Redis] + [Object Storage]
```

### 系统要求

**最低配置** (单实例):
- CPU: 2核
- 内存: 4GB
- 磁盘: 20GB SSD
- 网络: 100Mbps

**推荐配置** (生产环境):
- CPU: 4核+
- 内存: 8GB+
- 磁盘: 50GB SSD
- 网络: 1Gbps

### 使用Nginx反向代理

创建Nginx配置文件 `nginx/nginx.conf`:

```nginx
upstream bio_clean_backend {
    # 多个实例负载均衡
    server web1:8080;
    server web2:8080;
    server web3:8080;
}

server {
    listen 80;
    server_name your-domain.com;

    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL证书
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # 文件上传大小限制
    client_max_body_size 100M;

    # 超时设置
    proxy_connect_timeout 600;
    proxy_send_timeout 600;
    proxy_read_timeout 600;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;

    location / {
        proxy_pass http://bio_clean_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket支持
    location /ws {
        proxy_pass http://bio_clean_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 速率限制
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    location /api {
        limit_req zone=api burst=20;
        proxy_pass http://bio_clean_backend;
    }
}
```

### 环境变量配置

生产环境的`.env`配置:

```bash
# 安全配置
PHI_HASH_SALT=<use-secrets-manager>
ALLOWED_ORIGINS=https://your-domain.com,https://app.your-domain.com

# 数据库
DATABASE_URL=postgresql://user:password@db-host:5432/bioclean?sslmode=require

# Redis
REDIS_URL=redis://:password@redis-host:6379/0

# 日志
LOG_LEVEL=WARNING
ENABLE_AUDIT_LOGGING=true
LOG_FILE=/var/log/bio-clean/app.log

# 性能
WORKERS=4
MAX_FILE_SIZE_MB=100

# 监控
SENTRY_DSN=https://your-sentry-dsn
ENABLE_METRICS=true
```

### 使用Systemd管理

创建服务文件 `/etc/systemd/system/bio-clean.service`:

```ini
[Unit]
Description=Bio Clean Agent
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=bioagent
Group=bioagent
WorkingDirectory=/opt/bio-clean-agent
Environment="PATH=/opt/bio-clean-agent/.venv/bin"
EnvironmentFile=/opt/bio-clean-agent/.env
ExecStart=/opt/bio-clean-agent/.venv/bin/uvicorn \
    bio_clean_agent.web.app:app \
    --host 0.0.0.0 \
    --port 8080 \
    --workers 4

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bio-clean
sudo systemctl start bio-clean
sudo systemctl status bio-clean
```

---

## 云平台部署

### AWS部署

#### 使用ECS (Elastic Container Service)

1. **构建并推送Docker镜像到ECR**:

```bash
# 登录ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com

# 构建镜像
docker build -t bio-clean-agent .

# 标记镜像
docker tag bio-clean-agent:latest \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/bio-clean-agent:latest

# 推送镜像
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/bio-clean-agent:latest
```

2. **创建ECS任务定义** (`task-definition.json`):

```json
{
  "family": "bio-clean-agent",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "web",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/bio-clean-agent:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "LOG_LEVEL",
          "value": "INFO"
        }
      ],
      "secrets": [
        {
          "name": "PHI_HASH_SALT",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:bio-clean/phi-salt"
        },
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:bio-clean/db-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/bio-clean-agent",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "web"
        }
      }
    }
  ]
}
```

3. **创建服务**:

```bash
aws ecs create-service \
  --cluster bio-clean-cluster \
  --service-name bio-clean-service \
  --task-definition bio-clean-agent \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=web,containerPort=8080"
```

#### 使用RDS和ElastiCache

```bash
# PostgreSQL RDS
aws rds create-db-instance \
  --db-instance-identifier bio-clean-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --master-username bioclean \
  --master-user-password <password> \
  --allocated-storage 20 \
  --backup-retention-period 7 \
  --storage-encrypted

# Redis ElastiCache
aws elasticache create-cache-cluster \
  --cache-cluster-id bio-clean-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1
```

### Azure部署

使用Azure Container Instances:

```bash
# 创建资源组
az group create --name bio-clean-rg --location eastus

# 创建容器实例
az container create \
  --resource-group bio-clean-rg \
  --name bio-clean-agent \
  --image biocleanagent/bio-clean-agent:latest \
  --dns-name-label bio-clean-unique \
  --ports 8080 \
  --environment-variables \
    LOG_LEVEL=INFO \
  --secure-environment-variables \
    PHI_HASH_SALT=<your-salt> \
    DATABASE_URL=<your-db-url>
```

### Google Cloud Platform

使用Cloud Run:

```bash
# 构建镜像
gcloud builds submit --tag gcr.io/your-project/bio-clean-agent

# 部署
gcloud run deploy bio-clean-agent \
  --image gcr.io/your-project/bio-clean-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars LOG_LEVEL=INFO \
  --set-secrets PHI_HASH_SALT=bio-clean-phi-salt:latest
```

---

## 安全配置

### SSL/TLS证书

使用Let's Encrypt获取免费证书:

```bash
# 安装Certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 防火墙配置

```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 仅允许特定IP访问数据库
sudo ufw allow from 10.0.1.0/24 to any port 5432
```

### 密钥管理

**使用AWS Secrets Manager**:

```python
# src/bio_clean_agent/config.py
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name):
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager')

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        return get_secret_value_response['SecretString']
    except ClientError as e:
        raise e

# 使用
phi_salt = get_secret('bio-clean/phi-hash-salt')
```

### 审计日志

配置审计日志到外部服务:

```python
# src/bio_clean_agent/utils/logging.py
import logging
from pythonjsonlogger import jsonlogger

# 结构化日志
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

# 发送到CloudWatch Logs
import watchtower

logging.getLogger().addHandler(
    watchtower.CloudWatchLogHandler(
        log_group='/bio-clean-agent/audit',
        stream_name='production'
    )
)
```

---

## 监控和维护

### 健康检查

应用已包含健康检查端点:

```bash
# 检查应用状态
curl http://localhost:8080/health

# 响应示例
{
  "status": "healthy",
  "version": "0.3.0",
  "timestamp": "2025-10-28T10:30:00Z",
  "checks": {
    "database": "ok",
    "redis": "ok"
  }
}
```

### 日志收集

使用ELK Stack:

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.10.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.10.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

### 性能监控

使用Prometheus和Grafana:

```yaml
# docker-compose.monitoring.yml (续)
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

**Prometheus配置** (`prometheus.yml`):

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'bio-clean-agent'
    static_configs:
      - targets: ['web:8080']
```

### 备份策略

**数据库备份**:

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/bio_clean_$TIMESTAMP.sql"

# 备份
pg_dump -h db-host -U bioclean bioclean > "$BACKUP_FILE"

# 压缩
gzip "$BACKUP_FILE"

# 上传到S3
aws s3 cp "$BACKUP_FILE.gz" s3://your-bucket/backups/

# 删除7天前的备份
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete
```

**自动化备份** (crontab):

```cron
# 每天凌晨2点备份
0 2 * * * /opt/bio-clean-agent/backup.sh
```

### 更新和回滚

**更新流程**:

```bash
# 1. 备份数据库
./backup.sh

# 2. 拉取新镜像
docker-compose pull

# 3. 滚动更新
docker-compose up -d --no-deps --build web

# 4. 检查日志
docker-compose logs -f web

# 5. 验证健康检查
curl http://localhost:8080/health
```

**回滚流程**:

```bash
# 1. 停止当前版本
docker-compose down

# 2. 使用特定版本
docker-compose -f docker-compose.yml up -d \
  -e VERSION=0.2.0

# 3. 恢复数据库 (如需要)
psql -h db-host -U bioclean bioclean < backup.sql
```

---

## 故障排查

### 常见问题

#### 1. 容器启动失败

```bash
# 查看日志
docker-compose logs web

# 检查配置
docker-compose config

# 验证环境变量
docker-compose exec web env
```

#### 2. 数据库连接失败

```bash
# 测试数据库连接
docker-compose exec web python -c "
from sqlalchemy import create_engine
import os
engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    print('Connected successfully')
"
```

#### 3. 文件上传失败

```bash
# 检查目录权限
ls -la /app/uploads

# 检查磁盘空间
df -h
```

#### 4. 性能问题

```bash
# 查看资源使用
docker stats

# 数据库慢查询
# 在PostgreSQL中
SELECT * FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

---

## 合规性检查清单

部署前的检查清单:

### 安全
- [ ] HTTPS/TLS已启用
- [ ] 强密码和密钥管理
- [ ] CORS正确配置
- [ ] 文件上传验证
- [ ] 速率限制已启用
- [ ] 防火墙规则配置

### 数据保护
- [ ] PHI/PII检测和脱敏
- [ ] 审计日志已启用
- [ ] 数据加密 (静态和传输)
- [ ] 备份策略已实施
- [ ] 数据保留政策

### 可用性
- [ ] 健康检查配置
- [ ] 自动重启机制
- [ ] 监控和告警
- [ ] 负载均衡
- [ ] 灾难恢复计划

### HIPAA合规 (如适用)
- [ ] BAA协议签署
- [ ] 访问控制和审计
- [ ] 数据备份和恢复
- [ ] 事件响应计划
- [ ] 员工培训

---

## 联系和支持

- 文档: https://docs.bio-clean-agent.com
- GitHub Issues: https://github.com/yourusername/bio-clean-agent/issues
- 社区: Discord/Slack链接

---

**最后更新**: 2025-10-28
**版本**: 1.0
