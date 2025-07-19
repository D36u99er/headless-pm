#!/usr/bin/env python3
"""
Headless PM Client - A simple synchronous Python client for the Headless PM API

Usage:
    python headless_pm_client.py --help
    python headless_pm_client.py register --agent-id "backend_dev_senior_001" --role backend_dev --level senior
    python headless_pm_client.py tasks next --role backend_dev --level senior
    python headless_pm_client.py tasks lock 123 --agent-id "backend_dev_senior_001"
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urljoin
from pathlib import Path


def load_env_file():
    """从主项目目录加载.env文件"""
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and not os.getenv(key):  # Don't override existing env vars
                        os.environ[key] = value


class HeadlessPMClient:
    """Headless PM API的简单同步客户端"""
    
    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or os.getenv("HEADLESS_PM_URL", "http://localhost:6969")
        # Try API_KEY_HEADLESS_PM first, then API_KEY from .env, then HEADLESS_PM_API_KEY for backward compatibility
        self.api_key = api_key or os.getenv("API_KEY_HEADLESS_PM") or os.getenv("API_KEY") or os.getenv("HEADLESS_PM_API_KEY", "your-secret-api-key")
        self.headers = {"X-API-Key": self.api_key}
        
    def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """向API发出HTTP请求"""
        url = urljoin(self.base_url, path)
        kwargs.setdefault("headers", {}).update(self.headers)
        
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError as e:
            print(f"错误: {e}")
            if e.response.content:
                try:
                    error_detail = e.response.json().get("detail", str(e))
                    print(f"详情: {error_detail}")
                except:
                    print(f"响应: {e.response.text}")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"连接错误: {e}")
            sys.exit(1)
    
    # Agent Management
    def register_agent(self, agent_id: str, role: str, level: str, connection_type: str = "client"):
        """注册代理"""
        data = {
            "agent_id": agent_id,
            "role": role,
            "level": level,
            "connection_type": connection_type
        }
        return self._request("POST", "/api/v1/register", json=data)
    
    def list_agents(self):
        """列出所有已注册的代理"""
        return self._request("GET", "/api/v1/agents")
    
    def delete_agent(self, agent_id: str, requester_agent_id: str):
        """删除代理（仅PM）"""
        return self._request("DELETE", f"/api/v1/agents/{agent_id}", 
                           params={"requester_agent_id": requester_agent_id})
    
    # Project Context
    def get_context(self):
        """获取项目上下文和配置"""
        return self._request("GET", "/api/v1/context")
    
    # Epic Management
    def create_epic(self, name: str, description: str, agent_id: str):
        """创建新史诗（仅PM/架构师）"""
        data = {"name": name, "description": description}
        return self._request("POST", "/api/v1/epics", json=data, params={"agent_id": agent_id})
    
    def list_epics(self):
        """列出所有史诗及其进度"""
        return self._request("GET", "/api/v1/epics")
    
    def delete_epic(self, epic_id: int, agent_id: str):
        """删除史诗（仅PM）"""
        return self._request("DELETE", f"/api/v1/epics/{epic_id}", params={"agent_id": agent_id})
    
    # Feature Management
    def create_feature(self, epic_id: int, name: str, description: str, agent_id: str):
        """创建新功能（仅PM/架构师）"""
        data = {"epic_id": epic_id, "name": name, "description": description}
        return self._request("POST", "/api/v1/features", json=data, params={"agent_id": agent_id})
    
    def list_features(self, epic_id: int):
        """列出史诗的功能"""
        return self._request("GET", f"/api/v1/features/{epic_id}")
    
    def delete_feature(self, feature_id: int, agent_id: str):
        """删除功能（仅PM）"""
        return self._request("DELETE", f"/api/v1/features/{feature_id}", params={"agent_id": agent_id})
    
    # Task Management
    def create_task(self, feature_id: int, title: str, description: str, target_role: str,
                   difficulty: str, complexity: str, branch: str, agent_id: str):
        """创建新任务"""
        data = {
            "feature_id": feature_id,
            "title": title,
            "description": description,
            "target_role": target_role,
            "difficulty": difficulty,
            "complexity": complexity,
            "branch": branch
        }
        return self._request("POST", "/api/v1/tasks/create", json=data, params={"agent_id": agent_id})
    
    def get_next_task(self, role: str, level: str):
        """获取角色/级别的下一个可用任务"""
        return self._request("GET", "/api/v1/tasks/next", params={"role": role, "level": level})
    
    def lock_task(self, task_id: int, agent_id: str):
        """锁定任务以进行工作"""
        return self._request("POST", f"/api/v1/tasks/{task_id}/lock", params={"agent_id": agent_id})
    
    def update_task_status(self, task_id: int, status: str, agent_id: str, notes: Optional[str] = None):
        """更新任务状态"""
        data = {"status": status}
        if notes:
            data["notes"] = notes
        return self._request("PUT", f"/api/v1/tasks/{task_id}/status", 
                           json=data, params={"agent_id": agent_id})
    
    def add_task_comment(self, task_id: int, comment: str, agent_id: str):
        """向任务添加评论"""
        data = {"comment": comment}
        return self._request("POST", f"/api/v1/tasks/{task_id}/comment", 
                           json=data, params={"agent_id": agent_id})
    
    def delete_task(self, task_id: int, agent_id: str):
        """删除任务（仅PM）"""
        return self._request("DELETE", f"/api/v1/tasks/{task_id}", params={"agent_id": agent_id})
    
    # Document Management
    def create_document(self, doc_type: str, title: str, content: str, author_id: str,
                       meta_data: Optional[Dict] = None, expires_at: Optional[str] = None):
        """创建带@提及支持的文档"""
        data = {
            "doc_type": doc_type,
            "title": title,
            "content": content
        }
        if meta_data:
            data["meta_data"] = meta_data
        if expires_at:
            data["expires_at"] = expires_at
        return self._request("POST", "/api/v1/documents", json=data, params={"author_id": author_id})
    
    def list_documents(self, doc_type: Optional[str] = None, author_id: Optional[str] = None, limit: int = 50):
        """列出带过滤的文档"""
        params = {"limit": limit}
        if doc_type:
            params["doc_type"] = doc_type
        if author_id:
            params["author_id"] = author_id
        return self._request("GET", "/api/v1/documents", params=params)
    
    def get_document(self, document_id: int):
        """获取特定文档"""
        return self._request("GET", f"/api/v1/documents/{document_id}")
    
    def update_document(self, document_id: int, title: Optional[str] = None, 
                       content: Optional[str] = None, meta_data: Optional[Dict] = None):
        """更新文档"""
        data = {}
        if title:
            data["title"] = title
        if content:
            data["content"] = content
        if meta_data:
            data["meta_data"] = meta_data
        return self._request("PUT", f"/api/v1/documents/{document_id}", json=data)
    
    def delete_document(self, document_id: int):
        """删除文档"""
        return self._request("DELETE", f"/api/v1/documents/{document_id}")
    
    # Service Registry
    def register_service(self, service_name: str, ping_url: str, agent_id: str, 
                        port: Optional[int] = None, status: str = "up", meta_data: Optional[Dict] = None):
        """注册或更新服务"""
        data = {
            "service_name": service_name,
            "ping_url": ping_url,
            "status": status
        }
        if port:
            data["port"] = port
        if meta_data:
            data["meta_data"] = meta_data
        return self._request("POST", "/api/v1/services/register", json=data, params={"agent_id": agent_id})
    
    def list_services(self):
        """列出所有服务"""
        return self._request("GET", "/api/v1/services")
    
    def service_heartbeat(self, service_name: str, agent_id: str):
        """发送服务心跳"""
        return self._request("POST", f"/api/v1/services/{service_name}/heartbeat", 
                           params={"agent_id": agent_id})
    
    def unregister_service(self, service_name: str, agent_id: str):
        """取消注册服务"""
        return self._request("DELETE", f"/api/v1/services/{service_name}", 
                           params={"agent_id": agent_id})
    
    # Mentions
    def get_mentions(self, agent_id: str = None, unread_only: bool = True, limit: int = 50):
        """获取代理的提及（如果未提供agent_id，则获取所有代理）"""
        params = {"unread_only": unread_only, "limit": limit}
        if agent_id:
            params["agent_id"] = agent_id
        return self._request("GET", "/api/v1/mentions", params=params)
    
    def mark_mention_read(self, mention_id: int, agent_id: str):
        """将提及标记为已读"""
        return self._request("PUT", f"/api/v1/mentions/{mention_id}/read", 
                           params={"agent_id": agent_id})
    
    # Changes
    def get_changes(self, since: str, agent_id: str):
        """轮询自时间戳以来的变更"""
        return self._request("GET", "/api/v1/changes", 
                           params={"since": since, "agent_id": agent_id})
    
    # Changelog
    def get_changelog(self, limit: int = 50):
        """获取最近的任务状态变更"""
        return self._request("GET", "/api/v1/changelog", params={"limit": limit})
    


def format_output(data: Any):
    """美化打印JSON输出"""
    print(json.dumps(data, indent=2, default=str))


def validate_args(args, parser):
    """验证参数并提供有用的错误消息"""
    
    # Check for common mistake: trying to use "tasks list"
    if args.command == "tasks" and hasattr(args, 'task_action') and args.task_action == "list":
        print("错误: 没有'tasks list'命令")
        print("\n要获取可用任务，请使用: python3 headless_pm_client.py tasks next --role YOUR_ROLE --level YOUR_LEVEL")
        print("示例: python3 headless_pm_client.py tasks next --role backend_dev --level senior")
        print("\n这将返回适合您角色和技能级别的下一个可用任务。")
        sys.exit(1)
    
    # Custom validation for tasks next command
    if args.command == "tasks" and args.task_action == "next":
        if not hasattr(args, 'role') or not args.role:
            print("错误: tasks next需要--role参数")
            print("示例: python3 headless_pm_client.py tasks next --role backend_dev --level senior")
            print("\n可用角色: frontend_dev, backend_dev, qa, architect, pm")
            sys.exit(1)
        if not hasattr(args, 'level') or not args.level:
            print("错误: tasks next需要--level参数")
            print("示例: python3 headless_pm_client.py tasks next --role backend_dev --level senior")
            print("\n可用级别: junior, senior, principal")
            sys.exit(1)
    
    # Custom validation for changes command
    elif args.command == "changes":
        if not hasattr(args, 'since') or not args.since:
            print("错误: changes命令需要--since参数（Unix时间戳）")
            print("示例: python3 headless_pm_client.py changes --since 1736359200 --agent-id 'backend_dev_001'")
            sys.exit(1)
        if not hasattr(args, 'agent_id') or not args.agent_id:
            print("错误: changes命令需要--agent-id参数")
            print("示例: python3 headless_pm_client.py changes --since 1736359200 --agent-id 'backend_dev_001'")
            sys.exit(1)
    
    # Custom validation for mentions command - removed as agent_id is now optional
    
    # Validation for task status
    elif args.command == "tasks" and args.task_action == "status":
        if not hasattr(args, 'agent_id') or not args.agent_id:
            print("错误: tasks status需要--agent-id参数")
            print("示例: python3 headless_pm_client.py tasks status 123 --status dev_done --agent-id 'backend_dev_001'")
            sys.exit(1)
        if not hasattr(args, 'status') or not args.status:
            print("错误: tasks status需要--status参数")
            print("示例: python3 headless_pm_client.py tasks status 123 --status dev_done --agent-id 'backend_dev_001'")
            print("\n可用状态: created, under_work, dev_done, qa_done, documentation_done, committed")
            sys.exit(1)

def main():
    # Load .env file before processing arguments
    load_env_file()
    
    epilog_text = """
================================================================================
共享代理指令
================================================================================

所有代理都应遵循这些通用指令。

## 核心职责

### 获取您的API密钥：
- API可以从headless_pm/.env获取

### 注册您自己（关键）
- 根据您的代理角色注册自己：`python3 headless_pm_client.py register --agent-id "YOUR_AGENT_ID" --role YOUR_ROLE --level YOUR_LEVEL`
- 注册会自动返回您的下一个可用任务和任何未读提及
- 注册您管理的任何服务（参考service_responsibilities.md）

### 保持持续可用（关键）
- 每次接受新任务时监控@提及，并在15分钟内响应
- 闲置较长时间时发布每小时状态更新
- 完成任务后如果没有下一个任务，运行API指示的脚本
- 当您从API获得任务时，立即锁定并开始工作，不要停止

### 进度报告（关键）
**您必须主动报告您的进度**：
- 仅在需要其他团队成员时创建文档
- 立即报告阻塞器和问题
- 随着进展更新任务状态
- 使用@提及通知团队成员

### 沟通标准
- 始终提供详细、全面的内容
- 包括完整的上下文和技术细节
- 记录所有重要决策
- 在相关时分享截图/代码示例

## 任务工作流

### 1. 开始工作
- 检查可用任务：`python3 headless_pm_client.py tasks next --role YOUR_ROLE --level YOUR_LEVEL`
- 开始前锁定任务：`python3 headless_pm_client.py tasks lock TASK_ID --agent-id "YOUR_AGENT_ID"`
- 将状态更新为`under_work`：`python3 headless_pm_client.py tasks status TASK_ID --status under_work --agent-id "YOUR_AGENT_ID"`
- 创建一份宣布您正在处理的工作的文档：`python3 headless_pm_client.py documents create --type update --title "开始任务X" --content "开始处理TASK_TITLE" --author-id "YOUR_AGENT_ID"`

### 2. 工作期间
- 立即记录任何阻塞器
- 分享技术决策
- 需要时寻求帮助
- 必要时为其他团队成员创建任务

### 3. 完成工作
- 将状态更新为`dev_done`（对于开发者）或适当的状态：`python3 headless_pm_client.py tasks status TASK_ID --status dev_done --agent-id "YOUR_AGENT_ID" --notes "完成实现"`
- 创建包含可交付成果的完成文档：`python3 headless_pm_client.py documents create --type update --title "完成任务X" --content "完成TASK_TITLE。可交付成果：..." --author-id "YOUR_AGENT_ID"`
- 通知相关团队成员：在文档内容中使用@提及，例如，"@qa_001 准备好进行测试"
- 如适用，提交代码
- 完成任务后如果没有下一个任务，运行API指示的任何脚本

## 状态进展

### 开发流程
- `created`（已创建） → `under_work`（进行中） → `dev_done`（开发完成） → `qa_done`（测试完成） → `documentation_done`（文档完成） → `committed`（已提交）

### 关键状态规则
- 一次只能有一个任务处于`under_work`状态
- 更新状态时始终包含详细的备注
- 从`under_work`移出时状态会自动解锁任务

## Git工作流

### 次要任务（直接到主分支）
- 错误修复、小更新、文档
- 直接提交到主分支
- 将状态更新为`committed`

### 主要任务（功能分支）
- 新功能、破坏性变更
- 创建功能分支
- 提交PR进行审查
- 合并后将状态更新为`committed`

## 文档类型

- `status_update` - 通用状态公告
- `task_start` - 开始任务时
- `progress_update` - 每小时进度报告
- `task_complete` - 完成任务时
- `critical_issue` - 阻塞问题
- `update` - 通用更新
- `decision` - 架构/设计决策
- `review` - 代码/设计审查
- `standup` - 每日站会

## 服务管理

### 注册服务
对于您正在运行的微服务：
- 使用名称、URL和健康检查注册：`python3 headless_pm_client.py services register --name "SERVICE_NAME" --ping-url "http://localhost:PORT/health" --agent-id "YOUR_AGENT_ID" --port PORT`
- 如果服务尚未运行，启动它。 
- 检查服务是否按预期响应，如果不是，杀死旧进程并重新启动。

## 错误处理

始终优雅地处理错误：
- 捕获异常
- 清楚地记录错误
- 为阻塞器创建critical_issue文档
- 尽可能提供解决方案

## 持续运营最佳实践

### 积极工作期间
2. **具体** - 包括ID、错误消息、截图
3. **保持专注** - 一次一个任务
4. **彻底测试** - 在标记dev_done之前
4. **不要模拟** - 创建功能和E2E测试，除非被指示，否则不要模拟
5. **良好的文档** - 帮助未来的团队成员
6. **协作** - 使用@提及，提出问题

## 技能级别

- **junior**（初级） - 简单任务、基本功能、错误修复
- **senior**（高级） - 复杂功能、系统设计、优化
- **principal**（首席） - 架构、标准、团队领导

## 环境变量

关键路径和设置：
- `${SHARED_PATH}` - 用于工件的共享文件系统
- API始终运行在`http://localhost:6969`
- 检查`.env`以获取API密钥和配置

## 代理生命周期与持续运营


### 示例代理会话流程
```bash
# 1. 启动会话 - 注册并获取初始工作
python3 headless_pm_client.py register --agent-id "backend_dev_001" --role backend_dev --level senior

# 2. 处理分配的任务（如果有）
# ... 任务工作循环 ...

# 3. 通过API领取下一个任务
重要：无论何时完成您正在处理的工作，调用API获取下一个任务。

注意：API可能需要一段时间才能响应。请继续等待。

## 记住

目标是通过**持续可用性**实现高效的异步协作。您的更新和文档是团队保持同步的方式。在有疑问时，宁可多沟通也不要少沟通。

================================================================================
快速入门 - 常用命令示例
================================================================================

🚀 开始使用：
  python3 headless_pm_client.py register --agent-id "backend_dev_001" --role backend_dev --level senior
  # 注册返回您的代理信息、下一个可用任务和未读提及
  python3 headless_pm_client.py context

📋 处理任务：
  # 获取您的下一个任务（必须：--role和--level）
  python3 headless_pm_client.py tasks next --role backend_dev --level senior
  
  # 锁定任务（必须：task_id和--agent-id）
  python3 headless_pm_client.py tasks lock 123 --agent-id "backend_dev_001"
  
  # 更新任务状态（必须：task_id、--status和--agent-id）
  python3 headless_pm_client.py tasks status 123 --status under_work --agent-id "backend_dev_001"
  
  # 向任务添加评论
  python3 headless_pm_client.py tasks comment 123 --comment "正在处理这个 @qa_001" --agent-id "backend_dev_001"

  # 注意：没有'tasks list'命令 - 使用'tasks next'获取可用任务

📄 创建文档：
  # 创建更新文档
  python3 headless_pm_client.py documents create --type update --title "开始工作" --content "开始任务实现" --author-id "backend_dev_001"
  
  # 创建关键问题
  python3 headless_pm_client.py documents create --type critical_issue --title "阻塞问题" --content "数据库连接失败 @pm_001" --author-id "backend_dev_001"

🔄 轮询变更（必须：--since和--agent-id）：
  python3 headless_pm_client.py changes --since 1736359200 --agent-id "backend_dev_001"

📢 检查提及（必须：--agent-id）：
  python3 headless_pm_client.py mentions --agent-id "backend_dev_001"
  
🚀 重要：请求新任务时，API可能需要几分钟才能响应。请耐心等待。

================================================================================
完整命令参考
================================================================================

代理管理：
  register              - 注册带角色和技能级别的代理（返回代理信息、下一个任务和提及）
  agents list           - 列出所有已注册的代理  
  agents delete         - 删除代理（仅PM）
  context               - 获取项目上下文和配置
  
史诗管理：
  epics create          - 创建新史诗（仅PM/架构师）
  epics list            - 列出所有史诗及其进度
  epics delete          - 删除史诗（仅PM）
  
功能管理：
  features create       - 创建新功能（仅PM/架构师）  
  features list         - 列出史诗的功能
  features delete       - 删除功能（仅PM）
  
任务管理：
  tasks create          - 创建新任务
  tasks next            - 获取您角色/级别的下一个可用任务（需要：--role, --level）
  tasks lock            - 锁定任务以进行工作（需要：task_id, --agent-id）
  tasks status          - 更新任务状态（需要：task_id, --status, --agent-id）
  tasks comment         - 向任务添加带@提及的评论（需要：task_id, --comment, --agent-id）
  tasks delete          - 删除任务（仅PM）
  
文档管理：
  documents create      - 创建文档（需要：--type, --title, --content, --author-id）
  documents list        - 列出带过滤的文档
  documents get         - 按ID获取特定文档
  documents update      - 更新现有文档
  documents delete      - 删除文档
  
服务注册表：
  services register     - 注册/更新服务
  services list         - 列出所有已注册的服务
  services heartbeat    - 发送服务心跳
  services unregister   - 从注册表中删除服务
  
通知：
  mentions              - 获取代理的提及（需要：--agent-id）
  mention-read          - 将提及标记为已读
  
更新：
  changes               - 轮询自时间戳以来的变更（需要：--since, --agent-id）
  changelog             - 获取最近的任务状态变更

环境变量：
  HEADLESS_PM_URL       - API基础URL（默认：http://localhost:6969）
  API_KEY_HEADLESS_PM   - API认证密钥（最高优先级）
  API_KEY               - API认证密钥（来自.env文件）
  HEADLESS_PM_API_KEY   - API认证密钥（备用）

客户端会自动从项目根目录加载.env文件。

要获取任何命令的详细帮助，请使用：python3 headless_pm_client.py <command> -h
"""
    
    parser = argparse.ArgumentParser(
        description="Headless PM客户端 - Headless PM API的命令行界面",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog_text
    )
    
    # Global options
    parser.add_argument("--url", help="API base URL (default: $HEADLESS_PM_URL or http://localhost:6969)")
    parser.add_argument("--api-key", help="API key (default: $HEADLESS_PM_API_KEY)")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # Register agent
    register_parser = subparsers.add_parser("register", 
                                           help="注册代理（返回代理信息、下一个任务和提及）")
    register_parser.add_argument("--agent-id", required=True, help="唯一代理标识符")
    register_parser.add_argument("--role", required=True, 
                               choices=["frontend_dev", "backend_dev", "qa", "architect", "pm"])
    register_parser.add_argument("--level", required=True, 
                               choices=["junior", "senior", "principal"])
    register_parser.add_argument("--connection-type", default="client", 
                               choices=["client", "mcp"], help="连接类型")
    
    # List agents
    agents_parser = subparsers.add_parser("agents", help="代理管理")
    agents_sub = agents_parser.add_subparsers(dest="agents_action")
    
    agents_sub.add_parser("list", help="列出所有已注册的代理")
    
    agents_delete = agents_sub.add_parser("delete", help="删除代理（仅PM）")
    agents_delete.add_argument("--agent-id", required=True, help="要删除的代理ID")
    agents_delete.add_argument("--requester-agent-id", required=True, help="发出请求的PM代理ID")
    
    # Get context
    subparsers.add_parser("context", help="获取项目上下文和配置")
    
    # Epic commands
    epic_parser = subparsers.add_parser("epics", help="史诗管理")
    epic_sub = epic_parser.add_subparsers(dest="epic_action")
    
    epic_create = epic_sub.add_parser("create", help="创建新史诗（仅PM/架构师）")
    epic_create.add_argument("--name", required=True, help="史诗名称")
    epic_create.add_argument("--description", required=True, help="史诗描述")
    epic_create.add_argument("--agent-id", required=True, help="代理ID（必须是PM/架构师）")
    
    epic_sub.add_parser("list", help="列出所有史诗")
    
    epic_delete = epic_sub.add_parser("delete", help="删除史诗（仅PM）")
    epic_delete.add_argument("--epic-id", type=int, required=True, help="要删除的史诗ID")
    epic_delete.add_argument("--agent-id", required=True, help="PM代理ID")
    
    # Feature commands
    feature_parser = subparsers.add_parser("features", help="功能管理")
    feature_sub = feature_parser.add_subparsers(dest="feature_action")
    
    feature_create = feature_sub.add_parser("create", help="创建新功能（仅PM/架构师）")
    feature_create.add_argument("--epic-id", type=int, required=True, help="史诗ID")
    feature_create.add_argument("--name", required=True, help="功能名称")
    feature_create.add_argument("--description", required=True, help="功能描述")
    feature_create.add_argument("--agent-id", required=True, help="代理ID（必须是PM/架构师）")
    
    feature_list = feature_sub.add_parser("list", help="列出史诗的功能")
    feature_list.add_argument("--epic-id", type=int, required=True, help="史诗ID")
    
    feature_delete = feature_sub.add_parser("delete", help="删除功能（仅PM）")
    feature_delete.add_argument("--feature-id", type=int, required=True, help="要删除的功能ID")
    feature_delete.add_argument("--agent-id", required=True, help="PM代理ID")
    
    # Task commands
    task_parser = subparsers.add_parser("tasks", help="任务管理")
    task_sub = task_parser.add_subparsers(dest="task_action")
    
    task_create = task_sub.add_parser("create", help="创建新任务")
    task_create.add_argument("--feature-id", type=int, required=True, help="功能ID")
    task_create.add_argument("--title", required=True, help="任务标题")
    task_create.add_argument("--description", required=True, help="任务描述")
    task_create.add_argument("--target-role", required=True, 
                           choices=["frontend_dev", "backend_dev", "qa", "architect", "pm"])
    task_create.add_argument("--difficulty", required=True, 
                           choices=["junior", "senior", "principal"])
    task_create.add_argument("--complexity", required=True, 
                           choices=["major", "minor"])
    task_create.add_argument("--branch", required=True, help="Git分支名称")
    task_create.add_argument("--agent-id", required=True, help="创建者代理ID")
    
    task_next = task_sub.add_parser("next", 
                                    help="获取您角色/级别的下一个可用任务",
                                    epilog="示例: python3 headless_pm_client.py tasks next --role backend_dev --level senior")
    task_next.add_argument("--role", required=True, 
                          choices=["frontend_dev", "backend_dev", "qa", "architect", "pm"],
                          help="您的代理角色（必须）")
    task_next.add_argument("--level", required=True, 
                          choices=["junior", "senior", "principal"],
                          help="您的技能级别（必须）")
    
    task_lock = task_sub.add_parser("lock", 
                                   help="锁定任务以进行工作",
                                   epilog="示例: python3 headless_pm_client.py tasks lock 123 --agent-id 'backend_dev_001'")
    task_lock.add_argument("task_id", type=int, help="要锁定的任务ID")
    task_lock.add_argument("--agent-id", required=True, help="您的代理ID（必须）")
    
    task_status = task_sub.add_parser("status", 
                                     help="更新任务状态",
                                     epilog="示例: python3 headless_pm_client.py tasks status 123 --status dev_done --agent-id 'backend_dev_001' --notes '实现完成'")
    task_status.add_argument("task_id", type=int, help="任务ID")
    task_status.add_argument("--status", required=True, 
                           choices=["created", "under_work", "dev_done", 
                                   "qa_done", "documentation_done", "committed"],
                           help="新任务状态（必须）")
    task_status.add_argument("--agent-id", required=True, help="您的代理ID（必须）")
    task_status.add_argument("--notes", help="关于状态变更的可选备注")
    
    task_comment = task_sub.add_parser("comment", help="向任务添加评论")
    task_comment.add_argument("task_id", type=int, help="任务ID")
    task_comment.add_argument("--comment", required=True, help="评论文本（支持@提及）")
    task_comment.add_argument("--agent-id", required=True, help="代理ID")
    
    task_delete = task_sub.add_parser("delete", help="删除任务（仅PM）")
    task_delete.add_argument("task_id", type=int, help="要删除的任务ID")
    task_delete.add_argument("--agent-id", required=True, help="PM代理ID")
    
    # Document commands
    doc_parser = subparsers.add_parser("documents", help="文档管理")
    doc_sub = doc_parser.add_subparsers(dest="doc_action")
    
    doc_create = doc_sub.add_parser("create", 
                                   help="创建带@提及支持的文档",
                                   epilog="示例: python3 headless_pm_client.py documents create --type update --title 'API设计' --content '正在处理认证 @architect_001' --author-id 'backend_dev_001'")
    doc_create.add_argument("--type", required=True, 
                          choices=["standup", "critical_issue", "service_status", "update"],
                          help="文档类型（必须）")
    doc_create.add_argument("--title", required=True, help="文档标题（必须）")
    doc_create.add_argument("--content", required=True, help="文档内容，支持@提及（必须）")
    doc_create.add_argument("--author-id", required=True, help="您的代理ID（必须）")
    doc_create.add_argument("--meta-data", help="JSON元数据（可选）")
    doc_create.add_argument("--expires-at", help="ISO格式的过期日期时间（可选）")
    
    doc_list = doc_sub.add_parser("list", help="列出文档")
    doc_list.add_argument("--type", choices=["standup", "critical_issue", "service_status", "update"])
    doc_list.add_argument("--author-id", help="按作者过滤")
    doc_list.add_argument("--limit", type=int, default=50, help="最大结果数")
    
    doc_get = doc_sub.add_parser("get", help="获取特定文档")
    doc_get.add_argument("document_id", type=int, help="文档ID")
    
    doc_update = doc_sub.add_parser("update", help="更新文档")
    doc_update.add_argument("document_id", type=int, help="文档ID")
    doc_update.add_argument("--title", help="新标题")
    doc_update.add_argument("--content", help="新内容")
    doc_update.add_argument("--meta-data", help="新JSON元数据")
    
    doc_delete = doc_sub.add_parser("delete", help="删除文档")
    doc_delete.add_argument("document_id", type=int, help="文档ID")
    
    # Service commands
    service_parser = subparsers.add_parser("services", help="服务注册表")
    service_sub = service_parser.add_subparsers(dest="service_action")
    
    service_register = service_sub.add_parser("register", help="注册服务")
    service_register.add_argument("--name", required=True, help="服务名称")
    service_register.add_argument("--ping-url", required=True, help="健康检查URL")
    service_register.add_argument("--agent-id", required=True, help="所有者代理ID")
    service_register.add_argument("--port", type=int, help="端口号")
    service_register.add_argument("--status", default="up", choices=["up", "down", "starting"])
    service_register.add_argument("--meta-data", help="JSON元数据")
    
    service_sub.add_parser("list", help="列出所有服务")
    
    service_heartbeat = service_sub.add_parser("heartbeat", help="发送心跳")
    service_heartbeat.add_argument("service_name", help="服务名称")
    service_heartbeat.add_argument("--agent-id", required=True, help="所有者代理ID")
    
    service_unregister = service_sub.add_parser("unregister", help="取消注册服务")
    service_unregister.add_argument("service_name", help="服务名称")
    service_unregister.add_argument("--agent-id", required=True, help="所有者代理ID")
    
    # Mentions
    mentions_parser = subparsers.add_parser("mentions", 
                                          help="获取您的代理或所有代理的@提及",
                                          epilog="示例:\n  python3 headless_pm_client.py mentions --agent-id 'backend_dev_001'  # 获取特定代理的提及\n  python3 headless_pm_client.py mentions  # 获取所有代理的所有提及")
    mentions_parser.add_argument("--agent-id", help="您的代理ID（可选 - 如果未提供则返回所有提及）")
    mentions_parser.add_argument("--all", action="store_true", help="包括已读提及")
    mentions_parser.add_argument("--limit", type=int, default=50, help="最大结果数（默认：50）")
    
    mention_read = subparsers.add_parser("mention-read", help="将提及标记为已读")
    mention_read.add_argument("mention_id", type=int, help="提及ID")
    mention_read.add_argument("--agent-id", required=True, help="代理ID")
    
    # Changes
    changes_parser = subparsers.add_parser("changes", 
                                         help="轮询自某时间戳以来的变更",
                                         epilog="示例: python3 headless_pm_client.py changes --since 1736359200 --agent-id 'backend_dev_001'\n注意: 使用Unix时间戳（自纪元以来的秒数）")
    changes_parser.add_argument("--since", required=True, help="获取此后变更的Unix时间戳（必须）")
    changes_parser.add_argument("--agent-id", required=True, help="您的代理ID（必须）")
    
    # Changelog
    changelog_parser = subparsers.add_parser("changelog", help="获取最近的任务变更")
    changelog_parser.add_argument("--limit", type=int, default=50, help="最大结果数")
    
    # Token usage
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Validate arguments for better error messages
    validate_args(args, parser)
    
    # Initialize client
    client = HeadlessPMClient(args.url, args.api_key)
    
    # Execute commands
    try:
        if args.command == "register":
            result = client.register_agent(args.agent_id, args.role, args.level, args.connection_type)
            
        elif args.command == "agents":
            if args.agents_action == "list" or not args.agents_action:
                result = client.list_agents()
            elif args.agents_action == "delete":
                result = client.delete_agent(args.agent_id, args.requester_agent_id)
            else:
                agents_parser.print_help()
                sys.exit(1)
            
        elif args.command == "context":
            result = client.get_context()
            
        elif args.command == "epics":
            if args.epic_action == "create":
                result = client.create_epic(args.name, args.description, args.agent_id)
            elif args.epic_action == "list":
                result = client.list_epics()
            elif args.epic_action == "delete":
                result = client.delete_epic(args.epic_id, args.agent_id)
            else:
                epic_parser.print_help()
                sys.exit(1)
                
        elif args.command == "features":
            if args.feature_action == "create":
                result = client.create_feature(args.epic_id, args.name, args.description, args.agent_id)
            elif args.feature_action == "list":
                result = client.list_features(args.epic_id)
            elif args.feature_action == "delete":
                result = client.delete_feature(args.feature_id, args.agent_id)
            else:
                feature_parser.print_help()
                sys.exit(1)
                
        elif args.command == "tasks":
            if args.task_action == "create":
                result = client.create_task(args.feature_id, args.title, args.description,
                                          args.target_role, args.difficulty, args.complexity,
                                          args.branch, args.agent_id)
            elif args.task_action == "next":
                result = client.get_next_task(args.role, args.level)
            elif args.task_action == "lock":
                result = client.lock_task(args.task_id, args.agent_id)
            elif args.task_action == "status":
                result = client.update_task_status(args.task_id, args.status, args.agent_id, args.notes)
            elif args.task_action == "comment":
                result = client.add_task_comment(args.task_id, args.comment, args.agent_id)
            elif args.task_action == "delete":
                result = client.delete_task(args.task_id, args.agent_id)
            else:
                task_parser.print_help()
                sys.exit(1)
                
        elif args.command == "documents":
            if args.doc_action == "create":
                meta_data = json.loads(args.meta_data) if args.meta_data else None
                result = client.create_document(args.type, args.title, args.content,
                                              args.author_id, meta_data, args.expires_at)
            elif args.doc_action == "list":
                result = client.list_documents(args.type, args.author_id, args.limit)
            elif args.doc_action == "get":
                result = client.get_document(args.document_id)
            elif args.doc_action == "update":
                meta_data = json.loads(args.meta_data) if args.meta_data else None
                result = client.update_document(args.document_id, args.title, args.content, meta_data)
            elif args.doc_action == "delete":
                result = client.delete_document(args.document_id)
            else:
                doc_parser.print_help()
                sys.exit(1)
                
        elif args.command == "services":
            if args.service_action == "register":
                meta_data = json.loads(args.meta_data) if args.meta_data else None
                result = client.register_service(args.name, args.ping_url, args.agent_id,
                                               args.port, args.status, meta_data)
            elif args.service_action == "list":
                result = client.list_services()
            elif args.service_action == "heartbeat":
                result = client.service_heartbeat(args.service_name, args.agent_id)
            elif args.service_action == "unregister":
                result = client.unregister_service(args.service_name, args.agent_id)
            else:
                service_parser.print_help()
                sys.exit(1)
                
        elif args.command == "mentions":
            result = client.get_mentions(args.agent_id if hasattr(args, 'agent_id') else None, not args.all, args.limit)
            
        elif args.command == "mention-read":
            result = client.mark_mention_read(args.mention_id, args.agent_id)
            
        elif args.command == "changes":
            result = client.get_changes(args.since, args.agent_id)
            
        elif args.command == "changelog":
            result = client.get_changelog(args.limit)
            
            
        else:
            parser.print_help()
            sys.exit(1)
            
        format_output(result)
        
    except KeyboardInterrupt:
        print("\n中断")
        sys.exit(130)


if __name__ == "__main__":
    main()
