"""
枚举类型的中文翻译映射
"""

from src.models.enums import TaskStatus, AgentRole, DifficultyLevel, TaskComplexity, ConnectionType, TaskType
from src.models.document_enums import DocumentType, ServiceStatus

# 任务状态中文映射
TASK_STATUS_CN = {
    TaskStatus.CREATED: "已创建",
    TaskStatus.UNDER_WORK: "进行中",
    TaskStatus.DEV_DONE: "开发完成",
    TaskStatus.QA_DONE: "测试完成",
    TaskStatus.DOCUMENTATION_DONE: "文档完成",
    TaskStatus.COMMITTED: "已提交",
    TaskStatus.EVALUATION: "评估中",
    TaskStatus.APPROVED: "已批准"
}

# 代理角色中文映射
AGENT_ROLE_CN = {
    AgentRole.FRONTEND_DEV: "前端开发",
    AgentRole.BACKEND_DEV: "后端开发",
    AgentRole.QA: "质量保证",
    AgentRole.ARCHITECT: "架构师",
    AgentRole.PM: "项目经理"
}

# 难度级别中文映射
DIFFICULTY_LEVEL_CN = {
    DifficultyLevel.JUNIOR: "初级",
    DifficultyLevel.SENIOR: "高级",
    DifficultyLevel.PRINCIPAL: "首席"
}

# 任务复杂度中文映射
TASK_COMPLEXITY_CN = {
    TaskComplexity.MINOR: "次要",
    TaskComplexity.MAJOR: "主要"
}

# 连接类型中文映射
CONNECTION_TYPE_CN = {
    ConnectionType.MCP: "MCP协议",
    ConnectionType.CLIENT: "客户端"
}

# 任务类型中文映射
TASK_TYPE_CN = {
    TaskType.REGULAR: "常规",
    TaskType.WAITING: "等待中"
}

# 文档类型中文映射
DOCUMENT_TYPE_CN = {
    DocumentType.STANDUP: "每日站会",
    DocumentType.UPDATE: "更新",
    DocumentType.OBSERVATION: "观察",
    DocumentType.ISSUE: "问题",
    DocumentType.DECISION: "决策",
    DocumentType.RETROSPECTIVE: "回顾",
    DocumentType.PROPOSAL: "提案",
    DocumentType.ANNOUNCEMENT: "公告",
    DocumentType.RESEARCH: "研究",
    DocumentType.TUTORIAL: "教程",
    DocumentType.CRITICAL_ISSUE: "关键问题",
    DocumentType.PERFORMANCE_ISSUE: "性能问题",
    DocumentType.USER_STORY: "用户故事",
    DocumentType.TEST_RESULT: "测试结果",
    DocumentType.METRICS: "指标",
    DocumentType.GUIDELINES: "指南",
    DocumentType.EXPERIMENT: "实验",
    DocumentType.SUMMARY: "总结",
    DocumentType.REPORT: "报告",
    DocumentType.CHANGELOG: "更新日志",
    DocumentType.WORKFLOW: "工作流",
    DocumentType.DISCUSSION: "讨论",
    DocumentType.REVIEW: "审查",
    DocumentType.DIAGRAM: "图表"
}

# 服务状态中文映射
SERVICE_STATUS_CN = {
    ServiceStatus.UP: "正常",
    ServiceStatus.DOWN: "停机",
    ServiceStatus.DEGRADED: "降级",
    ServiceStatus.MAINTENANCE: "维护中"
}

def get_enum_description(enum_value):
    """获取枚举值的中文描述"""
    # 根据枚举类型返回对应的中文描述
    if isinstance(enum_value, TaskStatus):
        return TASK_STATUS_CN.get(enum_value, enum_value.value)
    elif isinstance(enum_value, AgentRole):
        return AGENT_ROLE_CN.get(enum_value, enum_value.value)
    elif isinstance(enum_value, DifficultyLevel):
        return DIFFICULTY_LEVEL_CN.get(enum_value, enum_value.value)
    elif isinstance(enum_value, TaskComplexity):
        return TASK_COMPLEXITY_CN.get(enum_value, enum_value.value)
    elif isinstance(enum_value, ConnectionType):
        return CONNECTION_TYPE_CN.get(enum_value, enum_value.value)
    elif isinstance(enum_value, TaskType):
        return TASK_TYPE_CN.get(enum_value, enum_value.value)
    elif isinstance(enum_value, DocumentType):
        return DOCUMENT_TYPE_CN.get(enum_value, enum_value.value)
    elif isinstance(enum_value, ServiceStatus):
        return SERVICE_STATUS_CN.get(enum_value, enum_value.value)
    else:
        return enum_value.value