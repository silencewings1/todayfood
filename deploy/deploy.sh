#!/usr/bin/env bash
# ============================================================
# todayfood 部署脚本（前端 Vue + 后端 FastAPI）
#
# 用法：
#   ./deploy/deploy.sh              # 部署全部（前端+后端）
#   ./deploy/deploy.sh --frontend   # 仅部署前端
#   ./deploy/deploy.sh --backend    # 仅部署后端
#
# 功能：
#   前端：调用本机原子发布脚本
#   后端：rsync 代码到 VPS → pip install → 重启 systemd
#
# 前提：SSH 免密已配、VPS 已装 nginx 和 Python 虚拟环境
# ============================================================
set -euo pipefail

# —— 配置区（按需修改）——
VPS_USER="root"
VPS_HOST="your-vps-ip"

# 本地路径
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"

# VPS 路径
REMOTE_BACKEND="/home/ospacer/project/todayfood/backend"
REMOTE_VENV="/home/ospacer/.py_food"
REMOTE_SERVICE="todayfood.service"

# —— 参数解析 ——
TARGET="all"
case "${1:-}" in
    --frontend) TARGET="frontend" ;;
    --backend)  TARGET="backend" ;;
    --all|"")   TARGET="all" ;;
    *) echo "用法: $0 [--frontend|--backend|--all]"; exit 1 ;;
esac

echo "================================================"
echo "  今日宜吃 / today food 部署（目标: $TARGET）"
echo "================================================"

# ============================================================
# 前端部署
# ============================================================
deploy_frontend() {
    echo ""
    echo "[前端] 执行原子发布..."
    "$PROJECT_DIR/deploy/deploy_frontend_atomic.sh"
}

# ============================================================
# 后端部署
# ============================================================
deploy_backend() {
    echo ""
    echo "[后端] 同步代码并重启..."

    # 1. 上传代码（排除本地环境文件）
    echo "[后端] 上传到 VPS ($VPS_HOST:$REMOTE_BACKEND)..."
    rsync -avz --delete \
        --exclude='.env' \
        --exclude='__pycache__/' \
        --exclude='*.pyc' \
        --exclude='.pytest_cache/' \
        --exclude='tests/' \
        --exclude='*.db' \
        --exclude='*.log' \
        "$BACKEND_DIR/" "$VPS_USER@$VPS_HOST:$REMOTE_BACKEND/"
    echo "后端代码上传完成"

    # 2. 安装依赖
    echo ""
    echo "[后端] 安装依赖..."
    ssh "$VPS_USER@$VPS_HOST" \
        "cd $REMOTE_BACKEND && $REMOTE_VENV/bin/pip install -r requirements.txt -q"
    echo "依赖安装完成"

    # 3. 重启服务
    echo ""
    echo "[后端] 重启 systemd 服务 ($REMOTE_SERVICE)..."
    ssh "$VPS_USER@$VPS_HOST" \
        "systemctl restart $REMOTE_SERVICE && systemctl status $REMOTE_SERVICE --no-pager -l | head -15"
    echo "后端已重启"
}

# —— 执行 ——
case "$TARGET" in
    frontend) deploy_frontend ;;
    backend)  deploy_backend ;;
    all)      deploy_frontend; deploy_backend ;;
esac

echo ""
echo "================================================"
echo "  今日宜吃 / today food 部署完成！"
echo "  前端: https://snowflow.cloud/projects/todayfood/"
echo "  API:  https://snowflow.cloud/projects/todayfood/api/"
echo "  后台: https://snowflow.cloud/projects/todayfood/admin/"
echo "================================================"
