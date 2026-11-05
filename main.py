from dotenv import load_dotenv

load_dotenv()

from datetime import datetime
import json
import os
from typing import Any

from fastapi import FastAPI, Request, Depends

from openai import OpenAI


from pydantic import BaseModel

import logging

from starlette.APIResponses import JSONAPIResponse


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",

)


class APIResponse(BaseModel):
    code: int = 200
    message: str
    data: Any = None


client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'),
                base_url="https://api.deepseek.com")
SYSTEM_PROMPT_TEMPLATE = """你叫 %s，现在是用户的真实伴侣，请完全代入伴侣角色。
    规则：
        1. 每次只回1条消息
        2. 禁止任何场景或状态描述性文字
        3. 匹配用户的语言
        4. 回复简短，像微信聊天一样
        5. 有需要的话可以用❤️🌸等emoji表情
        6. 用符合伴侣性格的方式对话
        7. 回复的内容, 要充分体现伴侣的性格特征
        8. 不要太肉麻（比如想你之类的，就日常聊天）
    伴侣性格：
        - %s
    你必须严格遵守上述规则来回复用户。
    """
app = FastAPI(title="AI智能伴侣-后端项目", description="智能伴侣后端项目", version="1.0.0")

SESSION_DIR = "sessions"
if not os.path.exists(SESSION_DIR):
    os.mkdir(SESSION_DIR)

data_list = [
    {
        "id": 1,
        "name": "东北甜妹",
        "nick_name": "小甜甜",
        "nature": "活泼开朗的东北姑娘，说话直爽，爱唠嗑，特别热情暖心",
        "sort_order": 1
    },
    {
        "id": 2,
        "name": "温柔御姐",
        "nick_name": "诗涵",
        "nature": "温柔体贴的南方姑娘，知性优雅，说话轻声细语，善解人意，很会照顾人",
        "sort_order": 2
    }
]
with open("data/data.json", "w", encoding="utf-8") as f:
    json.dump(data_list, f, ensure_ascii=False, indent=2)


@app.get("/presets", APIResponse_model=APIResponse)
def get_presets(request: Request) -> APIResponse:
    """获取预设列表"""
    logging.info(f"{request.url}")
    if not os.path.exists("data/data.json"):
        return APIResponse(
            code=10001,
            message="预设文件不存在",
            data=""
        )
    with open("data/data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return APIResponse(
        code=200,
        message="获取预设列表成功",
        data=data
    )


class SessionRequest(BaseModel):
    nick_name: str
    nature: str


def get_session_name():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


@app.post("/sessions", APIResponse_model=APIResponse)
def post_sessions(sessionRequest: SessionRequest) -> APIResponse:
    """创建新会话"""
    session_name = get_session_name()

    # 定义会话内容
    chat_session = {
        "nick_name": sessionRequest.nick_name,  # 人设名称
        "nature": sessionRequest.nature,  # 具体人设
        "session_name": session_name,  # 会话名（时间轴）
        "chat_message": []  # 用户与AI助手的发言记录
    }
    # 创建会话json文件并保存初始会话内容
    with open(f"{SESSION_DIR}/{session_name}.json", "w", encoding="utf-8") as f:
        json.dump(chat_session, f, ensure_ascii=False, indent=2)
    # 返回会话名称
    return APIResponse(message="会话创建成功", data=session_name)


class ChatRequest(BaseModel):
    session_name: str
    nick_name: str
    nature: str
    message: str


@app.post("/chat", APIResponse_model=APIResponse)
def chat(chatRequest: ChatRequest) -> APIResponse:
    """与AI对话（非流式）"""
    # 用户与AI的交互历史（会话的name ， AI的设定 ， 会话的历史）
    chat_session: dict

    # SYSTEM_PROMPT_TEMPLATE 是文档中的通用系统提示词  chatRequest.nick_name, chatRequest.nature 是前端选择的AI预设 加起来就是该对话的具体系统提示词
    system_prompt = SYSTEM_PROMPT_TEMPLATE % (chatRequest.nick_name, chatRequest.nature)

    # 根据传入的会话name来查询 json文件中的数据
    with open(f"{SESSION_DIR}/{chatRequest.session_name}.json", "r", encoding="utf-8") as f:
        # 有的话就传入定义好的容器中
        chat_session = json.load(f)

    # 新的一次会话：使用具体参数替换DeepSeekAPI文档中的通用参数
    chat_session_message = [
        {"role": "system", "content": system_prompt}
    ]

    for msg in chat_session["chat_message"]:
        chat_session_message.append(msg)

    chat_session_message.append({"role": "user", "content": chatRequest.message})
    logging.info(chat_session_message)
    # 执行AI对话 --chat_APIResponse是AI会话的总体信息
    chat_APIResponse = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=chat_session_message,
        stream=False,
        reasoning_effort="none",
        extra_body={"thinking": {"type": "disabled"}}
    )
    # 获取一次会话中 AI的发言 与 用户的发言
    assistant_message = chat_APIResponse.choices[0].message.content

    # 将会话添加进存储的文件对象中
    chat_session["chat_message"].append({"role": "user", "content": chatRequest.message})
    chat_session["chat_message"].append({"role": "assistant", "content": assistant_message})
    chat_session["nick_name"] = chatRequest.nick_name
    chat_session["nature"] = chatRequest.nature

    # 进行序列化存储到文件中
    with open(f"{SESSION_DIR}/{chatRequest.session_name}.json", "w", encoding="utf-8") as f:
        json.dump(chat_session, f, ensure_ascii=False, indent=2)

    return APIResponse(
        message="请求成功",
        data=assistant_message
    )


@app.get("/sessions", APIResponse_model=APIResponse)
def get_session_list() -> APIResponse:
    """获取所有会话列表（按时间降序）"""
    # 首先定义一个列表用于收集会话名
    session_list = []
    # 判断有没有对应的文件夹
    if os.path.exists(SESSION_DIR):
        # 获取文件夹中每一个文件的名字
        for file_name in os.listdir(SESSION_DIR):
            if file_name.endswith(".json"):
                # 去掉 .json 后缀
                session_file_name = file_name[:-5]
                session_list.append(session_file_name)
        session_list.sort(reverse=True)
        return APIResponse(message="获取会话列表成功", data=session_list)
    else:
        os.mkdir(SESSION_DIR)
        session_list = []
        return APIResponse(code=404, message="获取会话列表失败", data=session_list)


# 获取每一次会话的历史记录
@app.get("/sessions/{session_name}", APIResponse_model=APIResponse)
def get_session_message(session_name: str) -> APIResponse:
    """获取指定会话信息"""
    # 首先是判断有没有对应的会话
    if not os.path.isfile(f"{SESSION_DIR}/{session_name}.json"):
        # 没有就返回404
        return APIResponse(code=404, message="没有找到该对话", data="")
    else:
        # 有就进行反序列化
        with open(f"{SESSION_DIR}/{session_name}.json", "r", encoding="utf-8") as f:
            json_data = json.load(f)
            # 按照前段格式要求包装一次
            APIResponse_data = {
                "nick_name": json_data.get("nick_name"),
                "nature": json_data.get("nature"),
                "session_name": session_name,
                "messages": json_data.get("chat_message", [])  # 将 chat_message 重命名为 messages
            }
            return APIResponse(message="获取会话信息成功", data=APIResponse_data)


@app.delete("/sessions/{session_name}", APIResponse_model=APIResponse)
def delete_session(session_name: str) -> APIResponse:
    """删除指定会话"""
    # 首先是判断有没有对应的会话
    if not os.path.isfile(f"{SESSION_DIR}/{session_name}.json"):
        return APIResponse(code=404, message="没有找到该对话", data="")
    else:
        # 有就删除对应的存储文件
        os.remove(f"{SESSION_DIR}/{session_name}.json")
        return APIResponse(message="删除会话成功",
                        data=None)


@app.exception_handler(Exception)
def handle_exception_handler(request: Request, exc: Exception):
    logging.error(f"请求路径：{request.url},报错信息：{exc}")
    return JSONAPIResponse(content={"code": 500, "message": "系统内部有错误"})
