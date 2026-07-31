"""
真实 LLM 调用测试：验证 verify_result 自检机制能否发现语义错误。

使用 DeepSeek API 真实调用，不 mock。透明输出每次 LLM 的输入和返回。
"""
import asyncio
import json
import sys
import os

# ── 初始化项目环境 ──
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# 先初始化 LLM（导入会触发 app_config 加载）
from app.agent.llm import llm
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from app.prompt.prompt_loader import load_prompt

# 需要把 llm 包在可序列化的 Runnable 里 → 直接用 llm 即可（它已经是 BaseChatModel）


SEPARATOR = "=" * 72


async def test_scenario(name: str, query: str, sql: str, sql_result: list[dict]):
    """用真实 LLM 调用 verify_result prompt，输出完整请求和响应"""
    print(f"\n{SEPARATOR}")
    print(f"🧪 场景: {name}")
    print(SEPARATOR)

    # 构造结果摘要（复用项目中的 _summarize_result）
    from app.agent.nodes.verify_result import _summarize_result
    result_sample = _summarize_result(sql_result)
    result_sample_json = json.dumps(result_sample, ensure_ascii=False, default=str)

    print(f"\n📋 用户问题: {query}")
    print(f"📋 SQL:\n{sql}")
    print(f"📋 结果摘要: {json.dumps(result_sample, ensure_ascii=False, default=str)[:500]}")

    # 构造 prompt chain
    prompt = PromptTemplate(
        template=load_prompt("verify_result"),
        input_variables=["query", "sql", "result_sample"],
    )
    parser = JsonOutputParser()
    chain = prompt | llm | parser

    # 调用 LLM
    print(f"\n🤖 调用 LLM ({llm.model_name})...")
    try:
        response = await chain.ainvoke({
            "query": query,
            "sql": sql,
            "result_sample": result_sample_json,
        })
        print(f"\n📤 LLM 返回:")
        print(json.dumps(response, ensure_ascii=False, indent=2))

        # 判定
        passed = response.get("passed", False)
        confidence = response.get("confidence", "unknown")
        feedback = response.get("feedback", "")
        issues = response.get("issues", [])

        print(f"\n📊 判定: {'✅ 通过' if passed else '❌ 未通过'}")
        print(f"📊 置信度: {confidence}")
        if feedback:
            print(f"📊 反馈: {feedback}")
        if issues:
            print(f"📊 问题列表: {'; '.join(issues)}")
        return passed, confidence, feedback, issues

    except Exception as e:
        print(f"\n💥 LLM 调用异常: {type(e).__name__}: {e}")
        return None, None, str(e), []


async def main():
    # ── 场景 A: SQL 正确 ──
    await test_scenario(
        name="A - ✅ SQL 语义正确（按地区统计销售总额）",
        query="统计去年各地区的销售总额",
        sql="""SELECT r.region_name AS 地区,
       SUM(f.order_amount) AS 销售总额
FROM fact_order f
JOIN dim_region r ON f.region_id = r.region_id
JOIN dim_date d ON f.date_id = d.date_id
WHERE d.year = 2025
GROUP BY r.region_name
ORDER BY 销售总额 DESC""",
        sql_result=[
            {"地区": "华东", "销售总额": 128000.50},
            {"地区": "华南", "销售总额": 96500.00},
            {"地区": "华北", "销售总额": 72300.75},
            {"地区": "华中", "销售总额": 54200.00},
            {"地区": "西南", "销售总额": 38900.25},
        ]
    )

    # ── 场景 B: Wrong aggregation (AVG instead of SUM) ──
    await test_scenario(
        name="B - ❌ 聚合函数错误（AVG 代替 SUM）",
        query="统计去年各地区的销售总额",
        sql="""SELECT r.region_name AS 地区,
       AVG(f.order_amount) AS 销售总额
FROM fact_order f
JOIN dim_region r ON f.region_id = r.region_id
JOIN dim_date d ON f.date_id = d.date_id
WHERE d.year = 2025
GROUP BY r.region_name""",
        sql_result=[
            {"地区": "华东", "销售总额": 2133.34},
            {"地区": "华南", "销售总额": 1923.08},
            {"地区": "华北", "销售总额": 1807.52},
            {"地区": "华中", "销售总额": 1355.00},
            {"地区": "西南", "销售总额": 1296.68},
        ]
    )

    # ── 场景 C: Missing filter condition ──
    await test_scenario(
        name="C - ❌ 缺失过滤条件（缺少金牌会员 WHERE）",
        query="去年金牌会员的订单金额排名",
        sql="""SELECT c.customer_name AS 客户名称,
       SUM(f.order_amount) AS 订单总额
FROM fact_order f
JOIN dim_customer c ON f.customer_id = c.customer_id
JOIN dim_date d ON f.date_id = d.date_id
WHERE d.year = 2025
GROUP BY c.customer_name
ORDER BY 订单总额 DESC""",
        sql_result=[
            {"客户名称": "张三", "订单总额": 35000},
            {"客户名称": "王五", "订单总额": 28000},
            {"客户名称": "赵六", "订单总额": 22000},
            {"客户名称": "李四", "订单总额": 18000},
            {"客户名称": "孙七", "订单总额": 15000},
        ]
    )

    # ── 场景 D: Wrong dimension (group by wrong column) ──
    await test_scenario(
        name="D - ❌ 分组维度错误（按客户而非品类）",
        query="去年各品类的销售额排名",
        sql="""SELECT c.customer_name AS 客户,
       SUM(f.order_amount) AS 销售额
FROM fact_order f
JOIN dim_customer c ON f.customer_id = c.customer_id
JOIN dim_date d ON f.date_id = d.date_id
WHERE d.year = 2025
GROUP BY c.customer_name
ORDER BY 销售额 DESC""",
        sql_result=[
            {"客户": "张三", "销售额": 35000},
            {"客户": "王五", "销售额": 28000},
            {"客户": "赵六", "销售额": 22000},
            {"客户": "李四", "销售额": 18000},
            {"客户": "孙七", "销售额": 15000},
        ]
    )

    # ── 场景 E: COUNT vs SUM confusion ──
    await test_scenario(
        name="E - ❌ 聚合语义错误（COUNT 代替 SUM）",
        query="今年各地区的订单总量（件数）",
        sql="""SELECT r.region_name AS 地区,
       COUNT(f.order_quantity) AS 总销量
FROM fact_order f
JOIN dim_region r ON f.region_id = r.region_id
WHERE YEAR(f.date_id) = 2026
GROUP BY r.region_name""",
        sql_result=[
            {"地区": "华东", "总销量": 42},
            {"地区": "华南", "总销量": 38},
            {"地区": "华北", "总销量": 35},
            {"地区": "华中", "总销量": 28},
            {"地区": "西南", "总销量": 22},
        ]
    )

    # ── 场景 F: Correct with confidence ──
    await test_scenario(
        name="F - ✅ SQL 正确（按省份统计订单量 COUNT 正确）",
        query="统计各地区的订单数量",
        sql="""SELECT r.region_name AS 地区,
       COUNT(f.order_id) AS 订单数量
FROM fact_order f
JOIN dim_region r ON f.region_id = r.region_id
GROUP BY r.region_name""",
        sql_result=[
            {"地区": "华东", "订单数量": 42},
            {"地区": "华南", "订单数量": 38},
            {"地区": "华北", "订单数量": 35},
            {"地区": "华中", "订单数量": 28},
            {"地区": "西南", "订单数量": 22},
        ]
    )

    print(f"\n{SEPARATOR}")
    print("🏁 所有场景测试完成")


if __name__ == "__main__":
    asyncio.run(main())
