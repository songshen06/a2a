# A2A (Agent-to-Agent) 协议对接规范 v1.2 (ACP版)

## 1. 规范概述

### 1.1 项目目标

基于 A2A 开源协议，实现 NVIDIA Omniverse Kit 与 OpenCode 的端到端、无中间层打通。Kit 可直接调用 OpenCode 的代码生成/改写能力，核心聚焦 OpenUSD 场景代码的全生命周期处理（生成、改写、校验、写入）。

### 1.2 术语定义

| 术语              | 定义                                                                            |
| :---------------- | :------------------------------------------------------------------------------ |
| **A2A 协议**      | Agent-to-Agent Protocol，标准化 Agent 间通信协议，基于 **Stdio JSON-RPC (ACP)** |
| **Omniverse Kit** | 基于 OpenUSD 的模块化应用开发框架                                               |
| **OpenCode**      | 开源代码生成与执行引擎，支持 ACP 协议 (Agent Client Protocol)                   |
| **USDA**          | USD 的 ASCII 文本格式，人类可读且适配 LLM                                       |

## 2. 核心设计原则

- **A2A 原生优先**：不引入额外中间层。
- **USD 场景原生**：所有交互围绕 USDA 代码展开。
- **异步非阻塞 (Async-First)**：[新增] 所有进程交互必须采用异步模式，确保 Kit UI 在任务执行期间不卡死。
- **安全回溯 (Undo-Native)**：[新增] 深度集成 Kit 原生撤销系统，支持对 Agent 修改的物理撤销。
- **增量优先 (Incremental-First)**：[新增] 优先处理选中 Prim 的增量修改，以适配 LLM 上下文窗口限制。

## 3. 整体架构设计

### 3.1 架构分层

| 层级         | 组件                          | 核心职责                                |
| :----------- | :---------------------------- | :-------------------------------------- |
| **客户端层** | A2A Client Extension          | 协议实现、USD 读写、UI 控制、子进程管理 |
| **通信层**   | **ACP (JSON-RPC over Stdio)** | 标准化 JSON-RPC 消息交互                |
| **服务端层** | **OpenCode ACP Process**      | 通过 `opencode acp` 启动的本地子进程    |
| **增强层**   | Coding Agent + MCP            | USD 语法校验 (usdchecker)、逻辑生成     |

## 4. 核心模块详细规范

### 4.1 客户端：Omniverse Kit A2A Client Extension

- **Agent 管理**：配置 OpenCode 可执行文件路径 (e.g., `/usr/local/bin/opencode`)。
- **进程管理**：使用 `asyncio.create_subprocess_exec` 启动并维持与 `opencode acp` 的长连接。
- **任务管理**：通过 Stdin 发送 JSON-RPC 请求，监听 Stdout 处理响应。
- **USD 交互**：
  - **读取**：支持 `Usd.Stage.Flatten()` 处理，确保引用的资产能被 Agent 理解。
  - **写入**：利用 `Sdf.Layer` 操作实现非破坏性编辑。
- **撤销系统**：[新增] 必须使用 `omni.kit.undo` 封装写入操作，使用户可通过 Ctrl+Z 恢复。

### 4.2 能力增强：OpenCode + MCP

- **语法辅助**：[新增] 服务端必须集成 `usdchecker` 工具，在返回代码前进行强制语义校验，防止生成非法 Schema。
- **任务优先级**：[新增] 支持在请求参数中携带 `priority`，实时交互任务优先于后台批处理。

## 5. 核心接口规范 (符合 ACP / JSON-RPC 2.0)

### 5.1 任务创建接口 (method: `agent/generateCode`)

**Request (Client -> OpenCode):**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "agent/generateCode",
  "params": {
    "instruction": "优化材质",
    "context": {
      "file_path": "stage.usda",
      "code": "#usda 1.0 ...",
      "selection": ["/World/Sphere"]
    },
    "extraParams": {
      "enableSyntaxCheck": true,
      "mode": "incremental"
    }
  }
}
```

**Response (OpenCode -> Client):**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "generatedCode": "#usda 1.0 ...",
    "status": "completed",
    "message": "Task completed successfully"
  }
}
```

## 6. USD 数据交互与校验 (重点)

### 6.1 传输模式

- **增量模式 (推荐)**：仅导出选中节点的 USDA，减少 Token 消耗。
- **全量模式**：导出整个 Stage，需处理大规模场景下的内存保护。

### 6.2 写入前校验

- **语法校验**：通过 `pxr.Usd` 确认代码可被解析。
- **预览对比**：在写入前显示 Diff（差异）面板，由用户确认。

## 7. 落地验收标准 (优化版)

- **连接性**：UI 显示 Agent 在线状态及能力清单。
- **异步性**：发送长耗时任务时，Kit 视口操作依然流畅。
- **闭环性**：Agent 返回的代码经由 `usdchecker` 校验无误并能正确渲染。
- **回溯性**：用户通过 Kit 菜单或快捷键可撤销 Agent 执行的所有操作。

## 8. [新增] 本地 AI IDE 开发指南

为了确保 AI IDE 生成的代码质量，请遵循以下开发步骤：

- **环境隔离**：优先生成符合 Kit 标准的文件结构：

  ```text
  exts/omni.kit.a2a_client/
  ├── config/extension.toml
  ├── python/scripts/extension.py  # 核心逻辑
  └── data/icons/...
  ```

- **Mock 优先**：先让 IDE 编写一个 Mock CLI (`mock_opencode_cli.py`)，通过 stdio 交互，返回符合本规范的 JSON-RPC 伪数据。
- **错误处理**：要求 IDE 实现子进程异常退出后的重启和状态恢复机制。

## 9. 职责边界

- **OpenCode**：负责“写/构造”，即 USDA 文本生成与优化。
- **Omniverse Kit**：负责“读/渲染”，即 USD 解释执行与渲染呈现。
- **A2A 协议**：负责“传”，即标准化的 JSON-RPC 任务消息管道。
