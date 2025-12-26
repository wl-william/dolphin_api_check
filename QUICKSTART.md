# ⚡ 5 分钟快速开始

本指南帮助你在 5 分钟内运行 check_dolphin。

## 前置条件

- Docker 和 Docker Compose 已安装
- 或者 Python 3.7+ 已安装

## 方法一: Docker（最快）

### 1️⃣ 下载项目

```bash
git clone https://github.com/yourusername/check_dolphin.git
cd check_dolphin
```

### 2️⃣ 配置

```bash
# 复制配置文件
cp .env.example .env

# 编辑配置
nano .env
```

**最少需要配置这 3 项**：

```bash
DOLPHIN_BASE_URL=http://your-server:12345/dolphinscheduler
DOLPHIN_TOKEN=your-token-here
PROJECT_CODES=123456789
```

### 3️⃣ 启动

```bash
docker-compose up -d
```

### 4️⃣ 验证

```bash
# 查看日志
docker-compose logs -f

# 你应该看到类似输出：
# INFO - Starting workflow monitoring for projects: [123456789]
# INFO - Found 2 failed workflows in project 123456789
```

**✅ 完成！** 服务已在后台运行。

---

## 方法二: Python（传统方式）

### 1️⃣ 下载项目

```bash
git clone https://github.com/yourusername/check_dolphin.git
cd check_dolphin
```

### 2️⃣ 安装

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装
pip install -r requirements.txt
pip install -e .
```

### 3️⃣ 配置

```bash
cp .env.example .env
nano .env
```

配置必填项（同上）。

### 4️⃣ 运行

```bash
# 单次检查
check-dolphin monitor -p 123456789

# 持续监控
check-dolphin monitor -p 123456789 --continuous
```

---

## 📝 如何获取配置信息？

### 获取 DOLPHIN_BASE_URL

DolphinScheduler API 地址，通常是：

```
http://your-server-ip:12345/dolphinscheduler
```

或

```
https://your-domain.com/dolphinscheduler
```

### 获取 DOLPHIN_TOKEN

1. 登录 DolphinScheduler Web UI
2. 进入 **安全中心** → **令牌管理**
3. 点击 **创建令牌**
4. 选择用户，设置过期时间
5. 复制生成的 Token

### 获取 PROJECT_CODES

1. 登录 DolphinScheduler Web UI
2. 进入 **项目管理**
3. 在项目列表中找到项目代码（通常显示在项目名称旁边）
4. 或者从浏览器地址栏获取：
   ```
   http://your-server/dolphinscheduler/projects/123456789/...
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ 这是项目代码
   ```

如果要监控多个项目，用逗号分隔：

```bash
PROJECT_CODES=123456789,987654321,555666777
```

---

## 🔍 验证运行状态

### Docker 方式

```bash
# 查看容器状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 查看最近的日志
docker-compose logs --tail=50
```

### Python 方式

```bash
# 查看状态
check-dolphin status -p 123456789

# 你会看到：
# Project 123456789 status:
#   total: 10
#   success: 6
#   failure: 2
#   running: 1
#   other: 1
```

---

## 🎯 常用命令

### 查看工作流状态

```bash
check-dolphin status -p 123456789
```

### 手动重试特定工作流

```bash
check-dolphin retry -p 123456789 -i 456789
```

### 生成配置文件模板

```bash
check-dolphin config -o my-config.yaml
```

### 使用配置文件运行

```bash
check-dolphin -c config.yaml monitor --continuous
```

---

## ⚠️ 常见问题

### 1. Token 验证失败

**错误**: `API request failed: Token verification failed`

**解决**:
- 检查 Token 是否正确复制（没有多余空格）
- 检查 Token 是否过期
- 重新生成 Token

### 2. 连接超时

**错误**: `Request timeout`

**解决**:
- 检查 `DOLPHIN_BASE_URL` 是否正确
- 检查网络连接
- 检查 DolphinScheduler 服务是否运行

### 3. 找不到项目

**错误**: `Project not found`

**解决**:
- 确认项目代码是否正确
- 确认 Token 对应的用户是否有权限访问该项目

### 4. 没有失败的工作流

**日志**: `Found 0 failed workflows in project 123456789`

**说明**: 这是正常的，表示当前没有失败的工作流需要重试。

---

## 📚 下一步

- 📖 阅读完整文档: [README.md](README.md)
- 🚀 部署到生产环境: [DEPLOYMENT.md](DEPLOYMENT.md)
- 🔧 高级配置: [README.md#配置](README.md#配置)
- 💡 使用示例: [README.md#使用方法](README.md#使用方法)

---

## 🆘 需要帮助？

- 查看详细日志获取更多信息
- 提交 Issue: [GitHub Issues](https://github.com/yourusername/check_dolphin/issues)
- 查看故障排除文档: [DEPLOYMENT.md#故障排除](DEPLOYMENT.md#故障排除)
