<template>
  <div class="graph-page">
    <div class="header">
      <h2>知识图谱</h2>
      <div class="header-actions">
        <el-button type="primary" @click="refreshGraph">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 统计信息 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-statistic title="节点数量" :value="stats.node_count" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="边数量" :value="stats.edge_count" />
      </el-col>
      <el-col :span="12">
        <div class="entity-types">
          <span class="label">实体类型分布：</span>
          <el-tag
            v-for="(count, type) in stats.entity_type_counts"
            :key="type"
            class="type-tag"
          >
            {{ type }}: {{ count }}
          </el-tag>
        </div>
      </el-col>
    </el-row>

    <!-- 筛选 -->
    <el-card class="filter-card">
      <el-form inline>
        <el-form-item label="实体类型">
          <el-select v-model="filters.entityType" placeholder="全部" clearable @change="fetchNodes">
            <el-option
              v-for="(count, type) in stats.entity_type_counts"
              :key="type"
              :label="type"
              :value="type"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input
            v-model="filters.search"
            placeholder="节点名称"
            clearable
            @change="fetchNodes"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchNodes">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="20">
      <!-- 节点列表 -->
      <el-col :span="8">
        <el-card title="节点列表">
          <el-table
            :data="nodes"
            stripe
            height="500"
            v-loading="loading"
            @row-click="selectNode"
            highlight-current-row
          >
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="entity_type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ row.entity_type }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 图谱可视化 -->
      <el-col :span="16">
        <el-card>
          <div ref="graphContainer" class="graph-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 节点详情 -->
    <el-dialog v-model="showNodeDetail" title="节点详情" width="500px">
      <el-descriptions :column="1" border v-if="selectedNode">
        <el-descriptions-item label="名称">{{ selectedNode.name }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ selectedNode.entity_type }}</el-descriptions-item>
        <el-descriptions-item label="属性">
          <pre>{{ JSON.stringify(selectedNode.attributes, null, 2) }}</pre>
        </el-descriptions-item>
      </el-descriptions>

      <template #footer>
        <el-button @click="showNodeDetail = false">关闭</el-button>
        <el-button type="danger" @click="deleteSelectedNode">删除节点</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import { graphApi, type GraphNode, type GraphStats, type GraphEdge } from '../api'

const loading = ref(false)
const stats = ref<GraphStats>({
  node_count: 0,
  edge_count: 0,
  entity_type_counts: {}
})

const filters = reactive({
  entityType: '',
  search: ''
})

const nodes = ref<GraphNode[]>([])
const edges = ref<GraphEdge[]>([])
const selectedNode = ref<GraphNode | null>(null)
const showNodeDetail = ref(false)

// 图谱容器
const graphContainer = ref<HTMLElement | null>(null)
let graphChart: echarts.ECharts | null = null

const fetchStats = async () => {
  try {
    stats.value = await graphApi.getStats()
  } catch (error) {
    ElMessage.error('获取统计信息失败')
  }
}

const fetchNodes = async () => {
  loading.value = true
  try {
    const response = await graphApi.getNodes({
      entity_type: filters.entityType || undefined,
      search: filters.search || undefined,
      limit: 500
    })
    nodes.value = response.items

    // 同时获取边
    const edgesResponse = await graphApi.getEdges({ limit: 500 })
    edges.value = edgesResponse.items

    // 更新图表
    await nextTick()
    updateChart()
  } catch (error) {
    ElMessage.error('获取节点失败')
  } finally {
    loading.value = false
  }
}

const refreshGraph = () => {
  fetchStats()
  fetchNodes()
}

const selectNode = (row: GraphNode) => {
  selectedNode.value = row
  showNodeDetail.value = true
}

const deleteSelectedNode = async () => {
  if (!selectedNode.value) return

  try {
    await ElMessageBox.confirm('确定要删除此节点吗？', '警告', {
      type: 'warning'
    })
    await graphApi.deleteNode(selectedNode.value.id)
    ElMessage.success('删除成功')
    showNodeDetail.value = false
    refreshGraph()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const updateChart = () => {
  if (!graphContainer.value) return

  if (!graphChart) {
    graphChart = echarts.init(graphContainer.value)
  }

  // 准备 ECharts 数据
  const chartNodes = nodes.value.map((node, index) => ({
    id: String(index),
    name: node.name,
    entityType: node.entity_type,
    draggable: true
  }))

  // 建立节点名称到索引的映射
  const nameToIndex = new Map<string, number>()
  chartNodes.forEach((node, index) => {
    nameToIndex.set(node.name, index)
  })

  const chartEdges = edges.value
    .filter(edge => nameToIndex.has(edge.source_id) && nameToIndex.has(edge.target_id))
    .map(edge => ({
      source: String(nameToIndex.get(edge.source_id)),
      target: String(nameToIndex.get(edge.target_id)),
      label: {
        show: true,
        text: edge.relation_type,
        fontSize: 10
      }
    }))

  const option: echarts.EChartsOption = {
    animation: true,
    tooltip: {
      formatter: (params: any) => {
        if (params.dataType === 'node') {
          return `${params.data.name}<br/>类型: ${params.data.entityType}`
        }
        return params.data.label?.text || ''
      }
    },
    legend: {
      data: Object.keys(stats.value.entity_type_counts)
    },
    series: [{
      type: 'graph',
      layout: 'force',
      symbolSize: 40,
      roam: true,
      draggable: true,
      label: {
        show: true,
        position: 'bottom',
        fontSize: 10
      },
      edgeSymbol: ['circle', 'arrow'],
      edgeSymbolSize: [4, 10],
      data: chartNodes,
      links: chartEdges,
      lineStyle: {
        width: 1,
        curveness: 0.3
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: {
          width: 3
        }
      },
      force: {
        repulsion: 100,
        edgeLength: 100
      }
    }]
  }

  graphChart.setOption(option)
}

onMounted(() => {
  fetchStats()
  fetchNodes()

  // 响应窗口大小变化
  window.addEventListener('resize', () => {
    graphChart?.resize()
  })
})
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

.filter-card {
  margin-bottom: 20px;
}

.graph-container {
  width: 100%;
  height: 500px;
}
</style>
