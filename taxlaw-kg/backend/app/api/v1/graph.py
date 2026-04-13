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

            # 获取各类型节点数量
            type_result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as type, count(n) as count
            """)
            entity_type_counts = {record["type"]: record["count"] for record in type_result}

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
            # 构建查询
            query = "MATCH (n)"
            params = {}

            if entity_type:
                query = f"MATCH (n:{entity_type})"

            if search:
                query += " WHERE n.name CONTAINS $search"
                params["search"] = search

            # 获取总数
            count_query = query.replace("MATCH (n)", "MATCH (n) RETURN count(n) as total")
            if entity_type:
                count_query = f"MATCH (n:{entity_type}) RETURN count(n) as total"
            count_result = session.run(count_query, params)
            count_record = count_result.single()
            total = count_record["total"] if count_record else 0

            # 获取节点
            query += " RETURN n SKIP $offset LIMIT $limit"
            params["limit"] = limit
            params["offset"] = offset

            result = session.run(query, params)
            nodes = []
            for record in result:
                node = record["n"]
                labels = list(node.labels)
                properties = dict(node)
                nodes.append(GraphNode(
                    id=properties.get("id", str(node.id)),
                    name=properties.get("name", ""),
                    entity_type=labels[0] if labels else "Unknown",
                    attributes={k: v for k, v in properties.items() if k not in ["id", "name", "type"]}
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

            # 获取边
            query = f"{match_clause} RETURN s.name as source, t.name as target, type(r) as relation SKIP $offset LIMIT $limit"
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
    """更新节点"""
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            updates = []
            params = {"node_id": node_id}

            if node_data.name:
                updates.append("n.name = $name")
                params["name"] = node_data.name

            if node_data.attributes:
                for key, value in node_data.attributes.items():
                    updates.append(f"n.{key} = ${key}")
                    params[key] = value

            if updates:
                query = f"MATCH (n) WHERE n.id = $node_id SET {', '.join(updates)}"
                session.run(query, params)

            return {"message": "节点更新成功"}
    finally:
        driver.close()


@router.delete("/nodes/{node_id}")
async def delete_node(
    node_id: str,
    current_user = Depends(get_current_user)
):
    """删除节点及其关联边"""
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            # 先删除关联边
            session.run("MATCH (n) WHERE n.id = $node_id DETACH DELETE n", node_id=node_id)
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
