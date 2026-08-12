# 智达方舟 — 自然语言转 SQL 智能查询系统

> 让业务人员用大白话直接查数据库，将查数从 3 天缩短到 10 秒。

## 项目概述

面向企业内部数据查询场景构建的 Text-to-SQL 系统。用户用中文自然语言提问，系统自动完成语义理解 → 元数据检索 → SQL 生成 → 双层自愈校验 → 执行返回的全链路自动化。

## 核心亮点

- **12 节点 Agent DAG 工作流**：基于 LangGraph StateGraph 构建，支持并行召回、条件路由与自愈闭环
- **三路混合元数据检索**：Qdrant 向量检索 + ES/自研全文检索 + MySQL 关系型检索，并行执行
- **双层 SQL 自愈闭环**：EXPLAIN 语法校验 + LLM 四维度语义自检，语法修正一次通过率 80%，有效抑制大模型幻觉
- **自研零依赖搜索引擎**：纯 Python 实现（jieba 分词 + 倒排索引），接口兼容 AsyncElasticsearch
- **SSE 流式进度推送**：12 步工作流节点实时推送到前端，全流程可视化
- **全链路日志追踪**：FastAPI 中间件 + Loguru + ContextVar，每个请求自动注入唯一 request_id

## 完整链路图

### 12 节点 Agent DAG 工作流

```mermaid
graph TD
    START([用户自然语言提问]) --> N1["<b>1. extract_keywords</b><br/>jieba 分词 + 词性过滤<br/>提取关键词"]

    N1 --> N2["<b>2. recall_column</b><br/>LLM 扩展关键词<br/>Embedding → Qdrant 向量检索"]
    N1 --> N3["<b>3. recall_value</b><br/>LLM 扩展关键词<br/>ES / 自研全文检索"]
    N1 --> N4["<b>4. recall_metric</b><br/>LLM 扩展关键词<br/>Embedding → Qdrant 向量检索"]

    N2 --> N5["<b>5. merge_retrieved_info</b><br/>合并去重 + 补全主外键<br/>按表分组"]
    N3 --> N5
    N4 --> N5

    N5 --> N6["<b>6. filter_table</b><br/>LLM 精选表与字段"]
    N5 --> N7["<b>7. filter_metric</b><br/>LLM 精选指标"]

    N6 --> N8["<b>8. add_extra_context</b><br/>补充日期 / DB 版本信息"]
    N7 --> N8

    N8 --> N9["<b>9. generate_sql</b><br/>LLM 生成 SQL"]

    N9 --> N10{"<b>10. validate_sql</b><br/>EXPLAIN 语法校验"}
    
    N10 -->|"✅ 通过"| N12["<b>12. execute_sql</b><br/>执行查询"]
    N10 -->|"❌ 语法错误"| N11["<b>11. correct_sql</b><br/>LLM 根据 EXPLAIN 报错修正"]
    N11 --> N10

    N12 --> N13{"<b>verify_result</b><br/>LLM 五维语义自检<br/>聚合/过滤/分组/数据量/口径"}

    N13 -->|"✅ 通过"| END([返回查询结果])
    N13 -->|"❌ 未通过 + 重试&lt;2"| N11

    style START fill:#e1f5e1,stroke:#2e7d32,stroke-width:2px
    style END fill:#e1f5e1,stroke:#2e7d32,stroke-width:2px
    style N1 fill:#e3f2fd,stroke:#1565c0
    style N2 fill:#fff3e0,stroke:#e65100
    style N3 fill:#fff3e0,stroke:#e65100
    style N4 fill:#fff3e0,stroke:#e65100
    style N5 fill:#f3e5f5,stroke:#7b1fa2
    style N6 fill:#e8f5e9,stroke:#2e7d32
    style N7 fill:#e8f5e9,stroke:#2e7d32
    style N8 fill:#fce4ec,stroke:#c62828
    style N9 fill:#e3f2fd,stroke:#1565c0
    style N10 fill:#fff9c4,stroke:#f9a825
    style N11 fill:#ffccbc,stroke:#d84315
    style N12 fill:#c8e6c9,stroke:#388e3c
    style N13 fill:#fff9c4,stroke:#f9a825
```

> **关键路径说明**：蓝底节点为 LLM 推理节点，橙底为并行检索节点，黄底为校验决策节点，红底为修正节点。虚线回路构成**双层 SQL 自愈闭环**——第 1 层通过 EXPLAIN 修正语法错误，第 2 层通过五维语义校验修正逻辑错误。

### 系统分层架构

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
├── main.py
└── README.md             # 你正在看
```

详细使用文档见 [data-agent/README.md](data-agent/README.md) 与 [data-agent/rag智达方舟.md](data-agent/rag智达方舟.md)。

## 快速启动

```bash
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