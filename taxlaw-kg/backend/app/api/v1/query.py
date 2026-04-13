"""
问答接口
"""
from typing import List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends
from app.database import EntityType as EntityTypeModel, RelationType as RelationTypeModel
from app.api.deps import get_current_user
from app.services.lightrag_service import get_lightrag_service

router = APIRouter(prefix="/query", tags=["智能问答"])


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    use_kg: bool = Field(default=True)
    use_vector: bool = Field(default=True)
    top_k: int = Field(default=10, ge=1, le=50)


class Source(BaseModel):
    type: str
    content: str
    document_id: str = None
    document_name: str = None
    relevance_score: float = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    related_questions: List[str] = []


@router.post("/ask", response_model=QueryResponse)
async def ask_question(
    request: QueryRequest,
    current_user = Depends(get_current_user)
):
    """智能问答"""
    lightrag_service = get_lightrag_service()

    # 初始化 LightRAG（如未初始化）
    await lightrag_service.initialize()

    # 执行问答
    try:
        answer = await lightrag_service.query(request.question, top_k=request.top_k)
    except Exception as e:
        return QueryResponse(
            answer=f"问答服务暂时不可用: {str(e)}",
            sources=[],
            related_questions=[]
        )

    return QueryResponse(
        answer=str(answer) if answer else "抱歉，暂时无法回答这个问题。",
        sources=[],
        related_questions=[]
    )


@router.get("/schema-context")
async def get_schema_context(current_user = Depends(get_current_user)):
    """获取 Schema 上下文（用于增强问答）"""
    entity_types = EntityTypeModel.all()
    relation_types = RelationTypeModel.all()

    return {
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
