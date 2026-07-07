"""独立后台管理应用入口

启动方式：
    cd /path/to/todayfood
    python -m uvicorn admin.main:app --host 0.0.0.0 --port 9082 --reload

监听地址与端口从 config/app.toml [admin] 读取，
可由环境变量 ADMIN_HOST / ADMIN_PORT 覆盖。
"""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
for path in (PROJECT_ROOT, BACKEND_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from admin.backend.router import router as admin_router
from app.config import settings

ADMIN_FRONTEND = PROJECT_ROOT / "admin" / "frontend"

app = FastAPI(title="今日宜吃后台管理", version="0.1.0")
app.include_router(admin_router)

if ADMIN_FRONTEND.exists():
    app.mount("/admin/static", StaticFiles(directory=str(ADMIN_FRONTEND)), name="admin-static")


@app.get("/", include_in_schema=False)
@app.get("/admin", include_in_schema=False)
@app.get("/admin/", include_in_schema=False)
def serve_admin():
    return FileResponse(str(ADMIN_FRONTEND / "index.html"))


@app.get("/health", include_in_schema=False)
def health() -> dict:
    return {"status": "ok", "service": "todayfood-admin"}


def main() -> None:
    """本地启动入口：python -m admin.main"""
    import uvicorn
    uvicorn.run(
        "admin.main:app",
        host=settings.admin.host,
        port=settings.admin.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
