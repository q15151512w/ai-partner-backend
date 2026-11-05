from pydantic import BaseModel


class SessionRequest(BaseModel):
    nick_name: str
    nature: str


class SessionBatchRequest(BaseModel):
    """批量删除会话请求"""
    session_names: list[str]


class ChatRequest(BaseModel):
    session_name: str
    nick_name: str
    nature: str
    message: str
