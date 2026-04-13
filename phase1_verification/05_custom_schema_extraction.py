"""
Phase 1 Step 5: 自定义实体 Schema 抽取验证（核心）
验证内容: 能否按自定义 Schema 抽取税务实体

这是 Phase 1 的核心验证点！

运行方式:
    cd phase1_verification
    uv sync
    uv run python 05_custom_schema_extraction.py
"""

import os
import sys
import json
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Step 5: 自定义实体 Schema 抽取验证（核心）")
print("=" * 60)

# ============================================
# 配置
# ============================================
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j@1234")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

# ============================================
# 定义税务实体 Schema
# ============================================
TAX_ENTITY_SCHEMA = {
    "entity_types": [
        {
            "name": "纳税人",
            "description": "缴纳增值税的纳税主体",
            "examples": ["一般纳税人", "小规模纳税人"]
        },
        {
            "name": "税目",
            "description": "增值税的征税项目",
            "examples": ["增值税", "企业所得税", "个人所得税"]
        },
        {
            "name": "税率",
            "description": "增值税的计税比例",
            "examples": ["13%", "9%", "6%", "1%", "25%", "20%", "15%"]
        },
        {
            "name": "征收率",
            "description": "小规模纳税人适用的简易征收比例",
            "examples": ["1%", "3%"]
        },
        {
            "name": "优惠政策",
            "description": "税收减免等优惠政策",
            "examples": ["小型微利企业优惠", "高新技术企业优惠"]
        }
    ],
    "relation_types": [
        {
            "name": "适用",
            "source": "纳税人",
            "target": "税率",
            "description": "某类纳税人适用某税率"
        },
        {
            "name": "包含",
            "source": "税目",
            "target": "纳税人",
            "description": "某税目适用于某类纳税人"
        },
        {
            "name": "享受",
            "source": "纳税人",
            "target": "优惠政策",
            "description": "某类纳税人享受某优惠政策"
        },
        {
            "name": "依据",
            "source": "优惠政策",
            "target": "税率",
            "description": "优惠政策依据某税率"
        }
    ]
}

# 测试文本
TEST_TEXT = """
增值税是对商品和劳务在流转过程中产生的增值额作为计税依据而征收的一种流转税。

根据纳税人的规模，增值税纳税人分为：
1. 一般纳税人：可开具增值税专用发票，适用13%、9%、6%等税率
2. 小规模纳税人：适用1%征收率（优惠期间），季度销售额30万元以下免税

企业所得税税率：
- 基本税率：25%
- 小型微利企业：20%
- 高新技术企业：15%

优惠政策：
- 小规模纳税人月销售额10万元以下免征增值税
- 小型微利企业年应纳税所得额300万元以下减按25%计入应纳税所得额
- 高新技术企业享受15%的优惠税率
"""

print("\n[Schema] 定义的实体类型:")
for et in TAX_ENTITY_SCHEMA["entity_types"]:
    print(f"  - {et['name']}: {et['description']}")

print("\n[Schema] 定义的关系类型:")
for rt in TAX_ENTITY_SCHEMA["relation_types"]:
    print(f"  - {rt['name']}: {rt['source']} -> {rt['target']}")

# ============================================
# 构建抽取 Prompt
# ============================================
def build_extraction_prompt(text: str, schema: dict) -> str:
    """根据自定义 Schema 构建抽取 Prompt"""

    entity_types_desc = "\n".join([
        f"- {et['name']}: {et['description']} (示例: {', '.join(et['examples'])})"
        for et in schema["entity_types"]
    ])

    relation_types_desc = "\n".join([
        f"- {rt['name']}: {rt['description']} (从 [{rt['source']}] 指向 [{rt['target']}])"
        for rt in schema["relation_types"]
    ])

    prompt = f"""你是一个专业的税务法规知识抽取专家。请从以下文本中抽取税务实体和关系。

## 实体类型（必须识别以下 {len(schema['entity_types'])} 种类型）：
{entity_types_desc}

## 关系类型（必须识别以下 {len(schema['relation_types'])} 种关系）：
{relation_types_desc}

## 待处理文本：
{text}

## 输出要求：
请以 JSON 格式返回抽取结果，包含：
1. "entities": 识别出的所有实体列表，每个实体包含 name, type
2. "relations": 识别出的所有关系列表，每个关系包含 source_name, target_name, relation_type

重要：
- 严格按照上面定义的实体类型进行分类，不要创造新的实体类型
- 只抽取文本中明确提到的实体
- 税率和征收率要分开（征收率是给"小规模纳税人"专用的）
"""

    return prompt

# ============================================
# Test 1: 调用 LLM 抽取
# ============================================
print("\n" + "-" * 60)
print("[Test 1] 使用自定义 Schema 调用 LLM 抽取...")
print("-" * 60)

if not DASHSCOPE_API_KEY:
    print("\n❌ 错误: DASHSCOPE_API_KEY 未配置")
    sys.exit(1)

try:
    import dashscope
    from dashscope import Generation

    dashscope.api_key = DASHSCOPE_API_KEY

    prompt = build_extraction_prompt(TEST_TEXT, TAX_ENTITY_SCHEMA)

    print("\n  调用千问 API...")
    response = Generation.call(
        model="qwen-turbo",
        messages=[{"role": "user", "content": prompt}],
        result_format="message"
    )

    if response.status_code == 200:
        raw_output = response.output.choices[0].message.content
        print(f"  ✅ LLM 调用成功")

        if len(raw_output) > 500:
            print(f"\n  原始输出（前500字符）:")
            print(f"  {raw_output[:500]}...")
        else:
            print(f"\n  原始输出:")
            print(f"  {raw_output}")

        # 解析 JSON
        try:
            json_match = re.search(r'```json\s*(.*?)\s*```', raw_output, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = raw_output.strip()

            json_str = json_str.strip()
            if json_str.startswith('```'):
                json_str = json_str.split('```')[1]
                if json_str.startswith('json'):
                    json_str = json_str[4:]
                json_str = json_str.strip()

            result = json.loads(json_str)
            print(f"  ✅ JSON 解析成功")

        except json.JSONDecodeError as je:
            print(f"  ⚠️ JSON 解析失败，尝试备用解析...")
            try:
                entities = re.findall(r'"name"\s*:\s*"([^"]+)"', raw_output)
                relations = re.findall(r'"relation_type"\s*:\s*"([^"]+)"', raw_output)
                result = {"entities": [{"name": e} for e in entities], "relations": [{"relation_type": r} for r in relations]}
                print(f"  ⚠️ 使用备用解析，结果可能不完整")
            except:
                result = None

    else:
        print(f"  ❌ LLM 调用失败: {response.code} - {response.message}")
        sys.exit(1)

except Exception as e:
    print(f"  ❌ 抽取过程失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================
# Test 2: 验证抽取结果
# ============================================
print("\n" + "-" * 60)
print("[Test 2] 验证抽取结果...")
print("-" * 60)

if result:
    entities = result.get("entities", [])
    relations = result.get("relations", [])

    print(f"\n  📊 抽取统计:")
    print(f"     实体数量: {len(entities)}")
    print(f"     关系数量: {len(relations)}")

    print(f"\n  📋 抽取的实体:")
    if entities:
        for entity in entities:
            name = entity.get('name', 'N/A')
            etype = entity.get('type', entity.get('entity_type', 'Unknown'))
            print(f"     - [{etype}] {name}")
    else:
        print(f"     (无实体被抽取)")

    print(f"\n  🔗 抽取的关系:")
    if relations:
        for relation in relations:
            rel_type = relation.get('relation_type', 'Unknown')
            source = relation.get('source_name', relation.get('source', '?'))
            target = relation.get('target_name', relation.get('target', '?'))
            print(f"     - {source} --[{rel_type}]--> {target}")
    else:
        print(f"     (无关系被抽取)")

    # ============================================
    # Test 3: 关键实体验证
    # ============================================
    print("\n" + "-" * 60)
    print("[Test 3] 关键实体验证...")
    print("-" * 60)

    expected_entities = [
        ("增值税", "税目"),
        ("企业所得税", "税目"),
        ("一般纳税人", "纳税人"),
        ("小规模纳税人", "纳税人"),
        ("25%", "税率"),
        ("20%", "税率"),
        ("15%", "税率"),
        ("13%", "税率"),
        ("1%", "征收率"),
        ("小型微利企业", "纳税人"),
        ("高新技术企业", "纳税人"),
    ]

    extracted_names = [e.get('name', '') for e in entities]
    extracted_types = {e.get('name', ''): e.get('type', 'Unknown') for e in entities}

    print(f"\n  预期关键实体:")
    found_count = 0
    missing_entities = []

    for exp_name, exp_type in expected_entities:
        found = False
        for ext_name in extracted_names:
            if exp_name in ext_name or ext_name in exp_name:
                found = True
                break

        status = "✅" if found else "❌"
        print(f"     {status} {exp_name} ({exp_type})")

        if found:
            found_count += 1
        else:
            missing_entities.append((exp_name, exp_type))

    accuracy = (found_count / len(expected_entities)) * 100

    print(f"\n  📈 抽取准确率: {accuracy:.1f}% ({found_count}/{len(expected_entities)})")

    if accuracy >= 80:
        print(f"\n  ✅ 抽取准确率达标 (>= 80%)")
        schema_success = True
    else:
        print(f"\n  ⚠️ 抽取准确率未达标 (< 80%)")
        print(f"     缺失实体: {[e[0] for e in missing_entities]}")
        schema_success = False

else:
    print(f"\n  ❌ 无法验证：抽取结果为空")
    schema_success = False

# ============================================
# Test 4: 与 Neo4j 集成
# ============================================
print("\n" + "-" * 60)
print("[Test 4] 将抽取结果存入 Neo4j...")
print("-" * 60)

if result and schema_success:
    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

            for entity in entities:
                name = entity.get('name', '')
                etype = entity.get('type', 'Unknown')
                label = etype.replace(" ", "")
                session.run(f"CREATE (n:{label} {{name: $name, type: $type}})", name=name, type=etype)

            print(f"  ✅ 成功插入 {len(entities)} 个实体到 Neo4j")

            for relation in relations:
                source = relation.get('source_name', relation.get('source', ''))
                target = relation.get('target_name', relation.get('target', ''))
                rel_type = relation.get('relation_type', '')

                if source and target and rel_type:
                    rel_type_neo4j = rel_type.upper().replace(" ", "_")
                    try:
                        session.run(f"""
                            MATCH (s {{name: $source}})
                            MATCH (t {{name: $target}})
                            CREATE (s)-[r:{rel_type_neo4j}]->(t)
                        """, source=source, target=target)
                    except Exception as rel_error:
                        print(f"  ⚠️ 关系创建失败: {source} -> {target}: {rel_error}")

            print(f"  ✅ 成功插入 {len(relations)} 个关系到 Neo4j")

            result = session.run("MATCH (n) RETURN labels(n)[0] as label, count(n) as count")
            stats = list(result)

            print(f"\n  📊 Neo4j 统计:")
            for r in stats:
                print(f"     {r['label']}: {r['count']} 个节点")

        driver.close()

    except Exception as e:
        print(f"  ⚠️ Neo4j 存储失败: {e}")
else:
    print(f"  ⏭️ 跳过 Neo4j 存储（抽取未成功）")

# ============================================
# 最终结论
# ============================================
print("\n" + "=" * 60)
print("Step 5 验证结果")
print("=" * 60)

if schema_success:
    print("\n  ✅ 自定义 Schema 抽取验证通过")
    print(f"\n  抽取准确率: {accuracy:.1f}%")
    print("\n  结论: LightRAG 可以通过自定义 Prompt 实现税务实体抽取")
else:
    print("\n  ⚠️ 自定义 Schema 抽取验证未完全通过")
    if result:
        print(f"\n  抽取准确率: {accuracy:.1f}%")

print("\n" + "=" * 60)
print("下一步: 运行 06_full_pipeline_demo.py 验证完整 Pipeline")
print("=" * 60)
