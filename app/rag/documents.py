DOCUMENTS = [
    {
        "id":"doc_001",
        "content":(
            "GraphRAG项目使用Neo4j图数据库保存实体"
            "以及实体之间的关系。Neo4j主要承担知识图谱"
            "存储和多跳关系查询能力。"
        ),
        "metadata":{
            "source":"GraphRAG架构文档",
            "section":"Graph Storage"
        }
    },
    {
        "id":"doc_002",
        "content":(
            "企业知识库使用PostgreSQL和pgvector"
            "保存文本Embedding向量，并通过向量相似度"
            "完成语义检索。"
        ),
        "metadata":{
            "source":"RAG技术设计文档",
            "section":"Vector Store"
        }
    },
    {
        "id":"doc_003",
        "content":(
            "检索阶段采用Vector Search和BM25进行"
            "多路召回。Vector Search负责语义相似检索，"
            "BM25负责关键词、编号以及专有名词的精确匹配。"
        ),
        "metadata":{
            "source":"RAG技术设计文档",
            "section":"Retrieval"
        }
    },
    {
        "id":"doc_004",
        "content":(
            "Vector Search和BM25的排序结果通过"
            "Reciprocal Rank Fusion，也就是RRF算法进行融合，"
            "避免直接比较两个检索器不同量纲的原始分数。"
        ),
        "metadata":{
            "source":"RAG技术设计文档",
            "section":"Fusion"
        }
    },
    {
        "id":"doc_005",
        "content":(
            "RRF融合之后得到候选文档集合，"
            "再使用Cross Encoder Reranker对Query和Document"
            "进行联合编码并重新排序，最后选择Top-K文档。"
        ),
        "metadata":{
            "source":"RAG技术设计文档",
            "section":"Rerank"
        }
    },
    {
        "id":"doc_006",
        "content":(
            "Agent使用LangGraph进行工作流编排，"
            "通过State保存运行状态，通过Node执行具体任务，"
            "并通过Conditional Edge决定是否进入ToolNode。"
        ),
        "metadata":{
            "source":"Agent架构设计文档",
            "section":"LangGraph"
        }
    },
    {
        "id":"doc_007",
        "content":(
            "Agent短期记忆主要用于保存当前Thread内的对话状态，"
            "长期Memory则用于保存跨Thread仍然具有价值的用户偏好、"
            "长期事实和关键决策。"
        ),
        "metadata":{
            "source":"Agent架构设计文档",
            "section":"Memory"
        }
    }
]