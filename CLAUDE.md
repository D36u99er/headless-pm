# CLAUDE.md

此文件为Claude Code（claude.ai/code）在处理此仓库代码时提供指导。

## 环境设置

### 自动设置（推荐）
```bash
# 运行通用设置脚本 - 处理特定平台的要求
./setup/universal_setup.sh

# 这将：
# - 检测您的架构（ARM64用于原生Mac，x86_64用于Claude Code）
# - 创建适当的虚拟环境（venv或claude_venv）
# - 为您的平台安装正确的包版本
# - 如需要，从env-example创建.env
```

### 手动设置（如需要）
```bash
# 对于Claude Code（x86_64），使用claude_venv：
python -m venv claude_venv
source claude_venv/bin/activate
pip install pydantic==2.11.7 pydantic-core==2.33.2
pip install -r setup/requirements.txt

# 对于原生Mac（ARM64），使用标准venv：
python -m venv venv
source venv/bin/activate
pip install -r setup/requirements.txt

# 配置环境
cp env-example .env
# 使用API密钥和数据库配置编辑.env

# 初始化数据库
python -m src.cli.main init
python -m src.cli.main seed  # 可选：添加示例数据
```

### 运行应用程序

#### 快速启动（推荐）
```bash
# 首先激活您的虚拟环境
source venv/bin/activate  # 或 source claude_venv/bin/activate

# 使用自动启动脚本（检查环境、数据库、启动服务器）
./start.sh
```

#### 手动启动
```bash
# 运行API服务器
bash start.sh
```

`start.sh`脚本自动：
- ✅ 验证Python 3.11+要求  
- ✅ 检查必需的包是否已安装
- ✅ 如需要，从env-example创建.env
- ✅ 测试数据库连接
- ✅ 如需要，初始化数据库
- ✅ 检查端口可用性
- ✅ 使用正确配置启动服务器
- ✅ 仅启动在.env中定义了端口的服务

**服务端口配置：**
- 仅当在`.env`中定义了端口时才启动服务
- 要跳过某个服务，请删除或注释掉其端口变量：
  - `SERVICE_PORT` - API服务器（默认：6969）
  - `MCP_PORT` - MCP服务器（默认：6968） 
  - `DASHBOARD_PORT` - Web仪表板（默认：3001）

**注意**：运行启动脚本前请激活您的虚拟环境。

## 测试

### 运行测试
```bash
# 重要：为您的平台使用适当的虚拟环境
# 对于Claude Code（x86_64）：
source claude_venv/bin/activate

# 对于原生Mac（ARM64）：
source venv/bin/activate

# 带覆盖率运行所有测试
python -m pytest --cov=src --cov-report=term-missing

# 运行特定测试文件
python -m pytest tests/test_api.py -v
python -m pytest tests/test_models.py -v

# 不带覆盖率运行测试（更快）
python -m pytest -q

# 运行特定测试模式
python -m pytest -k "test_name_pattern"
```

### 测试覆盖状态
- **当前测试**：客户端集成测试
- **测试位置**：`tests/test_headless_pm_client.py`
- **额外测试**：计划的全面测试套件

### 测试架构说明
- API测试使用临时的基于文件的SQLite数据库（非内存）以避免连接问题
- 所有模型、枚举和服务都有全面的测试覆盖
- 测试包括文档创建、提及检测、服务注册表和任务生命周期

## 架构概述

Headless PM是一个用于LLM代理任务协调的REST API，具有基于文档的通信。关键架构决策：

1. **基于文档的通信**：代理通过带@提及支持的文档进行通信
2. **服务注册表**：通过心跳监控跟踪运行中的服务
3. **Git工作流集成**：主要任务使用功能分支和PR，次要任务直接提交到主分支
4. **变更轮询**：高效的轮询端点，代理可获取上次检查以来的更新
5. **基于角色的系统**：五个角色（frontend_dev、backend_dev、qa、architect、pm），每个角色可有多个代理
6. **任务复杂度**：主要/次要分类决定Git工作流（PR vs 直接提交）
7. **全面测试**：78个测试，71%覆盖率，包括完整的API测试

### 增强功能
- **史诗/功能/任务层次结构**：三级项目组织
- **文档表**：带提及检测的代理通信
- **服务注册表**：通过心跳监控和ping URL跟踪微服务
- **提及系统**：跨文档和任务的@用户名通知
- **变更API**：轮询端点返回自某时间戳以来的变更
- **任务复杂度**：主要/次要枚举驱动分支策略
- **连接类型**：区分MCP和客户端连接
- **任务评论**：带@提及的任务协作讨论
- **Python客户端助手**：完整的CLI界面（`headless_pm_client.py`）
- **MCP服务器**：Claude Code的自然语言界面
- **数据库迁移**：模式演进支持
- **Web仪表板**：带分析和监控的实时项目概览
- **基于端口的服务控制**：仅在.env中定义了端口时才启动服务

## 项目结构

```
headless-pm/
├── src/                    # 源代码
│   ├── api/               # FastAPI路由
│   ├── models/            # SQLModel数据库模型
│   ├── services/          # 业务逻辑
│   ├── cli/               # CLI命令
│   ├── mcp/               # MCP服务器实现
│   └── main.py            # FastAPI应用入口点
├── dashboard/             # Next.js Web仪表板
│   ├── src/               # 仪表板源代码
│   └── package.json       # 仪表板依赖项
├── tests/                 # 测试文件
├── migrations/            # 数据库迁移脚本
├── agent_instructions/    # 每个角色的markdown说明
├── agents/                # 代理工具和安装程序
│   └── claude/            # Claude Code专用工具
├── setup/                 # 安装和设置脚本
├── docs/                  # 项目文档
│   └── images/            # 仪表板截图
└── headless_pm_client.py  # Python CLI客户端
```

## 关键API端点

### 核心任务管理
- `POST /api/v1/register` - 注册代理，包含角色/技能级别和连接类型
- `GET /api/v1/context` - 获取项目上下文和路径
- `DELETE /api/v1/agents/{agent_id}` - 删除代理（仅PM）

### 史诗/功能/任务端点
- `POST /api/v1/epics` - 创建史诗（仅PM/架构师）
- `GET /api/v1/epics` - 列出带进度跟踪的史诗
- `DELETE /api/v1/epics/{id}` - 删除史诗（仅PM）
- `POST /api/v1/features` - 在史诗下创建功能
- `GET /api/v1/features/{epic_id}` - 列出史诗的功能
- `DELETE /api/v1/features/{id}` - 删除功能
- `POST /api/v1/tasks/create` - 创建新任务，带复杂度（主要/次要）
- `GET /api/v1/tasks/next` - 获取角色的下一个可用任务
- `POST /api/v1/tasks/{id}/lock` - 锁定任务以防止重复工作
- `PUT /api/v1/tasks/{id}/status` - 更新任务状态
- `POST /api/v1/tasks/{id}/comment` - 添加带@提及支持的评论

### 文档通信
- `POST /api/v1/documents` - 创建带自动@提及检测的文档
- `GET /api/v1/documents` - 列出带过滤的文档
- `GET /api/v1/mentions` - 获取代理的提及

### 服务注册表
- `POST /api/v1/services/register` - 注册服务，带可选ping URL
- `GET /api/v1/services` - 列出所有服务及健康状态
- `POST /api/v1/services/{name}/heartbeat` - 发送服务心跳
- `DELETE /api/v1/services/{name}` - 取消注册服务

### 变更与更新
- `GET /api/v1/changes` - 轮询自某时间戳以来的变更
- `GET /api/v1/changelog` - 获取最近的任务状态变更

## 技术栈

- **FastAPI** - REST API框架
- **SQLModel** - 结合SQLAlchemy + Pydantic的ORM
- **Pydantic** - 数据验证
- **SQLite/MySQL** - 数据库选项
- **Python 3.11+** - 运行时要求

## 开发笔记

### 实现状态
- ✅ **完全实现**：完整的REST API，包含所有端点
- ✅ **数据库模型**：SQLModel，具有适当的关系
- ✅ **CLI界面**：完整的命令行管理工具
- ✅ **Web仪表板**：Next.js仪表板，实时更新
- ✅ **测试**：78个测试，71%覆盖率
- ✅ **文档**：代理说明和工作流指南

### 关键实现细节
- **任务组织**：史诗 → 功能 → 任务层次结构
- **任务难度级别**：初级、高级、首席
- **任务复杂度**：主要（需要PR）、次要（直接提交）
- **代理通信**：通过带@提及检测的文档
- **代理类型**：客户端连接和MCP连接
- **服务监控**：基于心跳的健康跟踪，带可选ping URL
- **变更检测**：自时间戳以来的高效轮询
- **Git集成**：基于任务复杂度的自动化工作流
- **数据库**：SQLModel用于类型安全，支持SQLite和MySQL
- **API验证**：所有请求/响应数据使用Pydantic模型
- **MCP传输**：多种协议（HTTP、SSE、WebSocket、STDIO）
- **令牌跟踪**：MCP会话的使用统计

### 测试环境
- 使用`claude_venv`进行所有测试以确保兼容性
- API测试使用临时的基于文件的SQLite数据库
- 运行`python -m pytest tests/`来运行测试
- 客户端集成测试在`test_headless_pm_client.py`中实现

## Python客户端助手

`headless_pm_client.py`为API提供完整的CLI界面：

### 基本用法
```bash
# 注册代理
./headless_pm_client.py register --agent-id "dev_001" --role "backend_dev" --level "senior"

# 使用史诗/功能/任务
./headless_pm_client.py epics create --name "认证" --description "用户认证系统"
./headless_pm_client.py tasks next --role backend_dev --level senior
./headless_pm_client.py tasks lock 123 --agent-id "dev_001"
./headless_pm_client.py tasks status 123 --status "dev_done" --agent-id "dev_001"

# 与团队沟通
./headless_pm_client.py documents create --type "update" --title "进度" \
  --content "完成登录API @qa_001 请测试" --author-id "dev_001"
  
# 检查更新
./headless_pm_client.py mentions --agent-id "dev_001"
./headless_pm_client.py changes --since 1736359200 --agent-id "dev_001"
```

### 客户端功能
- 自动加载`.env`文件以获取API密钥
- 使用`--help`标志获取全面帮助
- 支持所有API端点
- 嵌入式代理说明
- 多个API密钥来源（按优先级顺序检查）

## 连接类型

代理可以使用两种连接类型注册：

### CLIENT连接
- 直接使用API的代理的默认选项
- 通过`headless_pm_client.py`或直接API调用注册时使用
- 示例：`./headless_pm_client.py register --agent-id "dev_001" --role "backend_dev"`

### MCP连接  
- 使用MCP服务器时自动设置
- 由Claude Code集成使用
- 提供自然语言界面
- 包含令牌使用跟踪

连接类型有助于区分不同的代理界面，并为每种类型启用适当的功能。

### 记忆点
- 8000端口完全用于另一个服务，不要更改！
