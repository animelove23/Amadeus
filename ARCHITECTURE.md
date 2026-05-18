# AI Character Engine 架构说明

## 1. 当前阶段

本项目已经从“骨架版”进入“基础可运行的工程版”。

这次重构刻意跳过了“只保留几个平铺文件”的初学者阶段，直接进入更接近真实项目的目录结构，因为当前目标已经不是证明 `tool calling` 能不能跑，而是让你开始学习：

- Agent 子系统如何独立演化
- Manager 如何只做编排，而不吞掉所有业务
- 工具系统如何为后续插件、记忆、RAG、MCP 做准备

当前代码仍然属于 **Level 2：基础可运行版**，但 Agent 部分已经开始朝 **Level 3：Shinsekai-like restoration** 的方向搭桥。

---

## 2. 当前目录结构

```text
llmproject/
├── agent/
│   ├── models.py          # Agent 的结构化数据模型
│   ├── registry.py        # 工具注册表与分组
│   ├── executor.py        # 工具执行器
│   ├── runtime.py         # 模型 ↔ 工具循环
│   └── builtin_tools.py   # 当前保留的最小内置工具
│
├── core/
│   ├── manager.py         # 应用编排层
│   ├── memory.py          # 对话历史
│   ├── messages.py        # UI / TTS / 流式事件协议
│   └── stream_parser.py   # 模型输出解析
│
├── llm/
│   ├── adapter.py         # LLM 供应商适配层
│   └── worker.py          # Qt 后台线程
│
├── services/
│   └── rag_service.py     # RAG 边界
│
├── ui/
│   └── desktop_window.py  # 桌面 UI
│
├── assets/
├── config.py
├── main.py
└── ARCHITECTURE.md
```

### 为什么要这样拆

```text
UI             只关心展示
Manager        只关心编排
AgentRuntime   只关心模型与工具的循环
ToolExecutor   只关心安全执行
ToolRegistry   只关心工具目录
LLMAdapter     只关心不同模型供应商
```

这种拆法的价值是：  
以后你想换模型、换 UI、接 RAG、接插件、加记忆，都不需要把一整台机器拆掉重造。

---

## 3. 一次完整对话的主流程

```text
DesktopChatWindow
        │
        ▼
     LLMWorker
        │
        ▼
      Manager
   ┌────┼───────────────┐
   ▼    ▼               ▼
Memory RAGService   AgentRuntime
                        │
                        ▼
                  ToolRegistry
                        │
                        ▼
                  ToolExecutor
                        │
                        ▼
                    Tool Result
                        │
                        └──────► 回流给模型
```

更细一点：

1. UI 收到用户输入。
2. `Manager._prepare_turn()`：
   - 把用户消息写入 memory
   - 向 RAG 请求补充上下文
   - 构造本轮 messages
3. `AgentRuntime.run()`：
   - 把工具 schema 发给模型
   - 读取模型是否返回 `tool_calls`
   - 如果没有工具调用，直接返回最终答案
   - 如果有工具调用，则交给 `ToolExecutor`
   - 把 `tool` 消息追加回上下文，再请求模型继续回答
4. `Manager` 只接收最终结果，并把 `assistant / tool / assistant` 这串消息整体写回 memory。
5. `LLMWorker + LLMStreamParser` 再把正文和情绪协议拆给 UI。

---

## 4. Agent 子系统逐层说明

### 4.1 `agent/models.py`

它定义 Agent 世界里的“共同语言”：

- `ToolSpec`
  - 一个工具的说明书
  - 包含名称、描述、参数 schema、处理函数、分组、风险等级
- `ToolCall`
  - 模型发出的调用请求
- `ToolResult`
  - 工具执行后的统一结果
- `AgentRunResult`
  - 一整个 Agent 回合的结果

**学习价值**：  
先把数据结构定稳，后面的调度逻辑就不会散成一地特殊情况。

### 4.2 `agent/registry.py`

它是“工具目录服务”。

当前已经支持：

- 注册工具
- 按名字查工具
- 按分组给模型暴露工具
- 搜索工具

这一步已经比最初的“一个列表里塞几个函数”更接近真实系统，因为未来你可以直接在这里扩展：

- `memory` 工具组
- `rag` 工具组
- `character` 工具组
- `filesystem` 工具组
- 插件工具组

### 4.3 `agent/executor.py`

它是“工具运行器”。

当前负责：

- 解析工具参数
- 执行真正的 handler
- 捕获异常
- 把错误也包装成模型能继续理解的结果

**关键思想**：  
工具失败不应该立刻炸穿整个应用。  
在 Agent 系统里，失败也常常应该成为“下一轮推理的输入”。

### 4.4 `agent/runtime.py`

它是“Agent 控制回路”。

当前负责：

- 调模型
- 读取 `tool_calls`
- 维护一次回合内的临时消息
- 调用工具执行器
- 把结果回流给模型
- 限制最大步数，避免死循环

这层从 `Manager` 中独立出来，是这次重构最重要的升级。  
因为从现在开始：

- `Manager` 不再理解每个工具细节
- 未来你要做 planner、反思、多步任务、风险确认，都可以优先长在 `AgentRuntime` 旁边，而不是把 `Manager` 塞成巨石

---

## 5. 为什么删掉 calculator

`calculator` 适合教学第一步，但不适合继续当工程 Agent 的代表工具。

原因：

1. 它太像“单函数 demo”
2. 它容易让你误以为 Agent = 一堆小工具
3. 它不能代表未来真正会遇到的工程问题：
   - 插件注入
   - 工具分组
   - 高风险操作
   - 长耗时任务
   - 工具发现
   - 记忆与 RAG 的联动

所以当前只保留 `get_current_time` 作为最小样例工具，重点转向 Agent 框架本身。

---

## 6. 从 Shinsekai 学到什么

> 以下比较基于当前能看到的 Shinsekai 源码结构，而不是猜测。

### 6.1 Shinsekai 的优势

#### A. 它把工具系统拆层了

Shinsekai 至少把这些职责拆开：

- `llm/tools/tool_manager.py`
  - 工具分组、激活组、工具搜索
- `llm/tools/tool_executor.py`
  - 工具执行、超时、风险确认、并行保护
- `llm/llm_manager.py`
  - 对话主循环、工具流式处理、历史修复
- `sdk/tool_registry.py`
  - 插件工具注册入口

这说明真正的工程 Agent 不是“一个类包打天下”，而是：

```text
目录层
执行层
调度层
插件接入层
```

#### B. 它已经考虑“工具发现”

Shinsekai 有 `search_tools` 与 `list_tool_groups` 这种 meta tool。  
这意味着当工具越来越多时，模型不必一次看见全部工具，而是可以先“查目录”，再按需激活。

#### C. 它已经考虑“生产环境里的脏活”

例如：

- 同名工具冲突处理
- 工具组激活
- 高风险工具确认
- 工具超时
- 冷却加载
- orphaned tool call 清理

这些都不是 demo 里最显眼的部分，却恰恰是工程系统最难的部分。

#### D. 它把插件当成一等公民

插件可以通过 SDK 注册工具，而宿主会把这些工具合并进统一的工具目录。  
这让 Agent 系统能从“单项目能力”扩展成“生态能力”。

### 6.2 Shinsekai 的技术难点

#### A. 工具调用协议很容易被历史消息污染

如果某条 assistant 消息里留下了 tool call，但对应 tool result 丢失，后续上下文会变脏。  
Shinsekai 专门有清理 orphaned tool calls 的逻辑，说明这一点在真实系统里会频繁出现。

#### B. 工具数量一多，暴露策略就变成问题

工具全量暴露：

- prompt 变长
- 模型更容易选错
- 成本更高

工具按需暴露：

- 又需要分组
- 搜索
- 激活策略

这本质上是“工具目录系统”的问题，不只是 prompt 问题。

#### C. 长耗时工具与模型加载会拖慢体验

Shinsekai 对 embedding / reranker 的加载做了冷却和预热逻辑。  
这说明一旦接入记忆、RAG、检索模型，Agent 就不再只是同步函数调用，而要面对运行时资源管理。

#### D. 高风险工具需要额外控制面

工具一旦能删文件、改配置、联网，单纯的 `execute()` 就不够了。  
你还需要：

- 风险等级
- 用户确认
- 超时
- 权限边界
- 审计日志

这也是为什么工程 Agent 不能只停留在“模型会调函数”。

---

## 7. 本项目当前与 Shinsekai 的对应关系

| 本项目 | 对应 Shinsekai 部分 | 当前等级 | 下一步 |
| --- | --- | --- | --- |
| `agent/registry.py` | `llm/tools/tool_manager.py` + 一部分 `sdk/tool_registry.py` | 基础可运行 | 加工具组激活策略、插件来源标记、工具搜索 meta tool |
| `agent/executor.py` | `llm/tools/tool_executor.py` | 基础可运行 | 加超时、风险确认、并发控制、执行日志 |
| `agent/runtime.py` | `llm/llm_manager.py` 中的 tool loop | 基础可运行 | 做真正的流式 tool calling、错误恢复、orphaned call 清理 |
| `core/manager.py` | `llm_manager.py` 的更高层编排职责 | 基础可运行 | 继续瘦身，未来把 session / memory policy 再拆出去 |
| `services/rag_service.py` | `memory_tools.py` 相关能力的前置边界 | 骨架 | 接真实检索、chunk、embedding、rerank、引用 |
| 插件系统 | `sdk/` + `core/plugins/` | 尚未实现 | 先做本地 Python 插件注册，再做独立插件发现 |

---

## 8. 当前还没做，但下一步最值得做的升级

按优先级排序：

1. **工具组控制**
   - 现在有 group 字段，但还没有按场景切换工具组
2. **Tool metadata event**
   - 让 UI 能显示“正在调用 get_current_time”
3. **流式 tool calling**
   - 当前是整轮结束后再把正文吐给 UI
4. **orphaned tool call 清理**
   - 防止历史消息被半截工具调用污染
5. **风险控制**
   - 为未来文件、网络、执行命令类工具做准备
6. **插件工具**
   - 让外部模块能注册到统一 `ToolRegistry`

---

## 9. 你现在最该学习的三个问题

1. 为什么 `Manager` 不能同时负责：
   - 记忆
   - RAG
   - 工具注册
   - 工具执行
   - 工具循环
2. 为什么工具系统一定要拆成：
   - `models`
   - `registry`
   - `executor`
   - `runtime`
3. 为什么一个“能调工具的聊天程序”，离“工程 Agent”还差：
   - 工具发现
   - 风险控制
   - 历史修复
   - 插件生态

把这三个问题吃透，你后面看 LangChain、LangGraph、MCP、Shinsekai，都会突然变得透明很多。
