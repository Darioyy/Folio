<template>
  <div class="feedback-page">
    <div class="page-header">
      <h2 class="page-title">建议箱</h2>
      <div class="header-actions">
        <el-select
          v-model="statusFilter"
          placeholder="全部状态"
          clearable
          style="width: 120px"
          @change="() => { page = 1; loadFeedback() }"
        >
          <el-option label="待处理" value="pending" />
          <el-option label="已处理" value="resolved" />
        </el-select>
        <el-button :icon="Refresh" circle text @click="loadFeedback" :loading="loading" />
      </div>
    </div>

    <el-table :data="items" v-loading="loading" row-class-name="feedback-row">
      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          <span :class="['type-tag', row.type]">{{ typeLabel(row.type) }}</span>
        </template>
      </el-table-column>

      <el-table-column label="标题" min-width="200">
        <template #default="{ row }">
          <span class="feedback-title" @click="openDetail(row)">{{ row.title }}</span>
        </template>
      </el-table-column>

      <el-table-column label="提交时间" width="120">
        <template #default="{ row }">
          <span class="time-cell">{{ fromNow(row.created_at) }}</span>
        </template>
      </el-table-column>

      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <span :class="['status-tag', row.status]">{{ statusLabel(row.status) }}</span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="110">
        <template #default="{ row }">
          <div class="row-actions">
            <el-button link type="primary" size="small" @click="openDetail(row)">查看</el-button>
            <el-button
              v-if="row.status !== 'resolved'"
              link type="danger" size="small"
              @click="handleClose(row)"
            >关闭</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <div v-if="total > pageSize" class="pagination">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="loadFeedback"
      />
    </div>

    <!-- 详情抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="current?.title || '反馈详情'"
      direction="rtl"
      size="420px"
    >
      <template v-if="current">
        <div class="detail-meta">
          <span :class="['type-tag', current.type]">{{ typeLabel(current.type) }}</span>
          <span :class="['status-tag', current.status]">{{ statusLabel(current.status) }}</span>
          <span class="detail-time">{{ fromNow(current.created_at) }}</span>
        </div>

        <div class="detail-section">
          <div class="detail-label">详细描述</div>
          <div class="detail-content">{{ current.content }}</div>
        </div>

        <div v-if="current.contact" class="detail-section">
          <div class="detail-label">联系方式</div>
          <div class="detail-content contact">{{ current.contact }}</div>
        </div>

        <div class="detail-section">
          <div class="detail-label">处理备注</div>
          <el-input
            v-model="noteInput"
            type="textarea"
            :rows="3"
            placeholder="添加处理备注..."
            maxlength="500"
          />
        </div>

        <div class="drawer-actions">
          <el-button
            type="primary"
            :loading="updating"
            :disabled="current.status === 'resolved'"
            @click="updateStatus('resolved')"
          >标记已处理</el-button>
          <el-button
            type="danger" plain
            :loading="updating"
            :disabled="current.status === 'resolved'"
            @click="updateStatus('resolved')"
          >关闭</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { feedbackApi, type FeedbackItem, type FeedbackStatus } from '@/api/modules/feedback'
import { useAppStore } from '@/stores/app'
import { fromNow } from '@/utils/format'

const appStore = useAppStore()

const loading = ref(false)
const updating = ref(false)
const items = ref<FeedbackItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const statusFilter = ref('')
const drawerVisible = ref(false)
const current = ref<FeedbackItem | null>(null)
const noteInput = ref('')

async function loadFeedback() {
  loading.value = true
  try {
    const res = await feedbackApi.getList({
      page: page.value,
      page_size: pageSize,
      ...(statusFilter.value ? { status: statusFilter.value } : {}),
    })
    items.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch {
    ElMessage.warning('建议箱功能即将上线')
  } finally {
    loading.value = false
  }
}

function openDetail(row: FeedbackItem) {
  current.value = row
  noteInput.value = row.note || ''
  drawerVisible.value = true
}

async function updateStatus(status: FeedbackStatus) {
  if (!current.value) return
  updating.value = true
  try {
    await feedbackApi.updateStatus(current.value.id, { status, note: noteInput.value || undefined })
    current.value.status = status
    current.value.note = noteInput.value
    const item = items.value.find(i => i.id === current.value!.id)
    if (item) { item.status = status; item.note = noteInput.value }
    appStore.refreshReviewCount()
    ElMessage.success('已更新')
  } catch {
    ElMessage.error('更新失败')
  } finally {
    updating.value = false
  }
}

async function handleClose(row: FeedbackItem) {
  await ElMessageBox.confirm('确认标记此反馈为已处理？', '提示', { type: 'warning' })
  try {
    await feedbackApi.updateStatus(row.id, { status: 'resolved' })
    row.status = 'resolved'
  } catch { /* ignore */ }
}

const typeLabel = (t: string) => ({ feature: '功能建议', bug: 'Bug 反馈', other: '其他' }[t] || t)
const statusLabel = (s: string) => ({ pending: '待处理', resolved: '已处理' }[s] || s)

onMounted(loadFeedback)
</script>

<style scoped lang="scss">
.feedback-page { max-width: 900px; }

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $spacing-lg;
}

.page-title {
  font-size: $font-xl;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
}

.type-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: $radius-sm;
  font-size: 12px;
  font-weight: 500;
  &.feature { color: $color-primary; background: rgba(90, 103, 216, 0.1); }
  &.bug { color: $color-danger; background: rgba(239, 68, 68, 0.1); }
  &.other { color: $color-gray-500; background: var(--el-fill-color); }
}

.status-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: $radius-sm;
  font-size: 12px;
  font-weight: 500;
  &.pending { color: $color-warning; background: rgba(245, 158, 11, 0.1); }
  &.resolved { color: $color-success; background: rgba(16, 185, 129, 0.1); }
}

.feedback-title {
  cursor: pointer;
  font-size: $font-sm;
  color: var(--el-text-color-primary);
  transition: color $transition-fast;
  &:hover { color: $color-primary; }
}

.time-cell {
  font-size: $font-xs;
  color: var(--el-text-color-secondary);
}

.row-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity $transition-fast;
}

:deep(.feedback-row:hover) .row-actions { opacity: 1; }

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: $spacing-lg;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  margin-bottom: $spacing-lg;
}

.detail-time {
  font-size: $font-xs;
  color: var(--el-text-color-placeholder);
  margin-left: auto;
}

.detail-section { margin-bottom: $spacing-lg; }

.detail-label {
  font-size: $font-xs;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: $spacing-xs;
}

.detail-content {
  font-size: $font-sm;
  color: var(--el-text-color-primary);
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  &.contact { color: $color-primary; }
}

.drawer-actions {
  display: flex;
  gap: $spacing-sm;
  padding-top: $spacing-lg;
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>
