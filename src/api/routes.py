from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List, Optional
import os

from src.models.database import get_session
from src.models.enums import TaskStatus, AgentRole, DifficultyLevel
from src.api.schemas import (
    AgentRegisterRequest, AgentResponse, AgentRegistrationResponse,
    EpicCreateRequest, FeatureCreateRequest,
    TaskCreateRequest, TaskResponse, TaskStatusUpdateRequest, TaskStatusUpdateResponse,
    TaskCommentRequest,
    ProjectContextResponse, EpicResponse, FeatureResponse,
    ChangelogResponse, MentionResponse
)
from src.api.dependencies import verify_api_key

# Import service functions
from src.services.agent_service import (
    register_or_update_agent, get_unread_mentions, list_all_agents, delete_agent
)
from src.services.task_service import (
    get_next_task_for_agent, wait_for_next_task
)
from src.services.task_management_service import (
    create_task, list_tasks, lock_task, update_task_status, 
    add_task_comment, delete_task, get_recent_changelog
)
from src.services.epic_feature_service import (
    create_epic, list_epics, create_feature, list_features_for_epic,
    delete_epic, delete_feature
)

router = APIRouter(prefix="/api/v1", dependencies=[Depends(verify_api_key)])


# Agent endpoints
@router.post("/register", response_model=AgentRegistrationResponse, 
    summary="注册代理",
    description="注册新代理或更新现有代理的最后看到时间戳。返回代理信息、下一个可用任务和任何未读提及。")
def register_agent(request: AgentRegisterRequest, db: Session = Depends(get_session)):
    # Register or update agent
    agent = register_or_update_agent(request, db)
    
    # Get next available task for this agent
    next_task = get_next_task_for_agent(agent, db)
    
    # Get unread mentions
    mentions = get_unread_mentions(agent.agent_id, db)
    
    return AgentRegistrationResponse(
        agent=AgentResponse(
            id=agent.id,
            agent_id=agent.agent_id,
            role=agent.role,
            level=agent.level,
            connection_type=agent.connection_type,
            last_seen=agent.last_seen
        ),
        next_task=next_task,
        mentions=mentions
    )


@router.get("/agents", response_model=List[AgentResponse],
    summary="列出所有代理", 
    description="获取所有已注册代理的列表")
def list_agents(db: Session = Depends(get_session)):
    return list_all_agents(db)


@router.delete("/agents/{agent_id}",
    summary="删除代理（仅PM）",
    description="删除代理记录。只有PM代理可以执行此操作。")
def delete_agent_endpoint(agent_id: str, requester_agent_id: str, db: Session = Depends(get_session)):
    return delete_agent(agent_id, requester_agent_id, db)


# Project context endpoint
@router.get("/context", response_model=ProjectContextResponse,
    summary="获取项目上下文",
    description="获取项目配置和文档路径")
def get_context():
    return ProjectContextResponse(
        project_name=os.getenv("PROJECT_NAME", "Headless PM"),
        shared_path=os.getenv("SHARED_PATH", "./shared"),
        instructions_path=os.getenv("INSTRUCTIONS_PATH", "./agent_instructions"),
        project_docs_path=os.getenv("PROJECT_DOCS_PATH", "./docs"),
        database_type="sqlite" if os.getenv("DATABASE_URL", "").startswith("sqlite") else "mysql"
    )


# Epic endpoints
@router.post("/epics", response_model=EpicResponse,
    summary="创建新史诗",
    description="PM和架构师可以创建史诗")
def create_epic_endpoint(request: EpicCreateRequest, agent_id: str, db: Session = Depends(get_session)):
    return create_epic(request, agent_id, db)


@router.get("/epics", response_model=List[EpicResponse],
    summary="列出所有史诗",
    description="获取所有史诗及其任务进度信息")
def list_epics_endpoint(db: Session = Depends(get_session)):
    return list_epics(db)


@router.delete("/epics/{epic_id}",
    summary="删除史诗（仅PM）",
    description="删除史诗及其所有功能和任务。只有PM代理可以执行此操作。")
def delete_epic_endpoint(epic_id: int, agent_id: str, db: Session = Depends(get_session)):
    return delete_epic(epic_id, agent_id, db)


# Feature endpoints
@router.post("/features", response_model=FeatureResponse,
    summary="创建新功能",
    description="PM和架构师可以在史诗中创建功能")
def create_feature_endpoint(request: FeatureCreateRequest, agent_id: str, db: Session = Depends(get_session)):
    return create_feature(request, agent_id, db)


@router.get("/features/{epic_id}", response_model=List[FeatureResponse],
    summary="列出史诗的功能",
    description="获取特定史诗的所有功能")
def list_features_endpoint(epic_id: int, db: Session = Depends(get_session)):
    return list_features_for_epic(epic_id, db)


@router.delete("/features/{feature_id}",
    summary="删除功能（仅PM）",
    description="删除功能及其所有任务。只有PM代理可以执行此操作。")
def delete_feature_endpoint(feature_id: int, agent_id: str, db: Session = Depends(get_session)):
    return delete_feature(feature_id, agent_id, db)


# Task endpoints
@router.post("/tasks/create", response_model=TaskResponse,
    summary="创建新任务",
    description="任何代理都可以为任何角色创建任务")
def create_task_endpoint(request: TaskCreateRequest, agent_id: str, db: Session = Depends(get_session)):
    return create_task(request, agent_id, db)


@router.get("/tasks", response_model=List[TaskResponse],
    summary="列出所有任务",
    description="获取所有任务，可按状态和角色过滤")
def list_tasks_endpoint(
    status: Optional[TaskStatus] = None,
    role: Optional[AgentRole] = None,
    db: Session = Depends(get_session)
):
    return list_tasks(status, role, db)


@router.get("/tasks/next", response_model=Optional[TaskResponse],
    summary="获取下一个可用任务",
    description="根据代理的角色和技能级别获取下一个任务。如果没有可用任务，最多等待3分钟，如果找不到则返回null。'role'和'level'查询参数都是必需的。使用'simulate=true'跳过等待以进行测试。使用'timeout'覆盖等待时间（以秒为单位）。")
def get_next_task(role: AgentRole = None, level: DifficultyLevel = None, 
                  simulate: bool = False, timeout: Optional[int] = None,
                  db: Session = Depends(get_session)) -> Optional[TaskResponse]:
    # Validate required parameters
    if role is None:
        raise HTTPException(
            status_code=400, 
            detail="缺少必需参数'role'。请提供有效的角色（例如：?role=frontend_dev）"
        )
    if level is None:
        raise HTTPException(
            status_code=400, 
            detail="缺少必需参数'level'。请提供有效的级别（例如：?level=senior）"
        )
    
    # 关闭当前会话，因为我们将在服务中使用新会话
    db.close()
    
    if simulate:
        # 用于测试/模拟，仅检查一次而不等待
        from src.services.task_service import get_next_task_for_agent
        from src.models.models import Agent
        from src.models.database import engine
        from sqlmodel import Session
        from datetime import datetime
        
        temp_agent = Agent(
            agent_id=f"temp_{role.value}_{level.value}",
            role=role,
            level=level,
            last_seen=datetime.utcnow()
        )
        
        with Session(engine) as fresh_db:
            return get_next_task_for_agent(temp_agent, fresh_db)
    else:
        # 使用处理等待和新数据库会话的服务函数
        # 使用提供的超时或默认为180秒（3分钟）
        wait_timeout = timeout if timeout is not None else 180
        return wait_for_next_task(role, level, timeout_seconds=wait_timeout)


@router.post("/tasks/{task_id}/lock", response_model=TaskResponse,
    summary="锁定任务",
    description="锁定任务以防止其他代理处理它")
def lock_task_endpoint(task_id: int, agent_id: str, db: Session = Depends(get_session)):
    return lock_task(task_id, agent_id, db)


@router.put("/tasks/{task_id}/status", response_model=TaskStatusUpdateResponse,
    summary="更新任务状态",
    description="更新任务状态，从UNDER_WORK状态移出时自动释放锁，并返回下一个可用任务")
def update_task_status_endpoint(task_id: int, request: TaskStatusUpdateRequest, 
                               agent_id: str, db: Session = Depends(get_session)):
    return update_task_status(task_id, request, agent_id, db)


@router.post("/tasks/{task_id}/comment",
    summary="添加任务评论",
    description="在评估阶段添加评论，带@提及检测")
def add_comment_endpoint(task_id: int, request: TaskCommentRequest,
                        agent_id: str, db: Session = Depends(get_session)):
    return add_task_comment(task_id, request, agent_id, db)


@router.delete("/tasks/{task_id}",
    summary="删除任务（仅PM）",
    description="删除任务。只有PM代理可以执行此操作。")
def delete_task_endpoint(task_id: int, agent_id: str, db: Session = Depends(get_session)):
    return delete_task(task_id, agent_id, db)


# Changelog endpoint
@router.get("/changelog", response_model=List[ChangelogResponse],
    summary="获取最近变更",
    description="获取项目中最近的任务状态变更")
def get_changelog(limit: int = 50, db: Session = Depends(get_session)):
    return get_recent_changelog(limit, db)