from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime
from src.models.enums import TaskStatus, AgentRole, DifficultyLevel, TaskComplexity, ConnectionType, TaskType
from src.models.document_enums import DocumentType, ServiceStatus

if TYPE_CHECKING:
    from typing import ForwardRef

# Request schemas
class AgentRegisterRequest(BaseModel):
    agent_id: str = Field(..., description="唯一代理标识符（例如：'frontend_dev_senior_001'）")
    role: AgentRole = Field(..., description="代理在项目中的角色")
    level: DifficultyLevel = Field(..., description="代理的技能级别")
    connection_type: Optional[ConnectionType] = Field(ConnectionType.CLIENT, description="连接类型（MCP 或 Client）")

class EpicCreateRequest(BaseModel):
    name: str = Field(..., description="史诗名称")
    description: str = Field(..., description="史诗描述")

class FeatureCreateRequest(BaseModel):
    epic_id: int = Field(..., description="此功能所属史诗的ID")
    name: str = Field(..., description="功能名称")
    description: str = Field(..., description="功能描述")

class TaskCreateRequest(BaseModel):
    feature_id: int = Field(..., description="此任务所属功能的ID")
    title: str = Field(..., description="简要任务标题")
    description: str = Field(..., description="详细任务描述")
    target_role: AgentRole = Field(..., description="应该处理此任务的角色")
    difficulty: DifficultyLevel = Field(..., description="任务难度级别")
    complexity: TaskComplexity = Field(TaskComplexity.MAJOR, description="任务复杂度（次要 = 直接提交到主分支，主要 = 需要PR）")
    branch: str = Field(..., description="此任务的Git分支")

class TaskStatusUpdateRequest(BaseModel):
    status: TaskStatus = Field(..., description="任务的新状态")
    notes: Optional[str] = Field(None, description="关于状态变更的可选备注")

class TaskCommentRequest(BaseModel):
    comment: str = Field(..., description="要添加到任务的评论")

# Response schemas
class AgentResponse(BaseModel):
    id: int
    agent_id: str
    role: AgentRole
    level: DifficultyLevel
    connection_type: Optional[ConnectionType]
    last_seen: datetime
    
    model_config = ConfigDict(from_attributes=True)

class AgentRegistrationResponse(BaseModel):
    agent: AgentResponse
    next_task: Optional["TaskResponse"] = None
    mentions: List["MentionResponse"] = []
    
    model_config = ConfigDict(from_attributes=True)

class ProjectContextResponse(BaseModel):
    project_name: str
    shared_path: str
    instructions_path: str
    project_docs_path: str
    database_type: str

class TaskResponse(BaseModel):
    id: int
    feature_id: int
    title: str
    description: str
    created_by: str  # agent_id
    target_role: AgentRole
    difficulty: DifficultyLevel
    complexity: TaskComplexity
    branch: str
    status: TaskStatus
    locked_by: Optional[str] = None  # agent_id
    locked_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    task_type: Optional[TaskType] = TaskType.REGULAR
    poll_interval: Optional[int] = None  # seconds for waiting tasks
    
    model_config = ConfigDict(from_attributes=True)

class TaskStatusUpdateResponse(BaseModel):
    task: TaskResponse
    next_task: Optional[TaskResponse] = None
    workflow_status: str = Field(..., description="continue | waiting | no_tasks")
    task_completed: Optional[int] = Field(None, description="已完成任务的ID")
    auto_continue: bool = Field(True, description="是否自动继续下一个任务")
    continuation_prompt: str = Field("继续下一个任务而无需等待确认", 
                                   description="自主继续的指令")
    session_momentum: str = Field("high", description="high | medium | low - 表示工作节奏")
    
    model_config = ConfigDict(from_attributes=True)

class EpicResponse(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    task_count: int = 0
    completed_task_count: int = 0
    in_progress_task_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)

class FeatureResponse(BaseModel):
    id: int
    epic_id: int
    name: str
    description: str
    
    model_config = ConfigDict(from_attributes=True)

class ChangelogResponse(BaseModel):
    id: int
    task_id: int
    old_status: TaskStatus
    new_status: TaskStatus
    changed_by: str
    notes: Optional[str] = None
    changed_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ErrorResponse(BaseModel):
    detail: str

# Document schemas
class DocumentCreateRequest(BaseModel):
    doc_type: DocumentType = Field(..., description="文档类型")
    title: str = Field(..., description="文档标题", max_length=200)
    content: str = Field(..., description="文档内容（支持Markdown）")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="额外的元数据")
    expires_at: Optional[datetime] = Field(None, description="自动清理过期时间")

class DocumentUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, description="更新的标题", max_length=200)
    content: Optional[str] = Field(None, description="更新的内容")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="更新的元数据")

class DocumentResponse(BaseModel):
    id: int
    doc_type: DocumentType
    author_id: str
    title: str
    content: str
    meta_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    mentions: List[str] = []  # List of mentioned agent_ids
    
    model_config = ConfigDict(from_attributes=True)

# Service schemas
class ServiceRegisterRequest(BaseModel):
    service_name: str = Field(..., description="唯一服务名称", max_length=100)
    ping_url: str = Field(..., description="用于健康检查的ping URL（例如：http://localhost:8080/health）")
    port: Optional[int] = Field(None, description="端口号（如适用）")
    status: ServiceStatus = Field("up", description="服务状态")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="额外的服务元数据")

class ServiceResponse(BaseModel):
    id: int
    service_name: str
    owner_agent_id: str
    ping_url: str
    port: Optional[int] = None
    status: ServiceStatus
    last_heartbeat: Optional[datetime] = None
    last_ping_at: Optional[datetime] = None
    last_ping_success: Optional[bool] = None
    meta_data: Optional[Dict[str, Any]] = None
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Mention schemas
class MentionResponse(BaseModel):
    id: int
    document_id: Optional[int] = None
    task_id: Optional[int] = None
    mentioned_agent_id: str
    created_by: str
    is_read: bool
    created_at: datetime
    document_title: Optional[str] = None
    task_title: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# Rebuild models to resolve forward references
AgentRegistrationResponse.model_rebuild()