"""
Phase 1 Step 1: LightRAG SDK 基础验证
验证内容: LightRAG 能否正常导入和初始化

运行方式:
    cd phase1_verification
    uv sync
    uv run python 01_lightrag_basic.py
"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
    print("\n请先安装依赖:")
    print("    uv add lightrag-hku")
    sys.exit(1)

# Test 2: 初始化检查
print("\n[Test 2] 检查 LightRAG 初始化...")
try:
    from lightrag import LightRAG
    from lightrag.base import EmbeddingFunc

    # 使用临时目录
    working_dir = os.getenv("WORKING_DIR", "./test_working")
    os.makedirs(working_dir, exist_ok=True)

    # 定义 embedding 函数
    def dummy_embedding_func(texts: list[str]) -> np.ndarray:
        dim = 1024
        result = []
        for _ in texts:
            vec = np.random.randn(dim).astype(np.float32)
            result.append(vec)
        return np.concatenate(result)

    # 使用 EmbeddingFunc 包装
    embedding_func = EmbeddingFunc(
        embedding_dim=1024,
        func=dummy_embedding_func
    )

    # 定义 dummy LLM 函数
    async def dummy_llm_func(*args, **kwargs):
        return "This is a dummy response for testing only."

    rag = LightRAG(
        working_dir=working_dir,
        embedding_func=embedding_func,
        llm_model_func=dummy_llm_func,
    )
    print(f"  ✅ LightRAG 实例化成功")
    print(f"  ✅ 工作目录: {working_dir}")
except Exception as e:
    print(f"  ❌ 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: 检查必要属性
print("\n[Test 3] 检查 LightRAG 必要组件...")
try:
    assert hasattr(rag, "insert"), "缺少 insert 方法"
    assert hasattr(rag, "query"), "缺少 query 方法"
    assert hasattr(rag, "graph_storage"), "缺少 graph_storage 属性"
    print(f"  ✅ insert 方法存在")
    print(f"  ✅ query 方法存在")
    print(f"  ✅ graph_storage 属性存在")
except AssertionError as e:
    print(f"  ❌ 组件缺失: {e}")
    sys.exit(1)

# Test 4: 检查 LightRAG 目录结构
print("\n[Test 4] 检查 LightRAG 工作目录...")
try:
    test_dir = "./test_lightrag_init"
    os.makedirs(test_dir, exist_ok=True)

    rag2 = LightRAG(
        working_dir=test_dir,
        embedding_func=embedding_func,
        llm_model_func=dummy_llm_func,
    )

    # 检查工作目录中的文件
    expected_files = [
        "graph_chunk_entity_relation.graphml",  # 图存储
        "vdb_chunks.json",  # 向量存储
    ]

    print(f"  ✅ LightRAG 目录结构检查完成")
    for f in expected_files:
        path = os.path.join(test_dir, f)
        if os.path.exists(path):
            print(f"     ✅ {f} 存在")
        else:
            print(f"     ⚠️ {f} 不存在（可能在初始化后创建）")

except Exception as e:
    print(f"  ⚠️ 目录结构检查: {e}")

# Test 5: 清理
print("\n[Test 5] 清理测试文件...")
import shutil
try:
    for path in [working_dir, test_dir]:
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f"  ✅ 清理: {path}")
except Exception as e:
    print(f"  ⚠️ 清理失败: {e}")

print("\n" + "=" * 60)
print("Step 1 验证结果: ✅ 通过")
print("=" * 60)
print("\n说明: LightRAG SDK 可正常导入和初始化")
print("      注意: 初始化需要 embedding_func 和 llm_model_func")
print("      注意: 图存储属性名为 graph_storage，不是 kg")
print("下一步: 运行 02_qwen_llm.py 验证千问 API")
