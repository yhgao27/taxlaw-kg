"""
Schema 管理接口（实体类型、关系类型）
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import EntityType as EntityTypeModel, RelationType as RelationTypeModel
from app.schemas.schema import (
    EntityTypeCreate,
    EntityTypeUpdate,
    EntityType as EntityTypeSchema,
    RelationTypeCreate,
    RelationTypeUpdate,
    RelationType as RelationTypeSchema,
    SchemaTemplate
)
from app.api.deps import get_current_user, require_admin

router = APIRouter(prefix="/schema", tags=["Schema 管理"])


# ============================================
# 实体类型接口
# ============================================
@router.get("/entity-types", response_model=List[EntityTypeSchema])
async def list_entity_types():
    """获取所有实体类型"""
    entity_types = EntityTypeModel.all()
    return [EntityTypeSchema(**et.to_dict()) for et in entity_types]


@router.get("/entity-types/{entity_type_id}", response_model=EntityTypeSchema)
async def get_entity_type(entity_type_id: str):
    """获取单个实体类型"""
    entity_type = EntityTypeModel.get(entity_type_id)
    if not entity_type:
        raise HTTPException(status_code=404, detail="实体类型不存在")
    return EntityTypeSchema(**entity_type.to_dict())


@router.post("/entity-types", response_model=EntityTypeSchema)
async def create_entity_type(
    entity_type_data: EntityTypeCreate,
    current_user = Depends(require_admin)
):
    """创建实体类型（需管理员权限）"""
    # 检查名称是否已存在
    existing = EntityTypeModel.first(name=entity_type_data.name)
    if existing:
        raise HTTPException(status_code=409, detail="实体类型名称已存在")

    entity_type = EntityTypeModel.create({
        **entity_type_data.model_dump(),
        "is_system": False
    })

    return EntityTypeSchema(**entity_type.to_dict())


@router.put("/entity-types/{entity_type_id}", response_model=EntityTypeSchema)
async def update_entity_type(
    entity_type_id: str,
    entity_type_data: EntityTypeUpdate,
    current_user = Depends(require_admin)
):
    """更新实体类型（需管理员权限）"""
    entity_type = EntityTypeModel.get(entity_type_id)
    if not entity_type:
        raise HTTPException(status_code=404, detail="实体类型不存在")

    if entity_type.is_system:
        raise HTTPException(status_code=400, detail="系统预置实体类型不可修改")

    # 检查新名称是否冲突
    if entity_type_data.name and entity_type_data.name != entity_type.name:
        existing = EntityTypeModel.first(name=entity_type_data.name)
        if existing:
            raise HTTPException(status_code=409, detail="实体类型名称已存在")

    # 更新数据
    update_data = entity_type_data.model_dump(exclude_unset=True)
    entity_type._data.update(update_data)
    entity_type.save()

    return EntityTypeSchema(**entity_type.to_dict())


@router.delete("/entity-types/{entity_type_id}")
async def delete_entity_type(
    entity_type_id: str,
    current_user = Depends(require_admin)
):
    """删除实体类型（需管理员权限）"""
    entity_type = EntityTypeModel.get(entity_type_id)
    if not entity_type:
        raise HTTPException(status_code=404, detail="实体类型不存在")

    if entity_type.is_system:
        raise HTTPException(status_code=400, detail="系统预置实体类型不可删除")

    entity_type.delete()
    return {"message": "实体类型删除成功"}


# ============================================
# 关系类型接口
# ============================================
@router.get("/relation-types", response_model=List[RelationTypeSchema])
async def list_relation_types():
    """获取所有关系类型"""
    relation_types = RelationTypeModel.all()
    return [RelationTypeSchema(**rt.to_dict()) for rt in relation_types]


@router.get("/relation-types/{relation_type_id}", response_model=RelationTypeSchema)
async def get_relation_type(relation_type_id: str):
    """获取单个关系类型"""
    relation_type = RelationTypeModel.get(relation_type_id)
    if not relation_type:
        raise HTTPException(status_code=404, detail="关系类型不存在")
    return RelationTypeSchema(**relation_type.to_dict())


@router.post("/relation-types", response_model=RelationTypeSchema)
async def create_relation_type(
    relation_type_data: RelationTypeCreate,
    current_user = Depends(require_admin)
):
    """创建关系类型（需管理员权限）"""
    # 检查名称是否已存在
    existing = RelationTypeModel.first(name=relation_type_data.name)
    if existing:
        raise HTTPException(status_code=409, detail="关系类型名称已存在")

    # 检查 source_type 和 target_type 是否存在
    source_exists = EntityTypeModel.first(name=relation_type_data.source_type)
    if not source_exists:
        raise HTTPException(status_code=400, detail=f"源实体类型 '{relation_type_data.source_type}' 不存在")

    target_exists = EntityTypeModel.first(name=relation_type_data.target_type)
    if not target_exists:
        raise HTTPException(status_code=400, detail=f"目标实体类型 '{relation_type_data.target_type}' 不存在")

    relation_type = RelationTypeModel.create({
        **relation_type_data.model_dump(),
        "is_system": False
    })

    return RelationTypeSchema(**relation_type.to_dict())


@router.put("/relation-types/{relation_type_id}", response_model=RelationTypeSchema)
async def update_relation_type(
    relation_type_id: str,
    relation_type_data: RelationTypeUpdate,
    current_user = Depends(require_admin)
):
    """更新关系类型（需管理员权限）"""
    relation_type = RelationTypeModel.get(relation_type_id)
    if not relation_type:
        raise HTTPException(status_code=404, detail="关系类型不存在")

    if relation_type.is_system:
        raise HTTPException(status_code=400, detail="系统预置关系类型不可修改")

    update_data = relation_type_data.model_dump(exclude_unset=True)
    relation_type._data.update(update_data)
    relation_type.save()

    return RelationTypeSchema(**relation_type.to_dict())


@router.delete("/relation-types/{relation_type_id}")
async def delete_relation_type(
    relation_type_id: str,
    current_user = Depends(require_admin)
):
    """删除关系类型（需管理员权限）"""
    relation_type = RelationTypeModel.get(relation_type_id)
    if not relation_type:
        raise HTTPException(status_code=404, detail="关系类型不存在")

    if relation_type.is_system:
        raise HTTPException(status_code=400, detail="系统预置关系类型不可删除")

    relation_type.delete()
    return {"message": "关系类型删除成功"}


# ============================================
# Schema 模板
# ============================================
@router.get("/template", response_model=SchemaTemplate)
async def get_schema_template():
    """获取当前 Schema 模板（所有实体类型和关系类型）"""
    entity_types = EntityTypeModel.all()
    relation_types = RelationTypeModel.all()

    return SchemaTemplate(
        entity_types=[EntityTypeCreate(**et._data) for et in entity_types],
        relation_types=[RelationTypeCreate(**rt._data) for rt in relation_types]
    )


@router.post("/template/tax-default")
async def create_tax_default_template(current_user = Depends(require_admin)):
    """创建税务默认 Schema 模板"""
    # 预置实体类型
    default_entity_types = [
        {"name": "纳税人", "description": "纳税义务主体", "required_attributes": ["名称"], "optional_attributes": ["类型", "登记状态"]},
        {"name": "税目", "description": "税收分类具体项目", "required_attributes": ["名称"], "optional_attributes": ["税种", "征收品目"]},
        {"name": "税率", "description": "税额计算比例或金额", "required_attributes": ["数值"], "optional_attributes": ["类型", "适用条件"]},
        {"name": "征收率", "description": "小规模纳税人简易征收比例", "required_attributes": ["数值"], "optional_attributes": ["适用条件"]},
        {"name": "减免条件", "description": "税收减免的适用条件", "required_attributes": ["条件描述"], "optional_attributes": ["减免方式", "减免比例"]},
        {"name": "法规条款", "description": "具体法规条文", "required_attributes": ["条款号"], "optional_attributes": ["章节", "内容摘要"]},
        {"name": "优惠政策", "description": "税收优惠政策", "required_attributes": ["政策名称"], "optional_attributes": ["适用对象", "执行期限"]},
    ]

    # 预置关系类型
    default_relation_types = [
        {"name": "缴纳", "source_type": "纳税人", "target_type": "税目", "description": "纳税人缴纳某税目"},
        {"name": "适用", "source_type": "税目", "target_type": "税率", "description": "某税目适用某税率"},
        {"name": "可减免", "source_type": "税率", "target_type": "减免条件", "description": "某税率可按条件减免"},
        {"name": "依据", "source_type": "优惠政策", "target_type": "法规条款", "description": "优惠政策依据某法规条款"},
        {"name": "规定", "source_type": "法规条款", "target_type": "税目", "description": "法规条款规定某税目"},
        {"name": "享受", "source_type": "纳税人", "target_type": "优惠政策", "description": "纳税人享受某优惠政策"},
    ]

    # 插入实体类型
    for et_data in default_entity_types:
        existing = EntityTypeModel.first(name=et_data["name"])
        if not existing:
            EntityTypeModel.create({**et_data, "is_system": True})

    # 插入关系类型
    for rt_data in default_relation_types:
        existing = RelationTypeModel.first(name=rt_data["name"])
        if not existing:
            RelationTypeModel.create({**rt_data, "is_system": True})

    return {"message": "税务默认模板创建成功"}
