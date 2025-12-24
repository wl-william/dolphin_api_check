# check_dolphin

DolphinScheduler 工作流状态监测和失败重试工具

## 功能特性

- ✅ 获取 DolphinScheduler 项目中工作流执行状态
- ✅ 自动过滤执行失败的任务
- ✅ **智能任务验证**：重试前验证所有任务状态
  - 确保工作流中所有任务都已失败
  - 验证每个任务配置的重试次数已全部用完
  - 检查是否有任务仍在运行中
- ✅ 智能重试机制（支持最大重试次数限制）
- ✅ 持续监控模式
- ✅ 支持多项目监控
- ✅ 灵活的配置管理（环境变量、配置文件）
- ✅ 详细的日志记录

## 安装

### 方法 1: 从源码安装

```bash
# 克隆项目
cd check_dolphin

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装项目
pip install -e .
```

### 方法 2: 直接安装

```bash
pip install -e .
```

## 配置

### 方法 1: 使用环境变量

复制 `.env.example` 到 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```bash
# DolphinScheduler 配置
DOLPHIN_BASE_URL=http://your-dolphin-server:12345/dolphinscheduler
DOLPHIN_TOKEN=your-api-token-here
DOLPHIN_TIMEOUT=30

# 监控配置
MAX_RETRY_COUNT=3
RETRY_INTERVAL=60
CHECK_INTERVAL=300

# 项目配置
PROJECT_CODES=123456789,987654321
```

### 方法 2: 使用配置文件

生成示例配置文件：

```bash
check-dolphin config -o config.yaml
```

编辑 `config.yaml`：

```yaml
dolphinscheduler:
  base_url: http://your-dolphin-server:12345/dolphinscheduler
  token: your-api-token-here
  timeout: 30

monitor:
  max_retry_count: 3
  retry_interval: 60
  check_interval: 300
  continuous: false

projects:
  codes:
    - 123456789
    - 987654321

logging:
  level: INFO
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  file: check_dolphin.log
```

## 获取 DolphinScheduler Token

1. 登录 DolphinScheduler Web UI
2. 进入 **安全中心** → **令牌管理**
3. 点击 **创建令牌**
4. 选择用户并设置过期时间
5. 复制生成的 Token

## 获取项目代码 (Project Code)

1. 登录 DolphinScheduler Web UI
2. 进入 **项目管理**
3. 在项目列表中，项目代码显示在项目名称旁边
4. 或者在浏览器地址栏中，查看 URL 中的项目代码，例如：
   ```
   http://localhost:12345/dolphinscheduler/projects/123456789/...
   ```
   其中 `123456789` 就是项目代码

## 使用方法

### 1. 监控并重试失败的工作流

#### 单次监控

```bash
# 使用环境变量配置
check-dolphin monitor -p 123456789

# 使用配置文件
check-dolphin -c config.yaml monitor

# 监控多个项目
check-dolphin monitor -p 123456789 987654321

# 指定时间范围
check-dolphin monitor -p 123456789 --start-date "2025-01-01 00:00:00" --end-date "2025-01-31 23:59:59"
```

#### 持续监控模式

```bash
# 持续监控，每 5 分钟检查一次
check-dolphin monitor -p 123456789 --continuous

# 使用配置文件的持续监控设置
check-dolphin -c config.yaml monitor
```

### 2. 查看工作流状态摘要

```bash
# 查看单个项目状态
check-dolphin status -p 123456789

# 查看多个项目状态
check-dolphin status -p 123456789 987654321

# 使用配置文件
check-dolphin -c config.yaml status
```

### 3. 手动重试特定工作流实例

```bash
check-dolphin retry -p 123456789 -i 456789
```

其中：
- `-p`: 项目代码
- `-i`: 工作流实例 ID

### 4. 生成示例配置文件

```bash
# 生成 YAML 配置文件
check-dolphin config -o config.yaml

# 生成 JSON 配置文件
check-dolphin config -o config.json
```

## API 说明

### DolphinScheduler REST API 端点

本工具使用以下 DolphinScheduler REST API 端点：

1. **获取项目列表**
   ```
   GET /dolphinscheduler/projects
   ```

2. **获取工作流实例列表**
   ```
   GET /dolphinscheduler/projects/{projectCode}/process-instances
   ```

3. **获取工作流实例详情**
   ```
   GET /dolphinscheduler/projects/{projectCode}/process-instances/{id}
   ```

4. **重试工作流实例**
   ```
   POST /dolphinscheduler/projects/{projectCode}/executors/execute
   Body: {
     "processInstanceId": <instance_id>,
     "executeType": "REPEAT_RUNNING"
   }
   ```

### 工作流状态说明

**工作流级别状态**：
- `SUCCESS`: 成功
- `FAILURE`: 失败
- `STOP`: 停止
- `RUNNING_EXECUTION`: 运行中
- `READY_PAUSE`: 准备暂停
- `READY_STOP`: 准备停止
- `SUBMITTED_SUCCESS`: 提交成功
- `SERIAL_WAIT`: 串行等待

**任务级别状态**：
- `SUCCESS`: 任务成功
- `FAILURE`: 任务失败
- `STOP`: 任务停止
- `RUNNING_EXECUTION`: 任务运行中
- `KILL`: 任务被终止

## 智能任务验证机制

在重试工作流之前，系统会执行严格的任务级别验证，确保满足以下**所有条件**：

### 1. 所有任务必须已失败

工作流中的**每个任务**都必须处于失败状态（`FAILURE`、`STOP` 或 `KILL`），才允许重试整个工作流。

**示例场景**：
```
工作流状态：FAILURE
├── 任务A：FAILURE  ✓ 已失败
├── 任务B：FAILURE  ✓ 已失败
└── 任务C：SUCCESS  ✗ 还有成功的任务
结果：不允许重试（不是所有任务都失败）
```

### 2. 任务重试次数必须全部用完

如果任务配置了重试次数（`maxRetryTimes`），必须确认已经达到最大重试次数才能重试工作流。

**示例场景**：
```
任务A：
  - maxRetryTimes: 3  （配置最多重试3次）
  - retryTimes: 2     （已重试2次）
  - 状态：FAILURE
  结果：✗ 不允许重试（还有1次重试机会）

任务B：
  - maxRetryTimes: 3
  - retryTimes: 3     （已重试3次，用完所有机会）
  - 状态：FAILURE
  结果：✓ 允许重试
```

### 3. 不能有任务仍在运行

如果有任何任务还在运行中（`RUNNING_EXECUTION`），不允许重试工作流。

**示例场景**：
```
工作流状态：FAILURE
├── 任务A：FAILURE          ✓ 已失败
├── 任务B：RUNNING_EXECUTION ✗ 仍在运行
└── 任务C：FAILURE          ✓ 已失败
结果：不允许重试（有任务仍在运行）
```

### 验证流程图

```
监控到失败工作流
    ↓
检查工作流实例ID是否有效？
    ↓ 是
检查监控器重试次数是否达到上限？
    ↓ 否
获取工作流的所有任务实例
    ↓
是否有任务仍在运行？
    ↓ 否
是否所有任务都已失败？
    ↓ 是
检查每个失败任务的重试次数
    ↓
所有任务的重试次数都已用完？
    ↓ 是
✓ 标记为待重试任务
    ↓
执行工作流重试
```

### 验证日志示例

**通过验证的情况**：
```
INFO - Workflow 12345 task status: total=3, failed=3, running=0
INFO - Workflow 12345 validation passed: all 3 tasks have failed and exhausted retries
INFO - Retrying workflow: my_workflow (ID: 12345, State: FAILURE)
INFO - Successfully retried workflow 12345, retry count: 1
```

**未通过验证的情况**：
```
INFO - Workflow 12345 task status: total=3, failed=2, running=1
INFO - Cannot retry workflow 12345: Workflow has 1 tasks still running
WARNING - Skip retry for workflow my_workflow (ID: 12345): Workflow has 1 tasks still running
```

```
INFO - Workflow 67890 task status: total=3, failed=3, running=0
INFO - Cannot retry workflow 67890: Some tasks have not exhausted their retry attempts: task_A(2/3), task_B(1/3)
WARNING - Skip retry for workflow my_workflow (ID: 67890): Some tasks have not exhausted their retry attempts
```

## 项目结构

```
check_dolphin/
├── src/
│   └── check_dolphin/
│       ├── __init__.py          # 包初始化
│       ├── api_client.py        # DolphinScheduler API 客户端
│       ├── monitor.py           # 监控和重试逻辑
│       ├── config.py            # 配置管理
│       └── cli.py               # 命令行接口
├── tests/                       # 测试文件
├── requirements.txt             # 依赖列表
├── setup.py                     # 安装脚本
├── .env.example                 # 环境变量示例
├── .gitignore                   # Git 忽略文件
└── README.md                    # 项目说明
```

## 核心模块说明

### api_client.py

DolphinScheduler REST API 客户端，提供以下功能：
- 获取项目列表
- 获取工作流实例列表
- 获取工作流实例详情
- 重试工作流实例
- 获取任务实例列表

### monitor.py

工作流监控器，提供以下功能：
- 获取失败的工作流
- **任务级别验证**：验证所有任务状态和重试次数
- 判断是否应该重试
- 执行重试逻辑
- 持续监控模式
- 生成统计报告

**核心验证方法**：
- `check_task_retry_exhausted()`: 检查单个任务的重试次数是否用完
- `validate_workflow_tasks()`: 验证工作流中所有任务是否满足重试条件

### config.py

配置管理，支持：
- 从 YAML/JSON 文件加载配置
- 从环境变量加载配置
- 配置优先级：环境变量 > 配置文件 > 默认值

### cli.py

命令行接口，提供：
- `monitor`: 监控并重试失败的工作流
- `status`: 查看工作流状态摘要
- `retry`: 手动重试特定工作流
- `config`: 生成示例配置文件

## 示例场景

### 场景 1: 每天定时检查并重试失败任务

创建 cron 任务：

```bash
# 每天早上 9 点检查昨天的失败任务
0 9 * * * cd /path/to/check_dolphin && ./venv/bin/check-dolphin monitor -p 123456789
```

### 场景 2: 持续监控生产环境

```bash
# 以守护进程方式运行
nohup check-dolphin -c config.yaml monitor --continuous > monitor.log 2>&1 &
```

### 场景 3: 检查特定时间段的失败任务

```bash
check-dolphin monitor -p 123456789 \
  --start-date "2025-01-01 00:00:00" \
  --end-date "2025-01-31 23:59:59"
```

## 故障排除

### 1. Token 无效

**错误**: `API request failed: Token verification failed`

**解决方案**:
- 检查 Token 是否正确
- 检查 Token 是否过期
- 在 DolphinScheduler 安全中心重新生成 Token

### 2. 项目代码不存在

**错误**: `Project not found`

**解决方案**:
- 确认项目代码是否正确
- 确认用户是否有权限访问该项目

### 3. 连接超时

**错误**: `Request timeout`

**解决方案**:
- 检查网络连接
- 检查 DolphinScheduler 服务是否正常运行
- 增加 `timeout` 配置值

## 开发

### 运行测试

```bash
python -m pytest tests/
```

### 代码格式化

```bash
black src/
```

### 类型检查

```bash
mypy src/
```

## 参考资料

- [DolphinScheduler 官方文档](https://dolphinscheduler.apache.org)
- [DolphinScheduler API 文档](https://dolphinscheduler.apache.org/python/main/api.html)
- [DolphinScheduler GitHub](https://github.com/apache/dolphinscheduler)

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 作者

Your Name

## 更新日志

### v0.1.0 (2025-12-23)

- 初始版本
- 实现基本的监控和重试功能
- **智能任务验证机制**：
  - 验证所有任务都已失败
  - 验证任务重试次数已用完
  - 检查任务运行状态
- 支持配置文件和环境变量
- 提供命令行工具
