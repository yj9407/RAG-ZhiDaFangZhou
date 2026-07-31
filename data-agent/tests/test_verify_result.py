"""
验证 verify_result 自检机制的测试。

测试策略：
- 纯逻辑函数（_summarize_result）直接测试
- 节点函数通过 RunnableLambda 模拟 LLM 返回值，保持 LCEL 链路完整
- 图路由通过复制 lambda 逻辑测试
"""
import json
import pytest
from unittest.mock import patch, AsyncMock


# ============================================================
# 测试辅助函数 _summarize_result
# ============================================================

class TestSummarizeResult:
    """验证结果摘要函数，这是纯逻辑无依赖的。"""

    def test_empty_list(self):
        from app.agent.nodes.verify_result import _summarize_result
        summary = _summarize_result([])
        assert summary["row_count"] == 0
        assert summary["columns"] == []
        assert summary["sample"] == []

    def test_single_row(self):
        from app.agent.nodes.verify_result import _summarize_result
        data = [{"region": "华东", "total": 1000, "注": "测试"}]
        summary = _summarize_result(data)
        assert summary["row_count"] == 1
        assert summary["columns"] == ["region", "total", "注"]
        assert summary["sample"] == data
        assert summary["numeric_summary"]["total"]["min"] == 1000
        assert summary["numeric_summary"]["total"]["max"] == 1000
        assert summary["numeric_summary"]["total"]["avg"] == 1000

    def test_multiple_rows_with_mixed_types(self):
        from app.agent.nodes.verify_result import _summarize_result
        data = [
            {"region": "华东", "amount": 100.0, "cnt": 10},
            {"region": "华南", "amount": 200.0, "cnt": 20},
            {"region": "华北", "amount": 300.0, "cnt": 30},
        ]
        summary = _summarize_result(data)
        assert summary["row_count"] == 3
        assert "amount" in summary["numeric_summary"]
        assert summary["numeric_summary"]["amount"]["min"] == 100.0
        assert summary["numeric_summary"]["amount"]["max"] == 300.0
        assert summary["numeric_summary"]["amount"]["avg"] == 200.0
        assert summary["numeric_summary"]["amount"]["count"] == 3
        assert "region" not in summary["numeric_summary"]

    def test_large_result_truncated_to_5_rows(self):
        from app.agent.nodes.verify_result import _summarize_result
        data = [{"id": i, "val": i * 10} for i in range(100)]
        summary = _summarize_result(data)
        assert summary["row_count"] == 100
        assert len(summary["sample"]) == 5
        assert summary["sample"][0]["id"] == 0
        assert summary["sample"][4]["id"] == 4

    def test_none_values_handled(self):
        from app.agent.nodes.verify_result import _summarize_result
        data = [{"region": "华东", "amount": None}]
        summary = _summarize_result(data)
        assert summary["row_count"] == 1
        assert "amount" not in summary["numeric_summary"]


# ============================================================
# 测试 verify_result 节点决策逻辑
# ============================================================

class FakeWriter:
    def __init__(self):
        self.events = []

    def __call__(self, data):
        self.events.append(data)


class FakeRuntime:
    def __init__(self):
        self.stream_writer = FakeWriter()
        self.context = {}


def make_fake_llm(response_dict: dict):
    """创建一个 RunnableLambda 模拟 LLM，返回指定的 JSON 响应。
    这保证与 LangChain 的 LCEL（prompt | llm | parser）兼容。"""
    from langchain_core.runnables import RunnableLambda

    async def fake_ainvoke(messages, *args, **kwargs):
        return json.dumps(response_dict, ensure_ascii=False)

    return RunnableLambda(fake_ainvoke)


class TestVerifyResultDecision:
    """验证 verify_result 在各种输入下的决策路径。

    通过 RunnableLambda 模拟 LLM 返回值，保持 LCEL 链路完整可用。
    """

    @pytest.fixture
    def runtime(self):
        return FakeRuntime()

    # ── Case 1: sql_result is None → 跳过校验 ──

    @pytest.mark.asyncio
    async def test_sql_result_is_none_skips_verification(self, runtime):
        from app.agent.nodes.verify_result import verify_result

        state = {
            "query": "统计销售额",
            "sql": "SELECT SUM(amount) FROM ...",
            "sql_result": None,
            "retry_count": 0,
        }

        # 用 RunnableLambda 模拟 LLM
        llm = make_fake_llm({"passed": True, "confidence": "high", "feedback": "", "issues": []})

        with patch("app.agent.nodes.verify_result.llm", llm):
            result = await verify_result(state, runtime)

        assert result["verify_passed"] is True, "sql_result=None 时应跳过校验"
        assert result["confidence"] == "medium"

    # ── Case 2: 空结果 + retry_count=0 → 触发修正 ──

    @pytest.mark.asyncio
    async def test_empty_result_triggers_correction(self, runtime):
        from app.agent.nodes.verify_result import verify_result

        state = {
            "query": "统计销售额",
            "sql": "SELECT ...",
            "sql_result": [],
            "retry_count": 0,
        }

        llm = make_fake_llm({"passed": True, "confidence": "high", "feedback": "", "issues": []})

        with patch("app.agent.nodes.verify_result.llm", llm):
            result = await verify_result(state, runtime)

        assert result["verify_passed"] is False, "空结果应触发修正"
        assert result["retry_count"] == 1, "retry_count 应递增"
        assert "为空" in result["feedback"]

    # ── Case 3: 空结果 + retry_count=2 → 强制通过 + low confidence ──

    @pytest.mark.asyncio
    async def test_empty_result_gives_up_after_retries(self, runtime):
        from app.agent.nodes.verify_result import verify_result

        state = {
            "query": "统计销售额",
            "sql": "SELECT ...",
            "sql_result": [],
            "retry_count": 2,
        }

        llm = make_fake_llm({"passed": True, "confidence": "high", "feedback": "", "issues": []})

        with patch("app.agent.nodes.verify_result.llm", llm):
            result = await verify_result(state, runtime)

        assert result["verify_passed"] is True, "retry_count>=2 时应强制通过"
        assert result["confidence"] == "low"
        confidence_events = [
            e for e in runtime.stream_writer.events
            if isinstance(e, dict) and e.get("type") == "confidence"
        ]
        assert len(confidence_events) == 1
        assert confidence_events[0]["level"] == "low"

    # ── Case 4: LLM 返回 passed → 正常通过 ──

    @pytest.mark.asyncio
    async def test_llm_passes_goes_to_end(self, runtime):
        from app.agent.nodes.verify_result import verify_result

        state = {
            "query": "各地区的销售额",
            "sql": "SELECT region_name, SUM(amount) FROM fact_order ...",
            "sql_result": [{"region": "华东", "total": 100}],
            "retry_count": 0,
        }

        llm = make_fake_llm({
            "passed": True,
            "confidence": "high",
            "feedback": "",
            "issues": [],
        })

        with patch("app.agent.nodes.verify_result.llm", llm):
            result = await verify_result(state, runtime)

        assert result["verify_passed"] is True
        assert result["confidence"] == "high"
        assert result["feedback"] == ""

    # ── Case 5: LLM 返回 failed + retry_count=0 → 触发修正 ──

    @pytest.mark.asyncio
    async def test_llm_fails_triggers_correction(self, runtime):
        from app.agent.nodes.verify_result import verify_result

        state = {
            "query": "各地区的销售总额",
            "sql": "SELECT region_name, AVG(amount) FROM fact_order ...",
            "sql_result": [{"region": "华东", "avg": 123}],
            "retry_count": 0,
        }

        llm = make_fake_llm({
            "passed": False,
            "confidence": "low",
            "feedback": "聚合函数应为 SUM 而非 AVG",
            "issues": ["聚合函数错误"],
        })

        with patch("app.agent.nodes.verify_result.llm", llm):
            result = await verify_result(state, runtime)

        assert result["verify_passed"] is False
        assert result["retry_count"] == 1
        assert "SUM" in result["feedback"]

    # ── Case 6: LLM 返回 failed + retry_count=2 → 强制通过 ──

    @pytest.mark.asyncio
    async def test_llm_fails_gives_up_after_retries(self, runtime):
        from app.agent.nodes.verify_result import verify_result

        state = {
            "query": "各地区的销售总额",
            "sql": "SELECT ...",
            "sql_result": [{"region": "华东", "total": 100}],
            "retry_count": 2,
        }

        llm = make_fake_llm({
            "passed": False,
            "confidence": "low",
            "feedback": "仍然有问题",
            "issues": ["仍然有问题"],
        })

        with patch("app.agent.nodes.verify_result.llm", llm):
            result = await verify_result(state, runtime)

        assert result["verify_passed"] is True, "retry_count>=2 时应强制通过"
        assert result["confidence"] == "low"
        assert any(
            isinstance(e, dict) and e.get("type") == "confidence"
            for e in runtime.stream_writer.events
        )

    # ── Case 7: LLM 链抛出异常 → 容错通过 ──

    @pytest.mark.asyncio
    async def test_llm_exception_fails_open(self, runtime):
        from app.agent.nodes.verify_result import verify_result

        state = {
            "query": "各地区的销售额",
            "sql": "SELECT ...",
            "sql_result": [{"region": "华东", "total": 100}],
            "retry_count": 0,
        }

        # 让 LLM 抛出异常
        from langchain_core.runnables import RunnableLambda

        async def broken_ainvoke(*args, **kwargs):
            raise RuntimeError("LLM 服务不可用")

        broken_llm = RunnableLambda(broken_ainvoke)

        with patch("app.agent.nodes.verify_result.llm", broken_llm):
            result = await verify_result(state, runtime)

        assert result["verify_passed"] is True, "LLM 异常时应容错通过"
        assert result["confidence"] == "medium"
        assert result["feedback"] == ""


# ============================================================
# 测试 correct_sql 的路由逻辑（feedback vs error）
# ============================================================

class TestCorrectSqlRouting:
    """验证 correct_sql 节点正确选择语法修正 vs 语义修正分支"""

    @pytest.fixture
    def runtime(self):
        r = FakeRuntime()
        return r

    @pytest.fixture
    def base_state(self):
        return {
            "query": "统计各地区的销售总额",
            "sql": "SELECT ...",
            "table_infos": [],
            "metric_infos": [],
            "date_info": {"date": "2026-07-24", "weekday": "Friday", "quarter": "Q3"},
            "db_info": {"dialect": "mysql", "version": "8.0"},
        }

    def _make_llm(self, return_sql: str = "SELECT 1"):
        """创建可用的假 LLM，让 correct_sql 能走通 LCEL"""
        from langchain_core.runnables import RunnableLambda

        async def fake_invoke(*args, **kwargs):
            return return_sql

        return RunnableLambda(fake_invoke)

    @pytest.mark.asyncio
    async def test_feedback_mode_uses_correct_by_feedback_prompt(self, runtime, base_state):
        """当 feedback 非空时，应加载 correct_by_feedback.prompt"""
        from app.agent.nodes.correct_sql import correct_sql

        state = {**base_state, "error": "", "feedback": "聚合函数应为 SUM 而非 AVG"}

        llm = self._make_llm()

        with patch("app.agent.nodes.correct_sql.llm", llm), \
             patch("app.agent.nodes.correct_sql.load_prompt", return_value="语义模板") as mock_load:
            result = await correct_sql(state, runtime)

        mock_load.assert_called_once_with("correct_by_feedback")

    @pytest.mark.asyncio
    async def test_error_mode_uses_correct_sql_prompt(self, runtime, base_state):
        """当 error 非空、feedback 为空时，应加载 correct_sql.prompt"""
        from app.agent.nodes.correct_sql import correct_sql

        state = {**base_state, "error": "语法错误: 表不存在", "feedback": ""}

        llm = self._make_llm()

        with patch("app.agent.nodes.correct_sql.llm", llm), \
             patch("app.agent.nodes.correct_sql.load_prompt", return_value="语法模板") as mock_load:
            result = await correct_sql(state, runtime)

        mock_load.assert_called_once_with("correct_sql")

    @pytest.mark.asyncio
    async def test_feedback_takes_priority_over_error(self, runtime, base_state):
        """当 feedback 和 error 同时存在时，feedback 优先"""
        from app.agent.nodes.correct_sql import correct_sql

        state = {**base_state, "error": "旧语法错误", "feedback": "维度错误"}

        llm = self._make_llm()

        with patch("app.agent.nodes.correct_sql.llm", llm), \
             patch("app.agent.nodes.correct_sql.load_prompt", return_value="语义模板") as mock_load:
            result = await correct_sql(state, runtime)

        mock_load.assert_called_once_with("correct_by_feedback")


# ============================================================
# 测试 graph 条件路由逻辑
# ============================================================

class TestGraphConditionalRouting:
    """验证 verify_result 之后的图条件路由 lambda 逻辑"""

    # 从 graph.py 复制出来的 lambda（保持与源码一致）
    @staticmethod
    def routing_lambda(state):
        return (
            "end" if state.get("verify_passed", True) or state.get("retry_count", 0) >= 2
            else "correct_sql"
        )

    def test_verify_passed_routes_to_end(self):
        assert self.routing_lambda({"verify_passed": True, "retry_count": 0}) == "end"
        assert self.routing_lambda({"verify_passed": True, "retry_count": 3}) == "end"

    def test_verify_failed_with_retry_under_2_routes_to_correct_sql(self):
        assert self.routing_lambda({"verify_passed": False, "retry_count": 0}) == "correct_sql"
        assert self.routing_lambda({"verify_passed": False, "retry_count": 1}) == "correct_sql"

    def test_verify_failed_with_retry_ge_2_routes_to_end(self):
        assert self.routing_lambda({"verify_passed": False, "retry_count": 2}) == "end"
        assert self.routing_lambda({"verify_passed": False, "retry_count": 3}) == "end"

    def test_missing_keys_default_to_end(self):
        """防御性：即使 state 缺少 verify_passed 字段，应安全路由"""
        assert self.routing_lambda({}) == "end"
