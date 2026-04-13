# Phase 1 验证快速开始

## 前置条件

### 1. 安装 uv（如果未安装）

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 安装依赖

```bash
cd phase1_verification

# 使用 uv 安装依赖（推荐）
uv sync

# 或使用 pip（不推荐）
# pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env

# 编辑 .env 填入真实配置
nano .env  # 或使用任何文本编辑器
```

必需配置:
- `DASHSCOPE_API_KEY`: 阿里云千问 API Key
- `NEO4J_URI`: Neo4j 连接地址（默认: bolt://localhost:7687）
- `NEO4J_PASSWORD`: Neo4j 密码

### 4. 启动存储服务（如果本地没有运行）

```bash
# Neo4j
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/neo4j@1234 \
  neo4j:5

# Redis
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7

# Milvus
docker run -d \
  --name milvus \
  -p 19530:19530 -p 9091:9091 \
  milvusdb/milvus:latest
```

等待服务启动完成（约 30 秒）。

## 运行验证

按顺序运行以下 6 个验证脚本:

### Step 1: LightRAG SDK 基础验证

```bash
uv run python 01_lightrag_basic.py
```

### Step 2: 千问 API 验证

```bash
uv run python 02_qwen_llm.py
```

### Step 3: Neo4j 连接验证

```bash
uv run python 03_neo4j_basic.py
```

### Step 4: 完整集成验证

```bash
uv run python 04_lightrag_full_integration.py
```

### Step 5: 自定义 Schema 抽取验证（核心）

```bash
uv run python 05_custom_schema_extraction.py
```

这是最重要的验证！预期抽取准确率 >= 80%。

### Step 6: 完整 Pipeline 演示

```bash
uv run python 06_full_pipeline_demo.py
```

## 快速验证脚本

一键运行所有验证:

```bash
#!/bin/bash

echo "========================================"
echo "Phase 1 一键验证"
echo "========================================"

for step in 01 02 03 04 05 06; do
    echo ""
    echo ">>> 运行 Step ${step}..."
    uv run python "${step}_"*.py
    if [ $? -ne 0 ]; then
        echo "Step ${step} 失败，停止验证"
        exit 1
    fi
done

echo ""
echo "========================================"
echo "Phase 1 全部验证完成！"
echo "========================================"
```

## 常见问题

### Q1: 导入 lightrag 失败

```bash
uv add lightrag-hku
```

### Q2: Neo4j 连接失败

确保 Neo4j 已启动:
```bash
docker ps | grep neo4j
```

如果未启动:
```bash
docker start neo4j
```

### Q3: 千问 API 调用失败

检查 `.env` 中的 `DASHSCOPE_API_KEY` 是否正确。

获取 API Key: https://dashscope.console.aliyun.com/apiKey

### Q4: 抽取准确率低

Step 5 的核心验证。如果准确率 < 80%:

1. 检查 `DASHSCOPE_API_KEY` 是否有效
2. 尝试使用 `qwen-plus` 模型（修改代码中的 model 参数）
3. 优化 Prompt（增加 examples）

## 验证后

1. 填写验证报告: `REPORT_TEMPLATE.md`
2. 根据验证结果决定:
   - ✅ 通过 → 进入 Phase 2 开发
   - ❌ 未通过 → 分析问题，重新验证

## 验证通过后的下一步

参见: `../docs/Phase1-技术验证方案.md` 中的 "Phase 1 结束后决策" 部分。
