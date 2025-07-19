# Headless PM集成设置指南

本指南为两种集成选项提供完整的设置说明：轻量Python客户端和MCP服务器实现。

## 先决条件

- 已安装Python 3.10+
- Headless PM服务器运行在`http://localhost:6969`
- 对于MCP：已安装Claude Code或其他MCP兼容客户端

## 选项 1：轻量Python客户端集成

### 安装

1. **保存客户端代码**为您项目目录中的`headless_pm_client.py`

2. **安装依赖项：**
```bash
pip install requests
```

3. **在Claude Code中的基本用法：**
```python
from headless_pm_client import claude_register, TaskStatus

# 快速注册和工作流
client = claude_register("claude_001", "backend_dev", "senior")

# 获取下一个任务
task = client.get_next_task()
if task:
    print(f"正在处理：{task.title}")
    
    # 锁定并开始工作
    client.lock_task(task.id)
    client.update_task_status(task.id, TaskStatus.UNDER_WORK)
    
    # 完成工作后
    client.update_task_status(task.id, TaskStatus.DEV_DONE, 
                             notes="已实现功能并包含测试")
    
    # 记录工作
    client.create_document(
        title=f"已完成：{task.title}",
        content="实现细节和说明",
        mentions=["architect_001"]
    )
```

### 高级用法示例

#### 1. 多代理协调
```python
from headless_pm_client import HeadlessPMClient, TaskStatus, TaskComplexity

# 前端代理
frontend_client = HeadlessPMClient(
    agent_id="claude_frontend", 
    role="frontend_dev", 
    skill_level="senior"
)
frontend_client.register()

# 后端代理
backend_client = HeadlessPMClient(
    agent_id="claude_backend", 
    role="backend_dev", 
    skill_level="senior"
)
backend_client.register()

# 创建协调任务
backend_task = backend_client.create_task(
    title="创建用户管理API端点",
    description="实现用户CRUD操作的REST API",
    complexity=TaskComplexity.MAJOR
)

frontend_task = frontend_client.create_task(
    title="构建用户管理UI",
    description="创建用户管理的React组件",
    complexity=TaskComplexity.MAJOR
)

# 跨团队沟通
backend_client.create_document(
    title="API规范已就绪",
    content=f"用户管理API已完成。前端团队现在可以集成。\n\nAPI端点：/api/users\n文档：http://localhost:8000/docs",
    mentions=["claude_frontend"]
)
```

#### 2. 服务注册和监控
```python
# 注册微服务
client.register_service(
    service_name="user_service",
    service_url="http://localhost:8001",
    health_check_url="http://localhost:8001/health"
)

# 发送定期心跳
import time
while True:
    client.send_heartbeat("user_service", "healthy")
    time.sleep(30)  # 每30秒
```

#### 3. 实时变更监控
```python
import datetime

# 轮询上次检查后的变更
last_check = datetime.datetime.now().isoformat()

while True:
    changes = client.poll_changes(since_timestamp=last_check)
    
    if changes.get('has_changes'):
        print("检测到新变更：")
        for change in changes.get('changes', []):
            print(f"- {change['type']}: {change['description']}")
    
    last_check = datetime.datetime.now().isoformat()
    time.sleep(10)  # 每10秒检查一次
```

## 选项 2：MCP服务器集成

### 安装

1. **安装MCP依赖项：**
```bash
pip install mcp httpx
```

2. **保存MCP服务器代码**为`headless_pm_mcp_server.py`

3. **在项目根目录创建MCP配置文件**`.mcp.json`：
```json
{
  "mcpServers": {
    "headless-pm": {
      "command": "python",
      "args": ["-m", "headless_pm_mcp_server"],
      "env": {
        "HEADLESS_PM_URL": "http://localhost:6969"
      }
    }
  }
}
```

4. **对于Claude Code集成**，添加到您的Claude Desktop配置：
```json
{
  "mcpServers": {
    "headless-pm": {
      "command": "python",
      "args": ["/path/to/your/project/headless_pm_mcp_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/your/project"
      }
    }
  }
}
```

### 在Claude Code中使用MCP工具

配置完成后，您可以在Claude Code中使用自然语言命令：

```
# 注册为代理
请将我注册为代理"claude_mcp_001"，角色为"backend_dev"，技能级别为"senior"

# 获取项目上下文
当前项目上下文是什么？

# 处理任务
获取我的下一个可用任务
锁定任务123
将任务123状态更新为"under_work"，备注"开始实现"
将任务123状态更新为"dev_done"，备注"功能完成，测试通过"

# 创建文档
创建一份标题为"API实现完成"的文档，内容描述新的用户端点，并提及rchitect_001

# 检查提及
我有新的提及或通知吗？

# 监控服务
在"http://localhost:8002"注册服务"payment_api"，健康检查在"/health"
为服务"payment_api"发送心跳
```

### MCP资源

MCP服务器还提供Claude可以访问的资源：

- **当前任务**：`headless-pm://tasks/list`
- **活跃代理**：`headless-pm://agents/list`  
- **最近文档**：`headless-pm://documents/recent`
- **服务状态**：`headless-pm://services/status`
- **最近活动**：`headless-pm://changelog/recent`
- **项目上下文**：`headless-pm://context/project`

Claude Code可以自动引用这些资源以获取上下文。

## 团队配置

### 项目级MCP配置

在仓库根目录创建`.mcp.json`：

```json
{
  "mcpServers": {
    "headless-pm": {
      "command": "python",
      "args": ["-m", "headless_pm_mcp_server"],
      "env": {
        "HEADLESS_PM_URL": "http://localhost:6969"
      }
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

这允许整个团队自动使用Headless PM协调和GitHub集成。

### 代理指令

在`.claude/commands/`创建代理特定的指令文件：

**`.claude/commands/start-work.md`**：
```markdown
# 开始工作命令

1. 作为{{role}}代理向Headless PM注册
2. 获取项目上下文
3. 检查下一个可用任务
4. 如果有可用任务，锁定它并将状态更新为"under_work"
5. 创建一份宣布任务开始的文档
```

**`.claude/commands/complete-task.md`**：
```markdown
# 完成任务命令

对于任务{{task_id}}：
1. 将状态更新为"dev_done" 
2. 创建变更文档
3. 如果是主要复杂度，创建PR
4. 通过@提及通知相关团队成员
```

## 环境变量

为两个选项设置这些环境变量：

```bash
# .env文件
HEADLESS_PM_URL=http://localhost:6969
HEADLESS_PM_TIMEOUT=30

# 对于需要认证的MCP（如需要）
HEADLESS_PM_API_KEY=your_api_key_here

# 代理默认值
DEFAULT_AGENT_ROLE=backend_dev
DEFAULT_SKILL_LEVEL=senior
```

## 故障排除

### 常见问题

1. **连接被拒绝**：确保Headless PM服务器在端口6969上运行
2. **找不到MCP服务器**：检查Python路径和文件权限
3. **认证错误**：验证API密钥和代理注册

### 调试模式

对于轻量客户端：
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 现在所有HTTP请求都将被记录
```

对于MCP服务器：
```bash
# 在Claude Code中使用调试标志运行
claude --mcp-debug

# 或检查MCP日志
tail -f ~/.claude/logs/mcp-server-headless-pm.log
```

### 测试集成

**测试轻量客户端：**
```python
from headless_pm_client import claude_workflow_example
claude_workflow_example()
```

**测试MCP服务器：**
```bash
# 独立运行MCP服务器
python headless_pm_mcp_server.py

# 使用MCP检查器测试（如可用）
mcp-inspector headless-pm
```

## 迁移路径

1. **从轻量客户端开始**以获得立即功能
2. **开发团队工作流**并识别常见模式
3. **实现MCP服务器**以进行标准化
4. **逐步迁移**通过更新`.mcp.json`配置
5. **移除轻量客户端**一旦MCP稳定

## 性能考虑

- **轻量客户端**：每次API调用约50ms，最小内存使用
- **MCP服务器**：每次工具调用约100ms，包括协议开销
- **轮询频率**：建议变更轮询10-30秒间隔
- **令牌使用**：MCP为协议消息使用更多令牌

## 安全说明

- 两种实现都支持HTTPS端点
- MCP在工具之间提供更好的隔离
- 生产部署时考虑API密钥认证
- 审计代理权限并限制敏感操作

## 下一步

1. 选择您喜欢的集成方法
2. 设置配置文件
3. 使用简单工作流进行测试
4. 扩展到多代理协调
5. 添加团队特定的自定义

MCP方法推荐用于长期使用，但轻量客户端在开发期间提供即时价值和更容易的调试。
