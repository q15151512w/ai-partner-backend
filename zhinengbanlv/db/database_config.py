from dotenv import load_dotenv

load_dotenv()

import os
from contextlib import asynccontextmanager


from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from config import logger

DATABASE_URL = (
    f"mysql+aiomysql://{os.getenv('DB_USER', 'root')}:{os.getenv('DB_PASSWORD', '')}"
    f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'pythob_database')}"
)


# 1. 创建引擎(支持异步操作)
engine = create_async_engine(DATABASE_URL, echo=True)

# 3. 会话工厂(支持异步操作)
session_factory = async_sessionmaker(engine)


# def get_async_session_factory():
#     return session_factory()


async def get_async_session():
    session = session_factory()
    try:
        yield session
    except Exception as e:
        logger.error(e)
        await  session.rollback()
        raise
    finally:
        await session.close()


engine = None
session_factory = None
# 初始化引擎, 数据库连接池
async def init_db():
    global engine, session_factory
    engine = create_async_engine(DATABASE_URL, echo=True)
    session_factory = async_sessionmaker(engine)


# 销毁数据库连接池
async def close_db():
    global engine
    if engine:
        await engine.dispose()
