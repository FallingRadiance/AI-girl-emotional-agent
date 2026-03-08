# AI Girl 情感陪伴虚拟数字人 Agent

技术栈：`Vue 3 + Vite`（前端） / `FastAPI + LangGraph`（后端）

## 快速本地部署（推荐）

1. 克隆项目
```bash
git clone ...
cd AI_girl
```

2. 创建并安装后端环境
```bash
conda create -y -n ai_girl python=3.11
conda run -n ai_girl python -m pip install -r backend/requirements.txt
```

3. 安装前端依赖
```bash
cd frontend
npm install
cd ..
```

4. 配置模型 API（DeepSeek）
```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入 DEEPSEEK_API_KEY
```

5. 启动服务（两个终端）

终端 A：
```bash
./start_backend.sh
```

终端 B：
```bash
./start_frontend.sh
```

6. 打开页面
- 浏览器访问：`http://localhost:5173`

## 一键排障（白屏/缓存问题）

如果前端出现白屏或代码更新后页面异常，可执行：

```bash
cd frontend
rm -rf node_modules/.vite
npm run dev -- --host 0.0.0.0 --port 5173
```

## 已实现能力

1. Live2D 数字人形象
- 使用 `mao_pro_en/runtime` 模型文件
- 前端通过 `pixi-live2d-display` 渲染
- 文本情绪会驱动 Live2D 表情切换

2. Agent 对话（LangGraph）
- 状态图流程：决策 -> 工具调用 -> 回复 -> 记忆更新
- 支持 DeepSeek（OpenAI 兼容接口）

3. 情绪系统
- 输出 `emotion`：`happy|neutral|sad|angry|shy|surprised`
- 前端按 emotion 映射 expression

4. Tools（可扩展）
- `weather`：天气查询
- `datetime`：日期时间
- `news`：新闻查询
- `math`：数学计算
- 扩展方式：在 `backend/app/tools/builtin_tools.py` 注册新工具

5. 记忆系统（可查看）
- 短期记忆：最近对话窗口
- 长期记忆：用户事实/偏好抽取
- 前端可查看长短期记忆

6. 主动说话机制
- 用户静默超过 30 秒后触发主动消息
- 每个用户回合仅触发一次，避免刷屏
- 前端在用户首次发言后才开始轮询主动消息接口

7. Skills
- `empathetic_listener`（共情倾听）
- `mood_booster`（情绪提振）
- `life_coach`（目标拆解）
- `info_assistant`（工具查询）

## 项目结构

- `backend/`：FastAPI + LangGraph
- `frontend/`：Vue + Live2D
- `frontend/public/models/mao_pro_en/runtime/`：Live2D 模型资源

## 关键接口

- `POST /chat`
- `GET /memory/{session_id}`
- `GET /proactive/{session_id}`
- `GET /tools`

## 补充说明

- `.gitignore` 已排除 `node_modules`、`dist`、`.env`、本地数据库等本地产物。
- 因此仓库保持轻量；其他用户 clone 后按上面的“快速本地部署”安装依赖即可完整运行。
