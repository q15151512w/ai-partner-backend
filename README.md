# AI 智能伴侣 · 后端

基于 FastAPI 的 AI 伴侣后端，提供人设预设、会话管理与多轮对话接口，可对接 DeepSeek / SiliconFlow 等 OpenAI 兼容模型。

## 技术栈

- **Web**：FastAPI + Uvicorn
- **ORM**：SQLAlchemy（异步）+ aiomysql
- **数据库**：MySQL 8
- **模型**：DeepSeek（`main.py`）/ SiliconFlow（`zhinengbanlv/ai`）
- **配置**：环境变量 + `.env`（本地）

## 目录结构

```
.
├── main.py                  # 入口：单文件版接口
├── zhinengbanlv/            # 模块化版
│   ├── ai/                  # 模型客户端与 Prompt
│   ├── db/                  # 引擎、模型
│   ├── routers/             # presets / sessions / chat
│   └── schemas/             # 请求与响应体
├── realday12/               # 练习代码
├── data/data.json           # 人设种子数据
└── .env.example             # 环境变量模板
```

## 快速开始

```bash
# 1. 安装依赖
uv sync

# 2. 配置环境变量
cp .env.example .env
# 应用启动时会自动加载 .env，填入 DEEPSEEK_API_KEY / GUIJILIUDONG_APIKEY / 数据库连接

# 3. 建库（示例）
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS pythob_database DEFAULT CHARSET utf8mb4;"

# 4. 启动
uv run uvicorn main:app --reload --port 8000
```

接口文档：<http://127.0.0.1:8000/docs>

## 环境变量

| 变量 | 用途 | 必填 |
|---|---|---|
| `DEEPSEEK_API_KEY` | `main.py` 调 DeepSeek | 是 |
| `GUIJILIUDONG_APIKEY` | `zhinengbanlv/ai` 调 SiliconFlow | 二选一 |
| `DB_HOST` / `DB_PORT` | MySQL 地址 | 是 |
| `DB_USER` / `DB_PASSWORD` | MySQL 账号 | 是 |
| `DB_NAME` | 库名，默认 `pythob_database` | 是 |

## 安全说明

- `.env`、虚拟环境、日志均已加入 `.gitignore`；
- 仓库内不存放真实 Key、数据库密码或用户对话数据；
- 生产环境请使用最小权限数据库账号，不要用 `root`。
