from enum import Enum

class DocumentType(str, Enum):
    """文档类型"""
    STANDUP = "standup"  # 每日站会
    CRITICAL_ISSUE = "critical_issue"  # 关键问题
    SERVICE_STATUS = "service_status"  # 服务状态
    UPDATE = "update"  # 更新

class ServiceStatus(str, Enum):
    """服务状态"""
    UP = "up"  # 正常
    DOWN = "down"  # 停机
    STARTING = "starting"  # 启动中