from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
import os
import asyncio
from dotenv import load_dotenv
from contextlib import asynccontextmanager

load_dotenv()

from src.models.database import create_db_and_tables
from src.api.routes import router
from src.api.document_routes import router as document_router
from src.api.service_routes import router as service_router
from src.api.mention_routes import router as mention_router
from src.api.changes_routes import router as changes_router
from src.services.health_checker import health_checker
from src.api.swagger_config import get_swagger_ui_html, get_redoc_html

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    await health_checker.start()
    yield
    # Shutdown
    await health_checker.stop()

app = FastAPI(
    title="Headless PM API",
    description="用于LLM代理协调的轻量级项目管理API",
    version="1.0.0",
    docs_url=None,  # 禁用默认的 docs
    redoc_url=None,  # 禁用默认的 redoc
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)
app.include_router(document_router)
app.include_router(service_router)
app.include_router(mention_router)
app.include_router(changes_router)

# 自定义 Swagger UI 路由
@app.get("/api/v1/docs", response_class=HTMLResponse, include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - API 文档"
    )

# 自定义 ReDoc 路由
@app.get("/api/v1/redoc", response_class=HTMLResponse, include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - API 文档"
    )

@app.get("/", tags=["根目录"])
def read_root():
    return {
        "message": "Headless PM API",
        "docs": "/api/v1/docs",
        "health": "正常"
    }

@app.get("/health", tags=["健康检查"])
def health_check():
    """增强的健康检查端点，包含数据库状态"""
    from src.models.database import get_session
    from sqlmodel import select
    from src.models.models import Agent
    from datetime import datetime
    
    try:
        # Test database connection
        db = next(get_session())
        db.exec(select(Agent).limit(1))
        db.close()
        db_status = "健康"
    except Exception as e:
        db_status = f"不健康: {str(e)}"
    
    return {
        "status": "健康" if db_status == "健康" else "降级",
        "service": "headless-pm-api",
        "version": "1.0.0",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/status", tags=["健康检查"])
def status_check():
    """详细状态端点，包含系统指标"""
    from src.models.database import get_session
    from sqlmodel import select, func
    from src.models.models import Agent, Task, Document, Service
    from datetime import datetime, timedelta
    
    try:
        db = next(get_session())
        
        # 获取计数
        agent_count = db.exec(select(func.count(Agent.id))).first()
        task_count = db.exec(select(func.count(Task.id))).first()
        document_count = db.exec(select(func.count(Document.id))).first()
        service_count = db.exec(select(func.count(Service.id))).first()
        
        # 获取活跃代理（最近5分钟内看到）
        five_minutes_ago = datetime.utcnow().replace(microsecond=0) - timedelta(minutes=5)
        active_agents = db.exec(
            select(func.count(Agent.id)).where(Agent.last_seen > five_minutes_ago)
        ).first()
        
        db.close()
        
        return {
            "service": "headless-pm-api",
            "version": "1.0.0",
            "metrics": {
                "total_agents": agent_count,
                "active_agents": active_agents,
                "total_tasks": task_count,
                "total_documents": document_count,
                "total_services": service_count
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "service": "headless-pm-api",
            "version": "1.0.0",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "6969"))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)