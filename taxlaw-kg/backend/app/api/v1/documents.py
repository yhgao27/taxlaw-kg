"""
文档管理接口
"""
import os
import uuid
import shutil
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, BackgroundTasks
from app.database import Document as DocumentModel, EntityType as EntityTypeModel, RelationType as RelationTypeModel
from app.schemas.document import Document as DocumentSchema, DocumentUploadResponse, DocumentListResponse
from app.api.deps import get_current_user
from app.utils.file_parser import get_document_parser
from app.services.lightrag_service import get_lightrag_service
from app.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/documents", tags=["文档管理"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """上传文档"""
    # 检查文件类型
    parser = get_document_parser()
    file_type = parser.get_file_type(file.filename)
    if file_type is None:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    # 检查文件大小
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > settings.max_file_size:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({settings.max_file_size // (1024*1024)}MB)"
        )

    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(settings.upload_dir, unique_filename)

    # 保存文件
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # 创建文档记录
    doc = DocumentModel.create({
        "filename": unique_filename,
        "original_name": file.filename,
        "file_path": file_path,
        "file_type": file_type,
        "file_size": file_size,
        "status": "pending",
        "uploaded_by": "anonymous"
    })

    # 触发后台解析任务
    background_tasks.add_task(parse_document_task, doc.id)

    return DocumentUploadResponse(
        id=doc.id,
        filename=file.filename,
        status="pending",
        message="文档上传成功，正在解析..."
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """获取文档列表"""
    documents = DocumentModel.all()

    # 过滤
    if status:
        documents = [d for d in documents if d.status == status]
    if search:
        documents = [d for d in documents if search.lower() in d.original_name.lower()]

    # 排序（按创建时间倒序）
    documents.sort(key=lambda x: x.created_at, reverse=True)

    total = len(documents)

    # 分页
    start = (page - 1) * page_size
    end = start + page_size
    paginated = documents[start:end]

    return DocumentListResponse(
        items=[DocumentSchema(**d.to_dict()) for d in paginated],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{document_id}", response_model=DocumentSchema)
async def get_document(
    document_id: str,
    current_user = Depends(get_current_user)
):
    """获取文档详情"""
    doc = DocumentModel.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return DocumentSchema(**doc.to_dict())


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user = Depends(get_current_user)
):
    """删除文档"""
    doc = DocumentModel.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 删除文件
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    doc.delete()
    return {"message": "文档删除成功"}


@router.post("/{document_id}/reparse")
async def reparse_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """重新解析文档"""
    doc = DocumentModel.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    doc._data["status"] = "pending"
    doc.save()

    background_tasks.add_task(parse_document_task, doc.id)

    return {"message": "文档重新解析中...", "status": "pending"}


async def parse_document_task(document_id: str):
    """后台解析文档任务"""
    doc = DocumentModel.get(document_id)
    if not doc:
        return

    # 解析文档
    parser = get_document_parser()
    try:
        parsed_text = parser.parse(doc.file_path)
        doc._data["parsed_text"] = parsed_text
        doc._data["status"] = "completed"
    except Exception as e:
        doc._data["status"] = "failed"
        doc._data["parsed_text"] = f"解析失败: {str(e)}"

    doc.save()

    # 如果解析成功，进行实体抽取
    if doc.status == "completed" and parsed_text:
        await run_entity_extraction(doc)


async def run_entity_extraction(doc: DocumentModel):
    """运行实体抽取"""
    try:
        # 获取当前的 Schema
        entity_types = EntityTypeModel.all()
        relation_types = RelationTypeModel.all()

        if not entity_types:
            return

        # 构建 Schema 格式
        schema = {
            "entity_types": [
                {
                    "name": et.name,
                    "description": et.description,
                    "examples": []
                }
                for et in entity_types
            ],
            "relation_types": [
                {
                    "name": rt.name,
                    "source": rt.source_type,
                    "target": rt.target_type,
                    "description": rt.description
                }
                for rt in relation_types
            ]
        }

        # 调用 LightRAG 服务进行抽取
        lightrag_service = get_lightrag_service()
        result = await lightrag_service.insert_document(
            text=doc.parsed_text,
            schema=schema
        )

        doc._data["entity_count"] = result.get("entity_count", 0)
        doc._data["relation_count"] = result.get("relation_count", 0)
        doc._data["chunk_count"] = len(result.get("entities", []))
        doc.save()

    except Exception as e:
        print(f"实体抽取失败: {e}")
