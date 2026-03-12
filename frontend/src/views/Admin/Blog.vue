<template>
  <div class="admin-blog">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="文章管理" name="posts">
        <el-card class="filter-card">
          <div class="filter-row">
            <el-input v-model="searchUsername" placeholder="按用户名搜索" clearable style="width:200px" @keyup.enter="handleSearch" @clear="handleSearch">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-select v-model="filterCategory" placeholder="全部分类" clearable style="width:150px" @change="handleSearch">
              <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
            </el-select>
            <el-button type="primary" @click="handleSearch">查询</el-button>
          </div>
        </el-card>

        <el-card v-loading="postsLoading">
          <el-table :data="posts" style="width:100%">
            <el-table-column label="标题" min-width="200">
              <template #default="{ row }">
                <div class="title-cell">
                  <span class="post-title">{{ row.title }}</span>
                  <div class="title-badges">
                    <span v-if="row.review_status === 'pending'" class="badge-pending">审核中</span>
                    <el-tag v-if="row.is_hidden" type="danger" size="small" effect="light">已隐藏</el-tag>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="作者" width="110">
              <template #default="{ row }"><span class="cell-secondary">{{ row.author_nickname || row.author_name }}</span></template>
            </el-table-column>
            <el-table-column label="分类" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.category_name" size="small" effect="plain">{{ row.category_name }}</el-tag>
                <span v-else class="text-muted">—</span>
              </template>
            </el-table-column>
            <el-table-column label="数据统计" width="200">
              <template #default="{ row }">
                <div class="stats-row">
                  <span class="stat-chip stat-views">
                    <svg viewBox="0 0 16 16" width="12" height="12" fill="currentColor"><path d="M8 3C4.5 3 1.5 5.5 0 8c1.5 2.5 4.5 5 8 5s6.5-2.5 8-5c-1.5-2.5-4.5-5-8-5zm0 8a3 3 0 110-6 3 3 0 010 6zm0-4.5a1.5 1.5 0 100 3 1.5 1.5 0 000-3z"/></svg>
                    {{ fmtNum(row.view_count) }}
                  </span>
                  <span class="stat-chip stat-likes">
                    <svg viewBox="0 0 16 16" width="12" height="12" fill="currentColor"><path d="M8 14.25c-.345 0-.666-.168-.88-.44l-5.6-7a3.25 3.25 0 014.79-4.38L8 4.46l1.69-2.03a3.25 3.25 0 014.79 4.38l-5.6 7c-.214.272-.535.44-.88.44z"/></svg>
                    {{ fmtNum(row.like_count) }}
                  </span>
                  <span class="stat-chip stat-collects">
                    <svg viewBox="0 0 16 16" width="12" height="12" fill="currentColor"><path d="M8 1.5L10.09 5.73L14.78 6.44L11.39 9.74L12.18 14.41L8 12.21L3.82 14.41L4.61 9.74L1.22 6.44L5.91 5.73L8 1.5Z"/></svg>
                    {{ fmtNum(row.collect_count) }}
                  </span>
                  <span class="stat-chip stat-comments">
                    <svg viewBox="0 0 16 16" width="12" height="12" fill="currentColor"><path d="M2 2.5A1.5 1.5 0 013.5 1h9A1.5 1.5 0 0114 2.5v7A1.5 1.5 0 0112.5 11H9l-3 3v-3H3.5A1.5 1.5 0 012 9.5v-7z"/></svg>
                    {{ fmtNum(row.comment_count) }}
                  </span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="时间" width="100">
              <template #default="{ row }"><span class="cell-secondary">{{ formatDate(row.published_at || row.created_at) }}</span></template>
            </el-table-column>
            <el-table-column label="操作" width="110" fixed="right">
              <template #default="{ row }">
                <div class="action-btns">
                  <el-tooltip :content="row.is_hidden ? '恢复公开' : '隐藏博文'">
                    <el-button text :icon="row.is_hidden ? ViewIcon : HideIcon" size="small" :class="row.is_hidden ? 'btn-restore' : 'btn-hide'" @click="openVisibilityDialog(row)" />
                  </el-tooltip>
                  <el-tooltip v-if="row.review_status === 'pending'" content="处理申诉">
                    <el-button text size="small" class="btn-appeal" @click="openReviewDialog(row)">
                      <svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm.75 3.5v4.25a.75.75 0 01-1.5 0V4.5a.75.75 0 011.5 0zM8 11a1 1 0 110 2 1 1 0 010-2z"/></svg>
                    </el-button>
                  </el-tooltip>
                  <el-popconfirm title="确认删除该文章？此操作不可撤销。" confirm-button-text="删除" confirm-button-type="danger" @confirm="deletePost(row.id)">
                    <template #reference>
                      <el-button text :icon="DeleteIcon" class="btn-danger" size="small" />
                    </template>
                  </el-popconfirm>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-wrap">
            <el-pagination v-model:current-page="postsPage" v-model:page-size="postsPageSize" :total="postsTotal" :page-sizes="[20,50,100]" layout="total, sizes, prev, pager, next" background @change="loadPosts" />
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="分类管理" name="categories">
        <el-card>
          <div class="cat-header">
            <el-button type="primary" size="small" :icon="PlusIcon" @click="openAddCategory">新增分类</el-button>
          </div>
          <el-table :data="categories" v-loading="catsLoading" style="width:100%">
            <el-table-column label="分类名称" prop="name" min-width="140" />
            <el-table-column label="描述" prop="description" show-overflow-tooltip />
            <el-table-column label="文章数" prop="post_count" width="90" />
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <div class="action-btns">
                  <el-tooltip content="编辑"><el-button text :icon="EditIcon" size="small" @click="openEditCategory(row)" /></el-tooltip>
                  <el-popconfirm title="确认删除该分类？" confirm-button-text="删除" confirm-button-type="danger" @confirm="deleteCategory(row.id)">
                    <template #reference><el-button text :icon="DeleteIcon" class="btn-danger" size="small" /></template>
                  </el-popconfirm>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 分类 Dialog -->
    <el-dialog v-model="catDialogVisible" :title="editingCat ? '编辑分类' : '新增分类'" width="400px">
      <el-form :model="catForm" label-width="70px">
        <el-form-item label="名称"><el-input v-model="catForm.name" placeholder="分类名称" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="catForm.description" type="textarea" :rows="2" placeholder="可选描述" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="catDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="catSaving" @click="saveCategory">保存</el-button>
      </template>
    </el-dialog>

    <!-- 可见性 Dialog -->
    <el-dialog v-model="visDialogVisible" :title="visTarget?.is_hidden ? '恢复公开博文' : '隐藏博文'" width="440px">
      <p class="dialog-post-title">「{{ visTarget?.title }}」</p>
      <el-form v-if="!visTarget?.is_hidden" label-position="top">
        <el-form-item label="隐藏原因（将以通知形式告知作者）">
          <el-input v-model="visReason" type="textarea" :rows="3" placeholder="请填写隐藏原因，例如：违反社区规范" maxlength="200" show-word-limit />
        </el-form-item>
      </el-form>
      <p v-else class="dialog-hint">将该博文恢复为公开可见，恢复后不会主动发送通知。</p>
      <template #footer>
        <el-button @click="visDialogVisible = false">取消</el-button>
        <el-button :type="visTarget?.is_hidden ? 'primary' : 'danger'" :loading="visSaving" @click="confirmVisibility">
          {{ visTarget?.is_hidden ? '恢复公开' : '确认隐藏' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 申诉审核 Dialog -->
    <el-dialog v-model="reviewDialogVisible" title="处理审核申诉" width="480px">
      <div class="review-panel">
        <div class="review-field"><span class="review-label">博文标题</span><span class="review-value">{{ reviewTarget?.title }}</span></div>
        <div class="review-field">
          <span class="review-label">申诉理由</span>
          <p class="review-appeal-text">{{ reviewTarget?.appeal_reason || '（作者未填写理由）' }}</p>
        </div>
        <div v-if="showRejectReason" class="review-reject-wrap">
          <el-form label-position="top">
            <el-form-item label="拒绝原因（可选）">
              <el-input v-model="rejectReason" type="textarea" :rows="2" placeholder="告知作者拒绝原因" maxlength="200" show-word-limit />
            </el-form-item>
          </el-form>
        </div>
      </div>
      <template #footer>
        <el-button @click="reviewDialogVisible = false">取消</el-button>
        <el-button v-if="!showRejectReason" type="danger" :loading="reviewSaving" @click="showRejectReason = true">拒绝申诉</el-button>
        <template v-if="showRejectReason">
          <el-button @click="showRejectReason = false">返回</el-button>
          <el-button type="danger" :loading="reviewSaving" @click="handleReview('reject')">确认拒绝</el-button>
        </template>
        <el-button type="primary" :loading="reviewSaving" @click="handleReview('approve')">批准恢复</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Edit as EditIcon, Delete as DeleteIcon, Plus as PlusIcon, View as ViewIcon, Hide as HideIcon } from '@element-plus/icons-vue'
import { postsApi } from '@/api/modules/posts'
import { formatDate } from '@/utils/format'

interface PostRow {
  id: number; title: string; author_name: string; author_nickname: string
  category_name: string; status: string; view_count: number; like_count: number
  comment_count: number; collect_count: number; published_at: string; created_at: string
  is_hidden: number; hide_reason: string; review_status: 'none' | 'pending' | 'rejected'; appeal_reason: string
}
interface Category { id: number; name: string; description?: string; post_count?: number }

const activeTab = ref('posts')
const posts = ref<PostRow[]>([])
const postsLoading = ref(false)
const postsPage = ref(1)
const postsPageSize = ref(20)
const postsTotal = ref(0)
const searchUsername = ref('')
const filterCategory = ref<number | ''>('')
const categories = ref<Category[]>([])
const catsLoading = ref(false)
const catDialogVisible = ref(false)
const catSaving = ref(false)
const editingCat = ref<Category | null>(null)
const catForm = reactive({ name: '', description: '' })
const visDialogVisible = ref(false)
const visTarget = ref<PostRow | null>(null)
const visReason = ref('')
const visSaving = ref(false)
const reviewDialogVisible = ref(false)
const reviewTarget = ref<PostRow | null>(null)
const rejectReason = ref('')
const reviewSaving = ref(false)
const showRejectReason = ref(false)

const fmtNum = (n: number) => !n ? '0' : n >= 1000 ? (n / 1000).toFixed(1).replace(/\.0$/, '') + 'k' : String(n)

async function loadPosts() {
  postsLoading.value = true
  try {
    const res = await postsApi.adminGetAll({ page: postsPage.value, page_size: postsPageSize.value, username: searchUsername.value || undefined, category_id: filterCategory.value || undefined })
    if (res.success && res.data) { posts.value = res.data.items; postsTotal.value = res.data.total }
  } catch { ElMessage.error('获取文章列表失败') } finally { postsLoading.value = false }
}

async function loadCategories() {
  catsLoading.value = true
  try { const res = await postsApi.getCategories(); if (res.success && res.data) categories.value = res.data } catch { /* 静默 */ } finally { catsLoading.value = false }
}

function handleSearch() { postsPage.value = 1; loadPosts() }
function openVisibilityDialog(row: PostRow) { visTarget.value = row; visReason.value = ''; visDialogVisible.value = true }

async function confirmVisibility() {
  if (!visTarget.value) return
  const hide = !visTarget.value.is_hidden
  if (hide && !visReason.value.trim()) { ElMessage.warning('请填写隐藏原因'); return }
  visSaving.value = true
  try {
    await postsApi.setVisibility(visTarget.value.id, hide, visReason.value.trim() || undefined)
    ElMessage.success(hide ? '博文已隐藏，已通知作者' : '博文已恢复公开')
    visDialogVisible.value = false; loadPosts()
  } catch { ElMessage.error('操作失败') } finally { visSaving.value = false }
}

async function deletePost(id: number) {
  try { await postsApi.delete(id); ElMessage.success('已删除'); loadPosts() } catch { ElMessage.error('删除失败') }
}

function openReviewDialog(row: PostRow) { reviewTarget.value = row; rejectReason.value = ''; showRejectReason.value = false; reviewDialogVisible.value = true }

async function handleReview(action: 'approve' | 'reject') {
  if (!reviewTarget.value) return
  reviewSaving.value = true
  try {
    await postsApi.reviewAppeal(reviewTarget.value.id, action, rejectReason.value.trim() || undefined)
    ElMessage.success(action === 'approve' ? '已批准申诉，博文已恢复公开' : '已拒绝申诉')
    reviewDialogVisible.value = false; loadPosts()
  } catch { ElMessage.error('操作失败') } finally { reviewSaving.value = false }
}

function openAddCategory() { editingCat.value = null; catForm.name = ''; catForm.description = ''; catDialogVisible.value = true }
function openEditCategory(cat: Category) { editingCat.value = cat; catForm.name = cat.name; catForm.description = cat.description || ''; catDialogVisible.value = true }

async function saveCategory() {
  if (!catForm.name.trim()) { ElMessage.warning('分类名称不能为空'); return }
  catSaving.value = true
  try {
    editingCat.value ? await postsApi.updateCategory(editingCat.value.id, catForm) : await postsApi.createCategory(catForm)
    ElMessage.success('保存成功'); catDialogVisible.value = false; loadCategories()
  } catch { ElMessage.error('保存失败') } finally { catSaving.value = false }
}

async function deleteCategory(id: number) {
  try { await postsApi.deleteCategory(id); ElMessage.success('已删除'); loadCategories() } catch { ElMessage.error('删除失败') }
}

onMounted(() => { loadPosts(); loadCategories() })
</script>

<style scoped lang="scss">
.admin-blog { display: flex; flex-direction: column; gap: $spacing-md; }
.filter-card { :deep(.el-card__body) { padding: $spacing-md; } }
.filter-row { display: flex; gap: $spacing-sm; align-items: center; flex-wrap: wrap; }

.title-cell { display: flex; flex-direction: column; gap: 4px; }
.post-title { font-size: $font-sm; font-weight: 500; color: var(--el-text-color-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 260px; display: block; line-height: 1.4; }
.title-badges { display: flex; align-items: center; gap: 4px; }
.badge-pending { display: inline-flex; align-items: center; padding: 1px 7px; border-radius: $radius-sm; font-size: 11px; font-weight: 600; line-height: 18px; background: rgba(234,88,12,.1); color: #ea580c; border: 1px solid rgba(234,88,12,.25); }

.cell-secondary { font-size: $font-sm; color: var(--el-text-color-regular); }
.text-muted { color: var(--el-text-color-placeholder); font-size: $font-sm; }

.stats-row { display: flex; align-items: center; gap: 5px; flex-wrap: nowrap; }
.stat-chip { display: inline-flex; align-items: center; gap: 3px; font-size: 11px; font-weight: 500; padding: 2px 5px; border-radius: $radius-sm; line-height: 1; white-space: nowrap; }
.stat-views   { color: #6b7280; background: rgba(107,114,128,.08); }
.stat-likes   { color: #ef4444; background: rgba(239,68,68,.08); }
.stat-collects { color: #d97706; background: rgba(217,119,6,.08); }
.stat-comments { color: #3b82f6; background: rgba(59,130,246,.08); }

.action-btns { display: flex; align-items: center; gap: 2px; }
.btn-hide    { color: var(--el-text-color-secondary) !important; &:hover { color: var(--el-color-warning) !important; } }
.btn-restore { color: var(--el-color-success) !important; }
.btn-danger  { color: var(--el-color-danger) !important; }
.btn-appeal  { color: #ea580c !important; animation: pulse-appeal 2s ease-in-out infinite; }
@keyframes pulse-appeal { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

.pagination-wrap { margin-top: $spacing-md; display: flex; justify-content: flex-end; }
.cat-header { margin-bottom: $spacing-md; }

.dialog-post-title { font-size: $font-sm; font-weight: 500; color: var(--el-text-color-primary); margin: 0 0 $spacing-md; line-height: 1.5; }
.dialog-hint { font-size: 13px; color: var(--el-text-color-secondary); margin: 0; line-height: 1.6; }

.review-panel { display: flex; flex-direction: column; gap: $spacing-md; }
.review-field { display: flex; flex-direction: column; gap: 4px; }
.review-label { font-size: 12px; color: var(--el-text-color-secondary); font-weight: 500; text-transform: uppercase; letter-spacing: .04em; }
.review-value { font-size: $font-sm; font-weight: 500; color: var(--el-text-color-primary); }
.review-appeal-text { font-size: $font-sm; color: var(--el-text-color-regular); line-height: 1.6; margin: 0; padding: $spacing-sm $spacing-md; background: var(--el-fill-color-light); border-radius: $radius-md; border-left: 3px solid #ea580c; }
.review-reject-wrap { border-top: 1px solid var(--el-border-color-lighter); padding-top: $spacing-md; }
</style>
