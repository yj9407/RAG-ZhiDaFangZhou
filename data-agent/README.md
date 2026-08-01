# 智达方舟 — 自然语言转 SQL 智能查询系统

> 让业务人员用大白话直接查数据库，将查数从 3 天缩短到 10 秒。

## 项目概述

面向企业内部数据查询场景构建的 Text-to-SQL 系统。用户用中文自然语言提问（如"去年华东区销售额前三的省份"），系统自动完成语义理解 → 元数据检索 → SQL 生成 → 双层自愈校验 → 执行返回的全链路自动化。

## 核心亮点

- **12 节点 Agent DAG 工作流**：基于 LangGraph StateGraph 构建，支持并行召回、条件路由与自愈闭环
- **三路混合元数据检索**：Qdrant 向量检索 + Elasticsearch/自研全文检索 + MySQL 关系型检索，并行执行
- **双层 SQL 自愈闭环**：EXPLAIN 语法校验 + LLM 四维度语义自检，语法修正一次通过率 80%，有效抑制大模型幻觉
- **自研零依赖搜索引擎**：纯 Python 实现（jieba 分词 + 倒排索引），接口兼容 AsyncElasticsearch，开发环境零外部依赖
- **SSE 流式进度推送**：12 步工作流节点实时推送到前端，全流程可视化
- **全链路日志追踪**：FastAPI 中间件 + Loguru + ContextVar，单次请求所有日志自动注入唯一 request_id

## 技术栈

| 分类 | 技术 |
|------|------|
| 后端框架 | Python 3.12, FastAPI |
| Agent 工作流 | LangChain, LangGraph |
| LLM | DeepSeek / OpenAI 兼容协议 |
| 向量检索 | Qdrant（bge-large-zh-v1.5, COSINE 相似度） |
| 全文检索 | Elasticsearch / 内置 SimpleSearchClient |
| 关系型检索 | SQLAlchemy 2.0 + asyncmy + MySQL 8.0 |
| 中文分词 | jieba |
| 日志追踪 | Loguru + ContextVar |
| 前端 | Vue 3 + Vite（原生 Fetch + SSE 流式消费） |

## 架构设计

```
用户问题
  ↓
[1] jieba 分词提取关键词
  ↓
[2] Qdrant 向量检索字段  [3] ES/自研 全文检索维度值  [4] Qdrant 向量检索指标
  ↓                          ↓                          ↓
[5] 三路结果合并去重 + 补全主外键 + 按表分组
  ↓
[6] LLM 精选表与字段       [7] LLM 精选指标
  ↓
[8] 补充上下文（日期/数据库方言）
  ↓
[9] LLM 生成 SQL
  ↓
[10] EXPLAIN 语法校验
  ├─ 通过 → [12] 执行 SQL → 返回结果
  └─ 失败 → [11] LLM 根据报错修正 → 回到 [10]
```

## 最终效果

- 查数时效从 2-3 天缩短至 10 秒级
- 三路并行召回将检索耗时压缩至单路约 1/3
- SQL 自愈闭环一次校验通过率 80%，语义自检进一步拦截业务逻辑错误
- 新增数据表仅需配置 YAML 元数据 + 一条命令即可接入，无需修改业务代码

## 快速启动

```bash
# 环境要求：Python 3.12+, MySQL 8.0+, Qdrant, Node.js 18+

cd data-agent && uv sync

# 修改 conf/app_config.yaml —— 填写 LLM API Key 和地址
# 修改 conf/meta_config.yaml —— （可选）按需调整表/字段/指标定义

uv run python -m app.scripts.create_dw_data       # 创建测试数据
uv run python -m app.scripts.build_meta_knowledge -c conf/meta_config.yaml  # 构建元知识库
uv run python main.py                              # 启动后端 :8000

# 前端
cd data-agent-fronted && npm install && npm run dev
```

详细文档请参阅 [rag智达方舟.md](rag智达方舟.md)。

## 作者

李曜均 · 19120595422@163.com
