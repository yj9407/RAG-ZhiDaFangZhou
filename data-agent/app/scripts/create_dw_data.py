"""
创建数仓测试数据：在 dw 库中建表并插入样本数据。
基于 meta_config.yaml 的表定义生成。
"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


DW_URL = "mysql+asyncmy://atguigu:Atguigu.123@localhost:3306/dw?charset=utf8mb4"


async def create_dw_data():
    engine = create_async_engine(DW_URL)
    async with engine.begin() as conn:
        # ========== 维度表 ==========

        # 1. dim_region
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_region (
                region_id INT PRIMARY KEY AUTO_INCREMENT,
                province VARCHAR(50) COMMENT '省份',
                region_name VARCHAR(50) COMMENT '大区',
                country VARCHAR(50) DEFAULT '中国' COMMENT '国家'
            )
        """))

        # 2. dim_customer
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_customer (
                customer_id INT PRIMARY KEY AUTO_INCREMENT,
                customer_name VARCHAR(100) COMMENT '客户名称',
                gender VARCHAR(10) COMMENT '性别',
                member_level VARCHAR(30) COMMENT '会员等级'
            )
        """))

        # 3. dim_product
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_product (
                product_id INT PRIMARY KEY AUTO_INCREMENT,
                product_name VARCHAR(200) COMMENT '商品名称',
                category VARCHAR(100) COMMENT '品类',
                brand VARCHAR(100) COMMENT '品牌'
            )
        """))

        # 4. dim_date
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_date (
                date_id BIGINT PRIMARY KEY COMMENT '日期ID yyyyMMdd',
                year INT COMMENT '年',
                quarter INT COMMENT '季度',
                month INT COMMENT '月',
                day INT COMMENT '日'
            )
        """))

        # 5. fact_order
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fact_order (
                order_id INT PRIMARY KEY AUTO_INCREMENT,
                customer_id INT COMMENT '客户ID',
                product_id INT COMMENT '商品ID',
                date_id BIGINT COMMENT '日期ID',
                region_id INT COMMENT '地区ID',
                order_quantity INT COMMENT '购买数量',
                order_amount DECIMAL(12, 2) COMMENT '订单金额'
            )
        """))

        print("[OK]表结构创建完成")

    # ========== 插入数据 ==========
    async with engine.begin() as conn:
        # 先清空
        await conn.execute(text("DELETE FROM fact_order"))
        await conn.execute(text("DELETE FROM dim_region"))
        await conn.execute(text("DELETE FROM dim_customer"))
        await conn.execute(text("DELETE FROM dim_product"))
        await conn.execute(text("DELETE FROM dim_date"))

        # dim_region
        regions = [
            (1, '北京', '华北', '中国'),
            (2, '上海', '华东', '中国'),
            (3, '广东', '华南', '中国'),
            (4, '浙江', '华东', '中国'),
            (5, '四川', '西南', '中国'),
            (6, '湖北', '华中', '中国'),
            (7, '山东', '华东', '中国'),
            (8, '福建', '华南', '中国'),
        ]
        for r in regions:
            await conn.execute(text(
                "INSERT INTO dim_region (region_id, province, region_name, country) VALUES (:a,:b,:c,:d)"
            ), {"a": r[0], "b": r[1], "c": r[2], "d": r[3]})

        # dim_customer
        customers = [
            (1, '张三', '男', '金牌会员'),
            (2, '李四', '女', '银牌会员'),
            (3, '王五', '男', '普通会员'),
            (4, '赵六', '女', '金牌会员'),
            (5, '孙七', '男', '银牌会员'),
            (6, '周八', '女', '普通会员'),
            (7, '吴九', '男', '金牌会员'),
            (8, '郑十', '女', '普通会员'),
        ]
        for c in customers:
            await conn.execute(text(
                "INSERT INTO dim_customer (customer_id, customer_name, gender, member_level) VALUES (:a,:b,:c,:d)"
            ), {"a": c[0], "b": c[1], "c": c[2], "d": c[3]})

        # dim_product
        products = [
            (1, 'iPhone 15 Pro', '手机', '苹果'),
            (2, 'Mate 60 Pro', '手机', '华为'),
            (3, 'MacBook Air M3', '笔记本', '苹果'),
            (4, 'ThinkPad X1 Carbon', '笔记本', '联想'),
            (5, 'AirPods Pro 2', '耳机', '苹果'),
            (6, '小米14 Ultra', '手机', '小米'),
            (7, 'iPad Air', '平板', '苹果'),
            (8, 'FreeBuds Pro 3', '耳机', '华为'),
        ]
        for p in products:
            await conn.execute(text(
                "INSERT INTO dim_product (product_id, product_name, category, brand) VALUES (:a,:b,:c,:d)"
            ), {"a": p[0], "b": p[1], "c": p[2], "d": p[3]})

        # dim_date (2025年1月~12月)
        dates = []
        date_id = 20250101
        for m in range(1, 13):
            for d in range(1, 29):  # 每月28天，简化
                quarter = (m - 1) // 3 + 1
                dates.append((date_id, 2025, quarter, m, d))
                date_id += 1
        for dt in dates:
            await conn.execute(text(
                "INSERT INTO dim_date (date_id, year, quarter, month, day) VALUES (:a,:b,:c,:d,:e)"
            ), {"a": dt[0], "b": dt[1], "c": dt[2], "d": dt[3], "e": dt[4]})

        # fact_order — 生成 50 条订单
        import random
        random.seed(42)
        orders = []
        for i in range(1, 51):
            orders.append((
                i,
                random.choice(customers)[0],
                random.choice(products)[0],
                random.choice(dates)[0],
                random.choice(regions)[0],
                random.randint(1, 10),
                round(random.uniform(99, 9999), 2),
            ))
        for o in orders:
            await conn.execute(text(
                "INSERT INTO fact_order (order_id, customer_id, product_id, date_id, region_id, order_quantity, order_amount) "
                "VALUES (:a,:b,:c,:d,:e,:f,:g)"
            ), {"a": o[0], "b": o[1], "c": o[2], "d": o[3], "e": o[4], "f": o[5], "g": o[6]})

        print("[OK]测试数据插入完成")

    # 验证
    async with engine.begin() as conn:
        for table in ['dim_region', 'dim_customer', 'dim_product', 'dim_date', 'fact_order']:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  {table}: {count} 行")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_dw_data())
