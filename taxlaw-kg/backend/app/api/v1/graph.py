"""
图谱管理接口
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from app.schemas.graph import (
    GraphNode,
    GraphNodesResponse,
    GraphEdge,
    GraphEdgesResponse,
    GraphStats,
    GraphNodeCreate,
    GraphNodeUpdate,
    GraphEdgeCreate,
    GraphEdgeUpdate
)
from app.api.deps import get_current_user
from app.core.exceptions import NotFoundException
from app.config import get_settings
from neo4j import GraphDatabase

settings = get_settings()

router = APIRouter(prefix="/graph", tags=["图谱管理"])


def get_neo4j_driver():
    """获取 Neo4j 驱动"""
    return GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password)
    )


@router.get("/stats", response_model=GraphStats)
async def get_graph_stats(
    current_user = Depends(get_current_user)
):
    """获取图谱统计信息"""
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            # 获取节点数量
            node_result = session.run("MATCH (n) RETURN count(n) as count")
            node_record = node_result.single()
            node_count = node_record["count"] if node_record else 0

            # 获取边数量
            edge_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            edge_record = edge_result.single()
            edge_count = edge_record["count"] if edge_record else 0

            # 获取各类型节点数量 (排除 base 标签，显示实际业务类型)
            # 方式1: 有 entity_type 属性的节点 (LightRAG 创建)
            # 方式2: 无 entity_type 但有非 base 标签的节点
            result1 = session.run("""
                MATCH (n)
                WHERE n.entity_type IS NOT NULL
                RETURN n.entity_type as type, count(n) as count
            """)
            result2 = session.run("""
                MATCH (n)
                WHERE n.entity_type IS NULL
                WITH n, [l IN labels(n) WHERE l <> 'base'][0] as biz_label
                WHERE biz_label IS NOT NULL
                RETURN biz_label as type, count(n) as count
            """)
            entity_type_counts: Dict[str, int] = {}
            for record in result1:
                entity_type_counts[record["type"]] = record["count"]
            for record in result2:
                t = record["type"]
                entity_type_counts[t] = entity_type_counts.get(t, 0) + record["count"]

            return GraphStats(
                node_count=node_count,
                edge_count=edge_count,
                entity_type_counts=entity_type_counts
            )
    finally:
        driver.close()


@router.get("/nodes", response_model=GraphNodesResponse)
async def list_nodes(
    entity_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_user)
):
    """获取图谱节点"""
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            # 构建查询 - 统一使用 COALESCE 兼容两种节点 schema:
            #   自定义节点: name 字段存名称
            #   LightRAG 节点: entity_id 字段存名称
            match_clause = f"MATCH (n:{entity_type})" if entity_type else "MATCH (n)"
            where_clause = ""
            params: Dict[str, Any] = {}

            if search:
                # 同时搜索 name 和 entity_id
                where_clause = " WHERE n.name CONTAINS $search OR n.entity_id CONTAINS $search"
                params["search"] = search

            # 获取总数
            count_query = match_clause + where_clause + " RETURN count(n) as total"
            count_result = session.run(count_query, params)
            count_record = count_result.single()
            total = count_record["total"] if count_record else 0

            # 获取节点
            query = match_clause + where_clause + " RETURN n SKIP $offset LIMIT $limit"
            params["limit"] = limit
            params["offset"] = offset

            result = session.run(query, params)
            nodes = []
            for record in result:
                node = record["n"]
                labels = list(node.labels)
                properties = dict(node)

                # 兼容两种 schema: 自定义节点用 name, LightRAG 节点用 entity_id
                name = properties.get("name") or properties.get("entity_id") or ""

                # 兼容两种 label 结构:
                #   自定义节点: labels 如 ["纳税人"], 取 labels[0]
                #   LightRAG 节点: labels 如 ["base", "概念"], 排除 "base" 后取第一个
                display_labels = [l for l in labels if l != "base"]
                node_type = properties.get("entity_type") or (display_labels[0] if display_labels else (labels[0] if labels else "Unknown"))

                nodes.append(GraphNode(
                    id=properties.get("id", node.element_id),
                    name=name,
                    entity_type=node_type,
                    attributes={k: v for k, v in properties.items() if k not in ["id", "name", "type", "entity_id", "entity_type"]}
                ))

            return GraphNodesResponse(items=nodes, total=total)
    finally:
        driver.close()


@router.get("/edges", response_model=GraphEdgesResponse)
async def list_edges(
    source_type: Optional[str] = None,
    target_type: Optional[str] = None,
    relation_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_user)
):
    """获取图谱边"""
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            # 构建匹配模式
            source_label = f"(s:{source_type})" if source_type else "(s)"
            target_label = f"(t:{target_type})" if target_type else "(t)"
            rel_type = f":{relation_type}" if relation_type else ""
            match_clause = f"MATCH {source_label}-[r{rel_type}]->{target_label}"

            # 获取总数
            count_query = f"{match_clause} RETURN count(r) as total"
            count_result = session.run(count_query)
            count_record = count_result.single()
            total = count_record["total"] if count_record else 0

            # 获取边 - 兼容两种节点 schema (name vs entity_id)
            query = (
                f"{match_clause} "
                "RETURN COALESCE(s.name, s.entity_id) as source, "
                "       COALESCE(t.name, t.entity_id) as target, "
                "       type(r) as relation "
                "SKIP $offset LIMIT $limit"
            )
            params = {"limit": limit, "offset": offset}

            result = session.run(query, params)
            edges = []
            for record in result:
                edges.append(GraphEdge(
                    source_id=record["source"],
                    target_id=record["target"],
                    relation_type=record["relation"]
                ))

            return GraphEdgesResponse(items=edges, total=total)
    finally:
        driver.close()


@router.post("/nodes", response_model=GraphNode)
async def create_node(
    node_data: GraphNodeCreate,
    current_user = Depends(get_current_user)
):
    """创建节点"""
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            label = node_data.entity_type.replace(" ", "")
            properties = {**node_data.attributes, "name": node_data.name}

            session.run(
                f"CREATE (n:{label} $props)",
                props=properties
            )

            return GraphNode(
                id="",
                name=node_data.name,
                entity_type=node_data.entity_type,
                attributes=node_data.attributes
            )
    finally:
        driver.close()


@router.put("/nodes/{node_id}")
async def update_node(
    node_id: str,
    node_data: GraphNodeUpdate,
    current_user = Depends(get_current_user)
):
    """更新节点 (支持按 id / name / entity_id 查询)"""
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            updates = []
            params: Dict[str, Any] = {}

            # 优先用 name/entity_id 查询 (LightRAG 节点没有 id 属性)
            if node_data.name:
                updates.append("n.name = $name")
                params["name"] = node_data.name

            if node_data.attributes:
                for key, value in node_data.attributes.items():
                    updates.append(f"n.{key} = ${key}")
                    params[key] = value

            if updates:
                # 尝试三种方式匹配: name / entity_id / id 属性
                params["node_id"] = node_id
                query = (
                    "MATCH (n) "
                    "WHERE n.name = $node_id OR n.entity_id = $node_id OR n.id = $node_id "
                    f"SET {', '.join(updates)}"
                )
                session.run(query, params)

            return {"message": "节点更新成功"}
    finally:
        driver.close()


@router.delete("/nodes/{node_id}")
async def delete_node(
    node_id: str,
    current_user = Depends(get_current_user)
):
    """删除节点及其关联边 (支持按 id / name / entity_id 查询)"""
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            # 尝试三种方式匹配: name / entity_id / id 属性
            session.run(
                "MATCH (n) "
                "WHERE n.name = $node_id OR n.entity_id = $node_id OR n.id = $node_id "
                "DETACH DELETE n",
                node_id=node_id
            )
            return {"message": "节点删除成功"}
    finally:
        driver.close()


@router.post("/edges", response_model=GraphEdge)
async def create_edge(
    edge_data: GraphEdgeCreate,
    current_user = Depends(get_current_user)
):
    """创建边"""
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            rel_type = edge_data.relation_type.upper().replace(" ", "_")

            session.run(f"""
                MATCH (s {{name: $source}})
                MATCH (t {{name: $target}})
                CREATE (s)-[r:{rel_type}]->(t)
            """, source=edge_data.source_id, target=edge_data.target_id)

            return GraphEdge(
                source_id=edge_data.source_id,
                target_id=edge_data.target_id,
                relation_type=edge_data.relation_type
            )
    finally:
        driver.close()


@router.delete("/edges")
async def delete_edge(
    source_id: str,
    target_id: str,
    relation_type: str,
    current_user = Depends(get_current_user)
):
    """删除边"""
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            rel_type = relation_type.upper().replace(" ", "_")
            session.run(f"""
                MATCH (s {{name: $source}})-[r:{rel_type}]->(t {{name: $target}})
                DELETE r
            """, source=source_id, target=target_id)

            return {"message": "边删除成功"}
    finally:
        driver.close()
