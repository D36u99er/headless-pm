#!/bin/bash

# Headless PM 启动脚本
# 检查环境、数据库并启动API服务器

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Banner
echo -e "${BLUE}"
echo "🚀 Headless PM 启动脚本"
echo "==============================="
echo -e "${NC}"

# Detect architecture and suggest appropriate venv
ARCH=$(uname -m)
log_info "检测到架构: $ARCH"

if [[ "$ARCH" == "arm64" ]]; then
    EXPECTED_VENV="venv"
else
    EXPECTED_VENV="claude_venv"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    log_error "未找到 .env 文件！"
    log_info "正在从 env-example 复制到 .env..."
    if [ -f "env-example" ]; then
        cp env-example .env
        log_success "已从 env-example 创建 .env 文件"
        log_warning "请在继续之前编辑 .env 文件以配置您的设置"
        exit 1
    else
        log_error "未找到 env-example 文件！无法创建 .env"
        exit 1
    fi
fi

log_success "找到 .env 文件"

# Check if we're in a virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    log_success "虚拟环境已激活: $VIRTUAL_ENV"
    # Check if it's the expected venv for this architecture
    if [[ ! "$VIRTUAL_ENV" == *"$EXPECTED_VENV"* ]]; then
        log_warning "您使用的虚拟环境与 $ARCH 架构推荐的不同"
        log_info "推荐使用: $EXPECTED_VENV (运行 ./setup/universal_setup.sh 进行设置)"
    fi
else
    log_warning "未检测到虚拟环境！"
    log_info "请激活虚拟环境:"
    echo "  source $EXPECTED_VENV/bin/activate"
    log_info "或运行 ./setup/universal_setup.sh 设置环境"
fi

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    log_error "需要 Python 3.11+。当前版本: $PYTHON_VERSION"
    exit 1
fi

log_success "Python 版本: $PYTHON_VERSION"

# Check if required packages are installed
log_info "检查必需的包..."
if ! python -c "import fastapi, sqlmodel, uvicorn" 2>/dev/null; then
    log_error "未找到必需的包或存在兼容性问题！"
    log_info "这通常发生在架构不匹配时 (ARM64 vs x86_64)"
    log_info "推荐解决方案:"
    echo "  运行: ./setup/universal_setup.sh"
    echo "  这将为您的架构 ($ARCH) 创建正确的环境"
    exit 1
else
    log_success "找到必需的包"
fi

# Load environment variables from .env file
if [ -f ".env" ]; then
    # Export variables from .env file
    set -a
    source .env
    set +a
    log_success "已从 .env 加载环境变量"
else
    log_warning "未找到 .env 文件，使用默认值"
fi

# Check database configuration
DB_CONNECTION=${DB_CONNECTION:-"sqlite"}
log_info "数据库类型: $DB_CONNECTION"

# Test database connection
log_info "测试数据库连接..."
DB_TEST_OUTPUT=$(python -c "
print('开始数据库测试...')
from src.models.database import engine
print('引擎导入成功')
try:
    print('尝试连接...')
    with engine.connect() as conn:
        print('连接已建立')
        pass
    print('成功')
except Exception as e:
    print(f'失败: {e}')
" 2>&1)

log_info "数据库测试输出: $DB_TEST_OUTPUT"

if [[ "$DB_TEST_OUTPUT" == *"SUCCESS"* ]]; then
    log_success "数据库连接成功"
elif [[ "$DB_TEST_OUTPUT" == *"FAILED"* ]]; then
    log_warning "数据库连接失败。正在初始化数据库..."
    python -m src.cli.main init
    log_success "数据库已初始化"
else
    log_error "数据库测试失败，出现意外输出"
    log_info "输出内容: $DB_TEST_OUTPUT"
    exit 1
fi

# Check if database has tables
log_info "检查数据库模式..."
SCHEMA_OUTPUT=$(python -c "
print('开始模式检查...')
from src.models.database import engine
from sqlalchemy import text
print('模式导入成功')
try:
    print('连接数据库进行模式检查...')
    with engine.connect() as conn:
        print('模式连接已建立')
        if '$DB_CONNECTION' == 'sqlite':
            result = conn.execute(text(\"SELECT name FROM sqlite_master WHERE type='table'\"))
        else:
            result = conn.execute(text(\"SHOW TABLES\"))
        tables = result.fetchall()
        print(f'找到 {len(tables)} 个表')
        if len(tables) < 5:  # Expecting at least 5 core tables
            print('不完整')
        else:
            print('有效')
except Exception as e:
    print(f'错误: {e}')
" 2>&1)

log_info "模式检查输出: $SCHEMA_OUTPUT"

if [[ "$SCHEMA_OUTPUT" == *"VALID"* ]]; then
    log_success "数据库模式有效"
elif [[ "$SCHEMA_OUTPUT" == *"INCOMPLETE"* ]]; then
    log_warning "数据库模式不完整。正在重新初始化..."
    echo "y" | python -m src.cli.main reset 2>/dev/null || true
    python -m src.cli.main init
    log_success "数据库已重新初始化"
else
    log_error "模式检查失败"
    log_info "输出内容: $SCHEMA_OUTPUT"
    exit 1
fi

# Check port availability
PORT=${SERVICE_PORT:-6969}

# Only check port if service will be started
if [ ! -z "$SERVICE_PORT" ] || [ "$PORT" = "6969" ]; then
    log_info "检查端口 $PORT 是否可用..."
    if lsof -i :$PORT >/dev/null 2>&1; then
        log_warning "端口 $PORT 已被占用"
        log_info "您可能需要停止现有服务或使用其他端口"
    else
        log_success "端口 $PORT 可用"
    fi
fi

# Only check MCP port if defined
if [ ! -z "$MCP_PORT" ]; then
    log_info "检查 MCP 端口 $MCP_PORT 是否可用..."
    if lsof -i :$MCP_PORT >/dev/null 2>&1; then
        log_warning "MCP 端口 $MCP_PORT 已被占用"
        log_info "您可能需要停止现有服务或使用其他端口"
    else
        log_success "MCP 端口 $MCP_PORT 可用"
    fi
fi

# Only check dashboard port if defined
if [ ! -z "$DASHBOARD_PORT" ]; then
    log_info "检查仪表板端口 $DASHBOARD_PORT 是否可用..."
    if lsof -i :$DASHBOARD_PORT >/dev/null 2>&1; then
        log_warning "仪表板端口 $DASHBOARD_PORT 已被占用"
        log_info "您可能需要停止现有服务或使用其他端口"
    else
        log_success "仪表板端口 $DASHBOARD_PORT 可用"
    fi
fi

# Function to start MCP server in background
start_mcp_server() {
    log_info "正在端口 $MCP_PORT 上启动 MCP SSE 服务器..."
    uvicorn src.mcp.simple_sse_server:app --port $MCP_PORT --host 0.0.0.0 2>&1 | sed 's/^/[MCP] /' &
    MCP_PID=$!
    log_success "MCP SSE 服务器已在端口 $MCP_PORT 上启动 (PID: $MCP_PID)"
}

# Function to start dashboard in background
start_dashboard() {
    # Check if Node.js is installed
    if ! command -v node >/dev/null 2>&1; then
        log_warning "未找到 Node.js。仪表板需要 Node.js 18+ 才能运行。"
        log_info "请从 https://nodejs.org/ 安装 Node.js"
        return
    fi
    
    # Check Node version
    NODE_VERSION=$(node --version | cut -d'v' -f2)
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1)
    if [ "$NODE_MAJOR" -lt 18 ]; then
        log_warning "仪表板需要 Node.js 18+。当前版本: v$NODE_VERSION"
        return
    fi
    
    if [ -d "dashboard" ]; then
        log_info "正在端口 $DASHBOARD_PORT 上启动仪表板..."
        cd dashboard
        
        # Check if node_modules exists
        if [ ! -d "node_modules" ]; then
            log_warning "仪表板依赖项未安装。正在安装..."
            npm install >/dev/null 2>&1
            log_success "仪表板依赖项已安装"
        fi
        
        # Start the dashboard with the configured port
        npx next dev --port $DASHBOARD_PORT --turbopack 2>&1 | sed 's/^/[DASHBOARD] /' &
        DASHBOARD_PID=$!
        cd ..
        log_success "仪表板已在端口 $DASHBOARD_PORT 上启动 (PID: $DASHBOARD_PID)"
    else
        log_warning "未找到仪表板目录。跳过仪表板启动。"
        log_info "要安装仪表板，请运行: npx create-next-app@latest dashboard"
    fi
}

# Function to cleanup on exit
cleanup() {
    log_info "正在关闭..."
    if [ ! -z "$MCP_PID" ]; then
        kill $MCP_PID 2>/dev/null || true
        log_info "MCP 服务器已停止"
    fi
    if [ ! -z "$DASHBOARD_PID" ]; then
        kill $DASHBOARD_PID 2>/dev/null || true
        log_info "仪表板已停止"
    fi
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
        log_info "API 服务器已停止"
    fi
    exit 0
}

# Set up trap for cleanup
trap cleanup INT TERM

# Start the servers
log_info "所有检查已通过！正在启动 Headless PM 服务器..."
echo -e "${GREEN}"
echo "🌟 正在启动服务..."
if [ ! -z "$SERVICE_PORT" ] || [ "$PORT" = "6969" ]; then
    echo "📚 API 文档: http://localhost:$PORT/api/v1/docs"
fi
if [ ! -z "$MCP_PORT" ]; then
    echo "🔌 MCP HTTP 服务器: http://localhost:$MCP_PORT"
fi
if [ ! -z "$DASHBOARD_PORT" ]; then
    echo "🖥️  Web 仪表板: http://localhost:$DASHBOARD_PORT"
fi
echo "📊 CLI 仪表板: python -m src.cli.main dashboard"
echo "🛑 停止服务器: Ctrl+C"
echo -e "${NC}"

# Start MCP server in background (only if MCP_PORT is defined)
if [ ! -z "$MCP_PORT" ]; then
    start_mcp_server
else
    log_info "MCP_PORT 未在 .env 中定义，跳过 MCP 服务器启动"
fi

# Start dashboard in background (only if DASHBOARD_PORT is defined)
if [ ! -z "$DASHBOARD_PORT" ]; then
    start_dashboard
else
    log_info "DASHBOARD_PORT 未在 .env 中定义，跳过仪表板启动"
fi

# Start API server (only if SERVICE_PORT is defined or use default)
if [ ! -z "$SERVICE_PORT" ] || [ "$PORT" = "6969" ]; then
    log_info "正在端口 $PORT 上启动 API 服务器..."
    uvicorn src.main:app --reload --port $PORT --host 0.0.0.0 &
    API_PID=$!
else
    log_info "SERVICE_PORT 未在 .env 中定义，跳过 API 服务器启动"
fi

# Wait for all processes
wait $API_PID $MCP_PID $DASHBOARD_PID