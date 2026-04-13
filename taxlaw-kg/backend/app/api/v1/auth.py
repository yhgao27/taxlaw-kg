"""
认证接口（简化版 - 无需注册登录）
"""
from fastapi import APIRouter
from app.schemas.user import Token

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=Token)
async def login():
    """简化登录：直接返回 token"""
    return Token(access_token="dummy-token-for-now", token_type="bearer")


@router.post("/register")
async def register():
    """简化注册：直接返回成功"""
    return {"message": "注册功能已禁用"}


@router.get("/me")
async def get_me():
    """获取当前用户"""
    return {"id": "anonymous", "username": "anonymous", "role": "admin"}
