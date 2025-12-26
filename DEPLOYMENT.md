# 部署指南

本文档提供多种部署方式，选择最适合你的方式。

## 📦 部署方式总览

| 方式 | 难度 | 适用场景 | 优点 |
|------|------|----------|------|
| [Docker Compose](#方式一docker-compose推荐) | ⭐ | 生产环境 | 最简单，隔离性好 |
| [一键安装脚本](#方式二一键安装脚本) | ⭐⭐ | Linux 服务器 | 自动化程度高 |
| [Systemd 服务](#方式三systemd-服务) | ⭐⭐⭐ | Linux 服务器 | 系统集成好 |
| [手动安装](#方式四手动安装) | ⭐⭐⭐ | 开发/测试 | 灵活性高 |

---

## 方式一: Docker Compose（推荐）

### 最简单的部署方式，只需 3 步！

#### 1. 创建配置文件

创建 `.env` 文件：

```bash
# 复制示例文件
cp .env.example .env

# 编辑配置
nano .env
```

配置内容：

```bash
# DolphinScheduler 配置
DOLPHIN_BASE_URL=http://your-dolphin-server:12345/dolphinscheduler
DOLPHIN_TOKEN=your-api-token-here
DOLPHIN_TIMEOUT=30

# 监控配置
MAX_RETRY_COUNT=3
RETRY_INTERVAL=60
CHECK_INTERVAL=300
CONTINUOUS_MONITOR=true

# 项目配置（逗号分隔）
PROJECT_CODES=123456789,987654321

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/app/logs/check_dolphin.log
```

#### 2. 启动服务

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

#### 3. 管理服务

```bash
# 停止服务
docker-compose stop

# 重启服务
docker-compose restart

# 停止并删除容器
docker-compose down

# 查看状态
docker-compose ps
```

### 高级配置

#### 使用配置文件而非环境变量

1. 生成配置文件：
```bash
docker-compose run --rm check-dolphin check-dolphin config -o /app/config/config.yaml
```

2. 编辑 `config.yaml`

3. 修改 `docker-compose.yml`，取消注释配置文件相关行

#### 多实例部署

复制 `docker-compose.yml` 并修改服务名称和端口：

```yaml
services:
  check-dolphin-project1:
    build: .
    container_name: check-dolphin-project1
    environment:
      PROJECT_CODES: 123456789
    # ...

  check-dolphin-project2:
    build: .
    container_name: check-dolphin-project2
    environment:
      PROJECT_CODES: 987654321
    # ...
```

---

## 方式二: 一键安装脚本

### 适用于 Linux 服务器，自动完成所有安装步骤

#### 1. 下载项目

```bash
git clone https://github.com/yourusername/check_dolphin.git
cd check_dolphin
```

#### 2. 运行安装脚本

```bash
# 交互式安装
sudo bash install.sh

# 或者非交互式安装
sudo INSTALL_DIR=/opt/check_dolphin \
     INSTALL_AS_SERVICE=yes \
     NON_INTERACTIVE=1 \
     bash install.sh
```

#### 3. 配置

```bash
# 编辑配置文件
sudo nano /opt/check_dolphin/.env

# 填入你的 DolphinScheduler 配置
```

#### 4. 启动服务（如果选择了安装为服务）

```bash
# 启动服务
sudo systemctl start check-dolphin

# 查看状态
sudo systemctl status check-dolphin

# 开机自启
sudo systemctl enable check-dolphin

# 查看日志
sudo journalctl -u check-dolphin -f
```

---

## 方式三: Systemd 服务

### 适用于需要更多自定义的场景

#### 1. 手动安装项目

```bash
# 创建安装目录
sudo mkdir -p /opt/check_dolphin
cd /opt/check_dolphin

# 克隆项目
git clone https://github.com/yourusername/check_dolphin.git .

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install -e .
```

#### 2. 配置环境

```bash
# 复制配置文件
cp .env.example .env

# 编辑配置
nano .env
```

#### 3. 安装 systemd 服务

```bash
# 复制服务文件
sudo cp check-dolphin.service /etc/systemd/system/

# 编辑服务文件，修改路径和用户
sudo nano /etc/systemd/system/check-dolphin.service
```

需要修改的内容：
- `User=YOUR_USERNAME` → 改为实际用户名
- `Group=YOUR_GROUP` → 改为实际用户组
- `/path/to/check_dolphin` → 改为实际路径（如 `/opt/check_dolphin`）

#### 4. 启动服务

```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start check-dolphin

# 查看状态
sudo systemctl status check-dolphin

# 开机自启
sudo systemctl enable check-dolphin

# 查看日志
sudo journalctl -u check-dolphin -f
```

---

## 方式四: 手动安装

### 适用于开发和测试环境

#### 1. 克隆项目

```bash
git clone https://github.com/yourusername/check_dolphin.git
cd check_dolphin
```

#### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
pip install -e .
```

#### 4. 配置

```bash
# 复制配置文件
cp .env.example .env

# 编辑配置
nano .env
```

#### 5. 运行

```bash
# 单次运行
check-dolphin monitor -p 123456789

# 持续监控（前台运行）
check-dolphin monitor -p 123456789 --continuous

# 后台运行
nohup check-dolphin monitor -p 123456789 --continuous > monitor.log 2>&1 &
```

---

## 🔧 配置说明

### 环境变量配置 (.env)

```bash
# ==================== DolphinScheduler 配置 ====================
# DolphinScheduler API 地址
DOLPHIN_BASE_URL=http://localhost:12345/dolphinscheduler

# API 访问令牌（在 DolphinScheduler 安全中心生成）
DOLPHIN_TOKEN=your-token-here

# API 请求超时时间（秒）
DOLPHIN_TIMEOUT=30

# ==================== 监控配置 ====================
# 工作流最大重试次数（监控器级别）
MAX_RETRY_COUNT=3

# 重试间隔（秒）
RETRY_INTERVAL=60

# 检查间隔（秒）
CHECK_INTERVAL=300

# 是否持续监控
CONTINUOUS_MONITOR=true

# ==================== 项目配置 ====================
# 要监控的项目代码（逗号分隔）
PROJECT_CODES=123456789,987654321

# ==================== 日志配置 ====================
# 日志级别: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# 日志文件路径（留空则输出到控制台）
LOG_FILE=/var/log/check_dolphin.log
```

### YAML 配置文件 (config.yaml)

```yaml
dolphinscheduler:
  base_url: http://localhost:12345/dolphinscheduler
  token: your-token-here
  timeout: 30

monitor:
  max_retry_count: 3
  retry_interval: 60
  check_interval: 300
  continuous: true

projects:
  codes:
    - 123456789
    - 987654321

logging:
  level: INFO
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  file: /var/log/check_dolphin.log
```

---

## 📊 监控和管理

### Docker Compose

```bash
# 查看日志
docker-compose logs -f check-dolphin

# 查看最近 100 行日志
docker-compose logs --tail=100 check-dolphin

# 进入容器
docker-compose exec check-dolphin bash

# 重启服务
docker-compose restart check-dolphin
```

### Systemd 服务

```bash
# 查看实时日志
sudo journalctl -u check-dolphin -f

# 查看最近 100 行日志
sudo journalctl -u check-dolphin -n 100

# 查看特定时间的日志
sudo journalctl -u check-dolphin --since "2025-01-01" --until "2025-01-02"

# 重启服务
sudo systemctl restart check-dolphin

# 停止服务
sudo systemctl stop check-dolphin

# 禁用开机自启
sudo systemctl disable check-dolphin
```

---

## 🚀 生产环境建议

### 1. 使用配置文件而非环境变量

配置文件更安全，便于版本控制：

```bash
# 生成配置文件
check-dolphin config -o /etc/check_dolphin/config.yaml

# 设置权限
sudo chmod 600 /etc/check_dolphin/config.yaml
sudo chown check-dolphin:check-dolphin /etc/check_dolphin/config.yaml
```

### 2. 日志轮转

创建 `/etc/logrotate.d/check-dolphin`：

```
/var/log/check_dolphin.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 check-dolphin check-dolphin
    postrotate
        systemctl reload check-dolphin > /dev/null 2>&1 || true
    endscript
}
```

### 3. 监控告警

集成到你的监控系统（Prometheus, Grafana, etc.）：

```bash
# 检查服务状态
systemctl is-active check-dolphin

# 检查最近错误
journalctl -u check-dolphin -p err -n 10
```

### 4. 定期备份配置

```bash
# 备份脚本
#!/bin/bash
tar -czf check_dolphin_config_$(date +%Y%m%d).tar.gz \
    /opt/check_dolphin/.env \
    /opt/check_dolphin/config.yaml
```

---

## ⚠️ 故障排除

### Docker 相关

**问题**: 容器无法启动

```bash
# 查看详细日志
docker-compose logs check-dolphin

# 检查配置
docker-compose config

# 重新构建镜像
docker-compose build --no-cache
```

**问题**: 无法连接到 DolphinScheduler

```bash
# 检查网络连接
docker-compose exec check-dolphin ping your-dolphin-server

# 检查环境变量
docker-compose exec check-dolphin env | grep DOLPHIN
```

### Systemd 服务相关

**问题**: 服务启动失败

```bash
# 查看详细错误
sudo systemctl status check-dolphin -l

# 检查配置文件
sudo systemd-analyze verify check-dolphin.service

# 手动运行测试
sudo -u check-dolphin /opt/check_dolphin/venv/bin/check-dolphin monitor -p 123456789
```

**问题**: 服务频繁重启

```bash
# 查看崩溃日志
sudo journalctl -u check-dolphin -p err

# 增加日志级别到 DEBUG
# 编辑 .env: LOG_LEVEL=DEBUG
sudo systemctl restart check-dolphin
```

---

## 📝 升级指南

### Docker Compose

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

### Systemd 服务

```bash
cd /opt/check_dolphin

# 停止服务
sudo systemctl stop check-dolphin

# 备份配置
cp .env .env.backup

# 拉取更新
git pull

# 激活虚拟环境
source venv/bin/activate

# 更新依赖
pip install -r requirements.txt --upgrade
pip install -e . --upgrade

# 启动服务
sudo systemctl start check-dolphin
```

---

## 🔐 安全建议

1. **不要在代码中硬编码 Token**
   - 使用环境变量或配置文件
   - 设置适当的文件权限（600）

2. **限制服务权限**
   - 使用专用用户运行服务
   - 不要使用 root 权限

3. **定期更新 Token**
   - 设置 Token 过期时间
   - 定期轮换 Token

4. **网络安全**
   - 使用 HTTPS 连接 DolphinScheduler
   - 配置防火墙规则

---

## 📞 获取帮助

- 查看详细文档: [README.md](README.md)
- 提交问题: [GitHub Issues](https://github.com/yourusername/check_dolphin/issues)
