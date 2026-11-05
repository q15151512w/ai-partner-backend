from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, Depends, APIRouter

from ai import SYSTEM_PROMPT_TEMPLATE, client
from ai.llm_chat import deepseek_chat
from config import logger
from db import get_async_session, AiSession, AiMessage
from schemas import ChatRequest, APIResponse

from sqlalchemy import select

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=APIResponse)
async def chat(chatRequest: ChatRequest, request: Request,
               async_session: AsyncSession = Depends(get_async_session)) -> APIResponse:
    """与AI对话（非流式）"""
    # 用户与AI的交互历史（会话的name ， AI的设定 ， 会话的历史）
    chat_session: dict
    logger.info(f"{request.url}")

    # SYSTEM_PROMPT_TEMPLATE 是文档中的通用系统提示词  chatRequest.nick_name, chatRequest.nature 是前端选择的AI预设 加起来就是该对话的具体系统提示词
    system_prompt = SYSTEM_PROMPT_TEMPLATE % (chatRequest.nick_name, chatRequest.nature)

    # 根据传参获取对应的历史会话
    result_list = await async_session.execute(
        select(AiSession).where(AiSession.session_name == chatRequest.session_name))
    # 将查询到得行实例处理为映射类实例
    ai_session = result_list.scalars().first()
    # 判断有没有该数据
    if ai_session is None:
        return APIResponse(code=10001, message=f"会话 '{chatRequest.session_name}' 不存在")

    # 根据会话实例中的id与映射消息表中的 外键session_id来进行查找对应的消息数据 -->获取到行实例
    chat_history_message_list = await async_session.execute(
        select(AiMessage).where(AiMessage.session_id == ai_session.id).order_by(AiMessage.create_time))
    # 进行转化 -->列表中有多个映射消息类的实例
    chat_history_message = chat_history_message_list.scalars().all()

    # 新的一次会话：使用具体参数替换DeepSeekAPI文档中的通用参数
    chat_session_message = [
        {"role": "system", "content": system_prompt}
    ]

    for msg in chat_history_message:
        chat_session_message.append({"role": msg.role, "content": msg.content})

    chat_session_message.append({"role": "user", "content": chatRequest.message})
    logger.info(chat_session_message)

    # 执行AI对话 --chat_APIResponse是AI会话的总体信息
    chat_APIResponse = deepseek_chat(chat_session_message)

    # 获取一次会话中 AI的发言(用户发言是前端传进来的参数)
    assistant_message = chat_APIResponse.choices[0].message.content
    time_now = datetime.now()
    # 将数据存储进数据库中：
    async_session.add(
        AiMessage(session_id=ai_session.id, role="user", content=chatRequest.message, create_time=time_now))
    async_session.add(
        AiMessage(session_id=ai_session.id, role=chat_APIResponse.choices[0].message.role, content=assistant_message,
                  create_time=time_now,
                  ))
    await async_session.commit()
    return APIResponse(
        message="请求成功",
        data=assistant_message
    )
