#!/usr/bin/env python3
"""
Headless PM CLI - Command-line interface for project management
"""

import typer
from typing import Optional
from sqlmodel import Session, select
from tabulate import tabulate
from datetime import datetime
import os

from src.models.database import get_session, create_db_and_tables
from src.models.models import Agent, Epic, Feature, Task, Service, Document
from src.models.enums import TaskStatus, AgentRole, DifficultyLevel
from src.models.document_enums import DocumentType, ServiceStatus

app = typer.Typer(help="Headless PM - LLM代理项目管理")

def get_db() -> Session:
    """获取数据库会话"""
    return next(get_session())

@app.command()
def status():
    """显示项目状态概览"""
    db = get_db()
    
    # Count tasks by status
    task_counts = {}
    for status in TaskStatus:
        count = len(db.exec(select(Task).where(Task.status == status)).all())
        task_counts[status.value] = count
    
    # Count active agents
    agent_count = len(db.exec(select(Agent)).all())
    
    # Count active services
    active_services = len(db.exec(
        select(Service).where(Service.status == ServiceStatus.UP)
    ).all())
    
    # Recent documents
    recent_docs = len(db.exec(
        select(Document).where(
            Document.created_at > datetime.now().replace(hour=0, minute=0, second=0)
        )
    ).all())
    
    typer.echo("🚀 Headless PM 状态")
    typer.echo("=" * 50)
    typer.echo(f"已注册代理: {agent_count}")
    typer.echo(f"活跃服务: {active_services}")
    typer.echo(f"今日文档: {recent_docs}")
    typer.echo("\n任务分类:")
    
    for status, count in task_counts.items():
        typer.echo(f"  {status.replace('_', ' ').title()}: {count}")

@app.command()
def tasks(
    status: Optional[str] = typer.Option(None, help="按任务状态过滤"),
    role: Optional[str] = typer.Option(None, help="按目标角色过滤")
):
    """显示任务分配"""
    db = get_db()
    
    query = select(Task).order_by(Task.created_at.desc())
    
    if status:
        try:
            task_status = TaskStatus(status)
            query = query.where(Task.status == task_status)
        except ValueError:
            typer.echo(f"无效状态: {status}")
            return
    
    if role:
        try:
            agent_role = AgentRole(role)
            query = query.where(Task.target_role == agent_role)
        except ValueError:
            typer.echo(f"无效角色: {role}")
            return
    
    tasks = db.exec(query.limit(20)).all()
    
    if not tasks:
        typer.echo("未找到符合条件的任务")
        return
    
    # Prepare table data
    table_data = []
    for task in tasks:
        table_data.append([
            task.id,
            task.title[:30] + "..." if len(task.title) > 30 else task.title,
            task.target_role.value,
            task.difficulty.value,
            task.status.value.replace('_', ' '),
            task.creator.agent_id if task.creator else "unknown",
            task.locked_by_agent.agent_id if task.locked_by_agent else "-"
        ])
    
    headers = ["ID", "标题", "角色", "级别", "状态", "创建者", "锁定者"]
    typer.echo(tabulate(table_data, headers=headers, tablefmt="grid"))

@app.command()
def reset():
    """重置数据库（警告：删除所有数据）"""
    confirm = typer.confirm("这将删除所有数据。您确定吗？")
    if not confirm:
        typer.echo("操作已取消")
        return
    
    db = get_db()
    
    # Drop and recreate tables
    from src.models.database import engine
    from sqlmodel import SQLModel
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    
    typer.echo("✅ 数据库重置成功")

@app.command()
def agents():
    """列出已注册的代理"""
    db = get_db()
    
    agents = db.exec(select(Agent).order_by(Agent.last_seen.desc())).all()
    
    if not agents:
        typer.echo("没有已注册的代理")
        return
    
    table_data = []
    for agent in agents:
        last_seen = agent.last_seen.strftime("%Y-%m-%d %H:%M") if agent.last_seen else "Never"
        table_data.append([
            agent.agent_id,
            agent.role.value,
            agent.level.value,
            last_seen
        ])
    
    headers = ["代理ID", "角色", "级别", "最后见到"]
    typer.echo(tabulate(table_data, headers=headers, tablefmt="grid"))

@app.command()
def services():
    """列出已注册的服务"""
    db = get_db()
    
    services = db.exec(select(Service).order_by(Service.service_name)).all()
    
    if not services:
        typer.echo("没有已注册的服务")
        return
    
    table_data = []
    for service in services:
        port_str = str(service.port) if service.port else "-"
        last_heartbeat = service.last_heartbeat.strftime("%H:%M:%S") if service.last_heartbeat else "Never"
        
        table_data.append([
            service.service_name,
            service.owner_agent_id,
            port_str,
            service.status.value,
            last_heartbeat
        ])
    
    headers = ["服务", "所有者", "端口", "状态", "最后心跳"]
    typer.echo(tabulate(table_data, headers=headers, tablefmt="grid"))

@app.command()
def documents(
    doc_type: Optional[str] = typer.Option(None, help="按文档类型过滤")
):
    """列出最近的文档"""
    db = get_db()
    
    query = select(Document).order_by(Document.created_at.desc())
    
    if doc_type:
        try:
            document_type = DocumentType(doc_type)
            query = query.where(Document.doc_type == document_type)
        except ValueError:
            typer.echo(f"无效的文档类型: {doc_type}")
            return
    
    docs = db.exec(query.limit(20)).all()
    
    if not docs:
        typer.echo("未找到文档")
        return
    
    table_data = []
    for doc in docs:
        created = doc.created_at.strftime("%m-%d %H:%M")
        title = doc.title[:40] + "..." if len(doc.title) > 40 else doc.title
        
        table_data.append([
            doc.id,
            doc.doc_type.value,
            title,
            doc.author_id,
            created
        ])
    
    headers = ["ID", "类型", "标题", "作者", "创建时间"]
    typer.echo(tabulate(table_data, headers=headers, tablefmt="grid"))

@app.command()
def seed():
    """创建测试用的示例数据"""
    db = get_db()
    
    typer.echo("正在创建示例数据...")
    
    # 创建示例史诗和功能
    epic = Epic(
        name="用户认证",
        description="实现完整的用户认证系统"
    )
    db.add(epic)
    db.commit()
    db.refresh(epic)
    
    feature = Feature(
        epic_id=epic.id,
        name="登录系统",
        description="使用JWT认证的用户登录"
    )
    db.add(feature)
    db.commit()
    db.refresh(feature)
    
    # 创建示例代理
    agents = [
        Agent(
            agent_id="architect_principal_001",
            role=AgentRole.ARCHITECT,
            level=DifficultyLevel.PRINCIPAL
        ),
        Agent(
            agent_id="frontend_dev_senior_001",
            role=AgentRole.FRONTEND_DEV,
            level=DifficultyLevel.SENIOR
        ),
        Agent(
            agent_id="backend_dev_senior_001",
            role=AgentRole.BACKEND_DEV,
            level=DifficultyLevel.SENIOR
        ),
        Agent(
            agent_id="qa_senior_001",
            role=AgentRole.QA,
            level=DifficultyLevel.SENIOR
        )
    ]
    
    for agent in agents:
        db.add(agent)
    db.commit()
    
    # 创建示例任务
    architect = agents[0]
    
    tasks = [
        Task(
            feature_id=feature.id,
            title="设计登录UI原型",
            description="创建登录界面的线框图和原型",
            created_by_id=architect.id,
            target_role=AgentRole.FRONTEND_DEV,
            difficulty=DifficultyLevel.SENIOR,
            branch="feature/login-ui"
        ),
        Task(
            feature_id=feature.id,
            title="实现JWT认证API",
            description="创建使用JWT令牌的登录/登出端点",
            created_by_id=architect.id,
            target_role=AgentRole.BACKEND_DEV,
            difficulty=DifficultyLevel.SENIOR,
            branch="feature/jwt-auth"
        ),
        Task(
            feature_id=feature.id,
            title="编写认证测试",
            description="为认证系统创建全面的测试套件",
            created_by_id=architect.id,
            target_role=AgentRole.QA,
            difficulty=DifficultyLevel.SENIOR,
            branch="feature/auth-tests"
        )
    ]
    
    for task in tasks:
        db.add(task)
    db.commit()
    
    # 创建示例文档
    docs = [
        Document(
            doc_type=DocumentType.STANDUP,
            author_id="architect_principal_001",
            title="每日站会 - 架构",
            content="## 昨天\n- 审查了认证需求\n- 创建了初始任务分解\n\n## 今天\n- 最终确定API设计\n- 创建详细任务\n\n## 阻碍\n- 无"
        ),
        Document(
            doc_type=DocumentType.CRITICAL_ISSUE,
            author_id="qa_senior_001",
            title="测试环境故障",
            content="测试环境当前已停机。@backend_dev_senior_001 请调查。"
        )
    ]
    
    for doc in docs:
        db.add(doc)
    db.commit()
    
    typer.echo("✅ 示例数据创建成功！")
    typer.echo(f"已创建：1个史诗，1个功能，{len(tasks)}个任务，{len(agents)}个代理，{len(docs)}个文档")

@app.command()
def init():
    """初始化数据库并创建表"""
    create_db_and_tables()
    typer.echo("✅ 数据库初始化成功")

@app.command()
def dashboard():
    """启动实时仪表板"""
    from src.cli.dashboard import HeadlessPMDashboard
    dashboard = HeadlessPMDashboard()
    dashboard.run()

if __name__ == "__main__":
    app()