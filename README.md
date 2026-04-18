# CodeHive

CodeHive 是一个面向大型 monorepo 的**动态目录级代码阅读、重构与生成框架**。

- Root Agent = 蜂后（全局协调）
- 每个目录 = 蜂房（Directory Agent 独立处理）
- 每个目录必须有 `PROMPT.md`（职责/契约/规范）
- 强目录隔离（Agent 仅可读写自己的目录）

---

## 架构设计图（文本）

```text
                         +---------------------------+
                         |        RootAgent          |
                         |  (Queen / Coordinator)    |
                         +-------------+-------------+
                                       |
                      plan/review/schedule|persist architecture_summary.json
                                       v
+----------------------+     +----------------------+     +----------------------+
|      MessageBus      |<--->|      AgentPool       |<--->|   DirectoryAgent N   |
| topic + broadcast    |     | dynamic create/reuse |     | (sandboxed per dir)  |
+----------+-----------+     | idle recycle/rate    |     +----------+-----------+
           ^                 +----------------------+                |
           |                                                        read/write only
           | dependency notifications                               own directory tree
           |                                                        |
           |                         +----------------------+       v
           +-------------------------|   RefactorEngine     |  +-----------+
                                     | static scan + rewrite|  | PROMPT.md |
                                     +----------+-----------+  +-----------+
                                                |
                                     +----------v-----------+
                                     | TrainingSourceAgent  |
                                     | py/ts/go/cpp/rust    |
                                     +----------------------+
```

---

## 双模式运行

### Mode 1: Generation Mode

```bash
codehive generate --brief "项目需求..." --paradigm clean-architecture
```

流程：
1. RootAgent 解析 brief，生成目录树。
2. 为每个目录写入 `PROMPT.md`。
3. AgentPool 动态创建 DirectoryAgent 并并发执行。
4. DirectoryAgent 仅加载本目录 `PROMPT.md` + 全局摘要，生成目录代码。
5. MessageBus 发布目录变更事件，RootAgent 进行一致性审查。

### Mode 2: Refactor Mode（升级重点）

```bash
codehive refactor --path ./messy-repo --paradigm factory
```

流程：
1. RootAgent 扫描已有仓库并按目录创建 Analyzer Agent（DirectoryAgent in analyze mode）。
2. Analyzer 深读目录代码，逆向推断“原始可生成该代码的提示词”，写入 `PROMPT.md`。
3. 按语言自动选择训练源 Agent（Python/TypeScript/Go/C++/Rust）。
4. 执行静态分析（冗余/重复/坏味道）+ 自动重构（按指定范式）。
5. RootAgent 汇总结果并做全局一致性检查。

---

## 核心模块

- `RootAgent`：规划目录、逆向推断目录契约、全局审查。
- `DirectoryAgent`：目录级生成/分析/重构执行器（强隔离）。
- `AgentPool`：动态创建、复用、销毁、并发限流、闲置回收。
- `RefactorEngine`：执行代码清理和范式化重构。
- `training_sources.py`：多语言“专业训练源 Agent”规则库。
- `MessageBus`：跨目录变更通知和依赖协调。
- `Orchestrator`：统一编排 Generation/Refactor 两条主流程。

---

## 项目结构

```text
.
├── pyproject.toml
├── README.md
└── src/codehive
    ├── __init__.py
    ├── analyzers.py
    ├── cli.py
    ├── llm.py
    ├── messaging.py
    ├── models.py
    ├── orchestrator.py
    ├── pool.py
    ├── refactor_engine.py
    ├── sandbox.py
    ├── stats.py
    ├── training_sources.py
    └── agents
        ├── __init__.py
        ├── directory_agent.py
        └── root_agent.py
```

---

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

可选 Anthropic：

```bash
pip install -e .[anthropic]
export ANTHROPIC_API_KEY=YOUR_KEY
```

---

## 示例

### 生成模式

```bash
codehive generate \
  --brief "构建一个支持API、Web、任务调度和多语言SDK的企业平台" \
  --output-root ./generated \
  --paradigm ddd \
  --max-workers 6
```

### 重构模式

```bash
codehive refactor \
  --path ./messy-repo \
  --paradigm factory \
  --max-workers 6
```

---

## 扩展建议

1. 用 LangGraph 替换当前简单调度层，实现显式 DAG 状态流。
2. 将 MessageBus 替换为 Redis/NATS 支持跨进程 Agent。
3. 为 RefactorEngine 增加 AST 级变换（libcst/tree-sitter）以获得更高正确率。
4. 引入目录依赖拓扑排序，实现“先依赖后消费者”的智能调度。

---

## 目标

CodeHive 的最终目标是：

- **一句话生成可维护代码仓库**，或
- **把任意 Agent 产出的脏仓库自动重构为结构清晰、范式统一、可持续演进的专业级代码库。**
