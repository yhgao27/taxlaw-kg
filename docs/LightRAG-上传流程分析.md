# LightRAG 文件上传完整处理流程

## 1. 文件上传阶段

**接口**: `POST /api/v1/documents/upload`

```
前端 el-upload (auto-upload=false)
    ↓
FastAPI upload_document()
    ↓
1. 检查文件类型、大小
2. 生成唯一文件名 (UUID + 扩展名)
3. 保存到本地: settings.upload_dir (./uploads/)
4. 在 Redis 中创建 Document 记录 (key: document:{uuid})
5. 添加后台任务 parse_document_task
```

### 源码位置
- **接口**: `taxlaw-kg/backend/app/api/v1/documents.py` - `upload_document()`
- **文件保存**: `shutil.copyfileobj(file.file, f)`
- **Redis 记录**: `DocumentModel.create({...})`

---

## 2. 后台解析阶段 (Background Task)

**任务函数**: `parse_document_task(document_id)`

```
1. 从 Redis 获取 Document 记录
2. 调用 DocumentParser.parse() 提取文本
   ├── PDF: pymupdf / pdfplumber
   ├── Word: python-docx
   ├── Excel: openpyxl
   └── Text: 尝试 utf-8/gbk/gb2312/gb18030
3. 将解析文本存入 Redis Document.parsed_text
4. 更新状态 status = "completed"
5. 如果成功，调用 run_entity_extraction(doc)
```

### 源码位置
- **解析器**: `taxlaw-kg/backend/app/utils/file_parser.py` - `DocumentParser`

| 文件类型 | 解析方法 | 依赖库 |
|---------|---------|--------|
| PDF | `_parse_pdf()` | pymupdf / pdfplumber |
| Word | `_parse_word()` | python-docx |
| Excel | `_parse_excel()` | openpyxl |
| Text | `_parse_text()` | 内置 (多编码尝试) |

---

## 3. 实体抽取阶段

**任务函数**: `run_entity_extraction(doc)`

```
1. 从 Redis 获取 EntityType 和 RelationType Schema
2. 构建 Schema 格式:
   {
     "entity_types": [{"name": "纳税人", "description": "..."}, ...],
     "relation_types": [{"name": "缴纳", "source": "纳税人", "target": "税目"}, ...]
   }
3. 调用 LightRAGService.insert_document(text, schema)
```

### 源码位置
- `taxlaw-kg/backend/app/api/v1/documents.py` - `run_entity_extraction()`

---

## 4. LightRAG Service 处理

**函数**: `LightRAGService.insert_document()`

```
┌─────────────────────────────────────────────────────────────┐
│  LightRAGService.insert_document()                          │
│                                                             │
│  1. extract_entities(text, schema)                          │
│     ├── 构建抽取 Prompt (税务实体类型 + 关系类型描述)         │
│     ├── 调用 DashScope Generation API (qwen-turbo)          │
│     └── 解析 JSON 返回: {entities: [...], relations: [...]} │
│                                                             │
│  2. 存入 Neo4j                                              │
│     ├── 遍历 entities → CREATE (n:类型 {name, type})       │
│     └── 遍历 relations → MATCH + CREATE (s)-[r]->(t)       │
│                                                             │
│  3. 返回: {entity_count, relation_count, entities, relations}│
└─────────────────────────────────────────────────────────────┘
```

### 源码位置
- `taxlaw-kg/backend/app/services/lightrag_service.py`

### Prompt 示例
```
你是一个专业的税务法规知识抽取专家。请从以下文本中抽取税务实体和关系。

## 实体类型（必须识别以下 X 种类型）：
- 纳税人: 纳税义务主体 (示例: 企业、个人)
- 税目: 税收分类 (示例: 增值税、消费税)

## 关系类型（必须识别以下 X 种关系）：
- 缴纳: 从 [纳税人] 指向 [税目]
- 适用: 从 [税目] 指向 [税率]

## 输出要求：
请以 JSON 格式返回抽取结果，包含：
1. "entities": 识别出的所有实体列表
2. "relations": 识别出的所有关系列表
```

---

## 数据存储位置

### 1. 原始文件 (本地磁盘)
```
settings.upload_dir (默认: ./uploads/)
└── {uuid}.{ext}  (如: a1b2c3d4-e5f6.pdf)
```

### 2. Redis (数据索引)

| Key 模式 | 内容 | 示例 |
|----------|------|------|
| `document:{uuid}` | 文档元数据 | filename, file_path, status, parsed_text, entity_count... |
| `entity_type:{uuid}` | 实体类型定义 | name, description, required_attributes... |
| `relation_type:{uuid}` | 关系类型定义 | name, source_type, target_type... |
| `document:ids` | Redis Set，所有文档 ID | {uuid1, uuid2, ...} |
| `entity_type:ids` | Redis Set，所有实体类型 ID | {uuid1, uuid2, ...} |
| `relation_type:ids` | Redis Set，所有关系类型 ID | {uuid1, uuid2, ...} |

### 3. Neo4j (知识图谱)

**节点 (Label = 实体类型名称)**:
```cypher
(:纳税人 {name: "企业A", type: "纳税人"})
(:税目 {name: "增值税", type: "税目"})
(:税率 {name: "13%", type: "税率"})
```

**关系 (Type = 关系类型大写)**:
```cypher
(纳税人:`纳税A`)-[:缴纳]->(:税目:`增值税`)
(:税目:`增值税`)-[:适用]->(:税率:`13%`)
```

### 4. Milvus (向量存储)
```
LightRAG 自动管理 (当前因 embedding 问题未实际使用)
- Collection: taxlaw_kg
- 存储文档 chunk 的向量嵌入
```

### 5. LightRAG 工作目录
```
settings.lightrag_working_dir (默认: ./lightrag_working/)
├── lightrag.db (SQLite, LightRAG 内部状态)
└── 其他 LightRAG 生成的缓存文件
```

---

## 完整数据流图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   前端      │     │  FastAPI    │     │   Redis      │
│  el-upload  │────▶│  upload_    │────▶│  Document    │
│             │     │  document() │     │  {id: uuid}  │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                           ▼ 后台任务
                    ┌─────────────┐
                    │ parse_      │
                    │ document_   │
                    │ task()      │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
      ┌───────────────┐         ┌───────────────┐
      │ DocumentParser│         │ LightRAG      │
      │ .parse()      │         │ insert_       │
      │ 提取文本       │         │ document()    │
      └───────┬───────┘         └───────┬───────┘
              │                         │
              │  parsed_text             │ entities + relations
              ▼                         ▼
      ┌───────────────┐         ┌───────────────┐
      │ Redis         │         │ Neo4j         │
      │ parsed_text   │         │ 知识图谱      │
      └───────────────┘         └───────────────┘
```

---

## 相关文件索引

| 文件 | 职责 |
|------|------|
| `taxlaw-kg/backend/app/api/v1/documents.py` | 上传接口、解析任务 |
| `taxlaw-kg/backend/app/utils/file_parser.py` | 文档解析 (PDF/Word/Excel/Text) |
| `taxlaw-kg/backend/app/services/lightrag_service.py` | LightRAG 封装、实体抽取 |
| `taxlaw-kg/backend/app/database.py` | Redis 模型 (BaseModel, Document, EntityType...) |
| `taxlaw-kg/backend/app/config.py` | 配置管理 (upload_dir, redis_url...) |
