"""
Phase 1 Step 3: Neo4j 连接验证
验证内容: 能否正常连接和操作 Neo4j

运行方式:
    cd phase1_verification
    # 确保 Neo4j 已启动
    # docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5
    python 03_neo4j_basic.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Step 3: Neo4j 连接验证")
print("=" * 60)

# 检查环境变量
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "neo4j@1234")

print(f"\n[配置] Neo4j URI: {neo4j_uri}")
print(f"[配置] 用户名: {neo4j_user}")

# Test 1: 连接检查
print("\n[Test 1] 连接 Neo4j...")
try:
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    # 验证连接
    with driver.session() as session:
        result = session.run("RETURN 1 as n")
        record = result.single()
        assert record["n"] == 1

    print(f"  ✅ Neo4j 连接成功")

except Exception as e:
    print(f"  ❌ 连接失败: {e}")
    print("\n请确保 Neo4j 已启动:")
    print("  docker run -d \\")
    print("    --name neo4j \\")
    print("    -p 7474:7474 -p 7687:7687 \\")
    print("    -e NEO4J_AUTH=neo4j/password \\")
    print("    neo4j:5")
    sys.exit(1)

# Test 2: 创建节点
print("\n[Test 2] 创建纳税人节点...")
try:
    with driver.session() as session:
        # 创建纳税人节点
        session.run("""
            CREATE (t:TaxPayer {name: $name, type: $type})
        """, name="测试纳税人A", type="一般纳税人")

        # 验证创建
        result = session.run("MATCH (t:TaxPayer {name: $name}) RETURN t", name="测试纳税人A")
        record = result.single()

        assert record is not None, "节点创建失败"
        node = record["t"]
        assert node["name"] == "测试纳税人A"
        assert node["type"] == "一般纳税人"

    print(f"  ✅ 节点创建成功")
    print(f"     节点: TaxPayer, name=测试纳税人A, type=一般纳税人")

except Exception as e:
    print(f"  ❌ 创建失败: {e}")
    driver.close()
    sys.exit(1)

# Test 3: 创建税目节点
print("\n[Test 3] 创建税目节点...")
try:
    with driver.session() as session:
        session.run("""
            CREATE (tc:TaxCategory {name: $name, category: $category})
        """, name="增值税", category="流转税")

        result = session.run("MATCH (tc:TaxCategory {name: $name}) RETURN tc", name="增值税")
        record = result.single()

        assert record is not None
        print(f"  ✅ 税目节点创建成功")
        print(f"     节点: TaxCategory, name=增值税, category=流转税")

except Exception as e:
    print(f"  ❌ 创建失败: {e}")
    driver.close()
    sys.exit(1)

# Test 4: 创建关系
print("\n[Test 4] 创建关系...")
try:
    with driver.session() as session:
        # 创建关系
        session.run("""
            MATCH (p:TaxPayer {name: $payer})
            MATCH (tc:TaxCategory {name: $category})
            CREATE (p)-[r:PAYS {since: date()}]->(tc)
            RETURN p.name as payer, tc.name as category
        """, payer="测试纳税人A", category="增值税")

        # 验证关系
        result = session.run("""
            MATCH (p:TaxPayer {name: $payer})-[r:PAYS]->(tc:TaxCategory)
            RETURN p.name as payer, r.since as since, tc.name as category
        """, payer="测试纳税人A")

        record = result.single()
        assert record is not None
        assert record["payer"] == "测试纳税人A"
        assert record["category"] == "增值税"

    print(f"  ✅ 关系创建成功")
    print(f"     关系: 测试纳税人A -[:PAYS]-> 增值税")

except Exception as e:
    print(f"  ❌ 创建失败: {e}")
    driver.close()
    sys.exit(1)

# Test 5: 查询验证
print("\n[Test 5] 查询验证...")
try:
    with driver.session() as session:
        # 查询所有 TaxPayer
        result = session.run("MATCH (p:TaxPayer) RETURN p.name as name, p.type as type")
        records = list(result)

        print(f"  ✅ 查询成功")
        print(f"     TaxPayer 节点数量: {len(records)}")
        for r in records:
            print(f"       - {r['name']} ({r['type']})")

        # 查询关系
        result = session.run("MATCH (p)-[r]->(tc) RETURN p.name as payer, type(r) as rel, tc.name as category")
        records = list(result)

        print(f"     关系数量: {len(records)}")
        for r in records:
            print(f"       - {r['payer']} -[:{r['rel']}]-> {r['category']}")

except Exception as e:
    print(f"  ❌ 查询失败: {e}")
    driver.close()
    sys.exit(1)

# Test 6: 清理测试数据
print("\n[Test 6] 清理测试数据...")
try:
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        print(f"  ✅ 清理完成")
    driver.close()
except Exception as e:
    print(f"  ⚠️ 清理失败: {e}")
    print(f"     (不影响验证结果，可手动清理)")

print("\n" + "=" * 60)
print("Step 3 验证结果: ✅ 通过")
print("=" * 60)
print("\n说明: Neo4j 可正常连接和操作")
print("下一步: 运行 04_lightrag_full_integration.py 验证完整集成")
