import json

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def verify_result(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "校验结果", "status": "running"})

    query = state["query"]
    sql = state["sql"]
    sql_result = state.get("sql_result")  # 可能为 None
    retry_count = state.get("retry_count", 0)

    try:
        # ── 第1层校验：结果不存在（sql_result is None）→ 跳过校验 ──
        if sql_result is None:
            writer({"type": "progress", "step": "校验结果", "status": "success"})
            logger.info("sql_result 为 None，跳过结果校验")
            return {
                "verify_passed": True,
                "confidence": "medium",
                "feedback": "",
            }

        # ── 第1层校验：空结果 → 快速判定有问题（已知有数据时） ──
        if isinstance(sql_result, list) and len(sql_result) == 0:
            writer({"type": "progress", "step": "校验结果", "status": "success"})
            logger.warning(f"查询结果为空，SQL: {sql}")
            feedback = "查询结果为空，请检查过滤条件或时间范围是否正确"
            # 判断是否达到最大重试次数
            if retry_count >= 2:
                writer({"type": "confidence", "level": "low"})
                return {
                    "verify_passed": True,
                    "confidence": "low",
                    "feedback": feedback,
                }
            return {
                "verify_passed": False,
                "feedback": feedback,
                "retry_count": retry_count + 1,
            }

        # ── 第2层校验：LLM 语义验证 ──
        result_sample = _summarize_result(sql_result)

        prompt = PromptTemplate(
            template=load_prompt("verify_result"),
            input_variables=["query", "sql", "result_sample"],
        )
        parser = JsonOutputParser()
        chain = prompt | llm | parser

        verification = await chain.ainvoke({
            "query": query,
            "sql": sql,
            "result_sample": json.dumps(result_sample, ensure_ascii=False, default=str),
        })

        passed = verification.get("passed", False)
        feedback = verification.get("feedback", "")
        confidence = verification.get("confidence", "medium")
        issues = verification.get("issues", [])

        logger.info(f"结果校验结论: passed={passed}, confidence={confidence}, issues={issues}")

        if passed:
            writer({"type": "confidence", "level": confidence})
            writer({"type": "progress", "step": "校验结果", "status": "success"})
            return {
                "verify_passed": True,
                "confidence": confidence,
                "feedback": "",
            }
        else:
            # 校验未通过 → 判断重试次数
            if retry_count >= 2:
                # 已达最大重试次数，推送置信度后强制通过
                writer({"type": "confidence", "level": "low"})
                writer({"type": "progress", "step": "校验结果", "status": "success"})
                logger.warning(f"结果校验未通过，但已达最大重试次数，强制通过。反馈: {feedback}")
                return {
                    "verify_passed": True,
                    "confidence": "low",
                    "feedback": feedback,
                }
            else:
                writer({"type": "progress", "step": "校验结果", "status": "success"})
                logger.info(f"结果校验未通过，将进行第 {retry_count + 1} 次修正。反馈: {feedback}")
                return {
                    "verify_passed": False,
                    "feedback": feedback,
                    "retry_count": retry_count + 1,
                }

    except Exception as e:
        # 校验节点本身出错不应阻塞主流程，默认通过
        writer({"type": "progress", "step": "校验结果", "status": "error"})
        logger.error(f"结果校验异常，已跳过: {str(e)}")
        return {
            "verify_passed": True,
            "confidence": "medium",
            "feedback": "",
        }


def _summarize_result(results: list[dict]) -> dict:
    """对查询结果做摘要，降低 LLM 校验的 Token 开销"""
    if not results:
        return {"row_count": 0, "columns": [], "sample": []}

    columns = list(results[0].keys())
    sample = results[:5]

    # 对数值列做统计，辅助 LLM 判断聚合是否正确
    numeric_summary = {}
    for col in columns:
        numeric_values = [
            r[col] for r in results
            if isinstance(r[col], (int, float))
        ]
        if numeric_values:
            numeric_summary[col] = {
                "min": min(numeric_values),
                "max": max(numeric_values),
                "avg": sum(numeric_values) / len(numeric_values),
                "count": len(numeric_values),
            }

    return {
        "row_count": len(results),
        "columns": columns,
        "sample": sample,
        "numeric_summary": numeric_summary,
    }
