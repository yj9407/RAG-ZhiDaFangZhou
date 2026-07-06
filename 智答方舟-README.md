# 智答方舟 RAG 问答系统

## 项目背景

企业里业务人员想看数据，流程通常是：提需求 → 等排期 → 技术人员写 SQL → 导出 Excel。一次查数平均需要 2-3 天，效率低、沟通成本高。

## 解决方案

构建了一个自然语言转 SQL 的问答系统，业务人员直接用中文提问，系统自动理解语义、定位数据表和字段、生成 SQL、执行并返回结果，全程 10 秒级响应。

## 核心实现

**整体流程（LangGraph 12 节点 DAG 工作流）：**

1. 用户输入问题 → jieba 分词提取关键词
2. 三路并行元数据检索：
   - Qdrant 向量检索：字段名和指标的语义匹配（如"销售额"→ order_amount）
   - ES/内置搜索引擎：维度值匹配（如"华东区"→ 地区表枚举值）
   - MySQL 关系型检索：表结构 + 主外键关联补全
3. LLM 对召回结果进行精选，过滤无关表和字段
4. LLM 根据精选的元数据生成 SQL
5. EXPLAIN 语法校验：通过则直接执行；失败则将报错信息返回给 LLM 修正后再次校验（SQL 自愈闭环）
6. 执行 SQL，SSE 流式返回结果到前端

**关键设计：**

- **三路并行召回**：等待时间约等于最慢一路，而非三路相加
- **SQL 自愈闭环**：校验失败自动修正，一次校验通过率达 80%，有效抑制 LLM 幻觉
- **内置零依赖搜索引擎**：纯 Python 实现（jieba 分词 + 倒排索引），接口兼容 AsyncElasticsearch，无需安装 ES 即可运行
- **YAML 外置化元数据配置**：新增数据表只需改 YAML + 执行一条命令即可重建知识库索引
- **全链路日志追踪**：每个请求生成唯一 request_id，注入 Loguru 日志，排查问题可快速定位

## 技术栈

| 分类 | 技术 |
|------|------|
| 后端框架 | Python 3.12, FastAPI |
| Agent 工作流 | LangChain, LangGraph |
| 向量检索 | Qdrant（bge-large-zh-v1.5 embedding, COSINE 相似度） |
| 全文检索 | Elasticsearch / 内置 SimpleSearchClient |
| 关系型检索 | SQLAlchemy 2.0 + asyncmy + MySQL 8.0 |
| 中文分词 | jieba |
| 日志追踪 | Loguru + ContextVar |
| 前端 | Vue 3 + Vite（原生 Fetch API + SSE 流式消费） |

## 最终效果

- 查数时效从 2-3 天缩短至 10 秒级
- 三路并行检索将元数据检索耗时压缩至单路约 1/3
- SQL 自愈闭环使一次校验通过率达 80%

## 快速启动

```bash
# 环境要求：Python 3.12+, MySQL 8.0+, Qdrant, Node.js 18+

# 后端
cd data-agent
uv sync
# 修改 conf/app_config.yaml —— 填 LLM API Key 和地址
uv run python -m app.scripts.create_dw_data
uv run python -m app.scripts.build_meta_knowledge -c conf/meta_config.yaml
uv run python main.py                    # 启动后端 :8000

# 前端
cd data-agent-fronted
npm install
npm run dev                              # 启动前端 :5173
```

## 作者

李曜均 · 19120595422@163.com
