from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional

from src.models.database import get_session
from src.models.models import Mention, Document, Task, Agent
from src.api.schemas import MentionResponse
from src.api.dependencies import verify_api_key

router = APIRouter(prefix="/api/v1/mentions", tags=["Mentions"], dependencies=[Depends(verify_api_key)])

@router.get("", response_model=List[MentionResponse],
    summary="获取提及",
    description="获取特定代理的提及，或未提供agent_id时获取所有代理的提及")
def get_mentions(
    agent_id: Optional[str] = Query(None, description="Agent ID to get mentions for (optional - returns all mentions if not provided)"),
    unread_only: bool = Query(False, description="Only show unread mentions (default: False - shows all mentions)"),
    limit: int = Query(50, description="Maximum number of mentions to return"),
    db: Session = Depends(get_session)
):
    query = select(Mention)
    
    # Only filter by agent_id if provided
    if agent_id:
        query = query.where(Mention.mentioned_agent_id == agent_id)
    
    if unread_only:
        query = query.where(Mention.is_read == False)
    
    query = query.order_by(Mention.created_at.desc()).limit(limit)
    mentions = db.exec(query).all()
    
    # Build response with document/task titles
    responses = []
    for mention in mentions:
        response = MentionResponse(
            id=mention.id,
            document_id=mention.document_id,
            task_id=mention.task_id,
            mentioned_agent_id=mention.mentioned_agent_id,
            created_by=mention.created_by,
            is_read=mention.is_read,
            created_at=mention.created_at
        )
        
        # Add document title if it's a document mention
        if mention.document_id:
            document = db.get(Document, mention.document_id)
            if document:
                response.document_title = document.title
        
        # Add task title if it's a task mention
        if mention.task_id:
            task = db.get(Task, mention.task_id)
            if task:
                response.task_title = task.title
        
        responses.append(response)
    
    return responses

@router.get("/by-role", response_model=List[MentionResponse],
    summary="按角色获取提及",
    description="获取特定角色的所有代理的提及，或未指定角色时获取所有提及")
def get_mentions_by_role(
    role: Optional[str] = Query(None, description="Role to get mentions for (e.g., 'backend_dev', 'qa', etc.). If not provided, returns all mentions."),
    unread_only: bool = Query(False, description="Only show unread mentions (default: False - shows all mentions)"),
    limit: int = Query(50, description="Maximum number of mentions to return"),
    db: Session = Depends(get_session)
):
    # Start with base query
    query = select(Mention)
    
    # Filter by role if specified
    if role:
        # Get all agents with the specified role
        agents_with_role = db.exec(select(Agent).where(Agent.role == role)).all()
        agent_ids = [agent.agent_id for agent in agents_with_role]
        
        if not agent_ids:
            return []  # No agents with this role
        
        # Filter mentions for agents with this role
        query = query.where(Mention.mentioned_agent_id.in_(agent_ids))
    
    if unread_only:
        query = query.where(Mention.is_read == False)
    
    query = query.order_by(Mention.created_at.desc()).limit(limit)
    mentions = db.exec(query).all()
    
    # Build response with document/task titles
    responses = []
    for mention in mentions:
        response = MentionResponse(
            id=mention.id,
            document_id=mention.document_id,
            task_id=mention.task_id,
            mentioned_agent_id=mention.mentioned_agent_id,
            created_by=mention.created_by,
            is_read=mention.is_read,
            created_at=mention.created_at
        )
        
        # Add document title if it's a document mention
        if mention.document_id:
            document = db.get(Document, mention.document_id)
            if document:
                response.document_title = document.title
        
        # Add task title if it's a task mention
        if mention.task_id:
            task = db.get(Task, mention.task_id)
            if task:
                response.task_title = task.title
        
        responses.append(response)
    
    return responses

@router.put("/{mention_id}/read", response_model=MentionResponse,
    summary="标记提及为已读",
    description="将特定提及标记为已读")
def mark_mention_read(
    mention_id: int,
    agent_id: str = Query(..., description="Agent ID marking the mention as read"),
    db: Session = Depends(get_session)
):
    mention = db.get(Mention, mention_id)
    if not mention:
        raise HTTPException(status_code=404, detail="提及未找到")
    
    # Verify the mention is for this agent
    if mention.mentioned_agent_id != agent_id:
        raise HTTPException(status_code=403, detail="不能将其他代理的提及标记为已读")
    
    mention.is_read = True
    db.add(mention)
    db.commit()
    db.refresh(mention)
    
    response = MentionResponse(
        id=mention.id,
        document_id=mention.document_id,
        task_id=mention.task_id,
        mentioned_agent_id=mention.mentioned_agent_id,
        created_by=mention.created_by,
        is_read=mention.is_read,
        created_at=mention.created_at
    )
    
    # Add document/task title
    if mention.document_id:
        document = db.get(Document, mention.document_id)
        if document:
            response.document_title = document.title
    if mention.task_id:
        task = db.get(Task, mention.task_id)
        if task:
            response.task_title = task.title
    
    return response