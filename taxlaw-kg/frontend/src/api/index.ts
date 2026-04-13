import request from './request'

// ============================================
// 认证相关
// ============================================
export interface LoginForm {
  username: string
  password: string
}

export interface RegisterForm {
  username: string
  password: string
  role?: string
}

export interface User {
  id: string
  username: string
  role: string
  is_active: boolean
  created_at: string
}

export interface Token {
  access_token: string
  token_type: string
}

export const authApi = {
  login: (data: LoginForm) => request.post<Token>('/v1/auth/login', data),
  register: (data: RegisterForm) => request.post<User>('/v1/auth/register', data),
  getMe: () => request.get<User>('/v1/auth/me')
}

// ============================================
// Schema 相关
// ============================================
export interface EntityType {
  id: string
  name: string
  description: string
  required_attributes: string[]
  optional_attributes: string[]
  is_system: boolean
  created_at: string
}

export interface RelationType {
  id: string
  name: string
  source_type: string
  target_type: string
  description: string
  is_system: boolean
  created_at: string
}

export const schemaApi = {
  getEntityTypes: () => request.get<EntityType[]>('/v1/schema/entity-types'),
  getRelationTypes: () => request.get<RelationType[]>('/v1/schema/relation-types'),
  createEntityType: (data: Partial<EntityType>) => request.post<EntityType>('/v1/schema/entity-types', data),
  updateEntityType: (id: string, data: Partial<EntityType>) => request.put<EntityType>(`/v1/schema/entity-types/${id}`, data),
  deleteEntityType: (id: string) => request.delete(`/v1/schema/entity-types/${id}`),
  createRelationType: (data: Partial<RelationType>) => request.post<RelationType>('/v1/schema/relation-types', data),
  updateRelationType: (id: string, data: Partial<RelationType>) => request.put<RelationType>(`/v1/schema/relation-types/${id}`, data),
  deleteRelationType: (id: string) => request.delete(`/v1/schema/relation-types/${id}`),
  createTaxTemplate: () => request.post('/v1/schema/template/tax-default')
}

// ============================================
// 文档相关
// ============================================
export interface Document {
  id: string
  filename: string
  original_name: string
  file_path: string
  file_type: string
  file_size: number
  status: string
  parsed_text?: string
  chunk_count?: number
  entity_count?: number
  relation_count?: number
  created_at: string
}

export interface DocumentListResponse {
  items: Document[]
  total: number
  page: number
  page_size: number
}

export const documentApi = {
  upload: (file: FormData) => request.post('/v1/documents/upload', file, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  list: (params?: { page?: number; page_size?: number; status?: string; search?: string }) =>
    request.get<DocumentListResponse>('/v1/documents', { params }),
  get: (id: string) => request.get<Document>(`/v1/documents/${id}`),
  delete: (id: string) => request.delete(`/v1/documents/${id}`),
  reparse: (id: string) => request.post(`/v1/documents/${id}/reparse`)
}

// ============================================
// 图谱相关
// ============================================
export interface GraphNode {
  id: string
  name: string
  entity_type: string
  attributes: Record<string, any>
}

export interface GraphEdge {
  id?: string
  source_id: string
  target_id: string
  relation_type: string
}

export interface GraphStats {
  node_count: number
  edge_count: number
  entity_type_counts: Record<string, number>
}

export interface GraphNodesResponse {
  items: GraphNode[]
  total: number
}

export interface GraphEdgesResponse {
  items: GraphEdge[]
  total: number
}

export const graphApi = {
  getStats: () => request.get<GraphStats>('/v1/graph/stats'),
  getNodes: (params?: { entity_type?: string; search?: string; limit?: number; offset?: number }) =>
    request.get<GraphNodesResponse>('/v1/graph/nodes', { params }),
  getEdges: (params?: { source_type?: string; target_type?: string; relation_type?: string; limit?: number; offset?: number }) =>
    request.get<GraphEdgesResponse>('/v1/graph/edges', { params }),
  createNode: (data: Partial<GraphNode>) => request.post<GraphNode>('/v1/graph/nodes', data),
  updateNode: (nodeId: string, data: Partial<GraphNode>) => request.put(`/v1/graph/nodes/${nodeId}`, data),
  deleteNode: (nodeId: string) => request.delete(`/v1/graph/nodes/${nodeId}`),
  createEdge: (data: Partial<GraphEdge>) => request.post<GraphEdge>('/v1/graph/edges', data),
  deleteEdge: (sourceId: string, targetId: string, relationType: string) =>
    request.delete('/v1/graph/edges', { params: { source_id: sourceId, target_id: targetId, relation_type: relationType } })
}

// ============================================
// 问答相关
// ============================================
export interface QueryRequest {
  question: string
  use_kg?: boolean
  use_vector?: boolean
  top_k?: number
}

export interface Source {
  type: string
  content: string
  document_id?: string
  document_name?: string
  relevance_score?: number
}

export interface QueryResponse {
  answer: string
  sources: Source[]
  related_questions: string[]
}

export const queryApi = {
  ask: (data: QueryRequest) => request.post<QueryResponse>('/v1/query/ask', data),
  getSchemaContext: () => request.get('/v1/query/schema-context')
}
