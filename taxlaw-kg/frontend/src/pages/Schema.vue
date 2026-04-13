<template>
  <div class="schema-page">
    <div class="header">
      <h2>Schema 管理</h2>
      <div class="header-actions">
        <el-button type="success" @click="createTaxTemplate">
          <el-icon><DocumentAdd /></el-icon>
          创建税务默认模板
        </el-button>
        <el-button type="primary" @click="showEntityDialog = true">
          <el-icon><Plus /></el-icon>
          新增实体类型
        </el-button>
        <el-button type="primary" @click="showRelationDialog = true">
          <el-icon><Plus /></el-icon>
          新增关系类型
        </el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <!-- 实体类型 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>实体类型 ({{ entityTypes.length }})</span>
          </template>

          <el-table :data="entityTypes" stripe v-loading="loading">
            <el-table-column prop="name" label="名称" width="120" />
            <el-table-column prop="description" label="描述" min-width="150" />
            <el-table-column prop="is_system" label="系统" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.is_system" type="info">是</el-tag>
                <el-tag v-else>否</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button
                  link
                  type="primary"
                  size="small"
                  :disabled="row.is_system"
                  @click="editEntityType(row)"
                >
                  编辑
                </el-button>
                <el-button
                  link
                  type="danger"
                  size="small"
                  :disabled="row.is_system"
                  @click="deleteEntityType(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 关系类型 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>关系类型 ({{ relationTypes.length }})</span>
          </template>

          <el-table :data="relationTypes" stripe v-loading="loading">
            <el-table-column prop="name" label="名称" width="100" />
            <el-table-column label="关系" width="180">
              <template #default="{ row }">
                {{ row.source_type }} → {{ row.target_type }}
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" min-width="120" />
            <el-table-column prop="is_system" label="系统" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.is_system" type="info">是</el-tag>
                <el-tag v-else>否</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button
                  link
                  type="primary"
                  size="small"
                  :disabled="row.is_system"
                  @click="editRelationType(row)"
                >
                  编辑
                </el-button>
                <el-button
                  link
                  type="danger"
                  size="small"
                  :disabled="row.is_system"
                  @click="deleteRelationType(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 实体类型对话框 -->
    <el-dialog
      v-model="showEntityDialog"
      :title="editingEntity ? '编辑实体类型' : '新增实体类型'"
      width="500px"
    >
      <el-form ref="entityFormRef" :model="entityForm" :rules="entityRules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="entityForm.name" :disabled="!!editingEntity" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="entityForm.description" type="textarea" rows="3" />
        </el-form-item>
        <el-form-item label="必填属性" prop="required_attributes">
          <el-select
            v-model="entityForm.required_attributes"
            multiple
            allow-create
            filterable
            placeholder="输入后回车添加"
            style="width: 100%"
          >
            <el-option
              v-for="attr in entityForm.required_attributes"
              :key="attr"
              :label="attr"
              :value="attr"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="可选属性" prop="optional_attributes">
          <el-select
            v-model="entityForm.optional_attributes"
            multiple
            allow-create
            filterable
            placeholder="输入后回车添加"
            style="width: 100%"
          >
            <el-option
              v-for="attr in entityForm.optional_attributes"
              :key="attr"
              :label="attr"
              :value="attr"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showEntityDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEntityType">保存</el-button>
      </template>
    </el-dialog>

    <!-- 关系类型对话框 -->
    <el-dialog
      v-model="showRelationDialog"
      :title="editingRelation ? '编辑关系类型' : '新增关系类型'"
      width="500px"
    >
      <el-form
        ref="relationFormRef"
        :model="relationForm"
        :rules="relationRules"
        label-width="100px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="relationForm.name" :disabled="!!editingRelation" />
        </el-form-item>
        <el-form-item label="源实体类型" prop="source_type">
          <el-select v-model="relationForm.source_type" placeholder="选择源实体" style="width: 100%">
            <el-option
              v-for="et in entityTypes"
              :key="et.id"
              :label="et.name"
              :value="et.name"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="目标实体类型" prop="target_type">
          <el-select v-model="relationForm.target_type" placeholder="选择目标实体" style="width: 100%">
            <el-option
              v-for="et in entityTypes"
              :key="et.id"
              :label="et.name"
              :value="et.name"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="relationForm.description" type="textarea" rows="3" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showRelationDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRelationType">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { schemaApi, type EntityType, type RelationType } from '../api'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const loading = ref(false)
const entityTypes = ref<EntityType[]>([])
const relationTypes = ref<RelationType[]>([])

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    const [entities, relations] = await Promise.all([
      schemaApi.getEntityTypes(),
      schemaApi.getRelationTypes()
    ])
    entityTypes.value = entities
    relationTypes.value = relations
  } catch (error) {
    ElMessage.error('获取 Schema 失败')
  } finally {
    loading.value = false
  }
}

// 创建税务默认模板
const createTaxTemplate = async () => {
  try {
    await ElMessageBox.confirm('将创建预设的税务 Schema 模板，是否继续？', '提示', {
      type: 'info'
    })
    await schemaApi.createTaxTemplate()
    ElMessage.success('税务模板创建成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

// 实体类型操作
const showEntityDialog = ref(false)
const editingEntity = ref<EntityType | null>(null)
const entityFormRef = ref<FormInstance>()
const entityForm = reactive({
  name: '',
  description: '',
  required_attributes: [] as string[],
  optional_attributes: [] as string[]
})

const entityRules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }]
}

const editEntityType = (entity: EntityType) => {
  editingEntity.value = entity
  entityForm.name = entity.name
  entityForm.description = entity.description
  entityForm.required_attributes = [...entity.required_attributes]
  entityForm.optional_attributes = [...entity.optional_attributes]
  showEntityDialog.value = true
}

const saveEntityType = async () => {
  if (!entityFormRef.value) return

  await entityFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (editingEntity.value) {
          await schemaApi.updateEntityType(editingEntity.value.id, {
            description: entityForm.description,
            required_attributes: entityForm.required_attributes,
            optional_attributes: entityForm.optional_attributes
          })
          ElMessage.success('更新成功')
        } else {
          await schemaApi.createEntityType({
            name: entityForm.name,
            description: entityForm.description,
            required_attributes: entityForm.required_attributes,
            optional_attributes: entityForm.optional_attributes
          })
          ElMessage.success('创建成功')
        }
        showEntityDialog.value = false
        resetEntityForm()
        fetchData()
      } catch (error) {
        ElMessage.error('保存失败')
      }
    }
  })
}

const deleteEntityType = async (entity: EntityType) => {
  try {
    await ElMessageBox.confirm(`确定要删除实体类型「${entity.name}」吗？`, '警告', {
      type: 'warning'
    })
    await schemaApi.deleteEntityType(entity.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const resetEntityForm = () => {
  editingEntity.value = null
  entityForm.name = ''
  entityForm.description = ''
  entityForm.required_attributes = []
  entityForm.optional_attributes = []
}

// 关系类型操作
const showRelationDialog = ref(false)
const editingRelation = ref<RelationType | null>(null)
const relationFormRef = ref<FormInstance>()
const relationForm = reactive({
  name: '',
  source_type: '',
  target_type: '',
  description: ''
})

const relationRules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  source_type: [{ required: true, message: '请选择源实体类型', trigger: 'change' }],
  target_type: [{ required: true, message: '请选择目标实体类型', trigger: 'change' }]
}

const editRelationType = (relation: RelationType) => {
  editingRelation.value = relation
  relationForm.name = relation.name
  relationForm.source_type = relation.source_type
  relationForm.target_type = relation.target_type
  relationForm.description = relation.description
  showRelationDialog.value = true
}

const saveRelationType = async () => {
  if (!relationFormRef.value) return

  await relationFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (editingRelation.value) {
          await schemaApi.updateRelationType(editingRelation.value.id, {
            source_type: relationForm.source_type,
            target_type: relationForm.target_type,
            description: relationForm.description
          })
          ElMessage.success('更新成功')
        } else {
          await schemaApi.createRelationType({
            name: relationForm.name,
            source_type: relationForm.source_type,
            target_type: relationForm.target_type,
            description: relationForm.description
          })
          ElMessage.success('创建成功')
        }
        showRelationDialog.value = false
        resetRelationForm()
        fetchData()
      } catch (error) {
        ElMessage.error('保存失败')
      }
    }
  })
}

const deleteRelationType = async (relation: RelationType) => {
  try {
    await ElMessageBox.confirm(`确定要删除关系类型「${relation.name}」吗？`, '警告', {
      type: 'warning'
    })
    await schemaApi.deleteRelationType(relation.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const resetRelationForm = () => {
  editingRelation.value = null
  relationForm.name = ''
  relationForm.source_type = ''
  relationForm.target_type = ''
  relationForm.description = ''
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.schema-page {
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
</style>
