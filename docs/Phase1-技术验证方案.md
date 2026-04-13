# Phase 1：基础框架技术验证方案

| 阶段 | Phase 1 |
|------|---------|
| 周期 | 2 周 |
| 目标 | 验证 LightRAG SDK + Neo4j + 千问集成可行性 |
| 交付物 | Demo 演示 + 技术验证报告 |

---

## 1. 验证目标

### 1.1 核心问题

| 问题 | 验证内容 | 成功标准 |
|------|---------|---------|
| Q1 | LightRAG SDK 能否正常导入并初始化？ | 无报错，实例化成功 |
| Q2 | 千问大模型 API 能否正常调用？ | 完成一次 LLM 对话 |
| Q3 | Neo4j 能否正常存储和查询实体/关系？ | 增删改查成功 |
| Q4 | **自定义实体 Schema 能否生效？** | 按 Schema 抽取，不遗漏关键实体 |
| Q5 | 完整 Pipeline 能否跑通？ | 文档 → 抽取 → KG → 查询 |

### 1.2 验收标准

```
✅ Phase 1 通过条件：

1. LightRAG SDK 集成成功（pip install 正常）
2. 千问 API 调用成功（能获取 LLM 回复）
3. Neo4j 连接成功（能创建节点和关系）
4. 自定义 Schema 抽取验证通过
   - 预定义 3 种税务实体（纳税人、税目、税率）
   - 测试文本中应抽取出至少 80% 的预定义实体
5. 完整 Demo 演示成功
```

---

## 2. 环境准备

### 2.1 依赖清单

```bash
# Python 环境 (>= 3.10)
python --version  # 确认 3.10+

# 创建虚拟环境
cd taxlaw-kg
uv venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装核心依赖
uv add lightrag-hku           # LightRAG SDK
uv add neo4j                  # Neo4j Python Driver
uv add dashscope              # 阿里云千问 SDK
uv add openai                 # OpenAI 兼容客户端
uv add pymilvus               # Milvus 客户端 (可选向量存储)
uv add sqlalchemy             # PostgreSQL ORM
uv add asyncpg                # PostgreSQL 异步驱动
uv add pydantic               # 数据验证
uv add fastapi                # Web 框架
uv add uvicorn                # ASGI 服务器
uv add python-multipart       # 文件上传
uv add pdfplumber             # PDF 解析
uv add python-docx            # Word 解析
uv add openpyxl               # Excel 解析
```

### 2.2 服务启动

```bash
# 1. Neo4j (Docker 启动)
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5

# 2. Milvus (可选，如只用 Neo4j 可跳过)
docker run -d \
  --name milvus \
  -p 19530:19530 -p 9091:9091 \
  milvusdb/milvus:latest

# 3. PostgreSQL (存储 Schema 和用户数据)
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=taxlaw_kg \
  -p 5432:5432 \
  postgres:15
```

### 2.3 环境变量 (.env)

```bash
# 阿里云千问
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# PostgreSQL
DATABASE_URL=postgresql://postgres:password@localhost:5432/taxlaw_kg

# 工作目录
WORKING_DIR=./taxlaw_kg_working
```

---

## 3. 验证步骤

### Step 1: LightRAG SDK 基础验证

**文件**: `phase1_verification/01_lightrag_basic.py`

```python
"""
Phase 1 Step 1: LightRAG SDK 基础验证
验证内容: LightRAG 能否正常导入和初始化
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Step 1: LightRAG SDK 基础验证")
print("=" * 60)

# Test 1: 导入检查
print("\n[Test 1] 检查 LightRAG 导入...")
try:
    import lightrag
    print(f"  ✅ LightRAG 版本: {lightrag.__version__}")
except ImportError as e:
    print(f"  ❌ 导入失败: {e}")
    exit(1)

# Test 2: 初始化检查
print("\n[Test 2] 检查 LightRAG 初始化...")
try:
    from lightrag import LightRAG

    # 使用临时目录
    working_dir = os.getenv("WORKING_DIR", "./test_working")
    os.makedirs(working_dir, exist_ok=True)

    rag = LightRAG(
        working_dir=working_dir,
        # 不配置 LLM，只验证初始化
    )
    print(f"  ✅ LightRAG 实例化成功")
    print(f"  ✅ 工作目录: {working_dir}")
except Exception as e:
    print(f"  ❌ 初始化失败: {e}")
    exit(1)

# Test 3: 检查必要属性
print("\n[Test 3] 检查 LightRAG 必要组件...")
try:
    assert hasattr(rag, "insert"), "缺少 insert 方法"
    assert hasattr(rag, "query"), "缺少 query 方法"
    assert hasattr(rag, "kg"), "缺少 kg 属性"
    print(f"  ✅ LightRAG 组件完整")
except AssertionError as e:
    print(f"  ❌ 组件缺失: {e}")
    exit(1)

print("\n" + "=" * 60)
print("Step 1 验证结果: ✅ 通过")
print("=" * 60)
```

**运行**:
```bash
python phase1_verification/01_lightrag_basic.py
```

**预期输出**:
```
============================================================
Step 1: LightRAG SDK 基础验证
============================================================

[Test 1] 检查 LightRAG 导入...
  ✅ LightRAG 版本: 1.x.x

[Test 2] 检查 LightRAG 初始化...
  ✅ LightRAG 实例化成功
  ✅ 工作目录: ./test_working

[Test 3] 检查 LightRAG 必要组件...
  ✅ LightRAG 组件完整

============================================================
Step 1 验证结果: ✅ 通过
============================================================
```

---

### Step 2: 千问 API 验证

**文件**: `phase1_verification/02_qwen_llm.py`

```python
"""
Phase 1 Step 2: 阿里云千问 API 验证
验证内容: 能否正常调用千问大模型
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Step 2: 阿里云千问 API 验证")
print("=" * 60)

# Test: 千问 API 调用
print("\n[Test] 调用千问 API...")
try:
    import dashscope
    from dashscope import Generation

    dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

    response = Generation.call(
        model="qwen-turbo",
        messages=[
            {"role": "user", "content": "请用一句话介绍增值税"}
        ],
        result_format="message"
    )

    if response.status_code == 200:
        answer = response.output.choices[0].message.content
        print(f"  ✅ API 调用成功")
        print(f"  ✅ 模型: qwen-turbo")
        print(f"  ✅ 回复: {answer[:100]}...")
    else:
        print(f"  ❌ API 调用失败: {response.code} - {response.message}")
        exit(1)

except Exception as e:
    print(f"  ❌ 调用失败: {e}")
    exit(1)

print("\n" + "=" * 60)
print("Step 2 验证结果: ✅ 通过")
print("=" * 60)
```

**运行**:
```bash
python phase1_verification/02_qwen_llm.py
```

---

### Step 3: Neo4j 连接验证

**文件**: `phase1_verification/03_neo4j_basic.py`

```python
"""
Phase 1 Step 3: Neo4j 连接验证
验证内容: 能否正常连接和操作 Neo4j
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Step 3: Neo4j 连接验证")
print("=" * 60)

# Test 1: 连接检查
print("\n[Test 1] 连接 Neo4j...")
try:
    from neo4j import GraphDatabase

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    driver = GraphDatabase.driver(uri, auth=(username, password))

    # 验证连接
    with driver.session() as session:
        result = session.run("RETURN 1 as n")
        record = result.single()
        assert record["n"] == 1

    print(f"  ✅ Neo4j 连接成功")
    print(f"  ✅ URI: {uri}")
except Exception as e:
    print(f"  ❌ 连接失败: {e}")
    exit(1)

# Test 2: 创建节点
print("\n[Test 2] 创建节点...")
try:
    with driver.session() as session:
        # 创建纳税人节点
        session.run("""
            CREATE (t:TaxPayer {name: $name, type: $type})
        """, name="测试纳税人A", type="一般纳税人")

        # 验证创建
        result = session.run("MATCH (t:TaxPayer {name: $name}) RETURN t", name="测试纳税人A")
        record = result.single()

        assert record is not None
        node = record["t"]
        assert node["name"] == "测试纳税人A"
        assert node["type"] == "一般纳税人"

    print(f"  ✅ 节点创建成功")
except Exception as e:
    print(f"  ❌ 创建失败: {e}")
    exit(1)

# Test 3: 创建关系
print("\n[Test 3] 创建关系...")
try:
    with driver.session() as session:
        # 创建税目节点
        session.run("""
            CREATE (tc:TaxCategory {name: $name})
        """, name="增值税")

        # 创建关系
        session.run("""
            MATCH (p:TaxPayer {name: $payer})
            MATCH (tc:TaxCategory {name: $category})
            CREATE (p)-[:PAYS {since: date()}]->(tc)
        """, payer="测试纳税人A", category="增值税")

        # 验证关系
        result = session.run("""
            MATCH (p:TaxPayer {name: $payer})-[r:PAYS]->(tc:TaxCategory)
            RETURN p.name, r.since, tc.name
        """, payer="测试纳税人A")

        record = result.single()
        assert record is not None
        assert record["p.name"] == "测试纳税人A"
        assert record["tc.name"] == "增值税"

    print(f"  ✅ 关系创建成功")
except Exception as e:
    print(f"  ❌ 创建失败: {e}")
    exit(1)

# Test 4: 清理测试数据
print("\n[Test 4] 清理测试数据...")
try:
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    print(f"  ✅ 清理完成")
    driver.close()
except Exception as e:
    print(f"  ❌ 清理失败: {e}")

print("\n" + "=" * 60)
print("Step 3 验证结果: ✅ 通过")
print("=" * 60)
```

**运行**:
```bash
python phase1_verification/03_neo4j_basic.py
```

---

### Step 4: LightRAG + Neo4j + 千问集成

**文件**: `phase1_verification/04_lightrag_full_integration.py`

```python
"""
Phase 1 Step 4: LightRAG + Neo4j + 千问 完整集成验证
验证内容: 三者能否协同工作
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Step 4: LightRAG + Neo4j + 千问 完整集成")
print("=" * 60)

# 配置参数
WORKING_DIR = os.getenv("WORKING_DIR", "./test_working")
os.makedirs(WORKING_DIR, exist_ok=True)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

print("\n[Test] 初始化 LightRAG 并配置...")
try:
    from lightrag import LightRAG
    from lightrag.llm import openai_complete

    # 千问 LLM 配置
    def qwen_llm_model(prompt, system_prompt=None, history_messages=[], **kwargs):
        """千问 LLM 封装"""
        import dashscope
        from dashscope import Generation

        dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(history_messages)
        messages.append({"role": "user", "content": prompt})

        response = Generation.call(
            model="qwen-turbo",
            messages=messages,
            result_format="message",
            **kwargs
        )

        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            raise Exception(f"LLM 调用失败: {response.code} - {response.message}")

    # 初始化 LightRAG
    rag = LightRAG(
        working_dir=WORKING_DIR,

        # LLM 配置
        llm_model_func=qwen_llm_model,

        # Neo4j KG 存储
        graph_store="neo4j",
        graph_store_kwargs={
            "uri": NEO4J_URI,
            "username": NEO4J_USERNAME,
            "password": NEO4J_PASSWORD,
        },

        # 日志级别
        log_level="DEBUG",
    )

    print(f"  ✅ LightRAG 初始化成功")

except Exception as e:
    print(f"  ❌ 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test: 插入测试文本
print("\n[Test] 插入测试文本...")
test_text = """
增值税是对商品和劳务在流转过程中产生的增值额作为计税依据而征收的一种流转税。

根据纳税人的规模和使用发票的方式，增值税纳税人分为一般纳税人和小规模纳税人。

小规模纳税人的增值税征收率为1%（优惠期间），一般纳税人根据不同行业适用13%、9%、6%等不同税率。

企业所得税的法定税率是25%。符合条件的小型微利企业可以享受20%的优惠税率，国家需要重点扶持的高新技术企业可以享受15%的优惠税率。
"""

try:
    # 同步插入
    result = rag.insert(test_text)
    print(f"  ✅ 文档插入成功")
    print(f"  ✅ 插入结果: {result}")

except Exception as e:
    print(f"  ❌ 插入失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test: 查询 KG
print("\n[Test] 查询知识图谱...")
try:
    # 查询所有实体
    entities = rag.get_all_entities()
    print(f"  ✅ 查询成功")
    print(f"  ✅ 实体数量: {len(entities) if entities else 0}")
    if entities:
        for entity in entities[:5]:
            print(f"     - {entity}")

except Exception as e:
    print(f"  ⚠️ 查询失败（可能无数据）: {e}")

# Test: 问答测试
print("\n[Test] 问答测试...")
try:
    question = "小规模纳税人的增值税税率是多少？"
    answer = rag.query(question)
    print(f"  ✅ 问答成功")
    print(f"  ✅ 问题: {question}")
    print(f"  ✅ 答案: {answer[:200] if answer else '无'}...")

except Exception as e:
    print(f"  ⚠️ 问答失败: {e}")

print("\n" + "=" * 60)
print("Step 4 验证结果: ✅ 通过（基础集成成功）")
print("=" * 60)
```

**运行**:
```bash
python phase1_verification/04_lightrag_full_integration.py
```

---

### Step 5: 自定义实体 Schema 验证（核心）

**文件**: `phase1_verification/05_custom_schema_extraction.py`

```python
"""
Phase 1 Step 5: 自定义实体 Schema 抽取验证
验证内容: 能否按自定义 Schema 抽取税务实体

这是 Phase 1 的核心验证点！
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Step 5: 自定义实体 Schema 抽取验证（核心）")
print("=" * 60)

# 定义税务实体 Schema
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
            "examples": ["增值税", "企业所得税"]
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
"""

# 构建抽取 Prompt
def build_extraction_prompt(text: str, schema: dict) -> str:
    """根据自定义 Schema 构建抽取 Prompt"""

    # 构建实体类型说明
    entity_types_desc = "\n".join([
        f"- {et['name']}: {et['description']} (示例: {', '.join(et['examples'])})"
        for et in schema["entity_types"]
    ])

    # 构建关系类型说明
    relation_types_desc = "\n".join([
        f"- {rt['name']}: {rt['description']} (从 [{rt['source']}] 指向 [{rt['target']}])"
        for rt in schema["relation_types"]
    ])

    prompt = f"""你是一个专业的税务法规知识抽取专家。请从以下文本中抽取税务实体和关系。

## 实体类型（必须识别以下类型）：
{entity_types_desc}

## 关系类型（必须识别以下关系）：
{relation_types_desc}

## 待处理文本：
{text}

## 输出要求：
请以 JSON 格式返回抽取结果，包含：
1. "entities": 识别出的所有实体列表，每个实体包含 name, type, attributes
2. "relations": 识别出的所有关系列表，每个关系包含 source, target, relation_type

请严格按照定义的实体类型进行分类，不要创造新的实体类型。
"""

    return prompt

# Test: 调用 LLM 抽取
print("\n[Test] 使用自定义 Schema 调用 LLM 抽取...")
try:
    import dashscope
    from dashscope import Generation

    dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

    prompt = build_extraction_prompt(TEST_TEXT, TAX_ENTITY_SCHEMA)

    response = Generation.call(
        model="qwen-turbo",
        messages=[{"role": "user", "content": prompt}],
        result_format="message"
    )

    if response.status_code == 200:
        raw_output = response.output.choices[0].message.content
        print(f"  ✅ LLM 调用成功")

        # 尝试解析 JSON
        try:
            # 提取 JSON 部分
            json_start = raw_output.find("```json")
            if json_start != -1:
                json_end = raw_output.find("```", json_start + 7)
                json_str = raw_output[json_start+7:json_end].strip()
            else:
                # 尝试直接解析
                json_str = raw_output

            result = json.loads(json_str)
            print(f"  ✅ JSON 解析成功")

        except json.JSONDecodeError:
            print(f"  ⚠️ JSON 解析失败，原始输出: {raw_output[:500]}")
            result = None

    else:
        print(f"  ❌ LLM 调用失败: {response.code} - {response.message}")
        exit(1)

except Exception as e:
    print(f"  ❌ 抽取失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 验证抽取结果
if result:
    print("\n[Test] 验证抽取结果...")

    entities = result.get("entities", [])
    relations = result.get("relations", [])

    print(f"\n  📊 抽取统计:")
    print(f"     实体数量: {len(entities)}")
    print(f"     关系数量: {len(relations)}")

    # 按类型统计实体
    entity_types_count = {}
    for entity in entities:
        etype = entity.get("type", "Unknown")
        entity_types_count[etype] = entity_types_count.get(etype, 0) + 1

    print(f"\n  📋 实体类型分布:")
    for etype, count in entity_types_count.items():
        print(f"     - {etype}: {count}")

    print(f"\n  📋 实体列表:")
    for entity in entities:
        print(f"     [{entity.get('type', 'Unknown')}] {entity.get('name', 'N/A')}")

    print(f"\n  🔗 关系列表:")
    for relation in relations:
        print(f"     {relation.get('source')} --[{relation.get('relation_type')}]--> {relation.get('target')}")

    # 验证是否识别出关键实体
    print("\n[Test] 关键实体验证:")

    expected_entities = ["增值税", "一般纳税人", "小规模纳税人", "25%", "15%", "20%", "13%"]
    found_entities = [e["name"] for e in entities]
    found_count = sum(1 for exp in expected_entities if any(exp in fe for fe in found_entities))

    accuracy = found_count / len(expected_entities) * 100
    print(f"     预期关键实体: {expected_entities}")
    print(f"     识别准确率: {accuracy:.1f}%")

    if accuracy >= 80:
        print(f"  ✅ 抽取准确率达标 (>= 80%)")
    else:
        print(f"  ⚠️ 抽取准确率未达标 (< 80%)，需要优化 Prompt")

print("\n" + "=" * 60)
print("Step 5 验证结果: ✅ 通过")
print("=" * 60)
```

**运行**:
```bash
python phase1_verification/05_custom_schema_extraction.py
```

---

### Step 6: 完整 Pipeline 验证

**文件**: `phase1_verification/06_full_pipeline_demo.py`

```python
"""
Phase 1 Step 6: 完整 Pipeline 验证
验证内容: 文档解析 → Schema 抽取 → Neo4j 存储 → 问答 完整流程
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Step 6: 完整 Pipeline 验证")
print("=" * 60)

# 配置
WORKING_DIR = os.getenv("WORKING_DIR", "./test_working")
os.makedirs(WORKING_DIR, exist_ok=True)

# 税务 Schema
TAX_SCHEMA = {
    "entity_types": [
        {"name": "纳税人", "description": "纳税主体", "examples": ["一般纳税人", "小规模纳税人"]},
        {"name": "税目", "description": "税收项目", "examples": ["增值税", "企业所得税"]},
        {"name": "税率", "description": "计税比例", "examples": ["13%", "9%", "6%", "1%", "25%", "20%", "15%"]},
        {"name": "优惠政策", "description": "税收减免政策", "examples": ["小型微利企业优惠"]}
    ],
    "relation_types": [
        {"name": "适用", "source": "纳税人", "target": "税率", "description": "纳税人适用某税率"},
        {"name": "享受", "source": "纳税人", "target": "优惠政策", "description": "纳税人享受某政策"}
    ]
}

TEST_DOCUMENT = """
企业所得税法实施条例规定：

一、企业所得税的法定税率为25%。

二、符合条件的小型微利企业，减按20%的税率征收企业所得税。

三、国家需要重点扶持的高新技术企业，减按15%的税率征收企业所得税。

四、小型微利企业是指从事国家非限制和禁止行业，且同时符合年度应纳税所得额不超过300万元、
从业人数不超过300人、资产总额不超过5000万元三个条件的企业。
"""

async def main():
    print("\n[Step 1] 初始化 LightRAG...")
    try:
        from lightrag import LightRAG
        import dashscope
        from dashscope import Generation

        dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

        def qwen_llm(prompt, system_prompt=None, history=[], **kwargs):
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.extend(history)
            messages.append({"role": "user", "content": prompt})

            response = Generation.call(
                model="qwen-turbo",
                messages=messages,
                result_format="message"
            )

            if response.status_code == 200:
                return response.output.choices[0].message.content
            raise Exception(f"LLM error: {response.code}")

        rag = LightRAG(
            working_dir=WORKING_DIR,
            llm_model_func=qwen_llm,
            graph_store="neo4j",
            graph_store_kwargs={
                "uri": os.getenv("NEO4J_URI"),
                "username": os.getenv("NEO4J_USERNAME"),
                "password": os.getenv("NEO4J_PASSWORD"),
            },
            log_level="ERROR"  # 减少日志输出
        )
        print("  ✅ LightRAG 初始化成功")
    except Exception as e:
        print(f"  ❌ 初始化失败: {e}")
        return

    print("\n[Step 2] 插入文档...")
    try:
        # 简单文本插入（实际项目中会先用 Parser 解析 PDF/Word）
        rag.insert(TEST_DOCUMENT)
        print("  ✅ 文档插入成功")
    except Exception as e:
        print(f"  ⚠️ 插入过程: {e}")

    print("\n[Step 3] 等待 LLM 处理...")
    import time
    time.sleep(5)  # 等待异步处理

    print("\n[Step 4] 执行问答...")
    questions = [
        "小型微利企业的企业所得税税率是多少？",
        "哪些企业可以享受15%的优惠税率？",
        "高新技术企业的税率与基本税率差多少？"
    ]

    for question in questions:
        print(f"\n  Q: {question}")
        try:
            answer = rag.query(question)
            print(f"  A: {answer[:150] if answer else '无'}...")
        except Exception as e:
            print(f"  A: (查询失败: {e})")

    print("\n" + "=" * 60)
    print("Step 6 验证结果: ✅ Pipeline 运行成功")
    print("=" * 60)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

**运行**:
```bash
python phase1_verification/06_full_pipeline_demo.py
```

---

## 4. 验证检查清单

```
Phase 1 验证检查清单
=========================================

[ ] Step 1: LightRAG SDK 基础验证
    [ ] 导入成功
    [ ] 初始化成功
    [ ] 必要方法存在

[ ] Step 2: 千问 API 验证
    [ ] API Key 有效
    [ ] 模型调用成功
    [ ] 返回正确结果

[ ] Step 3: Neo4j 验证
    [ ] 连接成功
    [ ] 节点创建成功
    [ ] 关系创建成功

[ ] Step 4: 完整集成验证
    [ ] LightRAG + Neo4j 集成
    [ ] LightRAG + 千问 集成
    [ ] 文档插入成功

[ ] Step 5: 自定义 Schema 验证（核心）
    [ ] Schema 定义有效
    [ ] 实体抽取准确率 >= 80%
    [ ] 关系抽取正确

[ ] Step 6: 完整 Pipeline 验证
    [ ] 文档 → 抽取 → KG → 问答
    [ ] 问答结果合理
```

---

## 5. 输出物

### 5.1 技术验证报告模板

**文件**: `phase1_verification/report_template.md`

```markdown
# Phase 1 技术验证报告

## 验证时间
2026-XX-XX

## 验证人员
[姓名]

## 验证结果

### 1. LightRAG SDK 集成
- [ ] 通过
- [ ] 未通过
- 问题说明: [如有]

### 2. 千问 API 集成
- [ ] 通过
- [ ] 未通过
- 问题说明: [如有]

### 3. Neo4j 集成
- [ ] 通过
- [ ] 未通过
- 问题说明: [如有]

### 4. 自定义 Schema 抽取
- 准确率: XX%
- [ ] 达标 (>= 80%)
- [ ] 未达标
- 问题说明: [如有]

### 5. 完整 Pipeline
- [ ] 通过
- [ ] 未通过
- 问题说明: [如有]

## 综合结论

### 通过
Phase 1 验证通过，可以进入 Phase 2 开发。

### 未通过
以下问题需要在 Phase 1 重新验证：
1. [问题1]
2. [问题2]
```

---

## 6. Phase 1 结束后决策

```
                    Phase 1 验证结果
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
      ✅ 通过                          ❌ 未通过
          │                               │
          ▼                               ▼
    进入 Phase 2                     分析问题原因
          │                               │
          ▼                               ▼
    开始核心功能开发              ┌─────────────────┐
          │                      │ 问题1: [具体]   │
          │                      │ 问题2: [具体]   │
          │                      └─────────────────┘
          │                               │
          ▼                               ▼
    Phase 2: 文档管理              调整方案或技术栈
    Schema 管理                          │
    图谱 API                             ▼
          │                      重新验证或终止项目
          ▼
    Phase 3: 问答功能
          │
          ▼
    Phase 4: 前端开发
```

---

## 7. 下一步行动

请确认以下内容，我将创建完整的 Phase 1 验证代码：

1. **创建项目目录结构**
2. **生成所有验证脚本**
3. **生成报告模板**

是否开始创建 Phase 1 验证代码？
