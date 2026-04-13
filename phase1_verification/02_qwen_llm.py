"""
Phase 1 Step 2: 阿里云千问 API 验证
验证内容: 能否正常调用千问大模型

运行方式:
    cd phase1_verification
    python 02_qwen_llm.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Step 2: 阿里云千问 API 验证")
print("=" * 60)

# 检查 API Key
api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key or api_key == "your-api-key-here":
    print("\n❌ 错误: DASHSCOPE_API_KEY 未配置")
    print("\n请编辑 .env 文件，设置你的阿里云千问 API Key:")
    print("   DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx")
    print("\n获取 API Key: https://dashscope.console.aliyun.com/apiKey")
    sys.exit(1)

# Test: 千问 API 调用
print("\n[Test 1] 调用千问 API (qwen-turbo)...")
try:
    import dashscope
    from dashscope import Generation

    dashscope.api_key = api_key

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
        print(f"  ✅ 回复: {answer}")
    else:
        print(f"  ❌ API 调用失败")
        print(f"     错误码: {response.code}")
        print(f"     错误信息: {response.message}")
        sys.exit(1)

except Exception as e:
    print(f"  ❌ 调用失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: 测试更长上下文
print("\n[Test 2] 测试税务场景对话...")
try:
    from dashscope import Generation

    response = Generation.call(
        model="qwen-turbo",
        messages=[
            {"role": "system", "content": "你是一个专业的税务顾问。"},
            {"role": "user", "content": "小规模纳税人和一般纳税人的主要区别是什么？"}
        ],
        result_format="message"
    )

    if response.status_code == 200:
        answer = response.output.choices[0].message.content
        print(f"  ✅ 税务场景对话成功")
        print(f"  ✅ 回复: {answer[:200]}..." if len(answer) > 200 else f"  ✅ 回复: {answer}")
    else:
        print(f"  ⚠️ 税务对话失败: {response.message}")

except Exception as e:
    print(f"  ⚠️ 税务对话测试: {e}")

# Test 3: 测试 qwen-plus (更高精度模型)
print("\n[Test 3] 测试 qwen-plus 模型...")
try:
    from dashscope import Generation

    response = Generation.call(
        model="qwen-plus",
        messages=[
            {"role": "user", "content": "企业所得想税税率是多少？"}
        ],
        result_format="message",
        temperature=0.1
    )

    if response.status_code == 200:
        answer = response.output.choices[0].message.content
        print(f"  ✅ qwen-plus 调用成功")
        print(f"  ✅ 回复: {answer[:200]}..." if len(answer) > 200 else f"  ✅ 回复: {answer}")
    else:
        print(f"  ⚠️ qwen-plus 调用失败: {response.message}")
        print(f"     (qwen-plus 是付费模型，失败是正常的)")

except Exception as e:
    print(f"  ⚠️ qwen-plus 测试: {e}")

print("\n" + "=" * 60)
print("Step 2 验证结果: ✅ 通过")
print("=" * 60)
print("\n说明: 千问 API 可正常调用")
print("下一步: 运行 03_neo4j_basic.py 验证 Neo4j 连接")
