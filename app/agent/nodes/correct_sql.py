import yaml
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def correct_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "校正SQL", "status": "running"})

    sql = state["sql"]
    query = state["query"]
    table_infos = state["table_infos"]
    metric_infos = state["metric_infos"]
    date_info = state["date_info"]
    db_info = state["db_info"]

    # 从 state 读取错误信息和语义反馈
    error = state.get("error", "")
    feedback = state.get("feedback", "")

    try:
        output_parser = StrOutputParser()

        common_inputs = {
            "query": query,
            "table_infos": yaml.dump(table_infos, allow_unicode=True, sort_keys=False),
            "metric_infos": yaml.dump(metric_infos, allow_unicode=True, sort_keys=False),
            "date_info": yaml.dump(date_info, allow_unicode=True, sort_keys=False),
            "db_info": yaml.dump(db_info, allow_unicode=True, sort_keys=False),
            "sql": sql,
        }

        if feedback:
            # ── 语义校正模式（来自 verify_result 的反馈） ──
            prompt = PromptTemplate(
                template=load_prompt("correct_by_feedback"),
                input_variables=[
                    "query", "table_infos", "metric_infos",
                    "date_info", "db_info", "sql", "feedback",
                ],
            )
            chain = prompt | llm | output_parser
            result = await chain.ainvoke({
                **common_inputs,
                "feedback": feedback,
            })
            logger.info(f"语义反馈校正SQL: {result}")
        else:
            # ── 语法校正模式（来自 validate_sql 的错误信息） ──
            # 修复: input_variables 完整列出 template 中所有用到的变量
            prompt = PromptTemplate(
                template=load_prompt("correct_sql"),
                input_variables=[
                    "query", "table_infos", "metric_infos",
                    "date_info", "db_info", "sql", "error",
                ],
            )
            chain = prompt | llm | output_parser
            result = await chain.ainvoke({
                **common_inputs,
                "error": error,
            })
            logger.info(f"语法校正SQL: {result}")

        writer({"type": "progress", "step": "校正SQL", "status": "success"})
        return {"sql": result}
    except Exception as e:
        writer({"type": "progress", "step": "校正SQL", "status": "error"})
        logger.error(f"校正SQL失败:{str(e)}")
        raise
