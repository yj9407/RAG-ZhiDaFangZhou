# 数据通达（Data-Agent）—— 项目全套保姆级文档

> **文档版本**：v1.0  
> **适用人群**：后端开发工程师 / 全栈开发 / 运维部署人员  
> **前置知识要求**：Python 基础、FastAPI 基础、数据库基础、命令行操作  

---

## 目录

- [1. 项目基础信息](#1-项目基础信息)
  - [1.1 搭建初衷](#11-搭建初衷)
  - [1.2 项目核心功能](#12-项目核心功能)
  - [1.3 完整技术栈说明](#13-完整技术栈说明)
  - [1.4 项目适配环境与依赖版本要求](#14-项目适配环境与依赖版本要求)
  - [1.5 项目整体架构设计](#15-项目整体架构设计)
  - [1.6 核心模块分工](#16-核心模块分工)
- [2. 项目从零搭建完整步骤](#2-项目从零搭建完整步骤)
  - [2.1 前期环境准备](#21-前期环境准备)
  - [2.2 项目初始化搭建流程](#22-项目初始化搭建流程)
  - [2.3 项目基础配置流程](#23-项目基础配置流程)
  - [2.4 创建测试数据](#24-创建测试数据)
  - [2.5 构建元数据知识库](#25-构建元数据知识库)
- [3. 项目运行 & 启动方式](#3-项目运行--启动方式)
  - [3.1 本地开发启动完整流程](#31-本地开发启动完整流程)
  - [3.2 启动常见报错与解决方案](#32-启动常见报错与解决方案)
  - [3.3 打包构建命令](#33-打包构建命令)
  - [3.4 生产环境部署启动方式](#34-生产环境部署启动方式)
- [4. 项目必备插件/依赖包清单](#4-项目必备插件依赖包清单)
  - [4.1 所有安装的核心依赖](#41-所有安装的核心依赖)
  - [4.2 依赖安装/卸载/更新命令](#42-依赖安装卸载更新命令)
- [5. 完整项目目录结构文档](#5-完整项目目录结构文档)
  - [5.1 完整树形目录结构](#51-完整树形目录结构)
  - [5.2 每个文件夹、每个核心文件逐一详解](#52-每个文件夹每个核心文件逐一详解)
  - [5.3 项目核心文件优先级说明](#53-项目核心文件优先级说明)
  - [5.4 新增功能对应目录存放规范](#54-新增功能对应目录存放规范)
- [6. 项目开发规范 & 使用文档](#6-项目开发规范--使用文档)
  - [6.1 项目代码书写规范](#61-项目代码书写规范)
  - [6.2 新增功能标准流程](#62-新增功能标准流程)
  - [6.3 项目全局变量与方法](#63-项目全局变量与方法)
  - [6.4 接口请求与状态管理规则](#64-接口请求与状态管理规则)
- [7. 项目常见问题汇总](#7-项目常见问题汇总)
  - [7.1 启动/运行/打包报错全套方案](#71-启动运行打包报错全套方案)
  - [7.2 环境兼容与依赖冲突](#72-环境兼容与依赖冲突)
  - [7.3 开发过程高频踩坑点](#73-开发过程高频踩坑点)
- [8. 补充说明](#8-补充说明)

---

## 1. 项目基础信息

### 1.1 搭建初衷

**数据通达（Data-Agent）** 是一个企业级 Text-to-SQL 智能数据问答平台。核心目标是让每一位业务人员都用自然语言直接查询企业数据库，告别"提需求 → 排队等技术 → 写 SQL → 导出 Excel"的传统低效流程。

**核心理念**：让不懂 SQL 的人也能用大白话查到数据，将查数从 3 天缩短到 10 秒级响应。

### 1.2 项目核心功能

| 功能模块 | 说明 |
|---------|------|
| **自然语言→SQL** | 用户用中文自然提问（如"去年华东区销售额前三的门店"），AI 自动生成并执行 SQL |
| **混合元数据检索** | Qdrant 向量检索（字段/指标语义匹配）+ Elasticsearch 全文检索（维度值匹配）+ MySQL 关系型检索（表结构约束）三路并行召回 |
| **LLM 关键词扩展** | 在召回前先用大模型对查询自动扩展关键词，提升召回覆盖率 |
| **SQL 自动校验与自愈** | 生成 SQL → `EXPLAIN` 语法校验 → 报错自动路由到纠错节点 → LLM 修正 → 再次校验 → 通过后执行，形成"自愈闭环" |
| **SSE 流式进度推送** | 全流程每一步节点实时通过 Stream-Server-Event 推送进度给前端（抽取关键词→召回字段→合并→过滤→生成SQL→校验→执行） |
| **全链路日志追踪** | 每个请求生成唯一 `request_id`，注入到所有日志中，便于排查问题 |
| **元数据知识库自动构建** | 通过 YAML 配置表/字段/指标元数据 → 一键脚本自动导入 MySQL 元数据库、构建 Qdrant 向量索引、ES 全文索引 |

### 1.3 完整技术栈说明

**核心框架层**

| 技术 | 版本 | 作用 |
|------|------|------|
| **Python** | ≥ 3.12 | 编程语言 |
| **FastAPI** | ≥ 0.128.0 | Web 框架，提供 REST API + SSE 流式端点 |
| **Uvicorn** | 随 fastapi[standard] 安装 | ASGI 服务器，运行 FastAPI 应用 |
| **Pydantic** | 随 FastAPI 安装 | 请求/响应数据模型校验 |

**AI / LLM 层**

| 技术 | 版本 | 作用 |
|------|------|------|
| **LangChain** | ≥ 1.2.7 | LLM 调用抽象层（Prompt模板、链式调用、输出解析器） |
| **LangGraph** | ≥ 1.0.7 | 有状态多节点 Agent 工作流编排（StateGraph + 条件路由） |
| **langchain-deepseek** | ≥ 1.0.1 | DeepSeek LLM 适配器（本项目用 openai 兼容协议调用） |
| **langchain-huggingface** | ≥ 1.2.0 | HuggingFace Embedding 集成 |
| **sentence-transformers** | ≥ 5.6.0 | 向量编码底层依赖 |

**数据存储层**

| 技术 | 版本 | 作用 |
|------|------|------|
| **MySQL** | 任意支持版本 | 元数据库（meta）+ 数据仓库（dw）双库 |
| **SQLAlchemy 2.0** | ≥ 2.0.46 | ORM 框架（async 模式），管理数据库连接池、表模型映射 |
| **asyncmy** | ≥ 0.2.11 | MySQL 异步驱动 |
| **Qdrant** | ≥ 1.16.2 | 向量数据库，存储字段/指标的语义向量索引 |
| **Elasticsearch** | 8.x | 全文搜索引擎，存储维度枚举值的分词索引 |

**工具与辅助层**

| 技术 | 版本 | 作用 |
|------|------|------|
| **jieba** | ≥ 0.42.1 | 中文分词（抽取关键词 + 内置简易搜索引擎的分词） |
| **Loguru** | ≥ 0.7.3 | 日志框架，支持文件滚动、按时间保留、结构化输出 |
| **OmegaConf** | ≥ 2.3.0 | YAML 配置加载与管理 |
| **PyYAML** | ≥ 6.0.3 | YAML 解析底层库 |
| **huggingface-hub** | ≥ 0.36.0 | HuggingFace 模型仓库访问 |
| **cryptography** | ≥ 46.0.4 | SSL/加密支持 |

**包管理**

| 技术 | 作用 |
|------|------|
| **uv** | Python 包管理器（替代 pip），项目使用 `pyproject.toml` + `uv.lock` 管理依赖 |

### 1.4 项目适配环境与依赖版本要求

| 项目 | 最低要求 | 推荐版本 |
|------|---------|---------|
| **操作系统** | Windows 10+ / macOS 12+ / Linux Ubuntu 20.04+ | Ubuntu 22.04 LTS |
| **Python** | ≥ 3.12 | 3.12.x |
| **MySQL** | 5.7+（需要 InnoDB 引擎） | 8.0+ |
| **Elasticsearch** | 8.x（或使用内置纯 Python 替代） | 内置 `SimpleSearchClient` 零依赖替代 |
| **Qdrant** | 任意支持版本 | 最新稳定版 |
| **Embedding 服务** | HuggingFace Text Embedding Inference | `BAAI/bge-large-zh-v1.5` |
| **包管理器** | pip / uv | uv（推荐） |
| **内存** | ≥ 8 GB | ≥ 16 GB |
| **磁盘** | ≥ 10 GB 可用空间 | SSD |

> **重要说明**：Elasticsearch 安装复杂，本项目提供了 `app/clients/simple_search_engine.py`，一个**纯 Python 实现的内存搜索引擎**，使用 jieba 分词 + 内存索引，**无需安装 ES 即可运行**。如需生产级全文检索，再部署真实 ES。

### 1.5 项目整体架构设计

**Clean Architecture（清洁架构）分层模型**

```
               ┌─────────────────────────┐
               │   API 层 (FastAPI)       │  HTTP 入口、路由、依赖注入
               ├─────────────────────────┤
               │   Service 层             │  业务编排（查询服务、元知识构建服务）
               ├─────────────────────────┤
               │   Agent 层 (LangGraph)   │  12 节点 DAG 工作流（编排调度）
               │   └── Nodes              │  各节点的具体实现逻辑
               ├─────────────────────────┤
               │   Repository 层          │  数据访问抽象（MySQL / Qdrant / ES）
               ├─────────────────────────┤
               │   Client 层              │  外部客户端管理（连接池、生命周期）
               └─────────────────────────┘
                      ↕
┌──────────────────────────────────────────────┐
│  领域实体层 (Entities)  ←  跨层共享，纯数据  │
│  模型层 (Models)        ←  数据库表映射      │
│  配置层 (Conf)          ←  环境配置管理      │
│  提示词层 (Prompts)     ←  外部化 Prompt 文件│
└──────────────────────────────────────────────┘
```

**LangGraph 12 节点 DAG 工作流**

```
START
  │
  ▼
[1. extract_keywords]    ← jieba 分词提取关键词
  │
  ├──→ [2. recall_column]   ← LLM扩展关键词 → Embedding向量化 → Qdrant检索
  ├──→ [3. recall_value]    ← LLM扩展关键词 → ES/Jieba全文检索
  └──→ [4. recall_metric]   ← LLM扩展关键词 → Embedding向量化 → Qdrant检索
  │
  ▼  (三路并行汇聚)
[5. merge_retrieved_info]  ← 合并去重 + 补全主外键 + 聚合表结构
  │
  ├──→ [6. filter_table]    ← LLM 精选需要的表与字段
  └──→ [7. filter_metric]   ← LLM 精选需要的指标
  │
  ▼
[8. add_extra_context]    ← 补充当前日期/数据库版本信息
  │
  ▼
[9. generate_sql]         ← LLM 生成 SQL
  │
  ▼
[10. validate_sql]        ← EXPLAIN 语法校验
  │
  ├── (通过) ──→ [12. execute_sql]  ← 执行查询，返回结果
  └── (失败) ──→ [11. correct_sql]  ← LLM 根据报错修正 SQL → 再执行
                    │
                    └──→ END
```

### 1.6 核心模块分工

| 模块 | 路径 | 职责 |
|------|------|------|
| **API 路由** | `app/api/routers/` | 定义 HTTP 端点，接收请求，返回响应 |
| **API 依赖注入** | `app/api/dependencies.py` | 通过 FastAPI Depends 管理 Repository 的创建与注入 |
| **API 数据模型** | `app/api/schemas/` | Pydantic 请求/响应 Schema |
| **QueryService** | `app/services/query_service.py` | 执行 LangGraph 工作流，通过 SSE 流式返回结果 |
| **MetaKnowledgeService** | `app/services/meta_knowledge_service.py` | 读取 YAML 配置 → 导入 MySQL + Qdrant + ES，构建元知识库 |
| **Agent Graph** | `app/agent/graph.py` | 定义 12 节点的 DAG 执行图 |
| **Agent State** | `app/agent/state.py` | 工作流全局状态类型定义（TypedDict） |
| **Agent Context** | `app/agent/context.py` | 工作流运行时上下文（注入 Repository 实例） |
| **Agent Nodes** | `app/agent/nodes/*.py` | 12 个节点的具体业务逻辑实现 |
| **LLM 配置** | `app/agent/llm.py` | LLM 客户端初始化 |
| **Repository** | `app/repositories/` | 封装 MySQL/Qdrant/ES 的数据访问操作 |
| **Client Manager** | `app/clients/` | 外部客户端连接池管理与生命周期 |
| **Entities** | `app/entities/` | 纯数据类，核心领域对象 |
| **Models** | `app/models/` | SQLAlchemy ORM 表映射模型 |
| **Mappers** | `app/repositories/mysql/meta/mappers/` | Entity ↔ Model 转换映射 |
| **Conf** | `app/conf/` | 配置类定义 + 配置加载 |
| **Core** | `app/core/` | 日志、请求上下文、应用生命周期 |
| **Prompt** | `app/prompt/` | 外部化 Prompt 模板加载 |
| **Scripts** | `app/scripts/` | 一键建表/一键构建元知识库脚本 |

---

## 2. 项目从零搭建完整步骤

### 2.1 前期环境准备

#### 2.1.1 Python 环境

```bash
# 1. 确认 Python 版本 ≥ 3.12
python --version
# 期望输出: Python 3.12.x

# 2. 如果版本不对，去官网下载: https://www.python.org/downloads/

# 3. 安装 uv 包管理器（推荐）
# Windows (PowerShell):
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# 4. 验证 uv 安装
uv --version
```

#### 2.1.2 MySQL 环境

```bash
# 方式1: 本地安装 MySQL 8.0
# 下载: https://dev.mysql.com/downloads/mysql/

# 方式2: Docker 安装（推荐）
docker run -d \
  --name mysql-data-agent \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=root123 \
  -e MYSQL_USER=yj9407 \
  -e MYSQL_PASSWORD=Aa111111 \
  mysql:8.0

# 3. 登录 MySQL，创建两个数据库
mysql -u root -p

CREATE DATABASE meta CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE dw CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 确认用户权限
GRANT ALL PRIVILEGES ON meta.* TO 'yj9407'@'%';
GRANT ALL PRIVILEGES ON dw.* TO 'yj9407'@'%';
FLUSH PRIVILEGES;

-- 验证
SHOW DATABASES;
```

#### 2.1.3 Qdrant 向量数据库

```bash
# Docker 启动 Qdrant
docker run -d \
  --name qdrant-data-agent \
  -p 6333:6333 \
  -p 6334:6334 \
  qdrant/qdrant:latest

# 验证
curl http://localhost:6333/readyz
# 期望: 返回 OK 或 200 状态码
```

#### 2.1.4 Embedding 服务（HuggingFace Text Embedding Inference）

```bash
# 方式1: Docker 部署 TEI（推荐生产用）
# 需要 GPU: docker run --gpus all -p 8081:80 -e MODEL_ID=BAAI/bge-large-zh-v1.5 ghcr.io/huggingface/text-embeddings-inference:latest

# 方式2: 本项目直接用 HuggingFaceEmbeddings 本地加载模型（开发用）
# 在 app/clients/embedding_client_manager.py 中已配置 device="cpu"
# 首次运行会自动下载模型到本地缓存，约 1.3GB
# 无需单独部署服务！
```

> **注意**：本项目 `EmbeddingClientManager` 默认使用 `HuggingFaceEmbeddings` 本地加载模型（CPU 模式），**不需要单独启动 Embedding 服务**。`app_config.yaml` 中的 embedding.host/port 是预留配置，当前不使用。

### 2.2 项目初始化搭建流程

#### Step 1: 获取项目代码



# 确认目录结构
ls -la
# 应该看到: main.py, pyproject.toml, uv.lock, app/, conf/, prompts/, logs/
```

#### Step 2: 安装项目依赖

```bash
# 使用 uv 安装（推荐，速度极快）
uv sync

# 或者使用 pip 安装
pip install -e .

# 验证关键依赖安装成功
python -c "import fastapi; print(fastapi.__version__)"
python -c "import langgraph; print(langgraph.__version__)"
python -c "import qdrant_client; print(qdrant_client.__version__)"
python -c "import jieba; print(jieba.__version__)"
```

#### Step 3: 验证依赖安装

```bash
# 确认所有核心依赖可用
uv run python -c "
import fastapi, uvicorn, pydantic
import langchain, langgraph
import qdrant_client
import sqlalchemy, asyncmy
import jieba, loguru, omegaconf, yaml
import sentence_transformers
print('所有依赖导入成功！')
"
```

### 2.3 项目基础配置流程

#### 2.3.1 修改应用配置文件

编辑 [`conf/app_config.yaml`](conf/app_config.yaml)：

```yaml
logging:
  file:
    enable: true
    level: INFO          # 日志级别: DEBUG / INFO / WARNING / ERROR
    path: logs           # 日志文件存储目录
    rotation: "10 MB"    # 日志文件自动滚动大小
    retention: "7 days"  # 日志文件保留时长
  console:
    enable: true         # 是否同时输出到控制台
    level: INFO

db_meta:                 # 元数据库配置（存储表/字段/指标元信息）
  host: localhost
  port: 3306
  user: yj9407
  password: Aa111111
  database: meta

db_dw:                   # 数据仓库配置（实际业务数据）
  host: localhost
  port: 3306
  user: yj9407
  password: Aa111111
  database: dw

qdrant:                  # 向量数据库配置
  host: localhost
  port: 6333
  embedding_size: 1024   # 向量维度（bge-large-zh 是 1024 维）

embedding:               # Embedding 服务配置（预留，当前代码本地加载）
  host: localhost
  port: 8081
  model: BAAI/bge-large-zh-v1.5

es:                      # Elasticsearch 配置（可用内置 SimpleSearchClient 替代）
  host: localhost
  port: 9200
  index_name: data_agent

llm:                     # LLM 大模型配置 ★★★ 必须修改 ★★★
  model_name: gpt-5.2-codex          # 替换为你的模型名称
  api_key: <api-key>                  # 替换为你的 API Key
  base_url: https://api.openai-proxy.org/v1   # 替换为你的 API 地址
```

**⚠️ 必须修改的配置项**：
- `llm.api_key`：填写你的 LLM API Key
- `llm.base_url`：填写你的 LLM API 代理地址
- `llm.model_name`：填写你要使用的模型名称（如 `deepseek-chat`）

#### 2.3.2 修改元数据配置文件

编辑 [`conf/meta_config.yaml`](conf/meta_config.yaml)：这个文件定义了你的业务数据表结构、字段信息和指标定义。

```yaml
tables:                  # 表定义列表
  - name: dim_region     # 表名（必须与 dw 库中实际表名一致）
    role: dim            # 表类型: dim(维度表) / fact(事实表)
    description: 地区维度表，用于描述订单发生的地理区域信息。
    columns:             # 字段列表
      - name: region_id
        role: primary_key     # 字段角色: primary_key / foreign_key / measure / dimension
        description: 地区唯一标识。
        alias: [地区ID, 区域ID]   # 搜索别名（帮助语义检索匹配）
        sync: false            # 是否同步字段取值到 ES（枚举值需要同步）

      - name: region_name
        role: dimension
        description: 订单所属的大区名称，如华东、华南等。
        alias: [地区, 区域, 大区]
        sync: true             # 维度值需要同步到 ES，支持模糊搜索

metrics:                 # 指标定义列表
  - name: GMV
    description: 全称Gross Merchandise Value，表示所有订单的成交金额总和。
    relevant_columns:    # 关联的字段
      - fact_order.order_amount
    alias: [成交总额, 订单总额]   # 搜索别名
```

> **字段角色说明**：
> - `primary_key`：主键，不会自动加入召回结果
> - `foreign_key`：外键，用于表关联
> - `measure`：度量值（数值类型，可聚合计算）
> - `dimension`：维度字段（分组/筛选字段）

### 2.4 创建测试数据

```bash
# 运行数据仓库建表与测试数据插入脚本
uv run python -m app.scripts.create_dw_data
```

执行成功后输出：
```
[OK]表结构创建完成
[OK]测试数据插入完成
  dim_region: 8 行
  dim_customer: 8 行
  dim_product: 8 行
  dim_date: 336 行
  fact_order: 50 行
```

### 2.5 构建元数据知识库

```bash
# 将 meta_config.yaml 中的元数据导入 MySQL + Qdrant + ES
uv run python -m app.scripts.build_meta_knowledge -c conf/meta_config.yaml
```

执行过程日志：
```
加载配置文件
保存表信息到meta数据库
为字段信息建立向量索引
为字段取值建立全文索引
保存指标信息到meta数据库
为指标信息建立向量索引
元数据知识库构建完成
```

**这一步做了什么**：
1. 读取 `meta_config.yaml` 的表/字段/指标定义
2. 将表结构、字段信息存入 **MySQL meta 库**
3. 从数据仓库中查询字段的真实数据类型和示例值
4. 将字段名称、描述、别名分别向量化存入 **Qdrant**（COSINE 相似度检索）
5. 将需要同步的维度枚举值存入 **ES/内置搜索引擎**（中文分词全文检索）
6. 将指标信息向量化存入 **Qdrant**

---

## 3. 项目运行 & 启动方式

### 3.1 本地开发启动完整流程

#### 启动前检查清单

```bash
# ✅ 1. MySQL 是否启动
mysql -u yj9407 -pAa111111 -e "SELECT 1"

# ✅ 2. Qdrant 是否启动
curl http://localhost:6333/readyz

# ✅ 3. 确认配置文件已正确填写（尤其是 LLM API Key）
cat conf/app_config.yaml | grep api_key

# ✅ 4. 确认 meta 库已构建元数据
mysql -u yj9407 -pAa111111 meta -e "SELECT COUNT(*) FROM table_info; SELECT COUNT(*) FROM column_info;"

# ✅ 5. 确认 dw 库已有测试数据
mysql -u yj9407 -pAa111111 dw -e "SELECT COUNT(*) FROM fact_order;"
```

#### 方式一：直接运行 main.py（开发模式）



# 启动 FastAPI 服务
uv run python main.py
```

启动后输出类似：
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### 方式二：使用 uvicorn 命令（支持热重载）

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

`--reload` 参数会在代码修改后自动重启服务，开发阶段强烈推荐。

#### 验证服务是否启动成功

```bash
# 1. 访问 API 文档页面
# 浏览器打开: http://localhost:8000/docs

# 2. 测试查询接口
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "统计去年各地区的销售总额"}'
```

#### 启动流程图

```
配置检查 → 启动 MySQL → 启动 Qdrant → 构建元知识库 → 启动 FastAPI → 测试查询
```

### 3.2 启动常见报错与解决方案

| 报错信息 | 原因 | 解决方案 |
|---------|------|---------|
| `ModuleNotFoundError: No module named 'xxx'` | 依赖未安装 | 执行 `uv sync` 或 `pip install -r requirements.txt` |
| `sqlalchemy.exc.OperationalError: Can't connect to MySQL server` | MySQL 未启动 | 检查 MySQL 服务状态，确认端口 3306 |
| `ConnectionRefusedError: [Errno 61] Connection refused` | Qdrant 未启动 | 执行 `docker start qdrant-data-agent` |
| `qdrant_client.http.exceptions.UnexpectedResponse` | Qdrant 集合不存在 | 先运行 `python -m app.scripts.build_meta_knowledge -c conf/meta_config.yaml` 构建知识库 |
| `openai.AuthenticationError` | API Key 错误 | 检查 `conf/app_config.yaml` 中 `llm.api_key` 是否正确 |
| `ImportError: cannot import name 'xxx'` | Python 版本不匹配 | 检查 Python ≥ 3.12 |
| `No module named 'app'` | 未在项目根目录运行 | `cd` 到项目根目录再执行命令 |
| `SSL: CERTIFICATE_VERIFY_FAILED` | SSL 证书问题 | 检查 `cryptography` 包是否安装，或配置代理 |

### 3.3 打包构建命令

```bash
# 方式1: 使用 uv 构建分发包
uv build

# 方式2: 使用 pip 构建
pip install build && python -m build

# 打包后可安装为独立包
pip install dist/*.whl
```

### 3.4 生产环境部署启动方式

#### Docker 化部署（推荐）

```dockerfile
# Dockerfile（建议创建在项目根目录）
FROM python:3.12-slim

WORKDIR /app

# 安装 uv
RUN pip install uv

# 复制项目文件
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uv", "run", "python", "main.py"]
```

```bash
# 构建镜像
docker build -t data-agent:latest .

# 运行容器
docker run -d \
  --name data-agent \
  -p 8000:8000 \
  -v $(pwd)/conf:/app/conf \
  -v $(pwd)/logs:/app/logs \
  data-agent:latest
```

#### 使用 systemd 管理（Linux）

```ini
# /etc/systemd/system/data-agent.service
[Unit]
Description=Data Agent Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/data-agent
ExecStart=/usr/bin/uv run python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable data-agent
sudo systemctl start data-agent
sudo systemctl status data-agent
```

#### 生产环境环境变量覆盖配置

```bash
# 方式1: 创建 prod 配置文件
cp conf/app_config.yaml conf/app_config.prod.yaml
# 修改 prod 配置中的数据库地址、密码等

# 方式2: 修改 app/conf/app_config.py 的 config_file 路径
# 或在代码中支持环境变量覆盖
```

---

## 4. 项目必备插件/依赖包清单

### 4.1 所有安装的核心依赖

#### 生产依赖（运行时必须）

| 包名 | 版本要求 | 功能作用 | 为什么必须安装 |
|------|---------|---------|--------------|
| `fastapi[standard]` | ≥ 0.128.0 | Web 框架，提供 REST API、自动文档、数据校验 | 项目唯一 HTTP 入口框架，承载所有 API |
| `uvicorn` | 随 fastapi[standard] | ASGI 服务器 | 运行 FastAPI 应用的必备服务器 |
| `langgraph` | ≥ 1.0.7 | Agent 工作流编排引擎（StateGraph） | 项目核心——12 节点的 DAG 工作流全靠它 |
| `langchain` | ≥ 1.2.7 | LLM 调用抽象（Prompt、Chain、Parser） | 所有 LLM 交互的统一接口 |
| `langchain-deepseek` | ≥ 1.0.1 | DeepSeek LLM 适配器 | 本项目 LLM 调用的核心适配层 |
| `langchain-huggingface` | ≥ 1.2.0 | HuggingFace Embedding 集成 | 向量化文本的 Embedding 客户端 |
| `sentence-transformers` | ≥ 5.6.0 | 向量编码引擎 | Embedding 模型运行的底层库 |
| `sqlalchemy[asyncio]` | ≥ 2.0.46 | 异步 ORM 框架 | 管理 MySQL 连接池、表映射、查询 |
| `asyncmy` | ≥ 0.2.11 | MySQL 异步驱动 | SQLAlchemy 连接 MySQL 的底层驱动 |
| `qdrant-client` | ≥ 1.16.2 | Qdrant 向量数据库客户端 | 向量相似度检索的通信库 |
| `elasticsearch[async]` | ≥ 8, <9 | ES 异步客户端 | ES 全文检索的通信库 |
| `jieba` | ≥ 0.42.1 | 中文分词库 | 关键词提取 + 内置简易搜索引擎的分词 |
| `loguru` | ≥ 0.7.3 | 结构化日志框架 | 全链路 request_id 追踪日志 |
| `omegaconf` | ≥ 2.3.0 | YAML 配置管理 | 加载和结构化解析 YAML 配置文件 |
| `pyyaml` | ≥ 6.0.3 | YAML 解析库 | YAML 序列化/反序列化的底层依赖 |
| `huggingface-hub` | ≥ 0.36.0 | HuggingFace 模型仓库访问 | 下载和管理 HuggingFace 模型 |
| `cryptography` | ≥ 46.0.4 | 加密/SSL 支持 | 数据库连接加密、安全通信 |

#### 开发依赖（本项目未单独声明开发依赖，均在 dependencies 中）

> 本项目使用 `uv` 管理，所有依赖在 `pyproject.toml` 的 `[project].dependencies` 中声明。
> 如需添加类型检查等开发依赖，可在 `pyproject.toml` 中添加：
> ```toml
> [dependency-groups]
> dev = ["pytest>=8", "ruff>=0.11", "mypy>=1"]
> ```

### 4.2 依赖安装/卸载/更新命令

```bash
# ===== uv 命令（推荐） =====

# 安装所有依赖
uv sync

# 添加新依赖
uv add <package-name>
# 示例: uv add requests

# 添加开发依赖
uv add --dev pytest

# 移除依赖
uv remove <package-name>

# 更新所有依赖到最新版本
uv sync --upgrade

# 更新单个依赖
uv add <package-name>@latest

# 锁定当前依赖版本
uv lock

# ===== pip 命令（备用） =====

# 安装所有依赖
pip install -e .

# 添加新依赖
pip install <package-name> && pip freeze > requirements.txt

# 卸载依赖
pip uninstall <package-name>
```

**可选替代/避坑提示**：

| 原依赖 | 可替代方案 | 说明 |
|--------|-----------|------|
| `elasticsearch[async]` | 内置 `SimpleSearchClient` | 项目已内置纯 Python 内存搜索引擎，小数据量或开发阶段直接用内置的，无需装 ES |
| `asyncmy` | `aiomysql` / `pymysql` | asyncmy 性能更好，建议保持 |
| `qdrant-client` | `chromadb` / `milvus-lite` | Qdrant 更成熟稳定，生产环境推荐 |
| 外部 Embedding 服务 | 本地 `HuggingFaceEmbeddings` | 本地加载模型即可，无需额外部署 |

---

## 5. 完整项目目录结构文档

### 5.1 完整树形目录结构

```
data-agent/                                    # 📁 项目根目录
├── main.py                                    # 🚀 FastAPI 应用入口
├── pyproject.toml                             # 📋 项目元数据 + 依赖声明
├── uv.lock                                    # 🔒 依赖版本锁定文件
├── 数据通达.md                                # 📄 产品方案文档
├── 项目全套保姆级文档.md                       # 📖 本文档
│
├── conf/                                      # ⚙️ 配置文件目录
│   ├── app_config.yaml                        # 应用全局配置（数据库/LLM/Qdrant/ES/日志）
│   └── meta_config.yaml                       # 元数据配置（表/字段/指标定义）
│
├── prompts/                                   # 💬 LLM 提示词目录（外置 Prompt）
│   ├── extend_keywords_for_column_recall.prompt   # 扩展关键词（字段召回）
│   ├── extend_keywords_for_metric_recall.prompt   # 扩展关键词（指标召回）
│   ├── extend_keywords_for_value_recall.prompt    # 扩展关键词（值召回）
│   ├── filter_table_info.prompt                   # 过滤表与字段
│   ├── filter_metric_info.prompt                  # 过滤指标
│   ├── generate_sql.prompt                        # 生成 SQL
│   └── correct_sql.prompt                         # 纠正 SQL
│
├── logs/                                      # 📝 日志文件目录
│   └── app.log                                # 应用运行日志
│
└── app/                                       # 📦 应用核心代码
    ├── __init__.py
    │
    ├── agent/                                 # 🧠 Agent 工作流（LangGraph 核心）
    │   ├── __init__.py
    │   ├── state.py                           # 工作流全局状态类型定义（TypedDict）
    │   ├── context.py                         # 工作流运行时上下文类型（注入 Repository）
    │   ├── graph.py                           # StateGraph 构建 + 12 节点 DAG 定义 ★★★
    │   ├── llm.py                             # LLM 客户端初始化
    │   └── nodes/                             # 🔶 12 个工作流节点实现
    │       ├── __init__.py
    │       ├── extract_keywords.py            # [1] 抽取关键字（jieba 分词 + 词性过滤）
    │       ├── recall_column.py               # [2] 召回字段（LLM扩展 → Embedding → Qdrant）
    │       ├── recall_value.py                # [3] 召回值（LLM扩展 → ES/简易搜索）
    │       ├── recall_metric.py               # [4] 召回指标（LLM扩展 → Embedding → Qdrant）
    │       ├── merge_retrieved_info.py        # [5] 合并召回信息（去重 + 补主外键 + 分组）
    │       ├── filter_table.py                # [6] 过滤表与字段（LLM 精选）
    │       ├── filter_metric.py               # [7] 过滤指标（LLM 精选）
    │       ├── add_extra_context.py           # [8] 补充上下文（日期 + 数据库版本）
    │       ├── generate_sql.py                # [9] 生成 SQL（LLM）
    │       ├── validate_sql.py                # [10] 验证 SQL（EXPLAIN）
    │       ├── correct_sql.py                 # [11] 纠正 SQL（LLM 根据报错修正）
    │       └── execute_sql.py                 # [12] 执行 SQL（返回查询结果）
    │
    ├── api/                                   # 🌐 HTTP API 层
    │   ├── __init__.py
    │   ├── dependencies.py                    # FastAPI 依赖注入（Repository 工厂函数）
    │   ├── routers/                           # 路由定义
    │   │   ├── __init__.py
    │   │   └── query_router.py                # /api/query POST 路由（SSE 流式响应）
    │   └── schemas/                           # 请求/响应数据模型
    │       ├── __init__.py
    │       └── query_schema.py                # QuerySchema（Pydantic 请求体校验）
    │
    ├── services/                              # 🔧 业务服务层
    │   ├── __init__.py
    │   ├── query_service.py                   # QueryService（执行工作流 + SSE 返回）
    │   └── meta_knowledge_service.py          # MetaKnowledgeService（元知识库构建）
    │
    ├── repositories/                          # 🗄️ 数据仓库层（数据访问抽象）
    │   ├── __init__.py
    │   ├── es/                                # Elasticsearch 仓库
    │   │   ├── __init__.py
    │   │   └── value_es_repository.py         # ValueESRepository（值索引管理 + 搜索）
    │   ├── qdrant/                            # Qdrant 向量仓库
    │   │   ├── __init__.py
    │   │   ├── column_qdrant_repository.py    # ColumnQdrantRepository（字段向量管理 + 搜索）
    │   │   └── metric_qdrant_repository.py    # MetricQdrantRepository（指标向量管理 + 搜索）
    │   └── mysql/                             # MySQL 仓库
    │       ├── __init__.py
    │       ├── dw/                            # 数据仓库（dw 库）访问
    │       │   ├── __init__.py
    │       │   └── dw_mysql_repository.py     # DWMySQLRepository（列类型/值查询/EXPLAIN/执行）
    │       └── meta/                          # 元数据库（meta 库）访问
    │           ├── __init__.py
    │           ├── meta_mysql_repository.py   # MetaMySQLRepository（表/字段/指标 CRUD）
    │           └── mappers/                   # Entity ↔ Model ORM 映射器
    │               ├── __init__.py
    │               ├── table_info_mapper.py
    │               ├── column_info_mapper.py
    │               ├── column_metric_mapper.py
    │               └── metric_info_mapper.py
    │
    ├── clients/                               # 🔌 外部客户端管理器
    │   ├── __init__.py
    │   ├── embedding_client_manager.py        # EmbeddingClientManager（HuggingFace Embedding）
    │   ├── es_client_manager.py               # ESClientManager（Elasticsearch / 内置简易引擎）
    │   ├── mysql_client_manager.py            # MysqlClientManager（MySQL 连接池：meta + dw）
    │   ├── qdrant_client_manager.py           # QdrantClientManager（Qdrant 向量数据库）
    │   └── simple_search_engine.py            # SimpleSearchClient（纯 Python 内存搜索引擎 ★）
    │
    ├── entities/                              # 📐 领域实体（纯数据类，跨层共享）
    │   ├── __init__.py
    │   ├── table_info.py                      # TableInfo（表信息实体）
    │   ├── column_info.py                     # ColumnInfo（字段信息实体）
    │   ├── column_metric.py                   # ColumnMetric（字段-指标关联实体）
    │   ├── metric_info.py                     # MetricInfo（指标信息实体）
    │   └── value_info.py                      # ValueInfo（维度值信息实体）
    │
    ├── models/                                # 🗃️ SQLAlchemy ORM 模型（数据库表映射）
    │   ├── __init__.py
    │   ├── base.py                            # Base（ORM 基类，DeclarativeBase）
    │   ├── table_info_mysql.py                # TableInfoMySQL（table_info 表映射）
    │   ├── column_info_mysql.py               # ColumnInfoMySQL（column_info 表映射）
    │   ├── column_metric_mysql.py             # ColumnMetricMySQL（column_metric 表映射）
    │   └── metric_info_mysql.py               # MetricInfoMySQL（metric_info 表映射）
    │
    ├── conf/                                  # 🛠️ 应用内配置模块
    │   ├── __init__.py
    │   ├── config_loader.py                   # load_config() 通用配置加载工具函数
    │   ├── app_config.py                      # AppConfig 配置类定义（日志/数据库/LLM 等）
    │   └── meta_config.py                     # MetaConfig 配置类定义（表/字段/指标）
    │
    ├── core/                                  # ⚡ 核心基础设施
    │   ├── __init__.py
    │   ├── context.py                         # request_id_ctx_var（ContextVar 全链路追踪）
    │   ├── lifespan.py                        # FastAPI 生命周期管理（启动/关闭客户端连接）
    │   └── log.py                             # Loguru 日志配置（格式/文件/控制台/request_id 注入）
    │
    ├── prompt/                                # 📝 Prompt 加载模块
    │   ├── __init__.py
    │   └── prompt_loader.py                   # load_prompt() 从 prompts/ 目录加载 .prompt 文件
    │
    └── scripts/                               # 🔨 运维脚本
        ├── __init__.py
        ├── build_meta_knowledge.py            # 构建元知识库脚本（一键导入 MySQL + Qdrant + ES）
        └── create_dw_data.py                  # 创建测试数据脚本（建表 + 插入样本数据）
```

### 5.2 每个文件夹、每个核心文件逐一详解

#### 根目录文件

##### `main.py`
- **作用**：FastAPI 应用入口文件，创建 FastAPI 实例、注册路由、添加中间件
- **核心内容**：
  - 创建 `FastAPI(lifespan=lifespan)` 实例，绑定生命周期函数
  - `app.include_router(query_router)` 注册查询路由
  - `@app.middleware("http")` 添加全局中间件，每个请求自动生成 `uuid` 作为 `request_id`，注入到 `request_id_ctx_var`（ContextVar），实现全链路日志追踪
  - `if __name__ == '__main__'` 开发模式直接启动 uvicorn
- **修改注意事项**：
  - 新增路由时在此添加 `app.include_router()`
  - 新增中间件时在此添加（如 CORS、认证等）
  - ⚠️ 不要随意删除 `lifespan` 和 `request_id` 中间件

##### `pyproject.toml`
- **作用**：Python 项目元数据与依赖声明文件（PEP 621 标准）
- **核心内容**：
  - `[project]`：项目名称 `data-agent`、版本 `0.1.0`、Python 版本要求 `>=3.12`
  - `[project].dependencies`：17 个核心依赖包及版本约束
- **修改注意事项**：
  - 添加新依赖用 `uv add <package>` 命令，不要手动编辑
  - 修改 `requires-python` 需谨慎，与代码兼容性验证

##### `uv.lock`
- **作用**：依赖版本锁定文件（类似 `package-lock.json`）
- **核心内容**：所有依赖的精确版本、哈希值、依赖树
- **修改注意事项**：⚠️ 不要手动编辑，由 `uv lock` 自动生成

##### `数据通达.md`
- **作用**：产品方案文档（含简历项目经验模板）
- **核心内容**：产品定位、核心亮点、竞品对比、商业价值量化、场景演示

---

#### `conf/` 目录（配置文件）

##### `conf/app_config.yaml`
- **作用**：应用全局配置文件，所有运行时配置的集中管理
- **核心内容**：
  - `logging`：日志配置（文件/控制台开关、级别、路径、滚动、保留）
  - `db_meta` / `db_dw`：两个 MySQL 数据库的连接信息
  - `qdrant`：向量数据库连接 + embedding 维度
  - `embedding`：Embedding 服务配置（预留）
  - `es`：Elasticsearch 连接配置
  - `llm`：LLM 大模型 API 配置 ★ 必须修改
- **修改注意事项**：
  - ⚠️ 生产环境不要提交含真实密码的配置文件
  - 新增配置项时，需同步更新 `app/conf/app_config.py` 的 dataclass

##### `conf/meta_config.yaml`
- **作用**：业务元数据定义文件，描述数据仓库中的表、字段、指标
- **核心内容**：
  - `tables[]`：表列表，每张表含 name/role/description/columns
  - `columns[]`：字段列表，每个字段含 name/role/description/alias/sync
  - `metrics[]`：指标列表，每个指标含 name/description/relevant_columns/alias
- **修改注意事项**：
  - 新增表/字段/指标后，需重新运行 `python -m app.scripts.build_meta_knowledge -c conf/meta_config.yaml`
  - `alias` 直接影响语义检索召回率，建议覆盖多组同义词
  - `sync: true` 的字段值会被导入 ES 全文索引

---

#### `prompts/` 目录（Prompt 模板）

##### `prompts/extend_keywords_for_column_recall.prompt`
- **作用**：字段召回阶段的关键词扩展 Prompt，从用户问题中推断所需数据字段
- **使用场景**：`recall_column` 节点调用
- **输出格式**：JSON 数组 `["字段1", "字段2", ...]`

##### `prompts/extend_keywords_for_metric_recall.prompt`
- **作用**：指标召回阶段的关键词扩展 Prompt，从用户问题中识别度量意图
- **使用场景**：`recall_metric` 节点调用
- **输出格式**：JSON 数组 `["指标1", "指标2", ...]`

##### `prompts/extend_keywords_for_value_recall.prompt`
- **作用**：值召回阶段的关键词扩展 Prompt，提取用户问题中可能作为字段取值的词
- **使用场景**：`recall_value` 节点调用
- **输出格式**：JSON 数组 `["值1", "值2", ...]`

##### `prompts/filter_table_info.prompt`
- **作用**：从召回的候选表与字段中精选实际需要的表与字段
- **使用场景**：`filter_table` 节点调用
- **输出格式**：JSON 对象 `{"表名": ["字段1", "字段2"]}`

##### `prompts/filter_metric_info.prompt`
- **作用**：从召回的候选指标中精选实际需要的指标
- **使用场景**：`filter_metric` 节点调用
- **输出格式**：JSON 数组 `["指标名1"]`

##### `prompts/generate_sql.prompt`
- **作用**：SQL 生成 Prompt，根据过滤后的表/字段/指标/日期/数据库信息生成 SQL
- **使用场景**：`generate_sql` 节点调用
- **输出格式**：纯文本 SQL（无 Markdown 代码块）

##### `prompts/correct_sql.prompt`
- **作用**：SQL 纠错 Prompt，根据 EXPLAIN 报错信息修正 SQL
- **使用场景**：`correct_sql` 节点调用
- **输出格式**：纯文本 SQL（无 Markdown 代码块）

> **Prompt 设计原则**：所有 Prompt 外置为独立文件，便于非技术人员（如业务专家）调优，无需修改代码。

---

#### `app/agent/` 目录（Agent 工作流核心）

##### `app/agent/state.py`
- **作用**：定义 LangGraph `StateGraph` 的全局状态类型 `DataAgentState`（TypedDict）
- **核心字段**：
  - `query`：用户原始查询文本
  - `keywords`：jieba 提取 + LLM 扩展的关键词列表
  - `retrieved_columns/values/metrics`：三路召回的原始结果
  - `table_infos` / `metric_infos`：合并过滤后的表/指标信息
  - `date_info` / `db_info`：额外上下文（日期、数据库版本）
  - `sql`：LLM 生成的 SQL 语句
  - `error`：SQL 校验时的错误信息（None = 校验通过）
- **修改注意事项**：新增节点如需传递新状态，必须在此添加新字段

##### `app/agent/context.py`
- **作用**：定义 LangGraph 运行时上下文类型 `DataAgentContext`（TypedDict）
- **核心字段**：6 个 Repository/Client 实例注入
- **修改注意事项**：与 `graph.py` 中 `context_schema` 绑定

##### `app/agent/graph.py` ⭐⭐⭐
- **作用**：LangGraph 工作流图构建核心文件，定义 12 个节点 + 边关系 + 条件路由
- **核心流程**：
  1. `add_node()` 注册 12 个节点
  2. `add_edge()` 定义节点间流转关系（前 3 路并行召回 → 合并 → 并行过滤 → 补充上下文 → 生成SQL → 校验 → 条件分支）
  3. `add_conditional_edges()` 实现 SQL 校验的条件路由（通过 → 执行，失败 → 纠正 → 执行）
  4. `graph_builder.compile()` 编译为可执行的 `graph` 对象
- **修改注意事项**：
  - ⚠️ 这是项目流程核心文件，修改前必须深入理解 LangGraph
  - 新增节点：需同时 `add_node()` + `add_edge()`/`add_conditional_edges()`
  - 节点顺序不能随意更改

##### `app/agent/llm.py`
- **作用**：LLM 大模型客户端初始化
- **核心内容**：通过 `langchain.chat_models.init_chat_model` 创建 LLM 实例，使用 openai 兼容协议
- **修改注意事项**：配置从 `app_config.llm` 读取，修改 `app_config.yaml` 即可

##### `app/agent/nodes/` 目录（12 个工作流节点）

| 文件 | 节点名称 | 核心逻辑 | LLM调用 |
|------|---------|---------|---------|
| `extract_keywords.py` | extract_keywords | jieba 分词 + 词性过滤（名词/动词/形容词/英文等），合并原始 query | ❌ |
| `recall_column.py` | recall_column | LLM 扩展关键词 → Embedding → Qdrant COSINE 搜索 | ✅ |
| `recall_value.py` | recall_value | LLM 扩展关键词 → ES/Jieba 全文匹配搜索 | ✅ |
| `recall_metric.py` | recall_metric | LLM 扩展关键词 → Embedding → Qdrant COSINE 搜索 | ✅ |
| `merge_retrieved_info.py` | merge_retrieved_info | 合并去重 + 补全指标关联字段 + 补全主外键 + 按表分组 | ❌ |
| `filter_table.py` | filter_table | YAML 化表信息 → LLM 精选 → 过滤 | ✅ |
| `filter_metric.py` | filter_metric | YAML 化指标信息 → LLM 精选 → 过滤 | ✅ |
| `add_extra_context.py` | add_extra_context | 查询当前日期/星期/季度 + 数据库 dialect/version | ❌ |
| `generate_sql.py` | generate_sql | YAML 化全部上下文 → LLM 生成 SQL | ✅ |
| `validate_sql.py` | validate_sql | EXPLAIN 语法校验，失败时返回 error 信息 | ❌ |
| `correct_sql.py` | correct_sql | 将报错信息 + 原始上下文 → LLM 修正 SQL | ✅ |
| `execute_sql.py` | execute_sql | 执行 SQL → 返回查询结果 | ❌ |

> **节点统一约定**：
> - 每个节点函数签名为 `async def xxx(state: DataAgentState, runtime: Runtime[DataAgentContext])`
> - 通过 `runtime.stream_writer` 推送 SSE 进度事件
> - 通过 `runtime.context` 获取 Repository 实例
> - 返回值是 `DataAgentState` 的部分字段（dict），LangGraph 自动合并到全局 state

---

#### `app/api/` 目录（HTTP API）

##### `app/api/routers/query_router.py`
- **作用**：定义查询路由
- **端点**：`POST /api/query`
  - 请求体：`{"query": "统计去年各地区的销售总额"}`
  - 响应：`StreamingResponse`，`text/event-stream`（SSE 格式）
- **修改注意事项**：新增 API 端点建议在 `routers/` 下新建文件

##### `app/api/schemas/query_schema.py`
- **作用**：请求体 Pydantic 校验模型
- **核心内容**：`QuerySchema(BaseModel)` 含 `query: str` 字段
- **修改注意事项**：新增字段需同步更新 Service 层

##### `app/api/dependencies.py`
- **作用**：FastAPI 依赖注入工厂函数
- **核心内容**：
  - 7 个 Repository/Client 的 `Depends` 工厂函数
  - `get_query_service()` 组装所有依赖，创建 `QueryService` 实例
- **修改注意事项**：
  - 新增 Repository 在此添加工厂函数
  - 依赖注入链：Client → Repository → Service → Router

---

#### `app/services/` 目录（业务服务）

##### `app/services/query_service.py`
- **作用**：查询业务编排，将 LangGraph 工作流包装为 SSE 流式输出
- **核心逻辑**：
  1. 构造 `DataAgentContext`（注入各 Repository）
  2. 构造 `DataAgentState`（仅含 query）
  3. 调用 `graph.astream()` 执行工作流
  4. 将每个 chunk 转换为 `data: {json}\n\n` 的 SSE 格式 yield 出去
  5. 异常捕获，转换为 `type: "error"` 的 SSE 事件
- **修改注意事项**：这是 SSE 推送的唯一入口，修改需确保格式正确

##### `app/services/meta_knowledge_service.py`
- **作用**：元数据知识库构建服务
- **核心流程**：
  1. `build()` → 加载 YAML 配置
  2. `_save_tables_to_meta_db()` → 表/字段信息存入 MySQL meta 库
  3. `_save_column_info_to_qdrant()` → 字段名+描述+别名向量化存入 Qdrant
  4. `_save_value_info_to_es()` → 维度枚举值存入 ES/简易搜索引擎
  5. `_save_metrics_to_meta_db()` → 指标信息存入 MySQL meta 库
  6. `_save_metric_info_to_qdrant()` → 指标向量化存入 Qdrant
- **修改注意事项**：新增元数据类型（如时间粒度）需扩展此服务

---

#### `app/repositories/` 目录（数据仓库层）

##### `app/repositories/qdrant/column_qdrant_repository.py`
- **作用**：字段向量索引的 Qdrant 读写操作
- **核心方法**：
  - `ensure_collection()`：自动创建 collection（向量维度从配置读取，距离算法 COSINE）
  - `upsert()`：批量插入/更新向量（分批 20 条）
  - `search()`：相似度检索（默认阈值 0.6，返回 Top 5）
- **Collection 名称**：`data-agent-column`

##### `app/repositories/qdrant/metric_qdrant_repository.py`
- **作用**：指标向量索引的 Qdrant 读写操作
- **Collection 名称**：`data-agent-metric`
- **方法同** `ColumnQdrantRepository`

##### `app/repositories/es/value_es_repository.py`
- **作用**：维度值全文索引的 ES 读写操作
- **核心方法**：
  - `ensure_index()`：创建索引（ik_max_word 中文分词器）
  - `index()`：批量写入文档（分批 20 条）
  - `search()`：全文匹配搜索（match query）
- **索引名称**：`data-agent-value`

##### `app/repositories/mysql/meta/meta_mysql_repository.py`
- **作用**：元数据库（meta 库）的 CRUD 操作
- **核心方法**：
  - `save_table_infos()` / `save_column_infos()` / `save_metric_infos()` / `save_column_metrics()`
  - `get_column_info_by_id()` / `get_table_info_by_id()` / `get_key_columns_by_table_id()`
- **依赖**：通过 ORM Mapper 实现 Entity ↔ Model 转换

##### `app/repositories/mysql/dw/dw_mysql_repository.py`
- **作用**：数据仓库（dw 库）的查询操作
- **核心方法**：
  - `get_column_types()`：获取表的列类型
  - `get_column_values()`：获取列的枚举值
  - `get_db_info()`：获取数据库版本和 dialect
  - `validate_sql()`：EXPLAIN 语法校验
  - `execute_sql()`：执行 SQL 并返回结果

##### `app/repositories/mysql/meta/mappers/` 目录

| Mapper | Entity | Model |
|--------|--------|-------|
| `table_info_mapper.py` | `TableInfo` | `TableInfoMySQL` |
| `column_info_mapper.py` | `ColumnInfo` | `ColumnInfoMySQL` |
| `column_metric_mapper.py` | `ColumnMetric` | `ColumnMetricMySQL` |
| `metric_info_mapper.py` | `MetricInfo` | `MetricInfoMySQL` |

> 每个 Mapper 含两个静态方法：`to_entity(model)` 和 `to_model(entity)`，实现双向映射。

---

#### `app/clients/` 目录（外部客户端管理）

##### `app/clients/mysql_client_manager.py`
- **作用**：MySQL 连接池管理（异步引擎 + session 工厂）
- **核心参数**：连接池大小 10，自动预热检测，自动提交
- **全局实例**：`meta_mysql_client_manager` 和 `dw_mysql_client_manager`
- **生命周期**：`init()` → 使用 → `close()`

##### `app/clients/qdrant_client_manager.py`
- **作用**：Qdrant 异步客户端管理
- **全局实例**：`qdrant_client_manager`

##### `app/clients/es_client_manager.py`
- **作用**：ES 客户端管理（默认使用内置 `SimpleSearchClient`）
- **全局实例**：`es_client_manager`

##### `app/clients/embedding_client_manager.py`
- **作用**：HuggingFace Embedding 客户端管理
- **配置**：local 模式运行，CPU 推理，归一化向量输出
- **全局实例**：`embedding_client_manager`

##### `app/clients/simple_search_engine.py` ⭐
- **作用**：纯 Python 实现的简易搜索引擎，替代 Elasticsearch
- **核心能力**：jieba 中文分词 + 内存倒排索引 + 子串模糊匹配 + 打分排序
- **接口兼容**：完全模拟 `AsyncElasticsearch` 的 API（indices/bulk/search/close）
- **适用场景**：开发测试 / 小数据量 / 不想装 ES 的场景
- **限制**：数据在内存中，重启丢失，需重新构建知识库

---

#### `app/entities/` 目录（领域实体）

| 文件 | 类名 | 核心字段 | 用途 |
|------|------|---------|------|
| `table_info.py` | `TableInfo` | id, name, role, description | 表信息纯数据结构 |
| `column_info.py` | `ColumnInfo` | id, name, type, role, examples, description, alias, table_id | 字段信息纯数据结构 |
| `column_metric.py` | `ColumnMetric` | column_id, metric_id | 字段-指标关联纯数据结构 |
| `metric_info.py` | `MetricInfo` | id, name, description, relevant_columns, alias | 指标信息纯数据结构 |
| `value_info.py` | `ValueInfo` | id, value, column_id | 维度值纯数据结构 |

> **设计原则**：Entities 是纯 `@dataclass`，不含任何框架依赖，跨所有层共享。

---

#### `app/models/` 目录（ORM 模型）

| 文件 | 类名 | 对应数据库表 | 核心字段映射 |
|------|------|-------------|-------------|
| `base.py` | `Base` | - | SQLAlchemy DeclarativeBase 基类 |
| `table_info_mysql.py` | `TableInfoMySQL` | `table_info` | id(String)/name(String)/role(String)/description(Text) |
| `column_info_mysql.py` | `ColumnInfoMySQL` | `column_info` | id/name/type/role/examples(JSON)/description(Text)/alias(JSON)/table_id |
| `column_metric_mysql.py` | `ColumnMetricMySQL` | `column_metric` | column_id/metric_id（联合主键） |
| `metric_info_mysql.py` | `MetricInfoMySQL` | `metric_info` | id/name/description/relevant_columns(JSON)/alias(JSON) |

---

#### `app/conf/`（应用内配置模块）

| 文件 | 核心内容 |
|------|---------|
| `config_loader.py` | 通用配置加载函数 `load_config(config_file, schema_cls)` |
| `app_config.py` | `AppConfig` 等 dataclass 定义 + 从 `conf/app_config.yaml` 加载全局配置 |
| `meta_config.py` | `MetaConfig` 等 dataclass 定义（表/字段/指标配置结构） |

---

#### `app/core/`（核心基础设施）

| 文件 | 核心内容 |
|------|---------|
| `context.py` | `request_id_ctx_var = ContextVar("request_id", default="1")` — 全链路请求追踪 |
| `lifespan.py` | FastAPI 应用生命周期管理（启动时 init 5 个客户端，关闭时优雅释放连接） |
| `log.py` | Loguru 日志配置（格式/文件滚动/控制台输出/request_id 注入） |

---

#### `app/prompt/`（Prompt 加载）

| 文件 | 核心内容 |
|------|---------|
| `prompt_loader.py` | `load_prompt(name)` 从 `prompts/` 目录读取 `.prompt` 文件 |

---

#### `app/scripts/`（运维脚本）

| 文件 | 核心内容 |
|------|---------|
| `build_meta_knowledge.py` | 一键构建元知识库（`-c` 参数指定 meta_config 路径） |
| `create_dw_data.py` | 创建测试数据（建 5 张表 + 插入样本数据） |

---

### 5.3 项目核心文件优先级说明

#### 🔴 一级核心文件（不能随意修改）

| 文件 | 原因 |
|------|------|
| `app/agent/graph.py` | LangGraph 12 节点 DAG 定义，改动影响全流程 |
| `app/agent/state.py` | 全局状态类型，所有节点共享 |
| `app/agent/context.py` | 运行时上下文，依赖注入的桥梁 |
| `app/api/dependencies.py` | 所有 Repository 的依赖注入工厂 |
| `app/core/lifespan.py` | 应用启动/关闭的生命周期，客户端初始化和释放 |
| `conf/app_config.yaml` | 全局配置，改动影响所有外部连接 |
| `pyproject.toml` | 依赖声明，改动影响包管理 |

#### 🟡 二级核心文件（需理解后修改）

| 文件 | 原因 |
|------|------|
| `app/agent/nodes/*.py` | 各节点具体逻辑，修改需理解 LangGraph 约定 |
| `app/services/query_service.py` | SSE 流式格式约定 |
| `app/services/meta_knowledge_service.py` | 知识库构建流程 |
| `app/repositories/` | 数据访问逻辑，修改需理解数据库结构 |
| `app/clients/*_manager.py` | 客户端生命周期管理 |

#### 🟢 三级文件（可自由扩展）

| 文件 | 原因 |
|------|------|
| `app/entities/*.py` | 纯数据类，按需添加字段 |
| `app/models/*.py` | ORM 模型，按需添加新表 |
| `app/api/schemas/*.py` | 请求/响应模型 |
| `conf/meta_config.yaml` | 业务元数据定义 |
| `prompts/*.prompt` | Prompt 模板 |

### 5.4 新增功能对应目录存放规范

| 新增功能类型 | 存放位置 | 示例 |
|-------------|---------|------|
| 新增 API 端点 | `app/api/routers/` | `user_router.py` |
| 新增请求/响应模型 | `app/api/schemas/` | `user_schema.py` |
| 新增 Agent 节点 | `app/agent/nodes/` | `predict_trend.py` |
| 新增业务服务 | `app/services/` | `report_service.py` |
| 新增数据仓库 | `app/repositories/` | `redis/redis_repository.py` |
| 新增外部客户端 | `app/clients/` | `redis_client_manager.py` |
| 新增领域实体 | `app/entities/` | `report.py` |
| 新增数据库映射 | `app/models/` | `report_mysql.py` |
| 新增 Mapper | `app/repositories/mysql/meta/mappers/` | `report_mapper.py` |
| 新增 Prompt 模板 | `prompts/` | `generate_report.prompt` |
| 新增配置定义 | `app/conf/` | `report_config.py` |
| 新增运维脚本 | `app/scripts/` | `export_data.py` |
| 新增配置文件 | `conf/` | `report_config.yaml` |

---

## 6. 项目开发规范 & 使用文档

### 6.1 项目代码书写规范

#### Python 代码风格

```python
# 1. 命名规范
# 文件名：全小写，下划线分隔  snake_case
#   ✅ query_service.py, column_info.py
#   ❌ QueryService.py, column-info.py

# 类名：大驼峰 PascalCase
#   ✅ QueryService, ColumnInfo, MetaMySQLRepository
#   ❌ queryService, column_info

# 函数/方法名：小写蛇形 snake_case
#   ✅ async def extract_keywords(), def load_config()
#   ❌ async def ExtractKeywords(), def LoadConfig()

# 变量名：小写蛇形 snake_case
#   ✅ retrieved_columns, table_infos
#   ❌ RetrievedColumns, tableInfos

# 常量：全大写蛇形 UPPER_SNAKE_CASE
#   ✅ EMBEDDING_BATCH_SIZE = 10
#   ❌ embeddingBatchSize = 10

# 私有方法：单下划线前缀
#   ✅ def _save_tables_to_meta_db()
#   ❌ def save_tables_to_meta_db()  # 被外部调用时为公共方法
```

#### 项目特有约定

```python
# 1. 异步函数：所有 IO 操作使用 async/await
async def some_node(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    result = await repository.search(...)
    return {"field": result}

# 2. LangGraph 节点统一签名
async def node_name(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # state: 全局状态，通过 key 读写
    # runtime: 包含 context（注入的 Repository）+ stream_writer（SSE推送）
    
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "节点描述", "status": "running"})
    # ... 业务逻辑 ...
    writer({"type": "progress", "step": "节点描述", "status": "success"})
    return {"state_key": value}  # 返回需要更新的状态字段

# 3. SSE 事件格式约定
# Progress 事件: {"type": "progress", "step": "步骤名", "status": "running|success|error"}
# Result 事件:  {"type": "result", "data": [...]}
# Error 事件:   {"type": "error", "message": "错误详情"}

# 4. Entity 使用 @dataclass
from dataclasses import dataclass

@dataclass
class NewEntity:
    id: str
    name: str
    # ... 其他字段

# 5. Model 使用 SQLAlchemy Mapped
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class NewModel(Base):
    __tablename__ = "new_table"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
```

#### 日志规范

```python
from app.core.log import logger

# 使用正确的日志级别
logger.debug("调试信息，开发时使用")
logger.info("流程关键节点，如：抽取关键字: ['销售', '地区']")
logger.warning("异常但可恢复的情况")
logger.error("错误但不影响主流程")
logger.critical("致命错误，系统不可用")

# 不要在日志中输出敏感信息（密码、API Key 等）
```

### 6.2 新增功能标准流程

#### 新增一个 Agent 节点

**Step 1**：在 `app/agent/nodes/` 下创建节点文件

```python
# app/agent/nodes/my_new_node.py
from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger

async def my_new_node(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "我的新节点", "status": "running"})
    
    # 从 state 读取数据
    query = state["query"]
    # 从 context 获取 Repository
    my_repository = runtime.context["some_repository"]
    
    try:
        # 业务逻辑
        result = await my_repository.do_something(query)
        
        writer({"type": "progress", "step": "我的新节点", "status": "success"})
        return {"new_field": result}
    except Exception as e:
        writer({"type": "progress", "step": "我的新节点", "status": "error"})
        logger.error(f"新节点失败: {str(e)}")
        raise
```

**Step 2**：在 `app/agent/state.py` 添加新状态字段

```python
class DataAgentState(TypedDict):
    # ... 现有字段 ...
    new_field: str  # 新增
```

**Step 3**：在 `app/agent/graph.py` 注册节点和边

```python
from app.agent.nodes.my_new_node import my_new_node

graph_builder.add_node("my_new_node", my_new_node)
graph_builder.add_edge("some_existing_node", "my_new_node")
graph_builder.add_edge("my_new_node", "some_next_node")
```

#### 新增一个 API 端点

**Step 1**：创建 Schema

```python
# app/api/schemas/my_schema.py
from pydantic import BaseModel

class MyRequestSchema(BaseModel):
    param1: str
    param2: int = 10

class MyResponseSchema(BaseModel):
    result: str
```

**Step 2**：创建 Router

```python
# app/api/routers/my_router.py
from fastapi import APIRouter
from app.api.schemas.my_schema import MyRequestSchema

my_router = APIRouter()

@my_router.post("/api/my-endpoint")
async def my_endpoint(request: MyRequestSchema):
    return {"result": f"Hello {request.param1}"}
```

**Step 3**：在 `main.py` 注册路由

```python
from app.api.routers.my_router import my_router
app.include_router(my_router)
```

#### 新增一个外部数据源（如 Redis）

**Step 1**：创建 Client Manager

```python
# app/clients/redis_client_manager.py
import redis.asyncio as redis
from app.conf.app_config import app_config

class RedisClientManager:
    def __init__(self, config):
        self.client = None
    
    def init(self):
        self.client = redis.Redis(host=..., port=...)
    
    async def close(self):
        await self.client.close()

redis_client_manager = RedisClientManager(app_config.redis)
```

**Step 2**：在 `app/core/lifespan.py` 管理生命周期

**Step 3**：在 `app/api/dependencies.py` 添加依赖注入函数

#### 新增业务表

**Step 1**：在 `conf/meta_config.yaml` 的 `tables` 下添加表定义

**Step 2**：运行 `python -m app.scripts.build_meta_knowledge -c conf/meta_config.yaml` 重建知识库

### 6.3 项目全局变量与方法

#### 全局 ContextVar（全链路追踪）

```python
from app.core.context import request_id_ctx_var

# 每个 HTTP 请求会自动设置，无需手动设置
# 在需要异步传递 request_id 的场景中：
request_id_ctx_var.set(uuid.uuid4())
current_id = request_id_ctx_var.get()
```

#### 全局日志 Logger

```python
from app.core.log import logger

# 自动注入 request_id，日志格式：
# 2026-06-24 10:30:00.123 | INFO     | request_id - abc-123 | module:func:line - message
```

#### 全局配置

```python
from app.conf.app_config import app_config

# 访问任意配置项
app_config.llm.model_name
app_config.db_meta.host
app_config.qdrant.embedding_size
```

#### Prompt 加载

```python
from app.prompt.prompt_loader import load_prompt

# 加载 prompts/ 目录下的 .prompt 文件
template = load_prompt("generate_sql")  # 加载 prompts/generate_sql.prompt
```

#### LLM 实例

```python
from app.agent.llm import llm

# 直接使用全局 LLM 实例
response = await llm.ainvoke("Hello")
```

### 6.4 接口请求与状态管理规则

#### API 请求格式

```http
POST /api/query HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
    "query": "统计去年各地区的销售总额"
}
```

#### SSE 响应格式

```text
data: {"type":"progress","step":"抽取关键字","status":"running"}

data: {"type":"progress","step":"抽取关键字","status":"success"}

data: {"type":"progress","step":"召回字段","status":"running"}

data: {"type":"progress","step":"召回字段","status":"success"}

... (中间步骤) ...

data: {"type":"progress","step":"执行SQL","status":"success"}

data: {"type":"result","data":[{"region_name":"华东","total":12345.67},...]}
```

#### LangGraph 状态管理规则

1. **State 是累积式的**：每个节点返回的 dict 会**合并**到全局 state，不会覆盖未返回的字段
2. **并行节点的返回会合并**：`recall_column`、`recall_value`、`recall_metric` 三路并行执行，各自的返回值自动合并
3. **节点间通过 state 传递数据**：不通过参数传递，而是读写 state 字段
4. **Context 是只读的**：`runtime.context` 在运行时注入后不会改变，用于传递 Repository 实例

---

## 7. 项目常见问题汇总

### 7.1 启动/运行/打包报错全套方案

#### Q1: `ModuleNotFoundError: No module named 'app'`

**原因**：未在项目根目录运行 Python 命令。

**解决**：
```bash
# 确认当前目录
pwd
# 必须在 data-agent 目录下

# 使用 uv run 确保正确的 Python 环境
uv run python main.py
```

#### Q2: `sqlalchemy.exc.OperationalError: (2003, "Can't connect to MySQL server")`

**原因**：MySQL 服务未启动或连接配置错误。

**解决**：
```bash
# 1. 检查 MySQL 是否运行
# Windows:
net start MySQL80
# Linux:
sudo systemctl status mysql

# 2. 测试连接
mysql -h localhost -P 3306 -u yj9407 -pAa111111 -e "SELECT 1"

# 3. 检查 app_config.yaml 中数据库连接配置是否正确
```

#### Q3: `qdrant_client.http.exceptions.UnexpectedResponse: Not Found`

**原因**：Qdrant collection 不存在（未构建知识库）。

**解决**：
```bash
# 先构建元知识库
uv run python -m app.scripts.build_meta_knowledge -c conf/meta_config.yaml

# 再启动服务
uv run python main.py
```

#### Q4: `openai.AuthenticationError: Error code: 401`

**原因**：LLM API Key 未配置或错误。

**解决**：
```yaml
# conf/app_config.yaml
llm:
  api_key: <正确的API Key>  # 修改这里
  base_url: <正确的API地址>   # 修改这里
```

#### Q5: `ImportError: cannot import name 'xxx' from 'yyy'`

**原因**：依赖版本不兼容，常见于 langchain/langgraph 版本升级。

**解决**：
```bash
# 重新安装依赖
uv sync --reinstall

# 或清理缓存后重装
uv cache clean
uv sync
```

#### Q6: SSLEOFError / SSL 相关错误

**原因**：SSL 证书验证问题。

**解决**：
```bash
# 确认 cryptography 已安装
uv run python -c "import cryptography; print(cryptography.__version__)"

# 如有必要，配置代理（如果使用代理访问 LLM API）
set HTTPS_PROXY=http://your-proxy:port
```

#### Q7: `MemoryError` 或进程被 kill

**原因**：Embedding 模型加载占用内存过大。

**解决**：
- 确认 `app/clients/embedding_client_manager.py` 中 `device="cpu"`
- 如果内存 < 8GB，建议使用外部 Embedding 服务

### 7.2 环境兼容与依赖冲突

#### Python 版本不兼容

```bash
# 确保使用 Python 3.12+
python --version

# 如果安装了多个 Python 版本，使用 uv 指定版本
uv python pin 3.12
```

#### asyncmy 与 MySQL 版本兼容

| asyncmy 版本 | MySQL 版本 |
|-------------|-----------|
| ≥ 0.2.11 | MySQL 5.7+ / 8.0+ |

#### Jieba 分词兼容

- Jieba 0.42.1 支持 Python 3.12
- 如遇编码问题，确保所有文件使用 UTF-8

#### ES 客户端与 ES 服务端版本

- `elasticsearch-py` 8.x 兼容 ES 8.x 服务端
- 使用内置 `SimpleSearchClient` 可完全避开此问题

### 7.3 开发过程高频踩坑点

#### 踩坑1：修改 Prompt 后没有重启服务

**现象**：改了 `prompts/` 下的文件，但查询行为没变化。

**解决**：Prompt 在运行时读取，修改后需重启 FastAPI 服务。使用 `--reload` 模式可自动重启。

#### 踩坑2：忘记构建元知识库

**现象**：启动服务后查询报错 `collection not found`。

**解决**：先运行 `python -m app.scripts.build_meta_knowledge -c conf/meta_config.yaml`。

#### 踩坑3：meta_config.yaml 中表名与 dw 库不一致

**现象**：构建知识库时报 SQL 错误 `Table 'dw.xxx' doesn't exist`。

**解决**：确保 `meta_config.yaml` 中的 `tables[].name` 与 `dw` 库中的实际表名完全一致（包括大小写）。

#### 踩坑4：第一次运行 Embedding 很慢

**现象**：首次启动时长时间卡住。

**解决**：HuggingFace 模型首次加载需要下载（约 1.3GB），这是正常现象。后续会从缓存加载。

#### 踩坑5：SQL 校验失败但不自动纠正

**现象**：看到 `验证SQL` 状态为 `error`，但没有进入 `校正SQL` 节点。

**解决**：检查 `validate_sql` 节点的返回值，必须 `return {"error": str(e)}`，且 graph 中的 `add_conditional_edges` 条件判断正确。

#### 踩坑6：SSE 连接中断

**现象**：前端 SSE 连接断断续续或提前关闭。

**解决**：
- 确认 `StreamingResponse` 没有设置超时
- 在工作流中确保每个节点最终都有 `writer()` 推送事件，避免长时间无数据导致浏览器超时

#### 踩坑7：中文编码问题

**现象**：日志或 API 响应中出现乱码。

**解决**：
- `app/core/log.py` 中已设置 `encoding="utf-8"`
- API 响应中 `json.dumps(ensure_ascii=False)` 确保中文不转码

---

## 8. 补充说明

### 项目启动检查清单

```
□ Python 3.12+ 已安装
□ uv 已安装
□ MySQL 已启动（端口 3306）
□ meta 和 dw 数据库已创建
□ Qdrant 已启动（端口 6333）
□ conf/app_config.yaml 中 LLM API Key 已配置
□ 依赖已安装（uv sync）
□ 测试数据已创建（python -m app.scripts.create_dw_data）
□ 元知识库已构建（python -m app.scripts.build_meta_knowledge -c conf/meta_config.yaml）
□ FastAPI 服务可启动（python main.py 或 uvicorn main:app --reload）
□ API 文档可访问（http://localhost:8000/docs）
□ 查询接口可正常返回（curl -X POST http://localhost:8000/api/query ...)
```

### 开发快速参考卡片

| 操作 | 命令 |
|------|------|
| 安装依赖 | `uv sync` |
| 启动开发服务 | `uv run uvicorn main:app --reload` |
| 构建知识库 | `uv run python -m app.scripts.build_meta_knowledge -c conf/meta_config.yaml` |
| 创建测试数据 | `uv run python -m app.scripts.create_dw_data` |
| 查看依赖列表 | `uv tree` |
| 添加依赖 | `uv add <package>` |
| 更新依赖 | `uv sync --upgrade` |
| 运行 Python 脚本 | `uv run python <script>` |

### 项目关键链接

| 资源 | 地址 |
|------|------|
| FastAPI 文档 | https://fastapi.tiangolo.com/ |
| LangGraph 文档 | https://langchain-ai.github.io/langgraph/ |
| Qdrant 文档 | https://qdrant.tech/documentation/ |
| SQLAlchemy 2.0 文档 | https://docs.sqlalchemy.org/en/20/ |
| Loguru 文档 | https://github.com/Delgan/loguru |
| uv 文档 | https://docs.astral.sh/uv/ |

---

> **📝 文档维护说明**：本文档随项目迭代持续更新。如发现文档与实际代码不一致，请以最新代码为准，并同步更新文档。
>
> **🤖 最后生成**：Co-Authored-By: Claude <noreply@anthropic.com>
