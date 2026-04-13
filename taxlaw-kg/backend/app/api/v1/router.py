"""
API 路由汇总
"""
from fastapi import APIRouter
from app.api.v1 import auth, schema, documents, graph, query

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(schema.router)
api_router.include_router(documents.router)
api_router.include_router(graph.router)
api_router.include_router(query.router)
