"""
LightRAG 服务
封装 LightRAG 的初始化、文档插入、实体抽取、问答功能
"""
import os
import re
import json
import asyncio
from typing import Dict, List, Any, Optional
import numpy as np
from lightrag import LightRAG
from lightrag.base import EmbeddingFunc
from app.config import get_settings

settings = get_settings()


class LightRAGService:
    """LightRAG 服务封装"""

    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = working_dir or settings.lightrag_working_dir
        os.makedirs(self.working_dir, exist_ok=True)
        self.rag: Optional[LightRAG] = None
        self._initialized = False

    async def initialize(self):
        """初始化 LightRAG 实例"""
        if self._initialized:
            return

        # 设置 LightRAG 需要的环境变量
        os.environ["REDIS_URI"] = settings.redis_url
        os.environ["NEO4J_URI"] = settings.neo4j_uri
        os.environ["NEO4J_USERNAME"] = settings.neo4j_username
        os.environ["NEO4J_PASSWORD"] = settings.neo4j_password
        os.environ["MILVUS_URI"] = settings.milvus_uri
        os.environ["MILVUS_DB_NAME"] = settings.milvus_db_name

        # 定义 embedding 函数
        async def dashscope_embedding_func(texts: list[str]) -> np.ndarray:
            from dashscope import TextEmbedding

            if not settings.dashscope_api_key:
                raise ValueError("DASHSCOPE_API_KEY not configured")

            embeddings = []
            # TextEmbedding API 需要逐个处理文本
            for text in texts:
                response = TextEmbedding.call(
                    model=settings.embedding_model,
                    input=text,
                    api_key=settings.dashscope_api_key
                )
                if response.status_code == 200:
                    embedding_list = response.output['embeddings'][0]['embedding']
                    embeddings.append(np.array(embedding_list, dtype=np.float32))
                else:
                    raise Exception(f"Embedding API failed: {response.code}")

            if len(embeddings) == 1:
                return embeddings[0]
            return np.concatenate(embeddings)

        embedding_func = EmbeddingFunc(
            embedding_dim=settings.embedding_dim,
            func=dashscope_embedding_func
        )

        # 定义 LLM 函数（使用千问）
        async def qwen_llm_func(prompt, system_prompt=None, history_messages=[], **kwargs):
            from dashscope import Generation

            if not settings.dashscope_api_key:
                raise ValueError("DASHSCOPE_API_KEY not configured")

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.extend(history_messages)
            messages.append({"role": "user", "content": prompt})

            response = Generation.call(
                model=settings.llm_model_name,
                messages=messages,
                result_format="message"
            )

            if response.status_code == 200:
                return response.output.choices[0].message.content
            else:
                raise Exception(f"LLM 调用失败: {response.code}")

        self.rag = LightRAG(
            working_dir=self.working_dir,
            llm_model_func=qwen_llm_func,
            llm_model_name=settings.llm_model_name,
            embedding_func=embedding_func,
            graph_storage="Neo4JStorage",
            kv_storage="RedisKVStorage",
            doc_status_storage="RedisDocStatusStorage",
            vector_storage="MilvusVectorDBStorage",
            log_level="ERROR"
        )

        await self.rag.initialize_storages()
        self._initialized = True

    def build_extraction_prompt(self, text: str, schema: Dict[str, Any]) -> str:
        """根据自定义 Schema 构建抽取 Prompt"""

        entity_types_desc = "\n".join([
            f"- {et['name']}: {et['description']} (示例: {', '.join(et.get('examples', []))})"
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

    async def extract_entities(
        self,
        text: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用 LLM 抽取实体和关系"""

        if not self.rag:
            await self.initialize()

        prompt = self.build_extraction_prompt(text, schema)

        # 调用 LLM
        from dashscope import Generation

        if not settings.dashscope_api_key:
            raise ValueError("DASHSCOPE_API_KEY not configured")

        response = Generation.call(
            model=settings.llm_model_name,
            messages=[{"role": "user", "content": prompt}],
            result_format="message"
        )

        if response.status_code != 200:
            raise Exception(f"LLM 调用失败: {response.code} - {response.message}")

        raw_output = response.output.choices[0].message.content

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
            return result

        except json.JSONDecodeError as e:
            # 备用解析
            entities = re.findall(r'"name"\s*:\s*"([^"]+)"', raw_output)
            relations = re.findall(r'"relation_type"\s*:\s*"([^"]+)"', raw_output)
            return {
                "entities": [{"name": e} for e in entities],
                "relations": [{"relation_type": r} for r in relations]
            }

    async def insert_document(
        self,
        text: str,
        schema: Dict[str, Any],
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """插入文档并进行实体抽取"""

        if not self.rag:
            await self.initialize()

        # 1. 抽取实体
        extraction_result = await self.extract_entities(text, schema)

        entities = extraction_result.get("entities", [])
        relations = extraction_result.get("relations", [])

        # 2. 存入 Neo4j
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password)
        )

        try:
            with driver.session() as session:
                # 插入实体
                for entity in entities:
                    name = entity.get('name', '')
                    etype = entity.get('type', 'Entity')
                    label = etype.replace(" ", "")
                    session.run(
                        f"CREATE (n:{label} {{name: $name, type: $type}})",
                        name=name,
                        type=etype
                    )

                # 插入关系
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
                        except Exception as e:
                            print(f"  ⚠️ 关系创建失败: {source} -> {target}: {e}")
        finally:
            driver.close()

        return {
            "entity_count": len(entities),
            "relation_count": len(relations),
            "entities": entities,
            "relations": relations
        }

    async def query(self, question: str, top_k: int = 10) -> str:
        """问答查询 - 使用知识图谱直接查询"""
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password)
        )

        try:
            with driver.session() as session:
                # 搜索与问题相关的节点
                search_query = """
                MATCH (n)
                WHERE n.name CONTAINS $keyword
                RETURN n.name as name, labels(n)[0] as type
                LIMIT 20
                """
                # 提取问题中的关键词（简单分词）
                stop_words = {'有哪些', '有什么', '是什么', '如何', '怎么', '哪些', '吗', '呢', '的', '了', '是'}
                # 清理问题文本
                clean_q = question.replace('?', '').replace('？', '').replace('，', ' ').replace(',', ' ')
                words = clean_q.split()

                # 提取有意义的短词（2-6字符）作为关键词
                keywords = []
                for w in words:
                    for length in range(2, 7):
                        for i in range(len(w) - length + 1):
                            sub = w[i:i+length]
                            if sub not in stop_words:
                                keywords.append(sub)

                keywords = list(set(keywords))[:15]  # 去重并限制数量

                context_nodes = []
                for keyword in keywords[:10]:  # 最多取10个关键词
                    result = session.run(search_query, keyword=keyword)
                    for record in result:
                        context_nodes.append({
                            'name': record['name'],
                            'type': record['type']
                        })

                # 去重
                unique_nodes = {n['name']: n for n in context_nodes}.values()

                # 获取相关的关系
                context_relations = []
                if unique_nodes:
                    node_names = list(unique_nodes)[-10:]  # 最多10个节点
                    rel_query = f"""
                    MATCH (s)-[r]->(t)
                    WHERE s.name IN $names OR t.name IN $names
                    RETURN s.name as source, type(r) as relation, t.name as target
                    LIMIT 50
                    """
                    rel_result = session.run(rel_query, names=node_names)
                    for record in rel_result:
                        context_relations.append({
                            'source': record['source'],
                            'relation': record['relation'],
                            'target': record['target']
                        })

                # 构建上下文
                context = "## 知识图谱中的相关信息：\n\n"

                if unique_nodes:
                    context += "### 实体：\n"
                    for node in unique_nodes:
                        context += f"- {node['name']} ({node['type']})\n"
                    context += "\n"

                if context_relations:
                    context += "### 关系：\n"
                    for rel in context_relations:
                        context += f"- {rel['source']} --[{rel['relation']}]--> {rel['target']}\n"

                if not unique_nodes and not context_relations:
                    context += "（未找到相关实体和关系）\n"

                # 调用 LLM 生成回答
                system_prompt = """你是一个专业的税务法规问答助手。请根据提供的知识图谱信息回答用户的问题。
如果知识图谱中有相关信息，请基于这些信息作答。如果信息不足，请说明无法回答。
请用简洁、专业的语言回答。"""

                user_prompt = f"""## 用户问题：
{question}

{context}

## 请根据上述知识图谱信息回答问题："""

                # 调用 LLM
                from dashscope import Generation

                if not settings.dashscope_api_key:
                    return "LLM API未配置"

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]

                response = Generation.call(
                    model=settings.llm_model_name,
                    messages=messages,
                    result_format="message"
                )

                if response.status_code == 200:
                    return response.output.choices[0].message.content
                else:
                    return f"LLM调用失败: {response.message}"

        finally:
            driver.close()


# 全局实例
_lightrag_service: Optional[LightRAGService] = None


def get_lightrag_service() -> LightRAGService:
    """获取 LightRAG 服务实例"""
    global _lightrag_service
    if _lightrag_service is None:
        _lightrag_service = LightRAGService()
    return _lightrag_service
