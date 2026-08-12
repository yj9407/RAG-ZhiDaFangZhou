# 智达方舟 — 自然语言转 SQL 智能查询系统
## 项目概述

搭建企业级自然语言转 SQL 查询系统，让不懂 SQL 的业务人员直接对话数据库。

## 核心亮点

- **12 节点 Agent DAG 工作流**：基于 LangGraph StateGraph 构建，支持并行召回、条件路由与自愈闭环
- **三路混合元数据检索**：Qdrant 向量检索 + ES/自研全文检索 + MySQL 关系型检索，并行执行
- **双层 SQL 自愈闭环**：EXPLAIN 语法校验 + LLM 四维语义自检，语法修正一次通过率 80%，有效抑制大模型幻觉
- **自研零依赖搜索引擎**：纯 Python 实现（jieba 分词 + 倒排索引），接口兼容 AsyncElasticsearch
- **SSE 流式进度推送**：12 步工作流节点实时推送到前端，全流程可视化
- **全链路日志追踪**：FastAPI 中间件 + Loguru + ContextVar，每个请求自动注入唯一 request_id

## 完整链路图

12 节点 Agent DAG 工作流：

```mermaid
graph TD
    START(["💬 用户自然语言提问"]):::startEnd
    START --> N1["<b>① 关键词提取</b><br/>jieba 分词 + 词性过滤"]:::llm

    N1 --> N2["<b>② 召回字段</b><br/>Embedding → Qdrant"]:::search
    N1 --> N3["<b>③ 召回维度值</b><br/>ES / 自研全文检索"]:::search
    N1 --> N4["<b>④ 召回指标</b><br/>Embedding → Qdrant"]:::search

    N2 --> N5["<b>⑤ 合并与主外键补全</b><br/>去重 + 按表分组"]:::merge
    N3 --> N5
    N4 --> N5

    N5 --> N6["<b>⑥ 表与字段精选</b><br/>LLM 过滤无关列"]:::llm
    N5 --> N7["<b>⑦ 指标精选</b><br/>LLM 过滤无关指标"]:::llm

    N6 --> N8["<b>⑧ 补充上下文</b><br/>当前日期 / DB 版本"]:::ctx
    N7 --> N8

    N8 --> N9["<b>⑨ 生成 SQL</b><br/>LLM 推理"]:::llm

    N9 --> N10{"<b>⑩ 语法校验</b><br/>EXPLAIN"}:::decision

    N10 -->|"✅ 通过"| N12["<b>⑫ 执行查询</b><br/>MySQL"]:::exec
    N10 -->|"❌ 语法错误"| N11["<b>⑪ SQL 自愈</b><br/>LLM 根据 EXPLAIN 报错修正"]:::fix
    N11 -.-> N10

    N12 --> N13{"<b>⑬ 语义自检</b><br/>四维：聚合/过滤/分组/数据量"}:::decision

    N13 -->|"✅ 通过"| END(["✅ 返回查询结果"]):::startEnd
    N13 -.->|"❌ 未通过 + 重试&lt;2"| N11

    classDef startEnd fill:#eef6ee,stroke:#8fb98f,stroke-width:1.5px,color:#3a5a3a
    classDef llm fill:#eef4fb,stroke:#8fa8cf,stroke-width:1.5px,color:#3a4a6a
    classDef search fill:#fdf6ec,stroke:#cfa87f,stroke-width:1.5px,color:#6a543a
    classDef merge fill:#f6eff9,stroke:#b08fc9,stroke-width:1.5px,color:#5a3a6a
    classDef ctx fill:#fbeef3,stroke:#cf8fa8,stroke-width:1.5px,color:#6a3a4a
    classDef decision fill:#fbfaec,stroke:#c9c07f,stroke-width:1.5px,color:#6a653a
    classDef exec fill:#edf7ed,stroke:#8fbf8f,stroke-width:1.5px,color:#3a5a3a
    classDef fix fill:#fbefef,stroke:#cf8f8f,stroke-width:1.5px,color:#6a3a3a
```

> **关键路径说明**：🟢 入口/出口｜🔵 LLM 推理｜🟠 三路并行检索｜🟣 合并编排｜🟡 校验决策｜🔴 自愈修正。回路构成**双层 SQL 自愈闭环**——第 1 层通过 EXPLAIN 修正语法错误，第 2 层通过四维语义校验修正逻辑错误。

系统分层架构：

```mermaid
graph TB
    subgraph 前端层
        FE["Vue 3 + Vite<br/>SSE 流式进度展示"]
    end

    subgraph API 网关层
        GW["FastAPI<br/>请求路由 + 依赖注入<br/>全链路日志追踪"]
    end

    subgraph Agent 引擎层 ["Agent 引擎层 — LangGraph StateGraph"]
        AG["12 节点 DAG 编排<br/>状态管理 + 条件路由<br/>ContextVar 请求隔离"]
    end

    subgraph 服务层
        SV["QueryService<br/>查询编排 + 结果缓存"]
    end

    subgraph 数据检索层 ["数据检索层（三路混合并行）"]
        direction LR
        QD["Qdrant<br/>向量检索<br/>字段 / 指标语义匹配"]
        ES["ES / 自研引擎<br/>全文检索<br/>维度值模糊匹配"]
        MY["MySQL<br/>关系型检索<br/>表结构约束"]
    end

    subgraph 基础设施层
        direction LR
        LLM["DeepSeek API<br/>统一 LLM 调用"]
        LOG["Loguru + ContextVar<br/>全链路日志"]
    end

    FE -->|"HTTP + SSE"| GW
    GW --> AG
    AG --> SV
    SV --> QD
    SV --> ES
    SV --> MY
    AG -.-> LLM
    GW -.-> LOG
    AG -.-> LOG
```

## 技术栈

| 分类 | 技术 |
|------|------|
| 后端 | Python 3.12, FastAPI, LangGraph, DeepSeek |
| 向量检索 | Qdrant（bge-large-zh-v1.5） |
| 全文检索 | Elasticsearch / 自研 SimpleSearchClient |
| 关系型检索 | SQLAlchemy + asyncmy + MySQL 8.0 |
| 前端 | Vue 3 + Vite（原生 Fetch + SSE） |

## 仓库结构

```
RAG智达方舟/
├── data-agent/           # 后端服务（核心代码）
├── data-agent-fronted/   # 前端（Vue 3）
├── docker-compose.yml     # 一键启动 MySQL + Qdrant + ES + Kibana
├── main.py
└── README.md              # 你正在看
```

详细使用文档见 [data-agent/README.md](data-agent/README.md) 与 [data-agent/rag智达方舟.md](data-agent/rag智达方舟.md)。

## 快速启动

```bash
# 一键启动所有基础设施（MySQL + Qdrant + ES + Kibana + Embedding）
docker compose up -d

# 后端
cd data-agent && uv sync
uv run python -m app.scripts.create_dw_data
uv run python -m app.scripts.build_meta_knowledge -c conf/meta_config.yaml
uv run python main.py                              # :8000

# 前端
cd data-agent-fronted && npm install && npm run dev   # :5173
```

环境要求：Python 3.12+, MySQL 8.0+, Qdrant, Node.js 18+。

## 作者

李曜均 · 19120595422@163.com
