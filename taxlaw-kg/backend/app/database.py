"""
Redis 数据存储管理
所有数据（用户、Schema、文档）都存储在 Redis 中
"""
import json
import uuid
from typing import Optional, List, Any, Dict
from datetime import datetime
import redis
from app.config import get_settings

settings = get_settings()

# Redis 连接
_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    """获取 Redis 客户端"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            db=settings.redis_db,
            decode_responses=True
        )
    return _redis_client


def close_redis():
    """关闭 Redis 连接"""
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None


class BaseModel:
    """Redis 基础模型"""

    # Redis key 前缀，子类必须定义
    key_prefix: str = ""

    def __init__(self, id: str, data: Dict[str, Any]):
        self.id = id
        self._data = data

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, **self._data}

    @classmethod
    def _key(cls, id: str = None) -> str:
        """生成 Redis key"""
        if id:
            return f"{cls.key_prefix}:{id}"
        return cls.key_prefix

    @classmethod
    def _all_keys(cls) -> str:
        """所有记录的 key 模式"""
        return f"{cls.key_prefix}:*"

    @classmethod
    def _index_key(cls) -> str:
        """索引 key，存储所有 ID"""
        return f"{cls.key_prefix}:ids"

    @classmethod
    def create(cls, data: Dict[str, Any]) -> "BaseModel":
        """创建新记录"""
        id = str(uuid.uuid4())
        obj = cls(id=id, data=data)
        obj.save()
        return obj

    def save(self):
        """保存到 Redis"""
        r = get_redis()
        r.set(self._key(self.id), json.dumps(self._data, default=str))
        r.sadd(self._index_key(), self.id)

    def delete(self):
        """从 Redis 删除"""
        r = get_redis()
        r.delete(self._key(self.id))
        r.srem(self._index_key(), self.id)

    @classmethod
    def get(cls, id: str) -> Optional["BaseModel"]:
        """根据 ID 获取"""
        r = get_redis()
        data = r.get(cls._key(id))
        if data:
            return cls(id=id, data=json.loads(data))
        return None

    @classmethod
    def all(cls) -> List["BaseModel"]:
        """获取所有记录"""
        r = get_redis()
        ids = r.smembers(cls._index_key())
        result = []
        for id in ids:
            obj = cls.get(id)
            if obj:
                result.append(obj)
        return result

    @classmethod
    def delete_all(cls):
        """删除所有记录"""
        r = get_redis()
        ids = r.smembers(cls._index_key())
        for id in ids:
            r.delete(cls._key(id))
        r.delete(cls._index_key())

    @classmethod
    def count(cls) -> int:
        """获取数量"""
        r = get_redis()
        return r.scard(cls._index_key())

    @classmethod
    def find(cls, **kwargs) -> List["BaseModel"]:
        """简单查询，匹配所有 kwargs"""
        results = []
        for obj in cls.all():
            match = True
            for key, value in kwargs.items():
                if obj._data.get(key) != value:
                    match = False
                    break
            if match:
                results.append(obj)
        return results

    @classmethod
    def first(cls, **kwargs) -> Optional["BaseModel"]:
        """返回第一条匹配的记录"""
        results = cls.find(**kwargs)
        return results[0] if results else None


# ============================================
# 用户模型
# ============================================
class User(BaseModel):
    key_prefix = "user"

    @property
    def username(self) -> str:
        return self._data.get("username", "")

    @property
    def password_hash(self) -> str:
        return self._data.get("password_hash", "")

    @property
    def role(self) -> str:
        return self._data.get("role", "user")

    @property
    def is_active(self) -> bool:
        return self._data.get("is_active", True)

    @property
    def created_at(self) -> str:
        return self._data.get("created_at", "")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at
        }

    @classmethod
    def get_by_username(cls, username: str) -> Optional["User"]:
        """根据用户名查找"""
        return cls.first(username=username)


# ============================================
# 实体类型模型
# ============================================
class EntityType(BaseModel):
    key_prefix = "entity_type"

    @property
    def name(self) -> str:
        return self._data.get("name", "")

    @property
    def description(self) -> str:
        return self._data.get("description", "")

    @property
    def required_attributes(self) -> List[str]:
        return self._data.get("required_attributes", [])

    @property
    def optional_attributes(self) -> List[str]:
        return self._data.get("optional_attributes", [])

    @property
    def is_system(self) -> bool:
        return self._data.get("is_system", False)

    @property
    def created_at(self) -> str:
        return self._data.get("created_at", "")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "required_attributes": self.required_attributes,
            "optional_attributes": self.optional_attributes,
            "is_system": self.is_system,
            "created_at": self.created_at
        }


# ============================================
# 关系类型模型
# ============================================
class RelationType(BaseModel):
    key_prefix = "relation_type"

    @property
    def name(self) -> str:
        return self._data.get("name", "")

    @property
    def source_type(self) -> str:
        return self._data.get("source_type", "")

    @property
    def target_type(self) -> str:
        return self._data.get("target_type", "")

    @property
    def description(self) -> str:
        return self._data.get("description", "")

    @property
    def is_system(self) -> bool:
        return self._data.get("is_system", False)

    @property
    def created_at(self) -> str:
        return self._data.get("created_at", "")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "source_type": self.source_type,
            "target_type": self.target_type,
            "description": self.description,
            "is_system": self.is_system,
            "created_at": self.created_at
        }


# ============================================
# 文档模型
# ============================================
class Document(BaseModel):
    key_prefix = "document"

    @property
    def filename(self) -> str:
        return self._data.get("filename", "")

    @property
    def original_name(self) -> str:
        return self._data.get("original_name", "")

    @property
    def file_path(self) -> str:
        return self._data.get("file_path", "")

    @property
    def file_type(self) -> str:
        return self._data.get("file_type", "")

    @property
    def file_size(self) -> int:
        return self._data.get("file_size", 0)

    @property
    def status(self) -> str:
        return self._data.get("status", "pending")

    @property
    def parsed_text(self) -> str:
        return self._data.get("parsed_text", "")

    @property
    def chunk_count(self) -> int:
        return self._data.get("chunk_count", 0)

    @property
    def entity_count(self) -> int:
        return self._data.get("entity_count", 0)

    @property
    def relation_count(self) -> int:
        return self._data.get("relation_count", 0)

    @property
    def uploaded_by(self) -> str:
        return self._data.get("uploaded_by", "")

    @property
    def created_at(self) -> str:
        return self._data.get("created_at", "")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "filename": self.filename,
            "original_name": self.original_name,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "status": self.status,
            "parsed_text": self.parsed_text,
            "chunk_count": self.chunk_count,
            "entity_count": self.entity_count,
            "relation_count": self.relation_count,
            "uploaded_by": self.uploaded_by,
            "created_at": self.created_at
        }


def get_db():
    """兼容 SQLAlchemy 的 get_db 接口"""
    # Redis 不需要会话管理，返回 None
    yield None
