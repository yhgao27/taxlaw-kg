<template>
  <div class="dashboard">
    <h1>欢迎使用税务法规知识库</h1>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #409eff">
              <el-icon size="30"><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.documentCount }}</div>
              <div class="stat-label">文档数量</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #67c23a">
              <el-icon size="30"><User /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.entityCount }}</div>
              <div class="stat-label">实体数量</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #e6a23c">
              <el-icon size="30"><Connection /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.relationCount }}</div>
              <div class="stat-label">关系数量</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background-color: #f56c6c">
              <el-icon size="30"><ChatDotRound /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.schemaTypeCount }}</div>
              <div class="stat-label">Schema 类型</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷入口 -->
    <el-card class="quick-actions">
      <template #header>
        <span>快捷入口</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="quick-action-item" @click="$router.push('/documents')">
            <el-icon size="40" color="#409eff"><Upload /></el-icon>
            <span>上传文档</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="quick-action-item" @click="$router.push('/schema')">
            <el-icon size="40" color="#67c23a"><Setting /></el-icon>
            <span>管理 Schema</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="quick-action-item" @click="$router.push('/graph')">
            <el-icon size="40" color="#e6a23c"><Share /></el-icon>
            <span>查看图谱</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="quick-action-item" @click="$router.push('/query')">
            <el-icon size="40" color="#f56c6c"><ChatDotRound /></el-icon>
            <span>智能问答</span>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 最新文档 -->
    <el-card class="recent-docs">
      <template #header>
        <span>最新文档</span>
      </template>
      <el-table :data="recentDocs" style="width: 100%">
        <el-table-column prop="original_name" label="文件名" />
        <el-table-column prop="file_type" label="类型" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { documentApi, schemaApi, graphApi } from '../api'
import { ElMessage } from 'element-plus'

const stats = ref({
  documentCount: 0,
  entityCount: 0,
  relationCount: 0,
  schemaTypeCount: 0
})

const recentDocs = ref([])

const fetchStats = async () => {
  try {
    const [docs, entityTypes, relationTypes, graphStats] = await Promise.all([
      documentApi.list({ page_size: 100 }),
      schemaApi.getEntityTypes(),
      schemaApi.getRelationTypes(),
      graphApi.getStats()
    ])

    stats.value = {
      documentCount: docs.total,
      entityCount: graphStats.node_count,
      relationCount: graphStats.edge_count,
      schemaTypeCount: entityTypes.length + relationTypes.length
    }

    recentDocs.value = docs.items.slice(0, 5)
  } catch (error) {
    ElMessage.error('获取统计数据失败')
  }
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

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.dashboard h1 {
  margin-bottom: 30px;
  color: #333;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #999;
}

.quick-actions {
  margin-bottom: 20px;
}

.quick-action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 30px;
  cursor: pointer;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.quick-action-item:hover {
  background-color: #f5f7fa;
}

.quick-action-item span {
  font-size: 16px;
  color: #666;
}
</style>
