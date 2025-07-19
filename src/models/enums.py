from enum import Enum
from typing import Any

class TaskStatus(str, Enum):
    """任务状态"""
    CREATED = "created"  # 已创建
    UNDER_WORK = "under_work"  # 进行中
    DEV_DONE = "dev_done"  # 开发完成
    QA_DONE = "qa_done"  # 测试完成
    DOCUMENTATION_DONE = "documentation_done"  # 文档完成
    COMMITTED = "committed"  # 已提交
    # Legacy statuses (deprecated but kept for backward compatibility)
    EVALUATION = "evaluation"  # 评估中（已弃用）
    APPROVED = "approved"  # 已批准（已弃用）

class AgentRole(str, Enum):
    """代理角色"""
    FRONTEND_DEV = "frontend_dev"  # 前端开发
    BACKEND_DEV = "backend_dev"  # 后端开发
    QA = "qa"  # 质量保证
    ARCHITECT = "architect"  # 架构师
    PM = "pm"  # 项目经理

class DifficultyLevel(str, Enum):
    """难度级别"""
    JUNIOR = "junior"  # 初级
    SENIOR = "senior"  # 高级
    PRINCIPAL = "principal"  # 首席

class TaskComplexity(str, Enum):
    """任务复杂度"""
    MINOR = "minor"  # 次要 - 直接提交到主分支
    MAJOR = "major"  # 主要 - 需要PR

class ConnectionType(str, Enum):
    """连接类型"""
    MCP = "mcp"      # MCP协议 - Model Context Protocol
    CLIENT = "client"  # 客户端 - Direct API client

class TaskType(str, Enum):
    """任务类型"""
    REGULAR = "regular"   # 常规 - Normal development task
    WAITING = "waiting"   # 等待中 - Synthetic waiting task for polling