# CodeHive

CodeHive 是一个**动态目录级多 Agent 代码生成框架**，用于大型 monorepo / 复杂项目的初始化与增量演进。

它把“一个项目需求（project brief）”拆解为目录级职责契约，并由 Root Agent + Directory Agents 协同完成目录创建、契约文档（`CLAUDE.md`）生成与基础代码脚手架落地。

## 核心特性

- **Root Agent 规划阶段**
  - 解析项目需求。
  - 产出全局目录树（包含根目录 `.`）。
  - 生成每个目录专属 `CLAUDE.md`（职责、输入输出契约、依赖、规范、全局摘要）。
  - 输出 `architecture_summary.json` 供后续 Agent 使用。

- **Directory Agent 执行阶段**
  - 每个 Agent 只处理自己目录。
  - 基于目录契约生成脚手架（可扩展为补全/重构/测试）。
  - 通过目录沙箱实现“只读写本目录及子目录”的权限隔离。

- **动态 Agent Pool**
  - 按需创建、复用、释放目录 Agent。
  - 可作为后续“闲置回收、优先级调度”的基础。

- **消息总线与协调机制**
  - Directory Agent 完成变更后发布 `directory.changed` 事件。
  - Root/Orchestrator 可订阅并进行依赖影响分析与一致性检查。

- **并发执行与统计**
  - 支持多目录并发生成。
  - 输出任务成功/失败、活跃 Agent 数、总耗时等统计。

## 项目结构

```text
codehive/
├── pyproject.toml
├── README.md
└── src/
    └── codehive/
        ├── __init__.py
        ├── cli.py
        ├── llm.py
        ├── messaging.py
        ├── models.py
        ├── orchestrator.py
        ├── pool.py
        ├── sandbox.py
        ├── stats.py
        └── agents/
            ├── __init__.py
            ├── directory_agent.py
            └── root_agent.py
```

## 快速开始

### 1) 安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

如果要使用 Anthropic Claude：

```bash
pip install -e .[anthropic]
export ANTHROPIC_API_KEY=your_key
```

### 2) 运行入口脚本

```bash
codehive generate "构建一个支持插件系统、REST API、任务调度和可观测性的企业级平台" --output-root ./generated --max-workers 6
```

执行后将自动：

1. 规划目录结构。
2. 创建目录。
3. 在每个目录写入 `CLAUDE.md`。
4. 生成全局 `architecture_summary.json`。
5. 并发运行目录 Agent 做基础 scaffold。

## CLI 参数

- `brief`：项目需求描述（自然语言）。
- `--output-root`：生成项目的目标根目录（默认 `./generated`）。
- `--use-anthropic`：启用 Anthropic Claude 作为 Root 规划器。
- `--max-workers`：并发目录 Agent 数量。
- `--verbose`：输出 debug 日志。

## 关键模块说明

- `RootAgent`：负责需求分析、架构设计、目录树创建、全局摘要持久化。
- `DirectoryAgent`：目录级执行单元，受 `DirectorySandbox` 权限保护。
- `AgentPool`：动态管理目录 Agent 生命周期。
- `Orchestrator`：统一协调、并发执行、事件订阅、最终统计。
- `MessageBus`：目录间变更通知（可扩展到跨进程/队列）。

## 扩展指南

### 1) 接入真实代码生成

当前 `DirectoryAgent` 默认写入 `CLAUDE.md + .codehive.generated`。
可在 `run_task` 中新增动作：

- `generate_code`
- `refactor`
- `run_tests`

并按目录职责调用不同 Prompt 模板或工具链。

### 2) 增量更新

可通过比较历史 `architecture_summary.json` 与新版本差异，触发受影响目录的选择性执行。

### 3) 依赖拓扑调度

把 `DirectorySpec.dependencies` 构建为 DAG，可先跑上游目录，再并行下游目录。

### 4) Agent Pool 策略

为 `AgentPool` 增加：

- 空闲超时自动销毁
- 热目录常驻
- 按 token / rate limit 的配额调度

## 日志与错误处理

- 所有任务结果统一为 `TaskResult`。
- 失败任务保留错误信息，不中断其他目录并发任务。
- `RuntimeStats` 追踪总任务数、成功/失败数、活跃 Agent 数与耗时。

## 未来路线图

- 支持跨语言模板（Go/TS/Rust）。
- 支持多 LLM Router（Claude + OpenAI + 本地模型）。
- 支持持久化事件日志与可视化任务面板。
- 支持真正的“目录级权限隔离执行器”（容器/沙箱进程）。
