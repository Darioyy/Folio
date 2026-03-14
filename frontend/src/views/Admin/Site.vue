<template>
  <div class="site-page" v-loading="loading">
    <div class="site-grid">
      <!-- 左：表单卡片 -->
      <el-card class="form-card">
        <template #header>
          <div class="card-head">
            <span>站点设置</span>
            <div class="head-actions">
              <span v-if="saved" class="save-hint">已保存 ✓</span>
              <el-button type="primary" size="small" :loading="saving" @click="save">保存</el-button>
            </div>
          </div>
        </template>

        <div class="field-row">
          <div class="field-label">
            <span class="label-text">站点介绍</span>
            <span class="label-hint">展示在发现页右侧栏</span>
          </div>
          <div class="field-control">
            <el-input
              v-model="form.site_bio"
              type="textarea"
              :rows="5"
              placeholder="写一段简短的站点或站主介绍..."
              maxlength="500"
              show-word-limit
              resize="none"
            />
          </div>
        </div>

        <div class="field-row last">
          <div class="field-label">
            <span class="label-text">联系方式</span>
            <span class="label-hint">邮箱或社交账号</span>
          </div>
          <div class="field-control">
            <el-input
              v-model="form.site_contact"
              placeholder="例：contact@example.com"
              maxlength="200"
            />
          </div>
        </div>
      </el-card>

      <!-- 右：实时预览 -->
      <el-card class="preview-card">
        <template #header><span>效果预览</span></template>
        <div class="preview-body">
          <p class="preview-caption">发现页右侧栏中的显示效果</p>
          <div class="preview-widget">
            <div class="preview-owner">
              <div class="preview-avatar">{{ ownerInitial }}</div>
              <div class="preview-owner-info">
                <span class="preview-name">{{ ownerName }}</span>
                <span class="preview-meta">@{{ ownerUsername }} · 站主</span>
              </div>
            </div>
            <p class="preview-bio">{{ form.site_bio || '暂无介绍' }}</p>
            <div v-if="form.site_contact" class="preview-contact">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>
              </svg>
              <span>{{ form.site_contact }}</span>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { systemApi, type SiteInfo, type SiteOwner } from '@/api/modules/system'

const loading = ref(false)
const saving = ref(false)
const saved = ref(false)
const owner = ref<SiteOwner | null>(null)
const form = ref<SiteInfo>({ site_bio: '', site_contact: '' })

const ownerName = computed(() => owner.value?.nickname || owner.value?.username || 'Root')
const ownerUsername = computed(() => owner.value?.username || 'root')
const ownerInitial = computed(() => (ownerName.value[0] || 'R').toUpperCase())

async function load() {
  loading.value = true
  try {
    const [infoRes, ownerRes] = await Promise.all([systemApi.getSiteInfo(), systemApi.getOwner()])
    if (infoRes.data) { form.value.site_bio = infoRes.data.site_bio || ''; form.value.site_contact = infoRes.data.site_contact || '' }
    owner.value = ownerRes.data || null
  } catch { ElMessage.error('加载失败') } finally { loading.value = false }
}

async function save() {
  saving.value = true; saved.value = false
  try {
    await systemApi.updateSiteInfo(form.value)
    saved.value = true
    setTimeout(() => { saved.value = false }, 2500)
  } catch { ElMessage.error('保存失败') } finally { saving.value = false }
}

onMounted(load)
</script>

<style scoped lang="scss">
.site-page { max-width: 860px; }

.site-grid {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: $spacing-lg;
  align-items: start;

  @media (max-width: 720px) { grid-template-columns: 1fr; }
}

.card-head {
  display: flex; align-items: center; justify-content: space-between;
}
.head-actions { display: flex; align-items: center; gap: $spacing-sm; }
.save-hint { font-size: $font-xs; color: $color-success; }

// 字段行（与 Settings.vue 系统开关一致的边框分隔风格）
.field-row {
  display: flex;
  align-items: flex-start;
  gap: $spacing-md;
  padding: 14px 20px;
  border-bottom: 1px solid var(--color-border-subtle, var(--el-border-color-lighter));
  transition: background $transition-fast;

  &.last { border-bottom: none; }
  &:hover { background: rgba(0, 0, 0, 0.015); html.dark & { background: rgba(255,255,255,0.02); } }
}

.field-label {
  flex: 0 0 88px;
  padding-top: 7px;
  display: flex; flex-direction: column; gap: 3px;
}
.label-text { font-size: $font-sm; font-weight: 600; color: var(--color-text-primary); line-height: 1.4; }
.label-hint { font-size: $font-xs; color: var(--color-text-muted); line-height: 1.4; }
.field-control { flex: 1; min-width: 0; }

// 预览卡片
.preview-body { padding: 16px 20px; }
.preview-caption { font-size: $font-xs; color: var(--color-text-muted); margin: 0 0 10px; }

.preview-widget {
  background: var(--el-fill-color-light);
  border-radius: $radius-md;
  padding: $spacing-md;
  border: 1px solid var(--color-border-subtle, var(--el-border-color-lighter));
}

.preview-owner { display: flex; align-items: center; gap: $spacing-sm; margin-bottom: $spacing-sm; }
.preview-avatar {
  width: 34px; height: 34px; border-radius: 50%; flex-shrink: 0;
  background: linear-gradient(135deg, $color-primary, #7c3aed);
  color: #fff; display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700;
}
.preview-owner-info { display: flex; flex-direction: column; gap: 1px; }
.preview-name { font-size: $font-sm; font-weight: 600; color: var(--el-text-color-primary); }
.preview-meta { font-size: $font-xs; color: var(--el-text-color-secondary); }

.preview-bio {
  font-size: $font-xs; color: var(--el-text-color-secondary); line-height: 1.6;
  margin: 0 0 $spacing-xs; white-space: pre-wrap;
}
.preview-contact {
  display: flex; align-items: center; gap: 4px;
  font-size: $font-xs; color: var(--el-text-color-secondary);
  svg { flex-shrink: 0; opacity: 0.6; }
}
</style>
