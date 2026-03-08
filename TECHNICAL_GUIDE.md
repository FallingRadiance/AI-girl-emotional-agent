# AI Girl 项目技术讲解（前后端）

本文按“能力 -> 技术要点 -> 代码位置（文件 + 函数）”讲解整个项目。

## 1. 总体架构

- 前端：Vue 3 + Vite + Pixi + Live2D
- 后端：FastAPI + LangGraph
- 大模型：DeepSeek（OpenAI 兼容接口）
- 存储：SQLite（短期/长期记忆）
- 通信：前端 Axios 调后端 REST API

关键入口：
- 后端服务入口：`backend/app/main.py` -> 路由函数 `chat()` / `proactive()` / `memory()` / `tools()`
- Agent 主流程：`backend/app/agent/graph.py` -> `compile_graph()`、`run_chat()`
- 前端页面入口：`frontend/src/App.vue`（`onSend()`、`proactiveTick()`、`loadMemory()`）

## 2. 后端 Agent（LangGraph）核心流程

### 2.1 状态图编排

- 技术要点：把对话过程拆成“决策 -> 工具调用 -> 生成回复 -> 写记忆”的可控节点流。
- 代码位置：
  - `backend/app/agent/graph.py` -> `compile_graph()`
  - `backend/app/agent/graph.py` -> `node_decide()`
  - `backend/app/agent/graph.py` -> `node_call_tool()`
  - `backend/app/agent/graph.py` -> `node_respond()`
  - `backend/app/agent/graph.py` -> `node_update_memory()`
  - `backend/app/agent/graph.py` -> `route_tool()`

### 2.2 DeepSeek 决策输出（结构化 JSON）

- 技术要点：LLM 必须输出结构化字段（reply/emotion/use_tool/tool_name/tool_args），方便后续节点 deterministically 处理。
- 代码位置：
  - `backend/app/agent/llm.py` -> `build_llm()`（模型与 API 网关初始化）
  - `backend/app/agent/llm.py` -> `structured_decision()`（调用模型并解析 JSON）
  - `backend/app/agent/llm.py` -> `has_llm()`（API Key 存在性检查与降级）

### 2.3 技能（skills）选择

- 技术要点：根据用户输入关键词选择不同对话风格/能力角色，影响 system prompt。
- 代码位置：
  - `backend/app/agent/skills.py` -> 常量 `SKILLS`
  - `backend/app/agent/skills.py` -> `pick_skill(message)`
  - `backend/app/agent/graph.py` -> `node_decide()`（把 skill 注入 prompt）

## 3. 情绪系统（emotion）

### 3.1 后端侧情绪生成

- 技术要点：模型每次回复都返回 emotion 标签（happy/neutral/sad/angry/shy/surprised）。
- 代码位置：
  - `backend/app/agent/graph.py` -> `node_decide()`（定义输出 schema）
  - `backend/app/agent/graph.py` -> `node_respond()`（最终写回 `emotion`）
  - `backend/app/models/schemas.py` -> `ChatResponse`（对外 API 字段）

### 3.2 前端侧情绪驱动 Live2D

- 技术要点：将 emotion 映射到 Live2D expression，情绪变化触发表情切换。
- 代码位置：
  - `frontend/src/components/Live2DAvatar.vue` -> 常量 `expressionMap`
  - `frontend/src/components/Live2DAvatar.vue` -> `setExpression(emotion)`
  - `frontend/src/components/Live2DAvatar.vue` -> `watch(() => props.emotion, ...)`

## 4. Tools 调用能力与可扩展机制

### 4.1 工具注册与执行

- 技术要点：所有工具统一注册在 `TOOL_REGISTRY`，通过 `execute_tool()` 动态执行；新增工具只需“注册 + handler”。
- 代码位置：
  - `backend/app/tools/builtin_tools.py` -> `TOOL_REGISTRY`
  - `backend/app/tools/builtin_tools.py` -> `execute_tool(name, args)`

### 4.2 已实现工具

- 天气：`weather_tool(city)`
- 时间：`datetime_tool()`
- 新闻：`news_tool(limit)`
- 数学：`math_tool(expression)` + `_eval_ast(node)`（安全 AST 计算）
- 代码位置：
  - `backend/app/tools/builtin_tools.py` -> `weather_tool`
  - `backend/app/tools/builtin_tools.py` -> `datetime_tool`
  - `backend/app/tools/builtin_tools.py` -> `news_tool`
  - `backend/app/tools/builtin_tools.py` -> `math_tool`
  - `backend/app/tools/builtin_tools.py` -> `_eval_ast`

### 4.3 Agent 何时调用工具

- 技术要点：LLM 在 `node_decide()` 输出 `use_tool/tool_name/tool_args`，`route_tool()` 决定是否进工具节点。
- 代码位置：
  - `backend/app/agent/graph.py` -> `node_decide()`
  - `backend/app/agent/graph.py` -> `route_tool()`
  - `backend/app/agent/graph.py` -> `node_call_tool()`

### 4.4 工具结果自然语言化

- 技术要点：避免把结构化 dict 直接展示给用户，统一转为自然语言。
- 代码位置：
  - `backend/app/agent/graph.py` -> `format_tool_result(tool_name, result)`
  - `backend/app/agent/graph.py` -> `node_respond()`（拼接自然语言结果）

## 5. 记忆系统（短期 + 长期）

### 5.1 短期记忆

- 技术要点：保存最近对话（user/assistant），并做长度裁剪（最近 30 条）。
- 代码位置：
  - `backend/app/memory/store.py` -> `append_short(session_id, role, content)`
  - `backend/app/memory/store.py` -> `list_short(session_id, limit)`

### 5.2 长期记忆

- 技术要点：从用户语句中抽取偏好/事实，去重写入长期记忆。
- 代码位置：
  - `backend/app/agent/graph.py` -> `extract_long_memory(session_id, user_message)`
  - `backend/app/memory/store.py` -> `add_long(session_id, key, value)`
  - `backend/app/memory/store.py` -> `list_long(session_id, limit)`

### 5.3 记忆写回时机

- 技术要点：在图流程最后统一写记忆，确保“回复与记忆一致”。
- 代码位置：
  - `backend/app/agent/graph.py` -> `node_update_memory()`

### 5.4 记忆可查看能力

- 技术要点：后端暴露 memory API，前端展示短期/长期面板。
- 代码位置：
  - `backend/app/main.py` -> `memory(session_id)`
  - `frontend/src/services/api.js` -> `fetchMemory(sessionId)`
  - `frontend/src/components/MemoryPanel.vue`（展示）
  - `frontend/src/App.vue` -> `loadMemory()`

## 6. 主动说话（闲时自主发言）机制

### 6.1 判定机制

- 技术要点：用户静默超过阈值（30 秒）后触发，且每个用户回合只触发一次，避免刷屏。
- 代码位置：
  - `backend/app/memory/store.py` -> `touch_user()`
  - `backend/app/memory/store.py` -> `should_trigger_proactive(session_id, threshold_seconds)`
  - `backend/app/memory/store.py` -> `mark_proactive_sent(session_id)`
  - `backend/app/main.py` -> `proactive(session_id)`

### 6.2 前端轮询策略

- 技术要点：用户首次发言后才开始轮询，减少无意义请求。
- 代码位置：
  - `frontend/src/App.vue` -> `onSend()`（首次发言后启动轮询）
  - `frontend/src/App.vue` -> `proactiveTick()`
  - `frontend/src/services/api.js` -> `checkProactive(sessionId)`

## 7. Live2D 渲染要点

### 7.1 模型加载与运行时依赖

- 技术要点：使用 `pixi-live2d-display/cubism4` 加载 `mao_pro.model3.json`；依赖 `live2dcubismcore.min.js`。
- 代码位置：
  - `frontend/index.html`（引入 cubism core 脚本）
  - `frontend/src/components/Live2DAvatar.vue` -> `onMounted()`

### 7.2 Ticker 和自适应布局

- 技术要点：注册 Pixi Ticker、按画布大小自动缩放模型，避免显示裁切。
- 代码位置：
  - `frontend/src/components/Live2DAvatar.vue` -> `Live2DModel.registerTicker(PIXI.Ticker)`
  - `frontend/src/components/Live2DAvatar.vue` -> `fitModelToCanvas()`
  - `frontend/src/components/Live2DAvatar.vue` -> `onUnmounted()`（释放资源）

## 8. FastAPI 接口层

- 技术要点：前后端通过 REST 接口解耦；Chat、Tools、Memory、Proactive 分离。
- 代码位置：
  - `backend/app/main.py` -> `chat(req)`
  - `backend/app/main.py` -> `tools()`
  - `backend/app/main.py` -> `memory(session_id)`
  - `backend/app/main.py` -> `proactive(session_id)`

## 9. 前端状态与页面交互

- 技术要点：主页面维护 `messages/emotion/skill/memory` 状态，聊天区自动滚动。
- 代码位置：
  - `frontend/src/App.vue` -> `onSend()`
  - `frontend/src/App.vue` -> `loadMemory()`
  - `frontend/src/components/ChatPanel.vue` -> `submit()`
  - `frontend/src/components/ChatPanel.vue` -> `watch(messages.length)`

## 10. 配置与启动

- DeepSeek 配置：
  - `backend/app/config.py` -> `Settings`（`deepseek_api_key/deepseek_base_url/deepseek_model`）
- 启动脚本：
  - 根目录 `start_backend.sh`
  - 根目录 `start_frontend.sh`

## 11. 后续可扩展建议（当前结构已支持）

- 新增工具：在 `backend/app/tools/builtin_tools.py` 增加 handler 并注册到 `TOOL_REGISTRY`
- 新增技能：在 `backend/app/agent/skills.py` 扩展 `SKILLS` 与 `pick_skill()`
- 增强长期记忆：可将 `extract_long_memory()` 升级为 LLM 抽取 + 向量检索
- 增强情绪表现：在前端把 emotion 进一步映射到 motion（不仅 expression）
