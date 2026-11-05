from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from starlette.responses import JSONResponse

from db import get_async_session, init_db, close_db
from routers.presets import router as presets_router
from routers.deepseek_chat import router as deepseek_chat_router
from routers.sessions import router as session_router

from config import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI项目启动了")
    await  init_db()
    yield
    await  close_db()
    logger.info("FastAPI项目关闭了")


app = FastAPI(title="AI智能伴侣-后端项目", description="智能伴侣后端项目", version="1.0.0", lifespan=lifespan)
app.include_router(presets_router)
app.include_router(session_router)
app.include_router(deepseek_chat_router)


@app.exception_handler(Exception)
def handle_exception_handler(request: Request, exc: Exception):
    logger.error(f"请求路径：{request.url},报错信息：{exc}")
    return JSONResponse(content={"code": 500, "message": "系统内部有错误"})
