<template>
  <div class="reports-page">
    <el-card>
      <template #header>
        <div class="page-header">
          <span class="page-title">举报审核</span>
          <span class="page-desc">处理用户举报与申诉请求</span>
        </div>
      </template>

      <div class="toolbar">
        <el-select v-model="filterStatus" placeholder="筛选状态" clearable style="width: 150px" @change="loadReports">
          <el-option label="全部" value="" />
          <el-option label="待处理举报" value="reported" />
          <el-option label="举报已驳回" value="dismissed" />
          <el-option label="申诉待审" value="pending" />
          <el-option label="申诉被拒" value="rejected" />
          <el-option label="申诉通过" value="approved" />
        </el-select>
        <el-input v-model="filterUsername" placeholder="搜索作者" clearable style="width: 160px" @keyup.enter="loadReports" @clear="loadReports" />
        <el-button type="primary" @click="loadReports">查询</el-button>
      </div>

      <el-table :data="reports" v-loading="loading" stripe>
        <!-- 博文标题：链接 + 未处理红点 -->
        <el-table-column label="博文标题" min-width="220">
          <template #default="{ row }">
            <div class="title-cell">
              <span v-if="isUnprocessed(row)" class="unprocessed-dot" />
              <a :href="`/post/${row.id}`" target="_blank" rel="noopener" class="post-link" @click.stop>
                {{ row.title }}
              </a>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="作者" width="110">
          <template #default="{ row }">{{ row.author_nickname || row.author_name }}</template>
        </el-table-column>
        <el-table-column label="状态" width="96">
          <template #default="{ row }">
            <el-tag :type="getStatus(row).type" size="small">{{ getStatus(row).label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="举报" width="60">
          <template #default="{ row }">
            <span :class="['report-count', { danger: row.report_count > 2 }]">{{ row.report_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openDetail(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="total > pageSize" class="pagination">
        <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total"
          layout="prev, pager, next" @current-change="loadReports" />
      </div>
    </el-card>

    <!-- 详情 Drawer -->
    <el-drawer v-model="detailVisible" title="举报详情" size="460px" @open="onDrawerOpen">
      <div v-if="currentPost" class="detail-body">
        <!-- 博文信息 -->
        <div class="detail-section">
          <div class="detail-label">博文</div>
          <a :href="`/post/${currentPost.id}`" target="_blank" class="post-title-link">
            {{ currentPost.title }} ↗
          </a>
        </div>
        <div class="detail-section">
          <div class="detail-label">被举报者（作者）</div>
          <div class="reporter-item">
            <span class="reporter-name">{{ currentPost.author_nickname || currentPost.author_name }}</span>
            <span class="reporter-handle">@{{ currentPost.author_name }}</span>
          </div>
        </div>
        <div class="detail-section">
          <div class="detail-label">当前状态</div>
          <el-tag :type="getStatus(currentPost).type" size="small">{{ getStatus(currentPost).label }}</el-tag>
        </div>

        <!-- 举报者信息 -->
        <div v-if="reporters.length" class="detail-section">
          <div class="detail-label">举报者（共 {{ reporters.length }} 人）</div>
          <div class="reporter-list">
            <div v-for="r in reporters" :key="r.user_id" class="reporter-item">
              <span class="reporter-name">{{ r.nickname || r.username }}</span>
              <span class="reporter-handle">@{{ r.username }}</span>
              <span v-if="r.reason" class="reporter-reason">{{ r.reason }}</span>
            </div>
          </div>
        </div>

        <!-- 隐藏原因 / 申诉理由 -->
        <div v-if="currentPost.hide_reason" class="detail-section">
          <div class="detail-label">隐藏原因</div>
          <div class="detail-value reason-box">{{ currentPost.hide_reason }}</div>
        </div>
        <div v-if="currentPost.appeal_reason" class="detail-section">
          <div class="detail-label">申诉理由</div>
          <div class="detail-value appeal-box">{{ currentPost.appeal_reason }}</div>
        </div>

        <!-- 操作区（状态驱动） -->
        <div class="detail-actions">
          <!-- 申诉待审 -->
          <template v-if="currentPost.review_status === 'pending'">
            <el-button type="primary" :loading="actionLoading" @click="doAppeal('approve')">批准申诉（恢复博文）</el-button>
            <el-button type="danger" plain :loading="actionLoading" @click="triggerReject">拒绝申诉</el-button>
          </template>
          <!-- 未处理举报 -->
          <template v-else-if="isUnprocessed(currentPost) && canHide(currentPost)">
            <el-button type="danger" :loading="actionLoading" @click="triggerReportValid">举报有效（隐藏博文）</el-button>
            <el-button :loading="actionLoading" @click="doReportInvalid">举报无效（驳回）</el-button>
          </template>
          <!-- 其他：只查看 -->
          <template v-else>
            <a :href="`/post/${currentPost.id}`" target="_blank" class="view-link">查看原文 ↗</a>
          </template>
        </div>
      </div>
    </el-drawer>

    <!-- 拒绝申诉 Dialog -->
    <el-dialog v-model="rejectVisible" title="拒绝申诉" width="400px">
      <el-input v-model="inputReason" type="textarea" :rows="3" placeholder="拒绝原因（可选）" maxlength="500" show-word-limit resize="none" />
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button type="danger" :loading="actionLoading" @click="confirmReject">确认拒绝</el-button>
      </template>
    </el-dialog>

    <!-- 举报有效 Dialog -->
    <el-dialog v-model="reportValidVisible" title="举报有效 — 隐藏博文" width="400px">
      <p class="dialog-hint">博文将被隐藏，举报者将收到通知表示感谢，作者将收到隐藏通知。</p>
      <el-input v-model="inputReason" type="textarea" :rows="3" placeholder="隐藏原因（必填，将告知作者）" maxlength="500" show-word-limit resize="none" />
      <template #footer>
        <el-button @click="reportValidVisible = false">取消</el-button>
        <el-button type="danger" :loading="actionLoading" @click="confirmReportValid">确认隐藏</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { postsApi } from '@/api/modules/posts'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'

const userStore = useUserStore()
const appStore = useAppStore()
const canHide = (row: any) => userStore.isRoot || !row.author_is_root

// ---- 状态工具 ----
const isUnprocessed = (row: any) => !row.is_hidden && row.report_count > 0 && row.review_status === 'none'
function getStatus(row: any): { label: string; type: string } {
  if (row.review_status === 'approved')                        return { label: '申诉通过', type: 'success' }
  if (row.review_status === 'dismissed')                       return { label: '举报驳回', type: 'info' }
  if (row.is_hidden && row.review_status === 'rejected')       return { label: '申诉被拒', type: 'danger' }
  if (row.is_hidden && row.review_status === 'pending')        return { label: '申诉待审', type: 'warning' }
  if (row.is_hidden)                                           return { label: '已隐藏',   type: 'danger' }
  if (row.report_count > 0 && row.review_status === 'none')   return { label: '未处理',   type: 'warning' }
  return { label: '正常', type: 'info' }
}

// ---- 列表 ----
const loading = ref(false)
const reports = ref<any[]>([])
const total = ref(0), page = ref(1), pageSize = 20
const filterStatus = ref(''), filterUsername = ref('')

async function loadReports() {
  loading.value = true
  try {
    const res = await postsApi.adminGetAll({ page: page.value, page_size: pageSize, username: filterUsername.value || undefined, needs_review: 1 })
    if (res.success && res.data) {
      let items = res.data.items
      if (filterStatus.value === 'reported')   items = items.filter((p: any) => isUnprocessed(p))
      else if (filterStatus.value === 'pending')   items = items.filter((p: any) => p.review_status === 'pending')
      else if (filterStatus.value === 'rejected')  items = items.filter((p: any) => p.review_status === 'rejected')
      else if (filterStatus.value === 'approved')  items = items.filter((p: any) => p.review_status === 'approved')
      else if (filterStatus.value === 'dismissed') items = items.filter((p: any) => p.review_status === 'dismissed')
      reports.value = items
      // 客户端筛选后 total 按实际条数算（防止分页错乱）；全部显示时用服务端 total
      total.value = filterStatus.value ? items.length : res.data.total
    }
  } finally { loading.value = false }
}

// ---- 详情 Drawer ----
const detailVisible = ref(false)
const currentPost = ref<any>(null)
const reporters = ref<any[]>([])
const actionLoading = ref(false)

function openDetail(post: any) { currentPost.value = post; detailVisible.value = true }

async function onDrawerOpen() {
  if (!currentPost.value) return
  try {
    const res = await postsApi.getReporters(currentPost.value.id)
    reporters.value = res.success && res.data ? res.data : []
  } catch { reporters.value = [] }
}

// ---- 申诉审核 ----
const rejectVisible = ref(false)
const inputReason = ref('')

async function doAppeal(action: 'approve' | 'reject', reason?: string) {
  actionLoading.value = true
  try {
    await postsApi.reviewAppeal(currentPost.value.id, action, reason)
    ElMessage.success(action === 'approve' ? '已批准，博文已恢复' : '已拒绝申诉')
    detailVisible.value = false; rejectVisible.value = false
    appStore.refreshReviewCount()
    await loadReports()
  } catch { ElMessage.error('操作失败') } finally { actionLoading.value = false }
}
function triggerReject() { inputReason.value = ''; rejectVisible.value = true }
function confirmReject() { doAppeal('reject', inputReason.value.trim() || undefined) }

// ---- 举报处置 ----
const reportValidVisible = ref(false)

function triggerReportValid() { inputReason.value = ''; reportValidVisible.value = true }
async function confirmReportValid() {
  if (!inputReason.value.trim()) { ElMessage.warning('请填写隐藏原因'); return }
  actionLoading.value = true
  try {
    await postsApi.reportValid(currentPost.value.id, inputReason.value.trim())
    ElMessage.success('已隐藏博文并通知相关用户')
    reportValidVisible.value = false; detailVisible.value = false
    appStore.refreshReviewCount()
    await loadReports()
  } catch { ElMessage.error('操作失败') } finally { actionLoading.value = false }
}

async function doReportInvalid() {
  actionLoading.value = true
  try {
    await postsApi.reportInvalid(currentPost.value.id)
    ElMessage.success('已驳回举报，举报者将收到感谢通知')
    detailVisible.value = false
    appStore.refreshReviewCount()
    await loadReports()
  } catch { ElMessage.error('操作失败') } finally { actionLoading.value = false }
}

onMounted(loadReports)
</script>

<style scoped lang="scss">
.reports-page {}

.page-header { display: flex; align-items: baseline; gap: 12px; }
.page-title { font-size: $font-base; font-weight: 600; }
.page-desc { font-size: $font-xs; color: var(--color-text-muted); }

.toolbar {
  display: flex; align-items: center; gap: $spacing-sm;
  padding: 14px 20px; border-bottom: 1px solid var(--color-border); flex-wrap: wrap;
}

// 博文标题单元格
.title-cell { display: flex; align-items: center; gap: 6px; min-width: 0; }

.unprocessed-dot {
  flex-shrink: 0; width: 7px; height: 7px; border-radius: 50%; background: #ef4444;
}

.post-link {
  color: $color-primary; font-weight: 500; font-size: $font-sm; text-decoration: none;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0;
  transition: opacity 0.15s;
  &:hover { opacity: 0.75; text-decoration: underline; }
}

.report-count {
  font-size: $font-sm; font-weight: 600; color: var(--color-text-muted);
  &.danger { color: #e05555; }
}

.pagination { display: flex; justify-content: center; padding: $spacing-md 0; }

// Drawer
.detail-body { display: flex; flex-direction: column; gap: $spacing-md; }
.detail-section { display: flex; flex-direction: column; gap: 4px; }
.detail-label {
  font-size: $font-xs; font-weight: 600; color: var(--color-text-muted);
  text-transform: uppercase; letter-spacing: 0.05em;
}
.detail-value { font-size: $font-sm; color: var(--color-text-primary); line-height: 1.6; }
.post-title-link {
  font-size: $font-sm; font-weight: 600; color: $color-primary; text-decoration: none;
  &:hover { text-decoration: underline; }
}
.reason-box {
  background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.15);
  border-radius: $radius-sm; padding: 8px 12px; color: #b91c1c; font-size: $font-sm;
}
.appeal-box {
  background: rgba(90, 103, 216, 0.05); border: 1px solid rgba(90, 103, 216, 0.15);
  border-radius: $radius-sm; padding: 8px 12px; font-size: $font-sm;
}

// 举报者列表
.reporter-list { display: flex; flex-direction: column; gap: 6px; }
.reporter-item {
  display: flex; align-items: baseline; gap: 6px; flex-wrap: wrap;
  padding: 7px 10px;
  background: rgba(239, 68, 68, 0.04); border: 1px solid rgba(239, 68, 68, 0.12);
  border-radius: $radius-sm;
}
.reporter-name { font-size: $font-sm; font-weight: 600; color: var(--color-text-primary); }
.reporter-handle { font-size: $font-xs; color: var(--color-text-muted); }
.reporter-reason {
  font-size: $font-xs; color: var(--color-text-secondary); flex-basis: 100%;
  line-height: 1.5; font-style: italic;
}

.detail-actions {
  display: flex; gap: $spacing-sm; flex-wrap: wrap;
  padding-top: $spacing-sm; border-top: 1px solid var(--color-border);
}
.view-link {
  font-size: $font-sm; color: $color-primary; text-decoration: none; font-weight: 500;
  &:hover { text-decoration: underline; }
}
.dialog-hint {
  font-size: $font-sm; color: var(--color-text-secondary); margin: 0 0 12px; line-height: 1.6;
}
</style>
