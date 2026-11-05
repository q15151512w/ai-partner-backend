from datetime import datetime
from fastapi import Request, Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from config import logger
from db import get_async_session, AiSession, AiMessage
from schemas import APIResponse, SessionRequest, SessionBatchRequest
from sqlalchemy import select, delete

from utils import get_session_name

router =APIRouter(prefix="/sessions",tags=["sessions"])

@router.post("", response_model=APIResponse)
async def post_sessions(sessionRequest: SessionRequest, request: Request,
                        async_session: AsyncSession = Depends(get_async_session)) -> APIResponse:
    """创建新会话"""
    session_name = get_session_name()
    logger.info(f"{request.url}")
    # 定义会话内容
    chat_session = AiSession(session_name=session_name, nick_name=sessionRequest.nick_name,
                             nature=sessionRequest.nature, create_time=datetime.now(), update_time=datetime.now())

    # 将数据插入数据表中
    async_session.add(chat_session)
    await async_session.commit()
    logger.info(session_name)
    # 返回会话名称
    return APIResponse(message="会话创建成功", data=session_name)


@router.get("", response_model=APIResponse)
async def get_session_list(request: Request,
                           async_session: AsyncSession = Depends(get_async_session)) -> APIResponse:
    """获取所有会话列表（按时间降序）"""
    logger.info(f"{request.url}")
    session_result = await async_session.execute(select(AiSession.session_name).order_by(AiSession.create_time.desc()))
    session_list = list(session_result.scalars().all())
    logger.info(session_list)
    return APIResponse(message="获取会话列表成功", data=session_list)


@router.get("/{session_name}", response_model=APIResponse)
async def get_session_message(session_name: str, request: Request,
                              async_session: AsyncSession = Depends(get_async_session)) -> APIResponse:
    """获取指定会话信息"""
    logger.info(f"{request.url}")
    session_result = await async_session.execute(select(AiSession).where(AiSession.session_name == session_name))
    ai_session = session_result.scalars().first()

    chat_session = await async_session.execute(select(AiMessage).where(AiMessage.session_id == ai_session.id))
    ai_chat_messages = chat_session.scalars().all()

    APIResponse_data = {
        "nick_name": ai_session.nick_name,
        "nature": ai_session.nature,
        "session_name": session_name,
        "messages": [{"role": i.role, "content": i.content} for i in ai_chat_messages]
    }

    return APIResponse(message="获取会话信息成功", data=APIResponse_data)


@router.delete("/{session_name}", response_model=APIResponse)
async def delete_session(session_name: str, request: Request,
                         async_session: AsyncSession = Depends(get_async_session)) -> APIResponse:
    """删除指定会话"""
    logger.info(f"{request.url}")
    # 根据传入的会话名查找到对应的行数据（列表中的元祖中的元素）
    session_result = await async_session.execute(select(AiSession).where(AiSession.session_name == session_name))
    # 进行转化获取映射类的实例(要的是id)
    session = session_result.scalars().first()
    if not session:
        return APIResponse(code=10001, message=f"会话 '{session_name}' 不存在")
    # 根据获取到的会话实例的id进行删除
    await async_session.execute(delete(AiMessage).where(AiMessage.session_id == session.id))
    # 删除会话历史
    await async_session.delete(session)
    await async_session.commit()
    return APIResponse(message="删除会话成功",
                       data=None)


@router.delete("", response_model=APIResponse)
async def batch_delete_sessions(req: SessionBatchRequest, request: Request,
                                async_session: AsyncSession = Depends(get_async_session)) -> APIResponse:
    """批量删除多个会话（按 session_name）"""
    logger.info(f"{request.url}")
    if not req.session_names:
        return APIResponse(code=10001, message="会话列表不能为空")

    # 查出所有目标会话的 id
    session_result = await async_session.execute(
        select(AiSession).where(AiSession.session_name.in_(req.session_names)))
    session_objects = session_result.scalars().all()
    session_ids = [s.id for s in session_objects]

    if session_ids:
        # 删除这些会话关联的所有消息
        await async_session.execute(delete(AiMessage).where(AiMessage.session_id.in_(session_ids)))
        # 删除会话本身
        await async_session.execute(delete(AiSession).where(AiSession.id.in_(session_ids)))

    await async_session.commit()
    return APIResponse(message="批量删除会话成功",
                       data=None)
