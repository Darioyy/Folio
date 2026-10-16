<template>
  <!-- 举报对话框 -->
  <el-dialog v-model="reportVisible" title="举报博文" width="400px" :append-to-body="true">
    <p class="report-target">「{{ post?.title }}」</p>
    <el-input v-model="reportReason" type="textarea" :rows="4"
      placeholder="请描述举报原因（违规内容、虚假信息等）" maxlength="500" show-word-limit />
    <template #footer>
      <el-button @click="reportVisible = false">取消</el-button>
      <el-button type="primary" :loading="reportSaving" @click="submitReport">提交举报</el-button>
    </template>
  </el-dialog>

  <!-- 隐藏博文对话框（管理员） -->
  <el-dialog v-model="hideVisible" :title="post?.is_hidden ? '取消隐藏' : '隐藏博文'" width="400px" :append-to-body="true">
    <p class="report-target">「{{ post?.title }}」</p>
    <el-input v-if="!post?.is_hidden" v-model="hideReason" type="textarea" :rows="4"
      placeholder="请填写隐藏原因（必填，将通知作者）" maxlength="500" show-word-limit />
    <p v-else style="font-size:13px;color:var(--el-text-color-secondary);margin:0">确定要取消隐藏该博文吗？博文将重新公开。</p>
    <template #footer>
      <el-button @click="hideVisible = false">取消</el-button>
      <el-button type="danger" :loading="hideSaving" @click="submitHide">确认</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { Post } from '@/types/models'
import { postsApi } from '@/api/modules/posts'

const props = defineProps<{
  postId: number
  post: Post | null
}>()

const emit = defineEmits<{
  hidden: []
}>()

const reportVisible = defineModel<boolean>('reportVisible', { default: false })
const hideVisible   = defineModel<boolean>('hideVisible',   { default: false })

const reportReason = ref('')
const reportSaving = ref(false)
const hideReason   = ref('')
const hideSaving   = ref(false)

watch(reportVisible, (v) => { if (v) reportReason.value = '' })
watch(hideVisible,   (v) => { if (v) hideReason.value = '' })

async function submitReport() {
  if (!reportReason.value.trim()) { ElMessage.warning('请填写举报原因'); return }
  reportSaving.value = true
  try {
    await postsApi.reportPost(props.postId, reportReason.value.trim())
    ElMessage.success('举报已提交，管理员将尽快处理')
    reportVisible.value = false
  } catch { /* 拦截器已处理 */ } finally { reportSaving.value = false }
}

async function submitHide() {
  const isHiding = !props.post?.is_hidden
  if (isHiding && !hideReason.value.trim()) { ElMessage.warning('请填写隐藏原因'); return }
  hideSaving.value = true
  try {
    await postsApi.setVisibility(props.postId, isHiding, isHiding ? hideReason.value.trim() : undefined)
    ElMessage.success(isHiding ? '博文已隐藏' : '已取消隐藏')
    hideVisible.value = false
    emit('hidden')
  } catch { /* 拦截器已处理 */ } finally { hideSaving.value = false }
}
</script>

<style scoped lang="scss">
.report-target { font-size: 13px; font-weight: 500; color: var(--el-text-color-primary); margin: 0 0 12px; }
</style>
