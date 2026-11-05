from fastapi import Depends, Request, APIRouter
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import logger
from db import get_async_session, AiPreset
from schemas import APIResponse

router = APIRouter(prefix="/presets", tags=["presets"])

@router.get("", response_model=APIResponse)
async def get_presets(request: Request, async_session: AsyncSession = Depends(get_async_session)) -> APIResponse:
    """获取预设列表"""
    # 打印请求的路径
    logger.info(f"{request.url}")
    # 获取工作间
    # session = session_factory()  可以使用fastapi的继承连接对象，不用手动创建
    # # 获取 需要的字段->字典的列表 （但其实还是Mapping.ROW对象）
    # presets_result = await session.execute(
    #     select(AiPreset.id, AiPreset.name, AiPreset.nick_name, AiPreset.nature).order_by(
    #         AiPreset.sort_order.desc()))
    #
    # # 进行格式转换
    # presets_list = jsonable_encoder(presets_result.mappings().all())

    result = await async_session.execute(select(AiPreset).order_by(AiPreset.sort_order.desc()))
    # 使用all（）会消费掉原本返回的row对象 ，此时result的游标已被耗尽，再次读取将返回空列表，想要多次调用 使用saclars后的列表，就需要使用一个变量把它装起来
    presets_objects_list = result.scalars().all()
    presets_list = jsonable_encoder(presets_objects_list)

    # print(result.scalars().all())  # 此时会打印 [] 空列表
    # print(presets_objects_list)  # 此时才会打印想要的对象数据列表

    logger.info(presets_list)

    return APIResponse(
        code=200,
        message="获取预设列表成功",
        data=presets_list
    )
