# AI Girl 情感陪伴虚拟数字人 Agent

技术栈：`Vue 3 + Vite`（前端） / `FastAPI + LangGraph`（后端）

## 已实现能力

1. Live2D 数字人形象
- 使用 `mao_pro_en/runtime` 模型文件，前端通过 `pixi-live2d-display` 渲染
- 文本对话的情绪状态会驱动 Live2D 表情切换

2. Agent 对话（LangGraph）
- 后端以 `langgraph` 状态图实现：决策 -> 工具调用 -> 回复 -> 记忆更新
- 支持 DeepSeek API（OpenAI 兼容）作为大脑，已预留 API Key 配置

3. 情绪系统
- Agent 输出包含 `emotion` 字段（happy/neutral/sad/angry/shy/surprised）
- 前端依据 `emotion` 映射到模型 expression

4. Tools（可扩展）
- `weather`：Open-Meteo 免费天气 API
- `datetime`：本地时区日期时间
- `news`：Hacker News 开放 API 头条
- `math`：安全 AST 数学计算
- 扩展方式：在 `backend/app/tools/builtin_tools.py` 注册新 tool

5. 记忆系统（可查看）
- 短期记忆：最近 30 条对话
- 长期记忆：用户偏好/事实（规则抽取）
- 提供 `/memory/{session_id}` 接口，前端面板可查看

6. 主动说话机制
- 后端追踪用户最近发言时间
- 超过 10 秒无输入，`/proactive/{session_id}` 触发主动关心消息
- 前端每 2 秒轮询一次该接口

7. 主动设计的 skills
- `empathetic_listener`（共情倾听）
- `mood_booster`（情绪提振）
- `life_coach`（目标拆解）
- `info_assistant`（工具查询）

## 目录结构

- `backend/` FastAPI + LangGraph
- `frontend/` Vue + Live2D
- `frontend/public/models/mao_pro_en/runtime/` Live2D 模型资源

## 环境创建与依赖安装（已执行）

```bash
conda create -y -n ai_girl python=3.11
conda run -n ai_girl python -m pip install -r backend/requirements.txt
cd frontend && npm install
```

## 配置 DeepSeek API Key

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入 DEEPSEEK_API_KEY
```

## 启动

后端：
```bash
cd backend
conda run -n ai_girl uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

前端：
```bash
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

浏览器打开 `http://localhost:5173`

## 关键接口

- `POST /chat`
- `GET /memory/{session_id}`
- `GET /proactive/{session_id}`
- `GET /tools`

