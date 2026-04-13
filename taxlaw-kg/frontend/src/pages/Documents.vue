<template>
  <div class="documents-page">
    <div class="header">
      <h2>文档管理</h2>
      <el-button type="primary" @click="showUploadDialog = true">
        <el-icon><Upload /></el-icon>
        上传文档
      </el-button>
    </div>

    <!-- 搜索筛选 -->
    <el-card class="filter-card">
      <el-form inline>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable @change="fetchDocuments">
            <el-option label="已完成" value="completed" />
            <el-option label="处理中" value="pending" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input
            v-model="filters.search"
            placeholder="文件名"
            clearable
            @change="fetchDocuments"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchDocuments">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 文档列表 -->
    <el-card>
      <el-table :data="documents" v-loading="loading" stripe>
        <el-table-column prop="original_name" label="文件名" min-width="200" />
        <el-table-column prop="file_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag>{{ row.file_type.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="大小" width="120">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="entity_count" label="实体数" width="100" />
        <el-table-column prop="relation_count" label="关系数" width="100" />
        <el-table-column prop="created_at" label="上传时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewDocument(row)">
              查看
            </el-button>
            <el-button
              link
              type="warning"
              size="small"
              :disabled="row.status === 'pending'"
              @click="reparseDocument(row)"
            >
              重新解析
            </el-button>
            <el-button link type="danger" size="small" @click="deleteDocument(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchDocuments"
          @current-change="fetchDocuments"
        />
      </div>
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传文档" width="500px">
      <el-upload
        ref="uploadRef"
        drag
        :auto-upload="false"
        :limit="10"
        multiple
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        :file-list="fileList"
        accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.md"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖拽文件到此处或 <em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 PDF、Word、Excel、TXT 格式，单文件不超过 50MB，最多上传10个文件</div>
        </template>
      </el-upload>

      <template #footer>
        <el-button @click="handleCloseUpload">取消</el-button>
        <el-button type="primary" :loading="uploading" :disabled="fileList.length === 0" @click="handleUpload">
          上传 {{ fileList.length > 0 ? `(${fileList.length})` : '' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 文档详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="文档详情" width="800px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="文件名">{{ currentDocument?.original_name }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ currentDocument?.file_type }}</el-descriptions-item>
        <el-descriptions-item label="大小">{{ formatFileSize(currentDocument?.file_size || 0) }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentDocument?.status || '')">
            {{ getStatusText(currentDocument?.status || '') }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="实体数">{{ currentDocument?.entity_count }}</el-descriptions-item>
        <el-descriptions-item label="关系数">{{ currentDocument?.relation_count }}</el-descriptions-item>
        <el-descriptions-item label="上传时间" :span="2">
          {{ currentDocument?.created_at }}
        </el-descriptions-item>
      </el-descriptions>

      <el-divider />
      <h4>解析内容预览</h4>
      <div class="parsed-content">
        {{ currentDocument?.parsed_text || '暂无内容' }}
      </div>

      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadInstance, UploadRawFile, UploadUserFile } from 'element-plus'
import { documentApi, type Document } from '../api'

const loading = ref(false)
const documents = ref<Document[]>([])

const filters = reactive({
  status: '',
  search: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const fetchDocuments = async () => {
  loading.value = true
  try {
    const response = await documentApi.list({
      page: pagination.page,
      page_size: pagination.pageSize,
      status: filters.status || undefined,
      search: filters.search || undefined
    })
    documents.value = response.items
    pagination.total = response.total
  } catch (error) {
    ElMessage.error('获取文档列表失败')
  } finally {
    loading.value = false
  }
}

const formatFileSize = (size: number) => {
  if (!size) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let index = 0
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024
    index++
  }
  return `${size.toFixed(2)} ${units[index]}`
}

const getStatusType = (status: string) => {
  switch (status) {
    case 'completed':
      return 'success'
    case 'failed':
      return 'danger'
    default:
      return 'warning'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'completed':
      return '已完成'
    case 'failed':
      return '失败'
    case 'pending':
      return '处理中'
    default:
      return status
  }
}

// 上传
const showUploadDialog = ref(false)
const uploadRef = ref<UploadInstance>()
const fileList = ref<UploadUserFile[]>([])
const uploading = ref(false)

const handleFileChange = (uploadFile: UploadUserFile) => {
  // el-upload with auto-upload=false stores the raw file in uploadFile.raw
  const raw = (uploadFile as any).raw as UploadRawFile | undefined
  if (raw && !fileList.value.find(f => f.name === uploadFile.name)) {
    fileList.value = [...fileList.value, uploadFile]
  }
}

const handleFileRemove = (uploadFile: UploadUserFile) => {
  fileList.value = fileList.value.filter(f => f.name !== uploadFile.name)
}

const handleCloseUpload = () => {
  showUploadDialog.value = false
  fileList.value = []
}

const handleUpload = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择文件')
    return
  }

  uploading.value = true
  let successCount = 0
  let failCount = 0

  for (const file of fileList.value) {
    const raw = (file as any).raw as UploadRawFile | undefined
    if (!raw) continue

    const formData = new FormData()
    formData.append('file', raw)

    try {
      await documentApi.upload(formData)
      successCount++
    } catch (error) {
      failCount++
      console.error(`文件 ${file.name} 上传失败:`, error)
    }
  }

  uploading.value = false

  if (failCount === 0) {
    ElMessage.success(`成功上传 ${successCount} 个文件`)
  } else if (successCount === 0) {
    ElMessage.error(`上传失败`)
  } else {
    ElMessage.warning(`成功 ${successCount} 个，失败 ${failCount} 个`)
  }

  showUploadDialog.value = false
  fileList.value = []
  fetchDocuments()
}

// 查看
const showDetailDialog = ref(false)
const currentDocument = ref<Document | null>(null)

const viewDocument = (doc: Document) => {
  currentDocument.value = doc
  showDetailDialog.value = true
}

// 重新解析
const reparseDocument = async (doc: Document) => {
  try {
    await ElMessageBox.confirm('确定要重新解析此文档吗？', '提示', {
      type: 'warning'
    })
    await documentApi.reparse(doc.id)
    ElMessage.success('重新解析任务已提交')
    fetchDocuments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

// 删除
const deleteDocument = async (doc: Document) => {
  try {
    await ElMessageBox.confirm('确定要删除此文档吗？', '警告', {
      type: 'warning'
    })
    await documentApi.delete(doc.id)
    ElMessage.success('删除成功')
    fetchDocuments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchDocuments()
})
</script>

<style scoped>
.documents-page {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
}

.filter-card {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.parsed-content {
  max-height: 400px;
  overflow-y: auto;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  white-space: pre-wrap;
  font-size: 13px;
  line-height: 1.6;
}
</style>
