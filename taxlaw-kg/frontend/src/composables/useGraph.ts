/**
 * useGraph - G6 v4 图谱编辑 Composable
 *
 * G6 v4 API:
 * - 初始化: new G6.Graph({ container, ... })
 * - 数据: graph.data(data) then graph.render()
 * - 标签: labelCfg.style inside node style
 * - 事件: 'node:click' string events
 * - 更新: graph.changeData() for full update
 * - 增删: graph.addItem(), graph.removeItem(), graph.updateItem()
 */

import { ref, reactive, onMounted, onUnmounted, nextTick, type Ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Graph } from '@antv/g6'
import { graphApi, type GraphNode, type GraphEdge, type GraphStats } from '../api'

// 图谱状态
export interface GraphState {
  nodes: GraphNode[]
  edges: GraphEdge[]
  stats: GraphStats
  loading: boolean
}

// 选中项
export interface SelectedItem {
  type: 'node' | 'edge' | null
  id: string | null
  data: any
}

export function useGraph(containerRef: Ref<HTMLElement | null>) {
  // 状态
  const state = reactive<GraphState>({
    nodes: [],
    edges: [],
    stats: {
      node_count: 0,
      edge_count: 0,
      entity_type_counts: {}
    },
    loading: false
  })

  const selectedItem = ref<SelectedItem>({
    type: null,
    id: null,
    data: null
  })

  // 隐藏的节点ID集合
  const hiddenNodeIds = ref<Set<string>>(new Set())

  // G6 Graph 实例
  let graph: Graph | null = null

  // ============================================
  // G6 v4 初始化
  // ============================================
  const initGraph = () => {
    if (!containerRef.value) {
      console.error('Graph container not found')
      return
    }

    const container = containerRef.value
    console.log('Initializing G6 v4, container size:', container.clientWidth, container.clientHeight)

    // G6 v4: 创建 Graph 实例
    graph = new Graph({
      container: container,
      width: container.clientWidth || 800,
      height: container.clientHeight || 600,
      // 默认节点样式
      defaultNode: {
        type: 'circle',
        size: 100,
        style: {
          fill: '#3066BE',
          stroke: '#143F8A',
          lineWidth: 2,
          cursor: 'pointer'
        },
        labelCfg: {
          position: 'center',
          style: {
            fill: '#ffffff',
            fontSize: 12,
            fontWeight: 500,
            labelWordWrap: true,
            labelMaxWidth: 80,
            labelOverflow: 'ellipsis',
            labelText: (d: any) => d.model.label || d.id || ''
          }
        }
      },
      // 默认边样式
      defaultEdge: {
        type: 'quadratic',
        style: {
          stroke: '#B4B4B4',
          lineWidth: 1.5,
          endArrow: true,
          cursor: 'pointer'
        }
      },
      // 布局
      layout: {
        type: 'force',
        preventOverlap: true,
        nodeSize: 40,
        linkDistance: 100,
        nodeStrength: -50,
        edgeStrength: 0.1,
        collideStrength: 0.8,
        alpha: 0.1,
        alphaDecay: 0.05,
        alphaMin: 0.001
      },
      // 交互模式
      modes: {
        default: ['drag-canvas', 'zoom-canvas', 'drag-node', 'tooltip']
      },
      // tooltip 配置
      tooltip: {
        showTimeout: 200,
        hideTimeout: 100,
        offsetX: 10,
        offsetY: 10,
        getTooltip: (e: any) => {
          const model = e.item.getModel()
          return [
            { name: '名称', value: model.label || model.id || '' },
            { name: '类型', value: model.entity_type || '-' }
          ]
        }
      },
      // 动画
      animate: false,
      // 自动适应
      fitView: true,
      fitViewPadding: 50
    })

    // 绑定事件
    bindEvents()

    // 加载数据
    loadData()
  }

  // ============================================
  // 事件绑定 (G6 v4)
  // ============================================
  const bindEvents = () => {
    if (!graph) return

    // 点击节点
    graph.on('node:click', (evt: any) => {
      const { item, target } = evt
      const model = item.getModel()
      console.log('Node clicked:', model)

      selectedItem.value = {
        type: 'node',
        id: model.id,
        data: model
      }
      highlightNeighbors(model.id)
    })

    // 点击边
    graph.on('edge:click', (evt: any) => {
      const { item, target } = evt
      const model = item.getModel()
      console.log('Edge clicked:', model)

      selectedItem.value = {
        type: 'edge',
        id: model.id,
        data: model
      }
    })

    // 点击画布
    graph.on('canvas:click', () => {
      clearHighlight()
      selectedItem.value = { type: null, id: null, data: null }
    })

    // Hover 节点
    graph.on('node:mouseenter', (evt: any) => {
      const { item } = evt
      graph!.setItemState(item, 'hover', true)
    })

    graph.on('node:mouseleave', (evt: any) => {
      const { item } = evt
      graph!.setItemState(item, 'hover', false)
    })
  }

  // ============================================
  // 高亮邻居并隐藏无关节点
  // ============================================
  const highlightNeighbors = (nodeId: string) => {
    if (!graph) return

    clearHighlight()

    // 获取邻居节点
    const neighbors = graph.getNeighbors(nodeId, 'all')
    const neighborIds = new Set(neighbors.map((n: any) => n.getModel().id))
    neighborIds.add(nodeId)

    // 获取所有节点，隐藏非邻居节点
    const allNodes = graph.getNodes()
    hiddenNodeIds.value.clear()

    allNodes.forEach((node: any) => {
      const model = node.getModel()
      if (!neighborIds.has(model.id)) {
        graph!.hideItem(node)
        hiddenNodeIds.value.add(model.id)
      }
    })

    // 获取相关边
    const edges = graph.getEdges()
    edges.forEach((edge: any) => {
      const model = edge.getModel()
      if (model.source === nodeId || model.target === nodeId) {
        graph!.setItemState(edge, 'highlight', true)
      }
    })

    // 高亮邻居节点
    neighbors.forEach((node: any) => {
      graph!.setItemState(node, 'highlight', true)
    })
  }

  // ============================================
  // 清除高亮并恢复显示所有节点
  // ============================================
  const clearHighlight = () => {
    if (!graph) return

    // 恢复显示已隐藏的节点
    const allNodes = graph.getNodes()
    allNodes.forEach((node: any) => {
      const model = node.getModel()
      if (hiddenNodeIds.value.has(model.id)) {
        graph!.showItem(node)
      }
      graph!.clearItemStates(node)
    })
    hiddenNodeIds.value.clear()

    // 清除边的高亮
    const edges = graph.getEdges()
    edges.forEach((edge: any) => {
      graph!.clearItemStates(edge)
    })
  }

  // ============================================
  // 数据加载
  // ============================================
  const loadData = async () => {
    state.loading = true
    try {
      const [nodesRes, edgesRes, statsRes] = await Promise.all([
        graphApi.getNodes({ limit: 500 }),
        graphApi.getEdges({ limit: 500 }),
        graphApi.getStats()
      ])

      state.nodes = nodesRes.items
      state.edges = edgesRes.items
      state.stats = statsRes

      updateGraphData()
    } catch (error) {
      ElMessage.error('加载图谱数据失败')
      console.error(error)
    } finally {
      state.loading = false
    }
  }

  // ============================================
  // 更新 G6 图数据 (G6 v4)
  // ============================================
  const updateGraphData = () => {
    if (!graph) return

    // G6 v4 数据格式
    const g6Nodes = state.nodes.map(node => ({
      id: node.name,
      label: node.name,
      entity_type: node.entity_type,
      attributes: node.attributes || {}
    }))

    const g6Edges = state.edges.map(edge => ({
      id: edge.id || `${edge.source_id}-${edge.target_id}-${edge.relation_type}`,
      source: edge.source_id,
      target: edge.target_id,
      label: edge.relation_type
    }))

    console.log('G6 v4 data:', g6Nodes.length, 'nodes', g6Edges.length, 'edges')

    // G6 v4: 设置数据并渲染
    graph.data({
      nodes: g6Nodes,
      edges: g6Edges
    })

    graph.render()

    // 渲染完成后适应视图
    setTimeout(() => {
      graph?.fitView()
    }, 500)
  }

  // ============================================
  // 节点操作
  // ============================================
  const addNode = async (data: Partial<GraphNode>): Promise<boolean> => {
    if (!graph) return false

    try {
      const created = await graphApi.createNode(data)

      const newNode: GraphNode = {
        id: created.id || `node-${Date.now()}`,
        name: data.name!,
        entity_type: data.entity_type!,
        attributes: data.attributes || {}
      }

      state.nodes.push(newNode)

      // G6 v4 添加节点
      graph.addItem('node', {
        id: newNode.name,
        label: newNode.name,
        entity_type: newNode.entity_type,
        attributes: newNode.attributes
      })

      ElMessage.success('节点创建成功')
      return true
    } catch (error) {
      ElMessage.error('节点创建失败')
      return false
    }
  }

  const updateNode = async (nodeId: string, data: Partial<GraphNode>): Promise<boolean> => {
    if (!graph) return false

    try {
      const actualNode = state.nodes.find(n => n.name === nodeId)
      await graphApi.updateNode(actualNode?.id || nodeId, data)

      const index = state.nodes.findIndex(n => n.name === nodeId)
      if (index !== -1) {
        state.nodes[index] = { ...state.nodes[index], ...data }
      }

      // G6 v4 更新节点
      graph.updateItem(nodeId, {
        label: data.name ?? nodeId,
        entity_type: data.entity_type,
        attributes: data.attributes
      })

      ElMessage.success('节点更新成功')
      return true
    } catch (error) {
      ElMessage.error('节点更新失败')
      return false
    }
  }

  const removeNode = async (nodeId: string): Promise<boolean> => {
    if (!graph) return false

    try {
      await ElMessageBox.confirm('确定要删除此节点吗？', '警告', {
        type: 'warning'
      })

      const actualNode = state.nodes.find(n => n.name === nodeId)
      await graphApi.deleteNode(actualNode?.id || nodeId)

      state.nodes = state.nodes.filter(n => n.name !== nodeId)
      state.edges = state.edges.filter(e => e.source_id !== nodeId && e.target_id !== nodeId)

      // G6 v4 移除节点
      graph.removeItem(nodeId)

      selectedItem.value = { type: null, id: null, data: null }
      ElMessage.success('节点删除成功')
      return true
    } catch (error) {
      if (error !== 'cancel') {
        ElMessage.error('节点删除失败')
      }
      return false
    }
  }

  // ============================================
  // 边操作
  // ============================================
  const addEdge = async (data: Partial<GraphEdge>): Promise<boolean> => {
    if (!graph) return false

    try {
      const created = await graphApi.createEdge(data)

      const newEdge: GraphEdge = {
        id: created.id || `edge-${Date.now()}`,
        source_id: data.source_id!,
        target_id: data.target_id!,
        relation_type: data.relation_type!
      }

      state.edges.push(newEdge)

      // G6 v4 添加边
      graph.addItem('edge', {
        id: newEdge.id,
        source: data.source_id,
        target: data.target_id,
        label: data.relation_type
      })

      ElMessage.success('关系创建成功')
      return true
    } catch (error) {
      ElMessage.error('关系创建失败')
      return false
    }
  }

  const updateEdge = async (
    sourceId: string,
    targetId: string,
    oldRelationType: string,
    newRelationType: string
  ): Promise<boolean> => {
    if (!graph) return false

    try {
      await graphApi.deleteEdge(sourceId, targetId, oldRelationType)
      await graphApi.createEdge({
        source_id: sourceId,
        target_id: targetId,
        relation_type: newRelationType
      })

      const index = state.edges.findIndex(
        e => e.source_id === sourceId && e.target_id === targetId && e.relation_type === oldRelationType
      )
      if (index !== -1) {
        state.edges[index].relation_type = newRelationType
      }

      // G6 v4 更新边 - 找到对应的边并更新
      const edges = graph.getEdges()
      const edgeRecord = edges.find((edge: any) => {
        const model = edge.getModel()
        return model.source === sourceId && model.target === targetId && model.label === oldRelationType
      })

      if (edgeRecord) {
        graph.updateItem(edgeRecord, {
          label: newRelationType
        })
      }

      ElMessage.success('关系更新成功')
      return true
    } catch (error) {
      ElMessage.error('关系更新失败')
      return false
    }
  }

  const removeEdge = async (sourceId: string, targetId: string, relationType: string): Promise<boolean> => {
    if (!graph) return false

    try {
      await ElMessageBox.confirm('确定要删除此关系吗？', '警告', {
        type: 'warning'
      })

      await graphApi.deleteEdge(sourceId, targetId, relationType)

      state.edges = state.edges.filter(
        e => !(e.source_id === sourceId && e.target_id === targetId && e.relation_type === relationType)
      )

      // G6 v4 移除边 - 找到对应的边并删除
      const edges = graph.getEdges()
      const edgeRecord = edges.find((edge: any) => {
        const model = edge.getModel()
        return model.source === sourceId && model.target === targetId && model.label === relationType
      })

      if (edgeRecord) {
        graph.removeItem(edgeRecord)
      }

      selectedItem.value = { type: null, id: null, data: null }
      ElMessage.success('关系删除成功')
      return true
    } catch (error) {
      if (error !== 'cancel') {
        ElMessage.error('关系删除失败')
      }
      return false
    }
  }

  // ============================================
  // 画布操作
  // ============================================
  const refresh = () => {
    loadData()
  }

  const fitView = () => {
    graph?.fitView()
  }

  const zoom = (ratio: number) => {
    if (!graph) return
    const zoomRatio = graph.getZoom()
    graph.zoomTo(ratio, undefined)
  }

  // ============================================
  // 生命周期
  // ============================================
  const resize = () => {
    if (!graph || !containerRef.value) return
    graph.changeSize(containerRef.value.clientWidth, containerRef.value.clientHeight)
  }

  onMounted(async () => {
    await nextTick()

    if (containerRef.value) {
      const container = containerRef.value
      if (container.clientWidth === 0 || container.clientHeight === 0) {
        container.style.width = '800px'
        container.style.height = '600px'
      }
    }

    initGraph()
    window.addEventListener('resize', resize)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', resize)
    graph?.destroy()
  })

  // ============================================
  // 导出
  // ============================================
  return {
    state,
    selectedItem,
    graph: () => graph,
    loadData,
    refresh,
    addNode,
    updateNode,
    removeNode,
    addEdge,
    updateEdge,
    removeEdge,
    fitView,
    zoom,
    resize
  }
}
