# Enterprise GraphRAG Agent

面向企业知识库场景的 Agent 工程化原型，基于 **FastAPI + LangGraph + DeepSeek** 构建，组合 Hybrid RAG、Neo4j Graph Retrieval、Short/Long-term Memory、Context Engineering、Reliability、Observability 与 Evaluation。

> 当前仓库用于学习、验证与面试展示。部分组件采用本地 / In-Memory 实现，README 中会明确标注当前实现与生产化方向。

## 1. 核心能力

- **Agent Runtime**：LangGraph State / Node / Conditional Edge / ToolNode
- **Tool Calling**：普通问题直接回答，企业知识问题动态调用 `search_knowledge`
- **Hybrid RAG**：Vector Search + BM25 → RRF → Cross Encoder Rerank → Top-K
- **GraphRAG**：Neo4j 实体关系检索，与 Text Evidence 联合打包
- **Memory**：`thread_id` 级 Short-term Memory + `user_id` 级 Long-term Memory
- **Context Engineering**：统一组织 System Prompt、History、Memory、Tool Result 与 Current Query
- **Reliability**：Timeout / Retry / Exponential Backoff / Semaphore / Graceful Degradation
- **Observability**：Structured Logging、request_id、Prometheus Metrics
- **Evaluation**：Tool Selection / Tool Argument / Task Completion / Overall Pass / Latency

## 2. 整体链路

```text
User
  ↓
FastAPI
  ↓
LangGraph Agent
  ↓
ContextManager
  ↓
LLM
  ↓
Tool Calling
  ↓
search_knowledge
  ↓
┌───────────────────────┬───────────────────────┐
│ Hybrid Text Retrieval │ Neo4j Graph Retrieval │
│ Vector + BM25         │ Entity / Relation     │
│       ↓               │       ↓               │
│      RRF              │ Graph Evidence        │
│       ↓               │                       │
│ Cross Encoder Rerank  │                       │
│       ↓               │                       │
│ Text Evidence         │                       │
└───────────┬───────────┴───────────┬───────────┘
            ↓
       Context Packing
            ↓
        ToolMessage
            ↓
           LLM
            ↓
      Final Answer
```

## 3. 当前实现说明

### 3.1 Vector Retrieval

当前使用 `sentence-transformers` 的 `BAAI/bge-small-zh-v1.5`：

- 启动时对 Demo 文档做 Embedding
- 向量保存在当前进程内存
- Query Embedding 与文档向量通过余弦相似度召回

生产化可以进一步替换为 pgvector / Milvus / Elasticsearch Vector 等持久化向量存储。

### 3.2 BM25 + RRF + Rerank

- BM25：`rank-bm25`
- 中文分词：`jieba`
- 融合：Reciprocal Rank Fusion（RRF）
- 精排：Cross Encoder Reranker

整体：

```text
Vector Recall + BM25 Recall
          ↓
         RRF
          ↓
   Candidate Documents
          ↓
 Cross Encoder Rerank
          ↓
        Top-K
```

### 3.3 Graph Retrieval

当前 Graph Retrieval 使用 Neo4j：

- 从 Query 中抽取当前 Demo 支持的实体关键词
- 查询匹配节点及其相邻关系
- 将 `source / relation / target` 打包为 Graph Evidence

Neo4j 不可用时返回空 Graph Results，由 Text RAG 继续完成问答，避免图数据库成为系统单点依赖。

### 3.4 Short-term Memory

使用 LangGraph `InMemorySaver`：

```python
config = {
    "configurable": {
        "thread_id": thread_id
    }
}
```

相同 `thread_id` 可以恢复同一会话历史；不同 thread 相互隔离。

> `InMemorySaver` 仅适用于当前进程，本地开发时不要依赖 `--reload` 保留历史。生产环境应替换为持久化 Checkpointer。

### 3.5 Long-term Memory

当前 Long-term Memory 也是 **In-Memory 原型**：

- 以 `user_id` 区分用户
- 使用结构化 `key / value / importance`
- 同 key 采用 Upsert
- ContextManager 根据 Query 检索 Top-K Memory

生产化可进一步迁移至 PostgreSQL / Redis / Vector Store。

## 4. 项目目录

```text
enterprise-graphrag-agent/
├── app/
│   ├── agent/          # LangGraph State / Graph / Agent Node
│   ├── api/            # FastAPI Chat API
│   ├── core/           # Config / Reliability / Observability
│   ├── memory/         # Short/Long-term Memory 与 ContextManager
│   ├── rag/            # Vector / BM25 / RRF / Rerank / Graph Retrieval
│   ├── schemas/        # Pydantic Schema
│   ├── services/       # LLM / Neo4j Client
│   ├── tools/          # search_knowledge Tool
│   └── main.py
├── eval/               # Agent Evaluation
├── scripts/            # Neo4j Seed Script
├── tests/              # 手工验证脚本
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 5. 环境配置

### 5.1 Python

建议 Python 3.11+。

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
```

安装依赖：

```bash
pip install -r requirements.txt
```

### 5.2 环境变量

复制：

```bash
cp .env.example .env
```

Windows 可以直接复制文件，然后填写：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

> `.env` 已加入 `.gitignore`，不要把真实 Key 或密码提交到仓库。

## 6. Neo4j

启动本地 Neo4j 后，执行：

```bash
python scripts/seed_neo4j.py
```

用于写入 Demo 图谱数据。

Neo4j 未启动时，Graph Retrieval 会降级，Text RAG 仍可工作。

## 7. 启动服务

为了避免 `InMemorySaver` 在 reload 进程切换时丢失状态，本地验证 Memory 时建议：

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

服务地址：

- Swagger: `http://127.0.0.1:8001/docs`
- Health: `http://127.0.0.1:8001/health`
- Metrics: `http://127.0.0.1:8001/metrics`

## 8. API 示例

### POST `/chat`

```json
{
  "user_id": "user_001",
  "thread_id": "thread_001",
  "message": "GraphRAG项目的检索流程是什么？"
}
```

Response：

```json
{
  "answer": "..."
}
```

## 9. Demo 场景

### Hybrid RAG

```text
GraphRAG项目的检索流程是什么？
```

用于验证 Vector + BM25 + RRF + Rerank。

### Graph Retrieval

```text
GraphRAG中的实体关系存储在哪里？
```

Neo4j 正常时可同时获得 Text Evidence 与 Graph Evidence。

### Short-term Memory

第一轮：

```text
我正在开发一个GraphRAG项目。
```

第二轮保持同一 `thread_id`：

```text
我刚才说我正在开发什么项目？
```

### Thread Isolation

更换 `thread_id` 后，不应该继承上一 Thread 的 Short-term History。

## 10. Reliability

LLM 调用封装：

- Timeout
- Retry
- Exponential Backoff
- Semaphore
- Graceful Degradation

只对适合重试的瞬时异常进行 Retry，避免 Authentication / Bad Request 等确定性错误产生无效重试。

## 11. Observability

使用 ContextVar 贯穿：

```text
request_id / user_id / thread_id
```

Prometheus Metrics 覆盖：

- HTTP Requests / Latency
- LLM Calls / Latency
- Tool Calls / Latency

## 12. Agent Evaluation

运行：

```bash
python -m eval.evaluate_agent
```

当前指标：

- Tool Selection Accuracy
- Tool Argument Accuracy
- Task Completion Rate
- Overall Pass Rate
- Average Latency

仓库中保留一份 Demo Evaluation Dataset 和一次示例评测结果，方便理解评测流程；结果会受模型、网络和环境影响。

## 13. 当前限制

这是一个工程化学习原型，当前限制包括：

- Vector Store 目前为进程内 Embedding，而非持久化 pgvector
- Short-term Memory 使用 `InMemorySaver`
- Long-term Memory 使用进程内 Store
- Graph Entity Extraction 目前为 Demo 关键词匹配
- Demo 知识库规模较小
- Evaluation Dataset 规模较小

## 14. 可继续扩展

- Persistent Checkpointer
- pgvector / Milvus 等持久化 Vector Store
- LLM Structured Entity Extraction / Entity Linking
- Multi-hop Graph Retrieval
- Memory Conflict Resolution
- Token Budget / Context Compression
- Tracing 与更完整的线上 Evaluation
