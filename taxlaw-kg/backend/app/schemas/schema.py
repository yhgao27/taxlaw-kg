"""
Schema 管理 Schema (实体类型、关系类型)
"""
from pydantic import BaseModel, Field
from typing import Optional, List


# ============================================
# 实体类型 Schema
# ============================================
class EntityTypeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    required_attributes: List[str] = Field(default_factory=list)
    optional_attributes: List[str] = Field(default_factory=list)


class EntityTypeCreate(EntityTypeBase):
    pass


class EntityTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    required_attributes: Optional[List[str]] = None
    optional_attributes: Optional[List[str]] = None


class EntityTypeInDB(EntityTypeBase):
    id: str
    is_system: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class EntityType(EntityTypeInDB):
    pass


# ============================================
# 关系类型 Schema
# ============================================
class RelationTypeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    source_type: str = Field(..., min_length=1, max_length=100)
    target_type: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class RelationTypeCreate(RelationTypeBase):
    pass


class RelationTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    source_type: Optional[str] = Field(None, min_length=1, max_length=100)
    target_type: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class RelationTypeInDB(RelationTypeBase):
    id: str
    is_system: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class RelationType(RelationTypeInDB):
    pass


# ============================================
# Schema 模板
# ============================================
class SchemaTemplate(BaseModel):
    """完整的 Schema 模板"""
    entity_types: List[EntityTypeCreate]
    relation_types: List[RelationTypeCreate]


# ============================================
# LightRAG 抽取用的 Schema 格式
# ============================================
class TaxEntitySchema(BaseModel):
    """LightRAG 抽取用的税务 Schema"""
    entity_types: List[dict]
    relation_types: List[dict]
