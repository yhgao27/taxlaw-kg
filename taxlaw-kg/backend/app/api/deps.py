"""
API 依赖注入（无需认证）
"""

def get_current_user():
    """简化版：直接返回 None，不需要认证"""
    return None


def get_current_active_user():
    """获取当前用户"""
    return None


def require_admin():
    """管理员权限（简化版，总是通过）"""
    return None
