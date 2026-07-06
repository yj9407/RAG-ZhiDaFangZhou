"""
纯 Python 实现的简易搜索引擎，替代 Elasticsearch。
使用 jieba 分词 + 内存索引，零外部依赖（仅需 jieba）。
"""
import re
from collections import defaultdict
from dataclasses import asdict

import jieba


class SimpleIndex:
    """模拟 ES 的单个索引"""

    def __init__(self, name: str, mappings: dict):
        self.name = name
        self.mappings = mappings
        self._docs: dict[str, dict] = {}                   # id -> 原始文档
        self._tokens_index: dict[str, set[str]] = defaultdict(set)  # token -> doc_ids

    def _tokenize(self, text: str) -> set[str]:
        """中文分词，过滤纯数字和空白"""
        tokens = jieba.lcut(str(text).lower())
        return {t.strip() for t in tokens if t.strip() and not t.strip().isdigit()}

    def add_documents(self, docs: list[dict]):
        """批量添加文档"""
        for doc in docs:
            doc_id = doc.get("id", "")
            if not doc_id:
                continue
            self._docs[doc_id] = doc
            text = doc.get("value", "")
            tokens = self._tokenize(text)
            for token in tokens:
                self._tokens_index[token].add(doc_id)

    def search(self, keyword: str, min_score: float = 0.3, size: int = 5) -> dict:
        """
        搜索接口，返回格式兼容 ES search 结果。
        """
        query_tokens = self._tokenize(keyword)
        if not query_tokens:
            return {"hits": {"hits": []}}

        doc_scores: dict[str, float] = {}

        for token in query_tokens:
            # 精确 token 匹配
            for doc_id in self._tokens_index.get(token, set()):
                doc_scores[doc_id] = doc_scores.get(doc_id, 0) + 1.0

            # 子串匹配（权重减半）
            for idx_token, doc_ids in self._tokens_index.items():
                if token != idx_token and token in idx_token:
                    for doc_id in doc_ids:
                        doc_scores[doc_id] = doc_scores.get(doc_id, 0) + 0.5
                elif idx_token in token and token != idx_token:
                    for doc_id in doc_ids:
                        doc_scores[doc_id] = doc_scores.get(doc_id, 0) + 0.3

        if not doc_scores:
            return {"hits": {"hits": []}}

        max_score = max(doc_scores.values())
        scored = [
            (doc_id, score / max_score)
            for doc_id, score in doc_scores.items()
            if score / max_score >= min_score
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        scored = scored[:size]

        return {
            "hits": {
                "hits": [
                    {"_source": self._docs[doc_id], "_score": score}
                    for doc_id, score in scored
                ]
            }
        }


class SimpleSearchClient:
    """
    模拟 AsyncElasticsearch，接口兼容真实 ES 客户端。
    不连接外部服务，所有数据在内存中存储。
    """
    def __init__(self):
        self._indices: dict[str, SimpleIndex] = {}
        self._closed = False

    # ========== indices 接口 ==========

    class IndicesProxy:
        def __init__(self, parent: "SimpleSearchClient"):
            self._p = parent

        async def exists(self, index: str) -> bool:
            return index in self._p._indices

        async def create(self, index: str, mappings: dict):
            self._p._indices[index] = SimpleIndex(name=index, mappings=mappings)

    @property
    def indices(self) -> IndicesProxy:
        return self.IndicesProxy(self)

    # ========== bulk 接口 ==========

    async def bulk(self, operations: list):
        """批量写入文档，operations 为 ES bulk 格式"""
        docs: list[dict] = []
        current_index = None

        for i in range(0, len(operations), 2):
            action = operations[i]
            doc = dict(operations[i + 1])  # 拷贝，避免修改原数据
            if "index" in action:
                doc["id"] = action["index"]["_id"]
                current_index = action["index"].get("_index", "data-agent-value")
            docs.append(doc)

        if current_index and current_index in self._indices:
            self._indices[current_index].add_documents(docs)
        elif current_index:
            # 自动创建索引
            self._indices[current_index] = SimpleIndex(name=current_index, mappings={})
            self._indices[current_index].add_documents(docs)

    # ========== search 接口 ==========

    async def search(self, index: str, query: dict, min_score: float = 0.3, size: int = 5) -> dict:
        idx = self._indices.get(index)
        if not idx:
            return {"hits": {"hits": []}}

        match_query = query.get("match", {})
        keyword = match_query.get("value", "") if isinstance(match_query, dict) else str(match_query)
        return idx.search(keyword, min_score=min_score, size=size)

    # ========== close 接口 ==========

    async def close(self):
        self._closed = True
        self._indices.clear()
