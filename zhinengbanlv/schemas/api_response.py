# 定义统一的返回格式类
from typing import Any

from pydantic import BaseModel


class APIResponse(BaseModel):
    code: int = 200
    message: str
    data: Any = None