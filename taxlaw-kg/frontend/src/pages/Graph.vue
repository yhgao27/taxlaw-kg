<template>
  <div class="graph-page">
    <div class="header">
      <h2>知识图谱</h2>
      <div class="header-actions">
        <el-button type="primary" @click="handleAddNode">
          <el-icon><Plus /></el-icon>
          新增节点
        </el-button>
        <el-button @click="handleFitView">
          <el-icon><FullScreen /></el-icon>
          自适应
        </el-button>
        <el-button @click="graphComposable.refresh()">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 统计信息 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-statistic title="节点数量" :value="graphComposable.state.stats.node_count" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="边数量" :value="graphComposable.state.stats.edge_count" />
      </el-col>
      <el-col :span="12">
        <div class="entity-types">
          <span class="label">实体类型分布：</span>
          <el-tag
            v-for="(count, type) in graphComposable.state.stats.entity_type_counts"
            :key="type"
            class="type-tag"
            size="small"
          >
            {{ type }}: {{ count }}
          </el-tag>
        </div>
      </el-col>
    </el-row>

    <!-- 图谱区域 -->
    <el-row :gutter="20">
      <!-- 左侧：图谱可视化 -->
      <el-col :span="graphComposable.selectedItem.value.type ? 16 : 24">
        <el-card class="graph-card">
          <div ref="graphContainer" class="graph-container"></div>
        </el-card>
      </el-col>

      <!-- 右侧：属性编辑面板 -->
      <el-col :span="8" v-if="graphComposable.selectedItem.value.type">
        <el-card title="属性编辑" class="property-panel">
          <template #header>
            <div class="panel-header">
              <span>{{ graphComposable.selectedItem.value.type === 'node' ? '节点' : '关系' }}属性</span>
              <el-button
                :type="graphComposable.selectedItem.value.type === 'node' ? 'danger' : 'danger'"
                size="small"
                link
                @click="handleDelete"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </template>

          <!-- 节点属性编辑 -->
          <el-form v-if="graphComposable.selectedItem.value.type === 'node'" :model="nodeForm" label-width="80px">
            <el-form-item label="名称">
              <el-input v-model="nodeForm.name" placeholder="节点名称" />
            </el-form-item>
            <el-form-item label="类型">
              <el-select v-model="nodeForm.entity_type" placeholder="选择类型">
                <el-option
                  v-for="(count, type) in graphComposable.state.stats.entity_type_counts"
                  :key="type"
                  :label="type"
                  :value="type"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="属性">
              <div v-for="(value, key) in nodeForm.properties" :key="key" class="property-item">
                <el-input v-model="nodeForm.properties[key]" :placeholder="String(key)">
                  <template #prepend>{{ key }}</template>
                </el-input>
              </div>
              <el-button size="small" @click="addProperty" class="mt-10">
                <el-icon><Plus /></el-icon> 添加属性
              </el-button>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleUpdateNode" :loading="saving">
                保存修改
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 边属性编辑 -->
          <el-form v-if="graphComposable.selectedItem.value.type === 'edge'" :model="edgeForm" label-width="80px">
            <el-form-item label="源节点">
              <span>{{ edgeForm.source }}</span>
            </el-form-item>
            <el-form-item label="目标节点">
              <span>{{ edgeForm.target }}</span>
            </el-form-item>
            <el-form-item label="关系类型">
              <el-select v-model="edgeForm.relation_type" placeholder="选择关系类型">
                <el-option
                  v-for="type in relationTypes"
                  :key="type"
                  :label="type"
                  :value="type"
                />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleUpdateEdge" :loading="saving">
                保存修改
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- 新增节点对话框 -->
    <el-dialog v-model="showAddNodeDialog" title="新增节点" width="500px">
      <el-form :model="newNodeForm" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="newNodeForm.name" placeholder="节点名称" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="newNodeForm.entity_type" placeholder="选择类型">
            <el-option
              v-for="(count, type) in graphComposable.state.stats.entity_type_counts"
              :key="type"
              :label="type"
              :value="type"
            />
            <el-option label="自定义" value="__custom__" />
          </el-select>
        </el-form-item>
        <el-form-item label="自定义类型" v-if="newNodeForm.entity_type === '__custom__'">
          <el-input v-model="newNodeForm.custom_type" placeholder="输入自定义类型" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddNodeDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAddNode" :loading="saving">确定</el-button>
      </template>
    </el-dialog>

    <!-- 新增关系对话框 -->
    <el-dialog v-model="showAddEdgeDialog" title="新增关系" width="500px">
      <el-form :model="newEdgeForm" label-width="80px">
        <el-form-item label="源节点">
          <el-select v-model="newEdgeForm.source_id" placeholder="选择源节点">
            <el-option
              v-for="node in graphComposable.state.nodes"
              :key="node.id"
              :label="node.name"
              :value="node.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="目标节点">
          <el-select v-model="newEdgeForm.target_id" placeholder="选择目标节点">
            <el-option
              v-for="node in graphComposable.state.nodes"
              :key="node.id"
              :label="node.name"
              :value="node.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关系类型" required>
          <el-select v-model="newEdgeForm.relation_type" placeholder="选择关系类型">
            <el-option
              v-for="type in relationTypes"
              :key="type"
              :label="type"
              :value="type"
            />
            <el-option label="自定义" value="__custom__" />
          </el-select>
        </el-form-item>
        <el-form-item label="自定义类型" v-if="newEdgeForm.relation_type === '__custom__'">
          <el-input v-model="newEdgeForm.custom_relation_type" placeholder="输入自定义关系类型" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddEdgeDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAddEdge" :loading="saving">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { Plus, FullScreen, Refresh, Delete } from '@element-plus/icons-vue'
import { useGraph } from '../composables/useGraph'
import type { GraphNode, GraphEdge } from '../api'

// 图谱容器引用
const graphContainer = ref<HTMLElement | null>(null)

// 初始化 G6 composable
const graphComposable = useGraph(graphContainer)

// 选中的节点/边表单
const nodeForm = reactive({
  id: '',
  name: '',
  entity_type: '',
  properties: {} as Record<string, any>
})

const edgeForm = reactive({
  id: '',
  source: '',
  target: '',
  relation_type: '',
  old_relation_type: ''
})

// 新增节点表单
const newNodeForm = reactive({
  name: '',
  entity_type: '',
  custom_type: '',
  attributes: {} as Record<string, any>
})

// 新增边表单
const newEdgeForm = reactive({
  source_id: '',
  target_id: '',
  relation_type: '',
  custom_relation_type: ''
})

// 对话框状态
const showAddNodeDialog = ref(false)
const showAddEdgeDialog = ref(false)
const saving = ref(false)

// 预定义关系类型
const relationTypes = [
  '属于', '包含', '关联', '实施', '适用于', '参照', '缴纳', '申报', '扣除', '减免'
]

// 监听选中项变化，更新表单
watch(() => graphComposable.selectedItem.value, (newVal) => {
  if (newVal.type === 'node' && newVal.data) {
    nodeForm.id = newVal.data.id
    nodeForm.name = newVal.data.label
    nodeForm.entity_type = newVal.data.entity_type
    nodeForm.properties = { ...(newVal.data.attributes || {}) }
  } else if (newVal.type === 'edge' && newVal.data) {
    edgeForm.id = newVal.data.id || ''
    edgeForm.source = newVal.data.source
    edgeForm.target = newVal.data.target
    edgeForm.relation_type = newVal.data.label || ''
    edgeForm.old_relation_type = newVal.data.label || ''
  }
}, { immediate: true })

// ============================================
// 事件处理
// ============================================

/**
 * 新增节点
 */
const handleAddNode = () => {
  showAddNodeDialog.value = true
  newNodeForm.name = ''
  newNodeForm.entity_type = ''
  newNodeForm.custom_type = ''
  newNodeForm.attributes = {}
}

/**
 * 确认新增节点
 */
const confirmAddNode = async () => {
  if (!newNodeForm.name) return

  saving.value = true
  try {
    const entityType = newNodeForm.entity_type === '__custom__'
      ? newNodeForm.custom_type
      : newNodeForm.entity_type

    await graphComposable.addNode({
      name: newNodeForm.name,
      entity_type: entityType,
      attributes: newNodeForm.attributes
    })
    showAddNodeDialog.value = false
  } finally {
    saving.value = false
  }
}

/**
 * 新增关系
 */
const handleAddEdge = () => {
  showAddEdgeDialog.value = true
  newEdgeForm.source_id = ''
  newEdgeForm.target_id = ''
  newEdgeForm.relation_type = ''
  newEdgeForm.custom_relation_type = ''
}

/**
 * 确认新增关系
 */
const confirmAddEdge = async () => {
  if (!newEdgeForm.source_id || !newEdgeForm.target_id || !newEdgeForm.relation_type) return

  saving.value = true
  try {
    const relationType = newEdgeForm.relation_type === '__custom__'
      ? newEdgeForm.custom_relation_type
      : newEdgeForm.relation_type

    await graphComposable.addEdge({
      source_id: newEdgeForm.source_id,
      target_id: newEdgeForm.target_id,
      relation_type: relationType
    })
    showAddEdgeDialog.value = false
  } finally {
    saving.value = false
  }
}

/**
 * 更新节点
 */
const handleUpdateNode = async () => {
  saving.value = true
  try {
    await graphComposable.updateNode(nodeForm.id, {
      name: nodeForm.name,
      entity_type: nodeForm.entity_type,
      attributes: nodeForm.properties
    })
  } finally {
    saving.value = false
  }
}

/**
 * 更新边
 */
const handleUpdateEdge = async () => {
  saving.value = true
  try {
    await graphComposable.updateEdge(
      edgeForm.source,
      edgeForm.target,
      edgeForm.old_relation_type,
      edgeForm.relation_type
    )
  } finally {
    saving.value = false
  }
}

/**
 * 删除选中项
 */
const handleDelete = async () => {
  if (graphComposable.selectedItem.value.type === 'node') {
    await graphComposable.removeNode(graphComposable.selectedItem.value.id!)
  } else if (graphComposable.selectedItem.value.type === 'edge') {
    // G6 v4 下 edgeForm.source 和 edgeForm.target 是节点 ID
    await graphComposable.removeEdge(
      edgeForm.source,
      edgeForm.target,
      edgeForm.old_relation_type
    )
  }
}

/**
 * 添加属性
 */
const addProperty = () => {
  const key = `属性${Object.keys(nodeForm.properties).length + 1}`
  nodeForm.properties[key] = ''
}

/**
 * 自适应画布
 */
const handleFitView = () => {
  graphComposable.fitView()
}
</script>

<style scoped>
.graph-page {
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

.header-actions {
  display: flex;
  gap: 10px;
}

.stats-row {
  margin-bottom: 20px;
}

.entity-types {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.entity-types .label {
  font-weight: bold;
  color: #666;
}

.type-tag {
  margin-right: 5px;
}

.graph-card {
  height: calc(100vh - 280px);
  min-height: 500px;
}

.graph-card :deep(.el-card__body) {
  height: 100%;
  padding: 0;
}

.graph-container {
  width: 100%;
  height: 100%;
  min-height: 500px;
  background: #fafafa;
}

.property-panel {
  height: calc(100vh - 280px);
  min-height: 500px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.property-item {
  margin-bottom: 8px;
}

.mt-10 {
  margin-top: 10px;
}
</style>
