"""
图谱 Schema (KG 操作)
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID


# ============================================
# 图谱节点 Schema
# ============================================
class GraphNodeBase(BaseModel):
    name: str = Field(..., min_length=1)
    entity_type: str = Field(..., min_length=1)
    attributes: Dict[str, Any] = Field(default_factory=dict)


class GraphNodeCreate(GraphNodeBase):
    pass


class GraphNodeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    attributes: Optional[Dict[str, Any]] = None


class GraphNode(GraphNodeBase):
    id: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================
# 图谱边 Schema
# ============================================
class GraphEdgeBase(BaseModel):
    source_id: str
    target_id: str
    relation_type: str


class GraphEdgeCreate(GraphEdgeBase):
    pass


class GraphEdgeUpdate(BaseModel):
    relation_type: Optional[str] = Field(None, min_length=1)


class GraphEdge(GraphEdgeBase):
    id: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================
# 图谱查询响应
# ============================================
class GraphNodesResponse(BaseModel):
    items: List[GraphNode]
    total: int


class GraphEdgesResponse(BaseModel):
    items: List[GraphEdge]
    total: int


class GraphStats(BaseModel):
    node_count: int
    edge_count: int
    entity_type_counts: Dict[str, int]
