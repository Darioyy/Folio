<template>
  <div class="space-page">
    <AppHeader />

    <div v-if="pageLoading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <div v-else class="space-container">
      <!-- 用户卡片 -->
      <div class="user-card">
        <div class="user-cover"></div>
        <div class="user-info-section">
          <div class="avatar-wrapper">
            <div class="avatar-upload-area" @click="triggerAvatarUpload">
              <el-avatar :src="avatarUrl" :size="100" class="user-avatar">
                {{ avatarFallback }}
              </el-avatar>
              <div class="avatar-overlay">
                <el-icon><Camera /></el-icon>
                <span>更换头像</span>
              </div>
            </div>
            <input
              ref="avatarInputRef"
              type="file"
              accept="image/*"
              style="display: none"
              @change="handleAvatarChange"
            />
          </div>

          <div class="user-details">
            <div class="user-header">
              <h1 class="user-name">
                {{ displayName }}
                <el-tag v-if="user?.is_root === 1" type="danger" size="small" style="margin-left: 8px">ROOT</el-tag>
                <el-tag v-else-if="user?.is_admin === 1" type="warning" size="small" style="margin-left: 8px">ADMIN</el-tag>
              </h1>
              <p class="user-username">@{{ user?.username }}</p>
              <p class="user-signature">{{ user?.signature || '这个人很懒，什么都没留下' }}</p>
            </div>

            <div class="user-stats">
              <div class="stat-item clickable" @click="goToFollowing">
                <span class="stat-value">{{ user?.following_count || 0 }}</span>
                <span class="stat-label">关注</span>
              </div>
              <div class="stat-divider"></div>
              <div class="stat-item clickable" @click="goToFollowers">
                <span class="stat-value">{{ user?.followers_count || 0 }}</span>
                <span class="stat-label">粉丝</span>
              </div>
              <div class="stat-divider"></div>
              <div class="stat-item">
                <span class="stat-value">{{ (user as any).like_count || 0 }}</span>
                <span class="stat-label">获赞</span>
              </div>
              <div class="stat-divider"></div>
              <div class="stat-item">
                <span class="stat-value">{{ (user as any).collect_count || 0 }}</span>
                <span class="stat-label">收藏</span>
              </div>
            </div>
          </div>
        </div>
      </div><!-- /.user-card -->

      <!-- 区域 Tab -->
      <div class="zone-tabs" ref="zoneTabsRef">
        <span
          v-for="tab in zoneTabs"
          :key="tab.value"
          :class="['zone-tab', { active: activeZone === tab.value }]"
          @click="selectZone(tab.value)"
        >
          <el-icon><component :is="tab.icon" /></el-icon>
          {{ tab.label }}
        </span>
      </div>

      <!-- 文件区 -->
      <div v-show="activeZone === 'files'" class="zone-content">
        <div class="files-layout">
          <!-- 左侧分组侧边栏 -->
          <div class="groups-sidebar">
            <!-- 固定项：收藏夹 -->
            <div
              :class="['group-item', 'favorites-item', { active: showFavorites }]"
              title="收藏夹"
              @click="toggleFavorites"
            >
              <span class="group-icon-wrap">
                <!-- 星形收藏夹图标 -->
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" width="15" height="15">
                  <path d="M8 2l1.6 3.2 3.5.5-2.5 2.5.6 3.5L8 10l-3.2 1.7.6-3.5-2.5-2.5 3.5-.5L8 2z"/>
                </svg>
              </span>
              <span class="group-name">收藏夹</span>
            </div>

            <!-- 分隔线 + 快捷入口标题 -->
            <div class="sidebar-section">
              <div class="sidebar-header">
                <span class="sidebar-title">快捷入口</span>
                <span
                  class="group-counter"
                  :class="{ warn: rootGroups.length >= 15, full: rootGroups.length >= 20 }"
                  :title="`最多 20 个，当前 ${rootGroups.length} 个`"
                >{{ rootGroups.length }}/20</span>
              </div>
            </div>

            <!-- 自定义根文件夹（可拖拽排序） -->
            <VueDraggable
              v-model="rootGroups"
              :animation="150"
              handle=".drag-handle"
              class="draggable-list"
              @end="handleSortEnd"
            >
              <div
                v-for="group in rootGroups"
                :key="group.id"
                :class="['group-item', { active: isRootGroupActive(group.id) }]"
                @click="navigateIntoRoot(group)"
              >
                <span class="group-icon-wrap">
                  <svg class="icon-folder" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" width="16" height="16">
                    <path d="M1.5 5a1 1 0 011-1H5.6l1.1 1.5H13.5a1 1 0 011 1V12a1 1 0 01-1 1h-11a1 1 0 01-1-1V5z"/>
                  </svg>
                  <svg class="icon-handle drag-handle" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" width="16" height="16">
                    <line x1="3" y1="5.5" x2="13" y2="5.5"/>
                    <line x1="3" y1="8" x2="13" y2="8"/>
                    <line x1="3" y1="10.5" x2="13" y2="10.5"/>
                  </svg>
                </span>
                <input
                  v-if="renamingGroupId === group.id"
                  class="rename-input"
                  v-model="renameValue"
                  @blur="confirmRename(group)"
                  @keyup.enter="confirmRename(group)"
                  @keyup.esc="cancelRename"
                  ref="renameInputRef"
                  @click.stop
                />
                <span
                  v-else
                  class="group-name"
                  @dblclick.stop="startRename(group)"
                >{{ group.name }}</span>
                <el-dropdown
                  trigger="click"
                  @command="(cmd: string) => handleGroupCommand(cmd, group)"
                  @click.stop
                >
                  <span class="group-more-icon" @click.stop>
                    <el-icon><MoreFilled /></el-icon>
                  </span>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="rename">重命名</el-dropdown-item>
                      <el-dropdown-item command="delete" style="color: var(--el-color-danger)">删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </VueDraggable>

            <!-- 固定快捷方式（来自 localStorage） -->
            <div
              v-for="sc in shortcuts"
              :key="`sc-${sc.type}-${sc.id}`"
              :class="['group-item', 'shortcut-item']"
              @click="navigateShortcut(sc)"
            >
              <span class="group-icon-wrap shortcut-icon">
                <!-- 文件夹快捷方式：pin+folder图标 -->
                <svg v-if="sc.type === 'folder'" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" width="15" height="15">
                  <path d="M1.5 5a1 1 0 011-1H5.6l1.1 1.5H13.5a1 1 0 011 1V12a1 1 0 01-1 1h-11a1 1 0 01-1-1V5z"/>
                </svg>
                <!-- 文件快捷方式：文件图标 -->
                <svg v-else viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" width="15" height="15">
                  <path d="M3 2h7l3 3v9a1 1 0 01-1 1H3a1 1 0 01-1-1V3a1 1 0 011-1z"/>
                  <polyline points="10,2 10,5 13,5"/>
                </svg>
              </span>
              <span class="group-name shortcut-name">{{ sc.name }}</span>
              <span class="shortcut-remove" @click.stop="removeShortcut(sc)" title="移除">×</span>
            </div>

            <!-- 新建根文件夹 -->
            <div class="new-group-area">
              <template v-if="creatingGroup">
                <input
                  class="rename-input create-input"
                  v-model="newGroupName"
                  placeholder="文件夹名称"
                  @blur="confirmCreateGroup"
                  @keyup.enter="confirmCreateGroup"
                  @keyup.esc="cancelCreateGroup"
                  ref="newGroupInputRef"
                />
              </template>
              <button
                v-else
                class="new-group-btn"
                :disabled="rootGroups.length >= 20"
                :title="rootGroups.length >= 20 ? '最多 20 个入口' : '新建根目录文件夹'"
                @click="startCreateGroup"
              >
                <el-icon><Plus /></el-icon>
                新建文件夹
              </button>
            </div>

            <!-- 添加快捷入口按钮 -->
            <button class="add-shortcut-btn" @click="openShortcutPicker" title="从已有文件夹添加快捷入口">
              <el-icon><Plus /></el-icon>
              添加快捷入口
            </button>
          </div>

          <!-- 右侧主内容区 -->
          <div
            class="files-main"
            :class="{ 'drag-active': isDragOver }"
            @dragenter.prevent="onDragEnter"
            @dragleave="onDragLeave"
            @dragover.prevent
            @drop.prevent="onDrop"
          >
            <!-- 拖拽放置遮罩 -->
            <div v-if="isDragOver" class="drop-overlay">
              <div class="drop-overlay-inner">
                <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" width="52" height="52">
                  <path d="M24 4v28M12 20l12-16 12 16"/>
                  <path d="M8 36h32a2 2 0 002 2v4H6v-4a2 2 0 012-2z"/>
                </svg>
                <p>松开鼠标上传文件</p>
                <span v-if="currentFolderId && currentFolderId > 0">
                  上传到「{{ breadcrumb[breadcrumb.length - 1]?.name }}」
                </span>
                <span v-else>上传到未分组</span>
              </div>
            </div>
            <!-- 收藏夹内容区 -->
            <div v-show="showFavorites" class="collections-area" v-loading="collectionsLoading">
              <div class="collections-header">
                <span class="collections-title">收藏夹</span>
                <span class="collections-count">{{ collectionFiles.length }} 个文件</span>
              </div>
              <div v-if="collectionFiles.length > 0" class="content-grid">
                <FileCard
                  v-for="file in collectionFiles"
                  :key="file.id"
                  :file="file"
                  :show-author="true"
                  @click="handlePreview(file)"
                />
              </div>
              <el-empty v-else-if="!collectionsLoading" description="还没有收藏的文件" class="empty-state" />
              <div v-if="collectionsHasMore" class="load-more-wrap">
                <el-button size="small" :loading="collectionsLoadingMore" @click="loadMoreCollections">加载更多</el-button>
              </div>
            </div>

            <!-- 工具栏（面包屑上方） -->
            <div v-show="!showFavorites" class="files-toolbar">
              <div class="toolbar-left">
                <!-- 类型 Tab（非编辑模式） -->
                <div v-if="!isEditMode" class="content-tabs">
                  <span
                    v-for="tab in typeTabs"
                    :key="tab.value"
                    :class="['tab-item', { active: typeFilter === tab.value }]"
                    @click="handleTypeChange(tab.value)"
                  >
                    <el-icon><component :is="tab.icon" /></el-icon>
                    {{ tab.label }}
                  </span>
                </div>
              </div>

              <div class="toolbar-right">
                <!-- 批量操作按钮（编辑模式，紧靠完成按钮左侧） -->
                <template v-if="isEditMode">
                  <span class="batch-count">{{ selectedItems.size }} 项</span>
                  <button class="batch-action-btn" @click="selectAllItems">
                    {{ isAllSelected ? '取消' : '全选' }}
                  </button>
                  <button
                    class="batch-action-btn"
                    :disabled="selectedItems.size === 0"
                    @click="openBatchMove"
                  >移动</button>
                  <button
                    class="batch-action-btn"
                    :disabled="selectedItems.size !== 1"
                    @click="startBatchRename"
                  >重命名</button>
                  <button
                    class="batch-action-btn danger"
                    :disabled="selectedItems.size === 0"
                    @click="batchDelete"
                  >删除</button>
                  <div class="toolbar-sep"></div>
                </template>

                <!-- 视图切换 -->
                <button
                  class="icon-btn"
                  :data-tip="viewMode === 'grid' ? '列表' : '网格'"
                  @click="toggleViewMode"
                >
                  <svg v-if="viewMode === 'list'" viewBox="0 0 16 16" width="15" height="15" fill="currentColor">
                    <rect x="1" y="2" width="14" height="2" rx="1"/>
                    <rect x="1" y="7" width="14" height="2" rx="1"/>
                    <rect x="1" y="12" width="14" height="2" rx="1"/>
                  </svg>
                  <svg v-else viewBox="0 0 16 16" width="15" height="15" fill="currentColor">
                    <rect x="1" y="1" width="6" height="6" rx="1"/>
                    <rect x="9" y="1" width="6" height="6" rx="1"/>
                    <rect x="1" y="9" width="6" height="6" rx="1"/>
                    <rect x="9" y="9" width="6" height="6" rx="1"/>
                  </svg>
                </button>

                <!-- 可见性筛选循环按钮（全部 → 私有 → 公开） -->
                <button
                  v-if="!isEditMode"
                  :class="['icon-btn', { active: visFilter !== '' }]"
                  :data-tip="visFilter === '' ? '全部' : visFilter === 'private' ? '私有' : '公开'"
                  @click="cycleVisFilter"
                >
                  <!-- 全部：眼睛 -->
                  <svg v-if="visFilter === ''" viewBox="0 0 16 16" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M1 8s3-5 7-5 7 5 7 5-3 5-7 5-7-5-7-5z"/>
                    <circle cx="8" cy="8" r="2"/>
                  </svg>
                  <!-- 私有：锁（关闭） -->
                  <svg v-else-if="visFilter === 'private'" viewBox="0 0 16 16" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="7" width="10" height="8" rx="1.5"/>
                    <path d="M5 7V5a3 3 0 016 0v2"/>
                  </svg>
                  <!-- 公开：开锁（锁扣明显抬起，右侧缺口大） -->
                  <svg v-else viewBox="0 0 16 16" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="8" width="10" height="7" rx="1.5"/>
                    <path d="M5 8V5a3 3 0 016 0"/>
                  </svg>
                </button>

                <!-- 上传按钮（图标专用，主色/危险色） -->
                <button
                  v-if="!isEditMode"
                  :class="['icon-btn', 'upload-btn', { 'is-full': isStorageFull }]"
                  :data-tip="isStorageFull ? '空间已满' : '上传'"
                  @click="openUpload"
                >
                  <svg viewBox="0 0 16 16" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M8 10.5V3"/>
                    <polyline points="5,5.5 8,3 11,5.5"/>
                    <path d="M2.5 12.5h11"/>
                  </svg>
                </button>

                <!-- 编辑模式按钮（铅笔 ↔ 勾，最右侧） -->
                <button
                  :class="['icon-btn', { active: isEditMode }]"
                  :data-tip="isEditMode ? '完成' : '编辑'"
                  @click="toggleEditMode"
                >
                  <!-- 未激活：铅笔图标 -->
                  <svg v-if="!isEditMode" viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M11.5 2.5a1.414 1.414 0 012 2L5 13H3v-2L11.5 2.5z"/>
                  </svg>
                  <!-- 激活：勾选图标（完成） -->
                  <svg v-else viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3,8 7,12 13,4"/>
                  </svg>
                </button>
              </div>
            </div>

            <!-- 面包屑导航 -->
            <div v-show="!showFavorites" class="breadcrumb-bar">
              <!-- 面包屑根目录：只显示图标，不显示文字 -->
              <button class="crumb-item crumb-home" @click="navigateToAll" title="返回根目录">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" width="13" height="13">
                  <path d="M1.5 5a1 1 0 011-1H5.6l1.1 1.5H13.5a1 1 0 011 1V12a1 1 0 01-1 1h-11a1 1 0 01-1-1V5z"/>
                </svg>
              </button>
              <template v-for="(crumb, idx) in breadcrumb" :key="crumb.id">
                <svg class="crumb-sep" viewBox="0 0 8 14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" width="6" height="11">
                  <polyline points="1,2 6,7 1,12"/>
                </svg>
                <button
                  :class="['crumb-item', { 'crumb-current': idx === breadcrumb.length - 1 }]"
                  @click="navigateToCrumb(idx)"
                >{{ crumb.name }}</button>
              </template>
              <span class="crumb-spacer"></span>
              <button class="new-subfolder-btn" data-tip="新建子文件夹" @click="startCreateSubFolder">
                <!-- 文件夹 + 加号合并图标 -->
                <svg viewBox="0 0 18 16" width="17" height="16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M1 4a1 1 0 011-1h3.5l1.2 1.5H16a1 1 0 011 1V13a1 1 0 01-1 1H2a1 1 0 01-1-1V4z"/>
                  <line x1="9" y1="7" x2="9" y2="11"/>
                  <line x1="7" y1="9" x2="11" y2="9"/>
                </svg>
              </button>
            </div>

            <!-- 内容区 -->
            <div v-show="!showFavorites" class="files-area" v-loading="filesLoading || subFoldersLoading">
              <!-- 新建子文件夹内联输入（网格/列表共用） -->
              <div v-if="creatingSubFolder" class="new-subfolder-form">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" width="15" height="15" style="flex-shrink:0;color:var(--el-color-primary)">
                  <path d="M1.5 5a1 1 0 011-1H5.6l1.1 1.5H13.5a1 1 0 011 1V12a1 1 0 01-1 1h-11a1 1 0 01-1-1V5z"/>
                </svg>
                <input
                  class="rename-input subfolder-name-input"
                  v-model="newSubFolderName"
                  placeholder="文件夹名称"
                  ref="newSubFolderInputRef"
                  @blur="confirmCreateSubFolder"
                  @keyup.enter="confirmCreateSubFolder"
                  @keyup.esc="cancelCreateSubFolder"
                />
                <span class="subfolder-hint">↵ 确认 · ESC 取消</span>
              </div>

              <!-- 网格视图：文件夹 + 文件统一网格，卡片尺寸一致 -->
              <div v-if="viewMode === 'grid' && (subFolders.length > 0 || allFiles.length > 0)" class="content-grid">
                <!-- 文件夹卡片 -->
                <div
                  v-for="folder in subFolders"
                  :key="`folder-${folder.id}`"
                  :class="['folder-grid-card', {
                    'drag-over': dragOverFolderId === folder.id,
                    'is-selected': isEditMode && selectedItems.has(`folder:${folder.id}`),
                    'is-dragging-folder': draggingFolder?.id === folder.id,
                  }]"
                  :draggable="!isEditMode"
                  @click="isEditMode ? toggleSelect('folder', folder.id) : navigateDeep(folder)"
                  @dragstart="!isEditMode && onFolderDragStart($event, folder)"
                  @dragend="!isEditMode && onFolderDragEnd()"
                  @dragenter.prevent="!isEditMode && onFolderDragEnter($event, folder)"
                  @dragover="!isEditMode && onFolderDragOver($event)"
                  @dragleave="!isEditMode && onFolderDragLeave($event)"
                  @drop.stop.prevent="!isEditMode && onFolderDrop($event, folder)"
                >
                  <div class="thumbnail-wrap folder-thumb-area">
                    <div v-if="isEditMode" class="item-checkbox" @click.stop="toggleSelect('folder', folder.id)">
                      <svg :class="['check-circle', { checked: selectedItems.has(`folder:${folder.id}`) }]" viewBox="0 0 16 16" width="16" height="16"><circle cx="8" cy="8" r="7"/><polyline points="4.5,8 7,10.5 11.5,5"/></svg>
                    </div>
                    <svg viewBox="0 0 48 40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" width="48" height="40" style="color: var(--el-color-primary); opacity: 0.75">
                      <path d="M2 10a2 2 0 012-2h10l3 4H44a2 2 0 012 2v20a2 2 0 01-2 2H4a2 2 0 01-2-2V10z"/>
                    </svg>
                    <div v-if="!isEditMode" class="folder-actions-overlay" @click.stop>
                      <button class="overlay-action-btn" title="编辑" @click.stop="openFolderEdit(folder)">
                        <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11.5 2.5a1.414 1.414 0 012 2L5 13H3v-2L11.5 2.5z"/></svg>
                      </button>
                      <button class="overlay-action-btn danger" title="删除" @click.stop="deleteFolderWithCheck(folder)">
                        <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="3,5 13,5"/><path d="M5 5V3h6v2"/><path d="M4 5l.7 8h6.6L12 5"/></svg>
                      </button>
                    </div>
                  </div>
                  <div class="card-body">
                    <p class="card-title">{{ folder.name }}</p>
                    <p class="card-desc">{{ folder.file_count }} 个文件<template v-if="folder.children_count > 0"> · {{ folder.children_count }} 子文件夹</template></p>
                  </div>
                </div>

                <!-- 文件卡片 -->
                <div
                  v-for="file in allFiles"
                  :key="`file-${file.id}`"
                  :class="['hub-file-item', {
                    'is-dragging': isDraggingItem(file.id),
                    'is-selected': isEditMode && selectedItems.has(`file:${file.id}`)
                  }]"
                  :draggable="!isEditMode"
                  @dragstart="!isEditMode && onFileDragStart($event, file)"
                  @dragend="!isEditMode && onFileDragEnd()"
                  @click="isEditMode ? toggleSelect('file', file.id) : undefined"
                >
                  <div v-if="isEditMode" class="item-checkbox" @click.stop="toggleSelect('file', file.id)">
                    <svg :class="['check-circle', { checked: selectedItems.has(`file:${file.id}`) }]" viewBox="0 0 16 16" width="16" height="16"><circle cx="8" cy="8" r="7"/><polyline points="4.5,8 7,10.5 11.5,5"/></svg>
                  </div>
                  <FileCard :file="file" :show-author="false" :show-badge="false" @click="!isEditMode && handlePreview(file)" />
                  <div v-if="!isEditMode" class="card-actions" @click.stop>
                    <button class="overlay-action-btn" title="编辑" @click.stop="openEdit(file)">
                      <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11.5 2.5a1.414 1.414 0 012 2L5 13H3v-2L11.5 2.5z"/></svg>
                    </button>
                    <el-popconfirm
                      title="确认删除该文件？"
                      confirm-button-text="删除"
                      cancel-button-text="取消"
                      confirm-button-type="danger"
                      @confirm="handleDelete(file)"
                    >
                      <template #reference>
                        <button class="overlay-action-btn danger" title="删除">
                          <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="3,5 13,5"/><path d="M5 5V3h6v2"/><path d="M4 5l.7 8h6.6L12 5"/></svg>
                        </button>
                      </template>
                    </el-popconfirm>
                  </div>
                </div>
              </div>

              <!-- 列表视图 -->
              <div v-else-if="viewMode === 'list' && (allFiles.length > 0 || subFolders.length > 0)" class="file-list">
                <div :class="['list-header', { 'with-check': isEditMode }]">
                  <span v-if="isEditMode" class="col-check"></span>
                  <span class="col-icon"></span>
                  <span class="col-name">文件名</span>
                  <span class="col-visibility hide-mobile"></span>
                  <span class="col-size hide-mobile">大小</span>
                  <span class="col-time">时间</span>
                  <span class="col-actions">操作</span>
                </div>
                <!-- 文件夹行 -->
                <div
                  v-for="folder in subFolders"
                  :key="`f-${folder.id}`"
                  :class="['list-row', 'folder-row', {
                    'drag-over': dragOverFolderId === folder.id,
                    'is-selected': isEditMode && selectedItems.has(`folder:${folder.id}`),
                    'with-check': isEditMode,
                    'is-dragging-folder': draggingFolder?.id === folder.id,
                  }]"
                  :draggable="!isEditMode"
                  @click="isEditMode ? toggleSelect('folder', folder.id) : navigateDeep(folder)"
                  @dragstart="!isEditMode && onFolderDragStart($event, folder)"
                  @dragend="!isEditMode && onFolderDragEnd()"
                  @dragenter.prevent="!isEditMode && onFolderDragEnter($event, folder)"
                  @dragover="!isEditMode && onFolderDragOver($event)"
                  @dragleave="!isEditMode && onFolderDragLeave($event)"
                  @drop.stop.prevent="!isEditMode && onFolderDrop($event, folder)"
                >
                  <span v-if="isEditMode" class="col-check" @click.stop="toggleSelect('folder', folder.id)">
                    <svg :class="['check-circle', { checked: selectedItems.has(`folder:${folder.id}`) }]" viewBox="0 0 16 16" width="16" height="16"><circle cx="8" cy="8" r="7"/><polyline points="4.5,8 7,10.5 11.5,5"/></svg>
                  </span>
                  <span class="col-icon">
                    <svg viewBox="0 0 40 34" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" width="20" height="17" style="color: var(--el-color-primary); opacity: 0.8">
                      <path d="M2 8a2 2 0 012-2h9l2.5 3.5H36a2 2 0 012 2v16a2 2 0 01-2 2H4a2 2 0 01-2-2V8z"/>
                    </svg>
                  </span>
                  <div class="col-name">
                    <span class="row-title">{{ folder.name }}</span>
                    <span class="row-desc">{{ folder.file_count }} 个文件<template v-if="folder.children_count > 0"> · {{ folder.children_count }} 子文件夹</template></span>
                  </div>
                  <span class="col-visibility hide-mobile"></span>
                  <span class="col-size hide-mobile">—</span>
                  <span class="col-time hide-mobile" :title="formatDate(folder.created_at)">{{ formatDate(folder.created_at, 'MM-DD') }}</span>
                  <div class="col-actions" @click.stop>
                    <template v-if="!isEditMode">
                      <el-button text size="small" :icon="EditIcon" @click.stop="openFolderEdit(folder)" />
                      <el-button text size="small" :icon="DeleteIcon" class="danger-btn" @click.stop="deleteFolderWithCheck(folder)" />
                    </template>
                  </div>
                </div>
                <!-- 文件行 -->
                <div
                  v-for="file in allFiles"
                  :key="file.id"
                  :class="['list-row', {
                    'is-selected': isEditMode && selectedItems.has(`file:${file.id}`),
                    'with-check': isEditMode
                  }]"
                  :draggable="!isEditMode"
                  @dragstart="!isEditMode && onFileDragStart($event, file)"
                  @dragend="!isEditMode && onFileDragEnd()"
                  @click="isEditMode ? toggleSelect('file', file.id) : handlePreview(file)"
                >
                  <span v-if="isEditMode" class="col-check" @click.stop="toggleSelect('file', file.id)">
                    <svg :class="['check-circle', { checked: selectedItems.has(`file:${file.id}`) }]" viewBox="0 0 16 16" width="16" height="16"><circle cx="8" cy="8" r="7"/><polyline points="4.5,8 7,10.5 11.5,5"/></svg>
                  </span>
                  <span class="col-icon">
                    <div v-if="file.file_category === 'image'" class="list-thumb">
                      <img :src="getFileUrl(file.thumbnail_path || file.file_path)" :alt="file.title" loading="lazy" @error="(e) => ((e.target as HTMLImageElement).style.display = 'none')" />
                    </div>
                    <div v-else-if="file.file_category === 'video'" class="list-thumb">
                      <img v-if="file.thumbnail_path" :src="getFileUrl(file.thumbnail_path)" :alt="file.title" loading="lazy" @error="(e) => ((e.target as HTMLImageElement).style.display = 'none')" />
                      <el-icon v-else :size="20" style="color: #6366f1"><VideoPlay /></el-icon>
                    </div>
                    <FileTypeIcon v-else :mime-type="file.mime_type" :file-name="file.file_name" size="sm" />
                  </span>
                  <div class="col-name">
                    <span class="row-title">{{ file.title }}</span>
                    <span v-if="file.file_name && file.file_name !== file.title" class="row-desc">{{ file.file_name }}</span>
                  </div>
                  <span class="col-visibility hide-mobile" @click.stop>
                    <button
                      :class="['vis-toggle', { 'is-public': file.visibility === 'public' }]"
                      :title="file.visibility === 'public' ? '公开，点击设为私有' : '私有，点击设为公开'"
                      @click.stop="toggleVisibility(file)"
                    >
                      <svg v-if="file.visibility === 'public'" viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="8" width="10" height="7" rx="1.5"/><path d="M5 8V5a3 3 0 016 0"/></svg>
                      <svg v-else viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="7" width="10" height="8" rx="1.5"/><path d="M5 7V5a3 3 0 016 0v2"/></svg>
                    </button>
                  </span>
                  <span class="col-size hide-mobile">{{ formatFileSize(file.file_size) }}</span>
                  <span class="col-time" :title="formatDate(file.created_at)">{{ formatDate(file.created_at, 'MM-DD HH:mm') }}</span>
                  <div class="col-actions" @click.stop>
                    <el-button text size="small" :icon="EditIcon" @click="openEdit(file)" />
                    <el-popconfirm title="确认删除该文件？" confirm-button-text="删除" cancel-button-text="取消" confirm-button-type="danger" @confirm="handleDelete(file)">
                      <template #reference>
                        <el-button text size="small" :icon="DeleteIcon" class="danger-btn" />
                      </template>
                    </el-popconfirm>
                  </div>
                </div>
              </div>

              <el-empty v-else-if="!filesLoading && !subFoldersLoading" description="还没有文件，去上传吧" class="empty-state" />
            </div>
          </div>
        </div>
      </div>

      <!-- 上传对话框 -->
      <el-dialog
        v-model="uploadDialogVisible"
        title="上传文件"
        width="480px"
        :close-on-click-modal="!uploading"
        @close="resetUploadForm"
      >
        <el-form :model="uploadForm" label-width="70px" :disabled="uploading">
          <el-form-item label="文件">
            <el-button @click="triggerFileInput" style="width: 100%; justify-content: flex-start">
              <el-icon style="margin-right: 6px"><UploadIcon /></el-icon>
              {{ uploadForm.file ? uploadForm.file.name : '点击选择文件' }}
            </el-button>
            <input ref="fileInputRef" type="file" hidden @change="handleFileChange" />
          </el-form-item>
          <el-form-item label="标题">
            <el-input v-model="uploadForm.title" placeholder="可选，不填则用文件名" maxlength="200" show-word-limit />
          </el-form-item>
          <el-form-item label="上传到">
            <el-cascader
              v-model="uploadForm.targetFolderId"
              :options="folderCascaderOptions"
              :props="{ checkStrictly: true, emitPath: false, value: 'id', label: 'name', children: 'children' }"
              :placeholder="currentFolderId && currentFolderId > 0 ? breadcrumb[breadcrumb.length-1]?.name : '未分组（根目录）'"
              clearable
              style="width: 100%"
              @visible-change="(v: boolean) => v && loadFolderTree()"
            />
          </el-form-item>
          <el-form-item label="可见性">
            <el-select v-model="uploadForm.visibility" style="width: 180px">
              <el-option label="私有" value="private" />
              <el-option label="公开" value="public" />
            </el-select>
          </el-form-item>
          <el-form-item label="描述">
            <el-input
              v-model="uploadForm.description"
              type="textarea"
              :rows="2"
              placeholder="可选"
              maxlength="500"
            />
          </el-form-item>
          <el-form-item v-if="uploadProgress > 0" label="">
            <el-progress
              :percentage="uploadProgress"
              style="width: 100%"
              :status="uploadProgress === 100 ? 'success' : undefined"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button :disabled="uploading" @click="uploadDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="uploading" @click="handleUpload">上传</el-button>
        </template>
      </el-dialog>

      <!-- 编辑对话框 -->
      <el-dialog v-model="editDialogVisible" title="编辑文件信息" width="480px">
        <el-form :model="editForm" label-width="70px">
          <el-form-item label="标题">
            <el-input v-model="editForm.title" maxlength="200" show-word-limit />
          </el-form-item>
          <el-form-item label="描述">
            <el-input
              v-model="editForm.description"
              type="textarea"
              :rows="3"
              placeholder="可选"
              maxlength="500"
            />
          </el-form-item>
          <el-form-item label="移动到">
            <el-cascader
              v-model="editForm.targetGroupId"
              :options="folderCascaderOptions"
              :props="{ checkStrictly: true, emitPath: false, value: 'id', label: 'name', children: 'children' }"
              placeholder="保留当前位置"
              clearable
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="可见性">
            <el-select v-model="editForm.visibility" style="width: 180px">
              <el-option label="私有" value="private" />
              <el-option label="公开" value="public" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="editLoading" @click="handleEdit">保存</el-button>
        </template>
      </el-dialog>

      <!-- 批量移动对话框 -->
      <el-dialog v-model="showBatchMove" title="移动到文件夹" width="400px">
        <el-cascader
          v-model="batchMoveTarget"
          :options="folderCascaderOptions"
          :props="{ checkStrictly: true, emitPath: false, value: 'id', label: 'name', children: 'children' }"
          placeholder="选择目标文件夹（空=未分组）"
          clearable
          style="width: 100%"
        />
        <template #footer>
          <el-button @click="showBatchMove = false">取消</el-button>
          <el-button type="primary" :loading="batchMoveLoading" @click="executeBatchMove">移动</el-button>
        </template>
      </el-dialog>

      <!-- 快捷入口选取对话框 -->
      <el-dialog v-model="showShortcutPickerDialog" title="添加快捷入口" width="380px">
        <el-cascader
          v-model="shortcutPickerSelected"
          :options="folderTree"
          :props="{ checkStrictly: true, emitPath: false, value: 'id', label: 'name', children: 'children' }"
          placeholder="选择要添加的文件夹"
          clearable
          style="width: 100%"
        />
        <template #footer>
          <el-button @click="showShortcutPickerDialog = false">取消</el-button>
          <el-button type="primary" @click="confirmAddShortcut">添加</el-button>
        </template>
      </el-dialog>

      <!-- 文件夹编辑对话框 -->
      <el-dialog v-model="folderEditDialogVisible" title="编辑文件夹" width="400px">
        <el-form :model="editFolderForm" label-width="70px">
          <el-form-item label="名称">
            <el-input v-model="editFolderForm.name" maxlength="100" show-word-limit />
          </el-form-item>
          <el-form-item label="移动到">
            <el-cascader
              v-model="editFolderForm.targetParentId"
              :options="folderCascaderOptions"
              :props="{ checkStrictly: true, emitPath: false, value: 'id', label: 'name', children: 'children' }"
              placeholder="保留当前位置"
              clearable
              style="width: 100%"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="folderEditDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="folderEditLoading" @click="handleFolderEdit">保存</el-button>
        </template>
      </el-dialog>

      <!-- 批量重命名对话框 -->
      <el-dialog v-model="showBatchRenameDialog" title="重命名" width="400px">
        <el-form label-width="70px">
          <el-form-item label="新名称">
            <el-input v-model="batchRenameName" placeholder="输入新名称" maxlength="200" />
          </el-form-item>
          <el-form-item v-if="batchRenameIsMulti">
            <span style="font-size:12px;color:var(--el-text-color-secondary)">多项重命名时，后续项自动附加 (1)、(2)... 以避免重名</span>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showBatchRenameDialog = false">取消</el-button>
          <el-button type="primary" :loading="batchRenameLoading" @click="executeBatchRename">确认</el-button>
        </template>
      </el-dialog>

      <!-- 概况区 -->
      <div v-show="activeZone === 'overview'" class="zone-content">
        <!-- 存储卡片 -->
        <div class="settings-card">
          <div class="card-title">
            <el-icon><Coin /></el-icon>
            存储空间
          </div>
          <div v-if="storageInfo" class="storage-info">
            <div class="storage-bar-wrap">
              <div
                class="storage-bar"
                :style="{
                  width: storageInfo.storage_percentage + '%',
                  background: storageInfo.storage_percentage >= 90
                    ? 'var(--el-color-danger)'
                    : storageInfo.storage_percentage >= 70
                    ? 'var(--el-color-warning)'
                    : undefined
                }"
              ></div>
            </div>
            <p class="storage-text">
              已用 <strong>{{ formatSize(storageInfo.storage_used) }}</strong>
              &nbsp;/&nbsp;共 <strong>{{ formatSize(storageInfo.storage_quota) }}</strong>
              &nbsp;（{{ storageInfo.storage_percentage.toFixed(1) }}%）
            </p>
          </div>
          <el-skeleton v-else :rows="2" animated />
        </div>

        <!-- 文件统计 -->
        <div class="settings-card">
          <div class="card-title">
            <el-icon><FolderOpened /></el-icon>
            文件统计
          </div>
          <div class="stats-grid">
            <div class="stats-cell">
              <el-icon class="stats-icon image-icon"><Picture /></el-icon>
              <span class="stats-num">{{ myStats.media }}</span>
              <span class="stats-label">媒体</span>
            </div>
            <div class="stats-cell">
              <el-icon class="stats-icon resource-icon"><Folder /></el-icon>
              <span class="stats-num">{{ myStats.resources }}</span>
              <span class="stats-label">资源</span>
            </div>
            <div class="stats-cell">
              <el-icon class="stats-icon post-icon"><Document /></el-icon>
              <span class="stats-num">{{ myStats.posts }}</span>
              <span class="stats-label">文章</span>
            </div>
          </div>
        </div>

        <!-- 社交统计 -->
        <div class="settings-card">
          <div class="card-title">
            <el-icon><User /></el-icon>
            社交
          </div>
          <div class="social-stats">
            <div class="social-item clickable" @click="goToFollowers">
              <span class="social-num">{{ user?.followers_count || 0 }}</span>
              <span class="social-label">粉丝</span>
            </div>
            <div class="social-divider"></div>
            <div class="social-item clickable" @click="goToFollowing">
              <span class="social-num">{{ user?.following_count || 0 }}</span>
              <span class="social-label">关注</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 设置区 -->
      <div v-show="activeZone === 'settings'" class="zone-content">
        <!-- 资料设置 -->
        <div class="settings-card">
          <div class="card-title">
            <el-icon><Edit /></el-icon>
            资料设置
          </div>
          <el-form :model="profileForm" label-position="top" class="settings-form">
            <el-form-item label="用户 UID">
              <el-input :value="(user as any)?.uid || '--'" disabled />
              <div class="field-hint">系统随机分配，不可自行修改</div>
            </el-form-item>
            <el-form-item label="昵称">
              <el-input v-model="profileForm.nickname" placeholder="设置昵称" maxlength="30" show-word-limit />
            </el-form-item>
            <el-form-item label="个性签名">
              <el-input
                v-model="profileForm.signature"
                type="textarea"
                placeholder="写下你的个性签名"
                :rows="3"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="profileForm.email" type="email" placeholder="your@email.com" />
            </el-form-item>
            <el-form-item v-if="userStore.isRoot" label="用户名（超级管理员）">
              <el-input v-model="profileForm.username" placeholder="修改登录用户名" maxlength="50" />
              <div class="field-hint">修改用户名将影响登录凭据和个人主页链接</div>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="profileSaving" @click="saveProfile">保存资料</el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 隐私设置 -->
        <div class="settings-card">
          <div class="card-title">
            <el-icon><Lock /></el-icon>
            隐私设置
          </div>
          <div class="privacy-list">
            <div class="privacy-item">
              <div class="privacy-label">
                <span>展示统计</span>
                <span class="privacy-hint">是否公开文件数量等统计信息</span>
              </div>
              <el-switch
                v-model="privacyForm.privacy_stats"
                :active-value="1"
                :inactive-value="0"
                @change="savePrivacy"
              />
            </div>
            <div class="privacy-item">
              <div class="privacy-label">
                <span>展示内容</span>
                <span class="privacy-hint">是否在主页显示你的公开作品</span>
              </div>
              <el-switch
                v-model="privacyForm.privacy_content"
                :active-value="1"
                :inactive-value="0"
                @change="savePrivacy"
              />
            </div>
            <div class="privacy-item">
              <div class="privacy-label">
                <span>展示关注关系</span>
                <span class="privacy-hint">是否公开粉丝和关注列表</span>
              </div>
              <el-switch
                v-model="privacyForm.privacy_follow"
                :active-value="1"
                :inactive-value="0"
                @change="savePrivacy"
              />
            </div>
          </div>
        </div>

        <!-- 修改密码 -->
        <div class="settings-card">
          <div class="card-title">
            <el-icon><Key /></el-icon>
            修改密码
          </div>
          <el-form :model="passwordForm" label-position="top" class="settings-form">
            <el-form-item label="当前密码">
              <el-input v-model="passwordForm.old_password" type="password" show-password placeholder="输入当前密码" />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input v-model="passwordForm.new_password" type="password" show-password placeholder="输入新密码（至少6位）" />
            </el-form-item>
            <el-form-item label="确认新密码">
              <el-input v-model="passwordForm.confirm_password" type="password" show-password placeholder="再次输入新密码" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="passwordSaving" @click="savePassword">修改密码</el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 内测码兑换（仅普通用户可见） -->
        <div v-if="!userStore.isAdminOrRoot" class="settings-card">
          <div class="card-title">
            <el-icon><Ticket /></el-icon>
            内测码兑换
          </div>
          <el-form label-position="top" class="settings-form">
            <el-form-item label="内测码">
              <el-input
                v-model="redeemCode"
                placeholder="输入 8 位内测码"
                maxlength="8"
                style="width: 200px"
                :disabled="redeemLoading"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="redeemLoading" @click="handleRedeemCode">兑换</el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </div>

    <!-- 批量上传进度面板 -->
    <Transition name="upload-panel">
      <div v-if="showUploadPanel" class="batch-upload-panel">
        <div class="batch-panel-header">
          <span>上传队列（{{ uploadTasks.filter(t => t.status === 'done').length }}/{{ uploadTasks.length }}）</span>
          <button class="batch-panel-close" :disabled="batchUploading" @click="closeBatchPanel">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" width="14" height="14">
              <line x1="3" y1="3" x2="13" y2="13"/><line x1="13" y1="3" x2="3" y2="13"/>
            </svg>
          </button>
        </div>
        <div class="batch-panel-list">
          <div v-for="task in uploadTasks" :key="task.id" class="batch-task-row">
            <div class="batch-task-name" :title="task.file.name">{{ task.file.name }}</div>
            <div class="batch-task-bar">
              <div
                class="batch-task-fill"
                :class="task.status"
                :style="{ width: task.progress + '%' }"
              ></div>
            </div>
            <span class="batch-task-status">
              <template v-if="task.status === 'pending'">等待</template>
              <template v-else-if="task.status === 'uploading'">{{ task.progress }}%</template>
              <template v-else-if="task.status === 'done'">✓</template>
              <template v-else>✗</template>
            </span>
          </div>
        </div>
      </div>
    </Transition>

    <FilePreview v-model="previewVisible" :file="currentFile" :type="previewType" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, reactive, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  FolderOpened, Picture, VideoPlay, Folder, Document, User,
  Grid, Setting, DataLine, Camera, Edit, Lock, Unlock, Key, Coin, Ticket,
  MoreFilled, Plus,
  Upload as UploadIcon, Edit as EditIcon, Delete as DeleteIcon
} from '@element-plus/icons-vue'
import { VueDraggable } from 'vue-draggable-plus'
import AppHeader from '@/components/common/AppHeader.vue'
import FileCard from '@/components/business/FileCard.vue'
import FilePreview from '@/components/business/FilePreview.vue'
import FileTypeIcon from '@/components/business/FileTypeIcon.vue'
import { useUserStore } from '@/stores/user'
import { usersApi } from '@/api/modules/users'
import { hubApi } from '@/api/modules/hub'
import { filesApi } from '@/api/modules/files'
import { interactionsApi } from '@/api/modules/interactions'
import { groupsApi } from '@/api/modules/groups'
import { authApi } from '@/api/modules/auth'
import type { FileItem, User as UserType } from '@/types/models'
import type { StorageInfo } from '@/api/modules/hub'
import type { MyStats, PrivacySettings } from '@/api/modules/users'
import type { FileGroup } from '@/api/modules/groups'
import { formatFileSize, fromNow, getFileUrl, formatDate } from '@/utils/format'

type TypeFilter = '' | 'image' | 'video' | 'resource'
type VisFilter = '' | 'private' | 'public'
type ZoneType = 'files' | 'overview' | 'settings'

const router = useRouter()
const userStore = useUserStore()

const zoneTabs = [
  { value: 'overview' as ZoneType, label: '概况', icon: DataLine },
  { value: 'files' as ZoneType, label: '文件', icon: FolderOpened },
  { value: 'settings' as ZoneType, label: '设置', icon: Setting },
]

const typeTabs = [
  { value: '' as TypeFilter, label: '全部', icon: Grid },
  { value: 'resource' as TypeFilter, label: '资源', icon: Folder },
  { value: 'image' as TypeFilter, label: '图片', icon: Picture },
  { value: 'video' as TypeFilter, label: '视频', icon: VideoPlay },
]

// 状态
const pageLoading = ref(false)
const activeZone = ref<ZoneType>('overview')
const zoneTabsRef = ref<HTMLElement | null>(null)

// 收藏夹
const showFavorites = ref(false)
const collectionFiles = ref<FileItem[]>([])
const collectionsLoading = ref(false)
const collectionsLoadingMore = ref(false)
const collectionsPage = ref(1)
const collectionsHasMore = ref(false)

function selectZone(zone: ZoneType) {
  activeZone.value = zone
  nextTick(() => {
    zoneTabsRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

async function loadCollections(reset = true) {
  if (reset) {
    collectionsPage.value = 1
    collectionFiles.value = []
    collectionsLoading.value = true
  } else {
    collectionsLoadingMore.value = true
  }
  try {
    const res = await interactionsApi.getMyCollections(collectionsPage.value, 20)
    const items: FileItem[] = res.items || []
    const pagination = res.pagination
    if (reset) {
      collectionFiles.value = items
    } else {
      collectionFiles.value.push(...items)
    }
    collectionsHasMore.value = pagination ? collectionsPage.value < Math.ceil(pagination.total / pagination.page_size) : false
  } catch {
    // 静默失败
  } finally {
    collectionsLoading.value = false
    collectionsLoadingMore.value = false
  }
}

async function loadMoreCollections() {
  collectionsPage.value++
  await loadCollections(false)
}

function toggleFavorites() {
  showFavorites.value = !showFavorites.value
  if (showFavorites.value && collectionFiles.value.length === 0) {
    loadCollections()
  }
}

const user = computed(() => userStore.currentUser)

// 头像
const avatarInputRef = ref<HTMLInputElement | null>(null)
const avatarTimestamp = ref(Date.now())

const avatarUrl = computed(() => {
  const u = userStore.currentUser
  if (u?.avatar) {
    const base = authApi.getAvatarUrl()
    return `${base}?uid=${u.id}&t=${avatarTimestamp.value}`
  }
  return undefined
})

const avatarFallback = computed(() => {
  const u = userStore.currentUser
  return u?.nickname?.[0] || u?.username?.[0] || '?'
})

const displayName = computed(() => {
  const u = userStore.currentUser
  return u?.nickname || u?.username || ''
})

// 文件区
const typeFilter = ref<TypeFilter>('')
const visFilter = ref<VisFilter>('')
// 每个 Tab 独立的视图偏好（无存储时的智能默认：resource→列表，其余→网格）
const TAB_DEFAULT_VIEW: Record<TypeFilter, 'grid' | 'list'> = {
  '': 'grid', resource: 'list', image: 'grid', video: 'grid',
}
function getTabViewKey(tab: TypeFilter) {
  return `vs-space-view:${tab || 'all'}`
}
function getSavedTabView(tab: TypeFilter): 'grid' | 'list' {
  return (localStorage.getItem(getTabViewKey(tab)) as 'grid' | 'list' | null) ?? TAB_DEFAULT_VIEW[tab]
}
const viewMode = ref<'grid' | 'list'>(getSavedTabView(typeFilter.value))

// 编辑/批量选择模式
const isEditMode = ref(false)
const selectedItems = ref<Set<string>>(new Set())

// 批量操作状态
const showBatchMove = ref(false)
const batchMoveTarget = ref<number | null>(null)
const batchMoveLoading = ref(false)
const showBatchRenameDialog = ref(false)
const batchRenameName = ref('')
const batchRenameLoading = ref(false)
const batchRenameIsMulti = computed(() => selectedItems.value.size > 1)
const filesLoading = ref(false)
const toggleLoading = ref<number | null>(null)
const allFiles = ref<FileItem[]>([])
const previewVisible = ref(false)
const currentFile = ref<FileItem | null>(null)

// 分组侧边栏
const currentFolderId = ref<number | null>(null)  // null=全部，-1=未分组，n=文件夹 ID
const rootGroups = ref<FileGroup[]>([])
const breadcrumb = ref<{ id: number; name: string }[]>([])
const subFolders = ref<FileGroup[]>([])
const subFoldersLoading = ref(false)
const renamingGroupId = ref<number | null>(null)
const renameValue = ref('')
const renameInputRef = ref<HTMLInputElement | null>(null)
const creatingGroup = ref(false)
const newGroupName = ref('')
const newGroupInputRef = ref<HTMLInputElement | null>(null)
const creatingSubFolder = ref(false)
const newSubFolderName = ref('')
const newSubFolderInputRef = ref<HTMLInputElement | null>(null)

// ==================== 拖拽上传 ====================

interface UploadTask {
  id: string
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'done' | 'error'
}

const isDragOver = ref(false)
const dragCounter = ref(0)
const uploadTasks = ref<UploadTask[]>([])
const showUploadPanel = ref(false)
const batchUploading = ref(false)

// 文件拖拽移动
const draggingFile = ref<FileItem | null>(null)
const draggingFolder = ref<FileGroup | null>(null)
const isSidebarDragOver = ref(false)
const dragOverFolderId = ref<number | null>(null)
let folderHoverTimer: ReturnType<typeof setTimeout> | null = null
const moveHistory = ref<Array<{ fileId: number; prevGroupId: number | null }>>([])

// 快捷入口
interface Shortcut { type: 'folder' | 'file'; id: number; name: string }
const shortcuts = ref<Shortcut[]>([])
const SHORTCUT_KEY = computed(() => `vs-shortcuts:${userStore.currentUser?.id ?? 'anon'}`)

function loadShortcuts() {
  try {
    const raw = localStorage.getItem(SHORTCUT_KEY.value)
    shortcuts.value = raw ? JSON.parse(raw) : []
  } catch { shortcuts.value = [] }
}

function saveShortcuts() {
  localStorage.setItem(SHORTCUT_KEY.value, JSON.stringify(shortcuts.value))
}

function addShortcut(type: 'folder' | 'file', id: number, name: string) {
  if (shortcuts.value.some(s => s.type === type && s.id === id)) return
  shortcuts.value.push({ type, id, name })
  saveShortcuts()
  ElMessage.success('已添加到快捷入口')
}

function removeShortcut(sc: Shortcut) {
  shortcuts.value = shortcuts.value.filter(s => !(s.type === sc.type && s.id === sc.id))
  saveShortcuts()
}

// 快捷入口选取对话框
const showShortcutPickerDialog = ref(false)
const shortcutPickerSelected = ref<number | null>(null)

function openShortcutPicker() {
  shortcutPickerSelected.value = null
  loadFolderTree()
  showShortcutPickerDialog.value = true
}

function findFolderName(nodes: FolderNode[], targetId: number): string | undefined {
  for (const n of nodes) {
    if (n.id === targetId) return n.name
    if (n.children) {
      const found = findFolderName(n.children, targetId)
      if (found) return found
    }
  }
  return undefined
}

function confirmAddShortcut() {
  const id = shortcutPickerSelected.value
  if (!id) { ElMessage.warning('请选择文件夹'); return }
  const name = findFolderName(folderTree.value, id)
  if (name) addShortcut('folder', id, name)
  showShortcutPickerDialog.value = false
}

function navigateShortcut(sc: Shortcut) {
  if (sc.type === 'folder') {
    currentFolderId.value = sc.id
    breadcrumb.value = [{ id: sc.id, name: sc.name }]
    Promise.all([loadSubFolders(), loadFiles()])
  }
}

const previewType = computed<'media' | 'resource'>(() => {
  if (!currentFile.value) return 'media'
  return currentFile.value.file_category === 'resource' ? 'resource' : 'media'
})

// 判断文件是否正在被拖拽（单文件拖拽场景）
function isDraggingItem(fileId: number): boolean {
  return draggingFile.value?.id === fileId
}

// 同文件夹内列表排序（仅在文件夹内的列表视图且非编辑模式下启用）
const canSortInFolder = computed(() =>
  viewMode.value === 'list' &&
  currentFolderId.value !== null &&
  currentFolderId.value > 0 &&
  !isEditMode.value
)

async function handleFileSortEnd() {
  const ids = allFiles.value.map(f => f.id)
  try {
    await filesApi.sortInGroup(ids)
  } catch {
    // 排序保存失败静默处理
  }
}

// 概况区
const storageInfo = ref<StorageInfo | null>(null)
const myStats = reactive<MyStats>({ posts: 0, media: 0, resources: 0, total_size: 0 })

const isStorageFull = computed(() => {
  if (!storageInfo.value) return false
  const { storage_used, storage_quota } = storageInfo.value
  return storage_quota > 0 && storage_used >= storage_quota
})

// 设置区
const profileForm = reactive({ nickname: '', signature: '', email: '', username: '' })
const profileSaving = ref(false)

const privacyForm = reactive<{ privacy_stats: 0|1, privacy_content: 0|1, privacy_follow: 0|1 }>({
  privacy_stats: 1,
  privacy_content: 1,
  privacy_follow: 1
})

const passwordForm = reactive({ old_password: '', new_password: '', confirm_password: '' })
const passwordSaving = ref(false)

const redeemCode = ref('')
const redeemLoading = ref(false)

// ==================== 上传 ====================

const uploadDialogVisible = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const fileInputRef = ref<HTMLInputElement | null>(null)
const uploadForm = reactive({
  file: null as File | null,
  title: '',
  visibility: 'private' as 'private' | 'public',
  description: '',
  targetFolderId: undefined as number | undefined,
})

function openUpload() {
  if (isStorageFull.value && storageInfo.value) {
    ElMessageBox.alert(
      `您的存储空间已满，无法继续上传文件。\n\n已用：${formatSize(storageInfo.value.storage_used)}\n总量：${formatSize(storageInfo.value.storage_quota)}\n\n请先删除部分文件以释放空间，或联系管理员扩容。`,
      '存储空间不足',
      { type: 'error', confirmButtonText: '知道了', customClass: 'storage-full-alert' }
    )
    return
  }
  uploadDialogVisible.value = true
}

function triggerFileInput() {
  fileInputRef.value?.click()
}

function handleFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) {
    uploadForm.file = file
    uploadForm.title = file.name.replace(/\.[^.]+$/, '')
  }
}

function detectCategory(file: File): 'image' | 'video' | 'resource' {
  if (file.type.startsWith('image/')) return 'image'
  if (file.type.startsWith('video/')) return 'video'
  return 'resource'
}

async function handleUpload() {
  if (!uploadForm.file) { ElMessage.warning('请选择文件'); return }

  uploading.value = true
  uploadProgress.value = 0

  // 标题：使用输入值，否则回退到文件名（去扩展名）
  const title = uploadForm.title.trim() || uploadForm.file.name.replace(/\.[^.]+$/, '')

  const formData = new FormData()
  formData.append('file', uploadForm.file)
  formData.append('title', title)
  formData.append('category', detectCategory(uploadForm.file))
  formData.append('visibility', uploadForm.visibility)
  if (uploadForm.description.trim()) {
    formData.append('description', uploadForm.description.trim())
  }
  // 优先用弹窗选择的目标文件夹，其次回退到当前浏览文件夹
  const targetId = uploadForm.targetFolderId !== undefined
    ? uploadForm.targetFolderId
    : (currentFolderId.value && currentFolderId.value > 0 ? currentFolderId.value : undefined)
  if (targetId && targetId > 0) {
    formData.append('group_id', String(targetId))
  }

  try {
    await filesApi.uploadWithProgress(formData, (p) => { uploadProgress.value = p })
    ElMessage.success('上传成功')
    uploadDialogVisible.value = false
    await loadFiles()
    loadOverview()
  } catch {
    // 错误已由拦截器统一展示
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }
}

function resetUploadForm() {
  uploadForm.file = null
  uploadForm.title = ''
  uploadForm.visibility = 'private'
  uploadForm.description = ''
  uploadForm.targetFolderId = undefined
  uploadProgress.value = 0
  if (fileInputRef.value) fileInputRef.value.value = ''
}

// ==================== 编辑 ====================

const editDialogVisible = ref(false)
const editLoading = ref(false)
const editTargetId = ref<number | null>(null)
const editForm = reactive({ title: '', description: '', targetGroupId: undefined as number | undefined, visibility: 'private' as 'private' | 'public' })

// 文件夹 Cascader 数据（用于 "移动到" 选择器）
// id=-1 表示"未分组"，id>0 表示具体文件夹
interface FolderNode { id: number; name: string; children?: FolderNode[] }
const folderTree = ref<FolderNode[]>([])
const folderCascaderOptions = computed<FolderNode[]>(() => [
  { id: -1, name: '未分组（根目录）' },
  ...folderTree.value
])

// 加载文件夹树（用于"移动到"级联选择器）
async function loadFolderTree() {
  try {
    const rootRes = await groupsApi.list()
    const roots = rootRes.data || []
    // 递归加载子文件夹
    async function loadChildren(nodes: FolderNode[]): Promise<FolderNode[]> {
      return Promise.all(nodes.map(async (n) => {
        if (!n.id) return n
        const childRes = await groupsApi.getChildren(n.id)
        const children = childRes.data || []
        if (children.length === 0) return n
        return { ...n, children: await loadChildren(children.map(c => ({ id: c.id, name: c.name }))) }
      }))
    }
    folderTree.value = await loadChildren(roots.map(r => ({ id: r.id, name: r.name })))
  } catch {
    // 静默失败
  }
}

function openEdit(file: FileItem) {
  editTargetId.value = file.id
  editForm.title = file.title
  editForm.description = file.description || ''
  editForm.targetGroupId = undefined
  editForm.visibility = file.visibility as 'private' | 'public'
  loadFolderTree()
  editDialogVisible.value = true
}

async function handleEdit() {
  if (!editTargetId.value) return
  if (!editForm.title.trim()) { ElMessage.warning('标题不能为空'); return }
  editLoading.value = true
  try {
    const res = await filesApi.update(editTargetId.value, {
      title: editForm.title.trim(),
      description: editForm.description.trim() || undefined,
      visibility: editForm.visibility,
    })
    const idx = allFiles.value.findIndex(f => f.id === editTargetId.value)
    if (idx >= 0) allFiles.value[idx] = { ...allFiles.value[idx], ...res.data }
    // 如果选择了目标文件夹，执行移动（-1 表示未分组/根目录，转为 null 传给 API）
    if (editForm.targetGroupId !== undefined) {
      const groupId = editForm.targetGroupId === -1 ? null : editForm.targetGroupId
      await filesApi.updateGroup(editTargetId.value, groupId)
    }
    ElMessage.success('已保存')
    editDialogVisible.value = false
    await loadFiles()
  } catch {
    // 错误已由拦截器统一展示
  } finally {
    editLoading.value = false
  }
}

// ==================== 删除 ====================

async function handleDelete(file: FileItem) {
  try {
    await filesApi.delete(file.id)
    allFiles.value = allFiles.value.filter(f => f.id !== file.id)
    ElMessage.success('已删除')
    loadOverview()
  } catch {
    // 错误已由拦截器统一展示
  }
}

// ==================== 文件区 ====================

async function loadFiles() {
  filesLoading.value = true
  try {
    const vis = visFilter.value || undefined
    const cat = typeFilter.value || undefined
    const folderId = currentFolderId.value  // null=全部，-1=未分组，n=指定文件夹

    const res = await filesApi.getList({
      page_size: 200,
      ...(vis ? { visibility: vis } : {}),
      ...(cat ? { category: cat as 'image' | 'video' | 'resource' } : {}),
      ...(folderId !== null ? { group_id: folderId } : {}),
    })
    allFiles.value = res.items
  } catch {
    ElMessage.error('加载文件失败')
  } finally {
    filesLoading.value = false
  }
}

async function toggleVisibility(file: FileItem) {
  toggleLoading.value = file.id
  try {
    const res = await filesApi.toggleVisibility(file.id)
    if (res.data) file.visibility = res.data.visibility as 'private' | 'public'
    ElMessage.success(file.visibility === 'public' ? '已设为公开' : '已设为私有')
  } catch {
    ElMessage.error('切换可见性失败')
  } finally {
    toggleLoading.value = null
  }
}

function handlePreview(file: FileItem) {
  router.push({ name: 'FileDetail', params: { id: file.id } })
}

function handleTypeChange(val: TypeFilter) {
  typeFilter.value = val
  viewMode.value = getSavedTabView(val)   // 读取该 Tab 独立保存的视图偏好
  loadFiles()
}

// ==================== 视图切换（每 Tab 独立持久化） ====================

function toggleViewMode() {
  viewMode.value = viewMode.value === 'grid' ? 'list' : 'grid'
  localStorage.setItem(getTabViewKey(typeFilter.value), viewMode.value)
}

function cycleVisFilter() {
  if (visFilter.value === '') visFilter.value = 'private'
  else if (visFilter.value === 'private') visFilter.value = 'public'
  else visFilter.value = ''
  loadFiles()
}

// viewMode 持久化已在 toggleViewMode 内联处理，无需 watch

// ==================== 编辑模式 & 批量操作 ====================

function toggleEditMode() {
  isEditMode.value = !isEditMode.value
  if (!isEditMode.value) selectedItems.value = new Set()
}

function toggleSelect(type: 'file' | 'folder', id: number) {
  const key = `${type}:${id}`
  const next = new Set(selectedItems.value)
  if (next.has(key)) next.delete(key)
  else next.add(key)
  selectedItems.value = next
}

const isAllSelected = computed(() => {
  const total = allFiles.value.length + subFolders.value.length
  if (total === 0) return false
  return allFiles.value.every(f => selectedItems.value.has(`file:${f.id}`)) &&
    subFolders.value.every(g => selectedItems.value.has(`folder:${g.id}`))
})

function selectAllItems() {
  if (isAllSelected.value) {
    selectedItems.value = new Set()
  } else {
    const next = new Set<string>()
    allFiles.value.forEach(f => next.add(`file:${f.id}`))
    subFolders.value.forEach(g => next.add(`folder:${g.id}`))
    selectedItems.value = next
  }
}

async function batchDelete() {
  if (selectedItems.value.size === 0) return
  const fileIds = [...selectedItems.value]
    .filter(k => k.startsWith('file:'))
    .map(k => Number(k.slice(5)))
  const folderIds = [...selectedItems.value]
    .filter(k => k.startsWith('folder:'))
    .map(k => Number(k.slice(7)))
  const total = fileIds.length + folderIds.length
  try {
    await ElMessageBox.confirm(
      `确认删除已选的 ${total} 个项目？文件夹中的文件将移至未分组，此操作不可撤销。`,
      '批量删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
  } catch { return }
  let errCount = 0
  for (const id of fileIds) {
    try { await filesApi.delete(id) } catch { errCount++ }
  }
  for (const id of folderIds) {
    try { await groupsApi.delete(id) } catch { errCount++ }
  }
  if (errCount > 0) ElMessage.warning(`部分项目删除失败（${errCount} 个）`)
  else ElMessage.success(`已删除 ${total} 个项目`)
  selectedItems.value = new Set()
  await Promise.all([loadFiles(), loadRootGroups(), loadSubFolders()])
  loadOverview()
}

function openBatchMove() {
  loadFolderTree()
  batchMoveTarget.value = null
  showBatchMove.value = true
}

async function executeBatchMove() {
  if (selectedItems.value.size === 0) { showBatchMove.value = false; return }
  const fileIds = [...selectedItems.value]
    .filter(k => k.startsWith('file:'))
    .map(k => Number(k.slice(5)))
  batchMoveLoading.value = true
  let errCount = 0
  for (const id of fileIds) {
    // -1 表示未分组/根目录，转为 null 传给 API
    try { await filesApi.updateGroup(id, batchMoveTarget.value === -1 ? null : batchMoveTarget.value) } catch { errCount++ }
  }
  batchMoveLoading.value = false
  showBatchMove.value = false
  batchMoveTarget.value = null
  if (errCount > 0) ElMessage.warning(`部分文件移动失败（${errCount} 个）`)
  else ElMessage.success('移动完成')
  selectedItems.value = new Set()
  await loadFiles()
}

function startBatchRename() {
  if (selectedItems.value.size === 0) return
  const first = [...selectedItems.value][0]
  if (first.startsWith('file:')) {
    const id = Number(first.slice(5))
    const file = allFiles.value.find(f => f.id === id)
    batchRenameName.value = file?.title || ''
  } else {
    const id = Number(first.slice(7))
    const folder = subFolders.value.find(f => f.id === id)
    batchRenameName.value = folder?.name || ''
  }
  showBatchRenameDialog.value = true
}

async function executeBatchRename() {
  const baseName = batchRenameName.value.trim()
  if (!baseName) { ElMessage.warning('名称不能为空'); return }
  batchRenameLoading.value = true
  const items = [...selectedItems.value]
  let errCount = 0
  for (let i = 0; i < items.length; i++) {
    const name = i === 0 ? baseName : `${baseName}(${i})`
    const key = items[i]
    try {
      if (key.startsWith('file:')) {
        const id = Number(key.slice(5))
        const res = await filesApi.update(id, { title: name })
        const idx = allFiles.value.findIndex(f => f.id === id)
        if (idx >= 0) allFiles.value[idx] = { ...allFiles.value[idx], ...res.data }
      } else {
        const id = Number(key.slice(7))
        await groupsApi.rename(id, name)
      }
    } catch { errCount++ }
  }
  batchRenameLoading.value = false
  showBatchRenameDialog.value = false
  if (errCount > 0) ElMessage.warning(`部分重命名失败（${errCount} 个）`)
  else ElMessage.success('重命名完成')
  selectedItems.value = new Set()
  await Promise.all([loadFiles(), loadSubFolders()])
}

// ==================== 分组管理 ====================

async function loadRootGroups() {
  try {
    const res = await groupsApi.list()
    rootGroups.value = res.data || []
    // 若当前在根目录，同步更新 subFolders
    if (currentFolderId.value === null) {
      subFolders.value = rootGroups.value
    }
  } catch {
    // 静默失败
  }
}

async function loadSubFolders() {
  if (currentFolderId.value === null) {
    // 根目录：以根分组作为子文件夹展示
    subFolders.value = rootGroups.value
    return
  }
  if (currentFolderId.value === -1) {
    subFolders.value = []
    return
  }
  subFoldersLoading.value = true
  try {
    const res = await groupsApi.getChildren(currentFolderId.value)
    subFolders.value = res.data || []
  } catch {
    // 静默失败
  } finally {
    subFoldersLoading.value = false
  }
}

async function navigateToAll() {
  currentFolderId.value = null
  breadcrumb.value = []
  subFolders.value = rootGroups.value  // 根目录展示根分组
  await loadFiles()
}

async function navigateToUngrouped() {
  currentFolderId.value = -1
  breadcrumb.value = []
  subFolders.value = []
  await loadFiles()
}

async function navigateIntoRoot(group: FileGroup) {
  currentFolderId.value = group.id
  breadcrumb.value = [{ id: group.id, name: group.name }]
  await Promise.all([loadSubFolders(), loadFiles()])
}

async function navigateDeep(folder: FileGroup) {
  breadcrumb.value = [...breadcrumb.value, { id: folder.id, name: folder.name }]
  currentFolderId.value = folder.id
  await Promise.all([loadSubFolders(), loadFiles()])
}

async function navigateToCrumb(idx: number) {
  if (idx === breadcrumb.value.length - 1) return
  const crumb = breadcrumb.value[idx]
  breadcrumb.value = breadcrumb.value.slice(0, idx + 1)
  currentFolderId.value = crumb.id
  await Promise.all([loadSubFolders(), loadFiles()])
}

function isRootGroupActive(groupId: number): boolean {
  return breadcrumb.value.length > 0 && breadcrumb.value[0].id === groupId
}

async function handleSortEnd() {
  try {
    await groupsApi.sort(rootGroups.value.map(g => g.id))
  } catch {
    await loadRootGroups()
  }
}

function startRename(group: FileGroup) {
  renamingGroupId.value = group.id
  renameValue.value = group.name
  nextTick(() => {
    if (renameInputRef.value) {
      const el = Array.isArray(renameInputRef.value) ? renameInputRef.value[0] : renameInputRef.value
      el?.focus()
    }
  })
}

async function confirmRename(group: FileGroup) {
  if (renamingGroupId.value === null) return   // enter + blur 双触发守卫
  const name = renameValue.value.trim()
  renamingGroupId.value = null
  if (!name || name === group.name) return
  try {
    await groupsApi.rename(group.id, name)
    await loadRootGroups()
  } catch {
    ElMessage.error('重命名失败')
  }
}

function cancelRename() {
  renamingGroupId.value = null
}

function handleGroupCommand(cmd: string, group: FileGroup) {
  if (cmd === 'rename') {
    startRename(group)
  } else if (cmd === 'delete') {
    ElMessageBox.confirm(
      `确认删除文件夹「${group.name}」？其中的文件将移至未分组，子文件夹将上移一级。`,
      '删除文件夹',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    ).then(async () => {
      try {
        await groupsApi.delete(group.id)
        if (breadcrumb.value.length > 0 && breadcrumb.value[0].id === group.id) {
          await navigateToAll()
        }
        await Promise.all([loadRootGroups(), loadFiles()])
      } catch {
        ElMessage.error('删除文件夹失败')
      }
    }).catch(() => {})
  }
}

function startCreateGroup() {
  if (rootGroups.value.length >= 20) {
    ElMessage.warning('根目录最多 20 个文件夹，请整理后再新建')
    return
  }
  creatingGroup.value = true
  newGroupName.value = ''
  nextTick(() => {
    if (newGroupInputRef.value) {
      const el = Array.isArray(newGroupInputRef.value) ? newGroupInputRef.value[0] : newGroupInputRef.value
      el?.focus()
    }
  })
}

async function confirmCreateGroup() {
  if (!creatingGroup.value) return   // enter + blur 双触发守卫
  const name = newGroupName.value.trim()
  creatingGroup.value = false
  if (!name) return
  try {
    const res = await groupsApi.create(name)
    await loadRootGroups()
    if (res.data) await navigateIntoRoot(res.data)
  } catch {
    ElMessage.error('创建文件夹失败')
  }
}

function cancelCreateGroup() {
  creatingGroup.value = false
  newGroupName.value = ''
}

function startCreateSubFolder() {
  creatingSubFolder.value = true
  newSubFolderName.value = ''
  nextTick(() => {
    newSubFolderInputRef.value?.focus()
  })
}

async function confirmCreateSubFolder() {
  if (!creatingSubFolder.value) return   // enter + blur 双触发守卫
  const name = newSubFolderName.value.trim()
  creatingSubFolder.value = false
  if (!name || currentFolderId.value === null || currentFolderId.value === -1) return
  try {
    await groupsApi.create(name, currentFolderId.value)
    await loadSubFolders()
  } catch {
    ElMessage.error('创建文件夹失败')
  }
}

function cancelCreateSubFolder() {
  creatingSubFolder.value = false
  newSubFolderName.value = ''
}

function handleSubFolderCommand(cmd: string, folder: FileGroup) {
  if (cmd === 'rename') {
    ElMessageBox.prompt('', '重命名文件夹', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      inputValue: folder.name,
      inputPlaceholder: '文件夹名称',
    }).then(async ({ value }) => {
      const name = value?.trim()
      if (!name || name === folder.name) return
      try {
        await groupsApi.rename(folder.id, name)
        // 同步面包屑中的名称
        const crumbIdx = breadcrumb.value.findIndex(c => c.id === folder.id)
        if (crumbIdx >= 0) breadcrumb.value[crumbIdx].name = name
        await loadSubFolders()
      } catch {
        ElMessage.error('重命名失败')
      }
    }).catch(() => {})
  } else if (cmd === 'delete') {
    ElMessageBox.confirm(
      `确认删除文件夹「${folder.name}」？其中的文件将移至父文件夹，子文件夹将上移一级。`,
      '删除文件夹',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    ).then(async () => {
      try {
        await groupsApi.delete(folder.id)
        await Promise.all([loadSubFolders(), loadFiles()])
      } catch {
        ElMessage.error('删除文件夹失败')
      }
    }).catch(() => {})
  }
}

// ==================== 概况区 ====================

async function loadOverview() {
  try {
    const [storageRes, statsRes] = await Promise.all([
      hubApi.getStorageInfo(),
      usersApi.getMyStats()
    ])
    if (storageRes.data) {
      storageInfo.value = {
        storage_used: storageRes.data.storage_used ?? 0,
        storage_quota: storageRes.data.storage_quota ?? 0,
        storage_percentage: Number(storageRes.data.storage_percentage ?? 0),
      }
    }
    Object.assign(myStats, statsRes.data)
  } catch {
    // 静默失败
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
}

function goToFollowers() {
  if (user.value?.username) {
    router.push({ name: 'FollowList', params: { type: 'followers', username: user.value.username } })
  }
}

function goToFollowing() {
  if (user.value?.username) {
    router.push({ name: 'FollowList', params: { type: 'following', username: user.value.username } })
  }
}

// ==================== 设置区 ====================

function initSettingsForms() {
  const u = userStore.currentUser
  if (!u) return
  profileForm.nickname = u.nickname || ''
  profileForm.signature = (u as any).signature || ''
  profileForm.email = u.email || ''
  profileForm.username = u.username || ''
  // 隐私字段（currentUser 中有时没有这些字段，默认 1）
  privacyForm.privacy_stats = (u as any).privacy_stats ?? 1
  privacyForm.privacy_content = (u as any).privacy_content ?? 1
  privacyForm.privacy_follow = (u as any).privacy_follow ?? 1
}

async function saveProfile() {
  profileSaving.value = true
  try {
    // Root 专属：修改自己的用户名
    const u = userStore.currentUser
    if (userStore.isRoot && u && profileForm.username.trim() && profileForm.username.trim() !== u.username) {
      await usersApi.update(u.id, { username: profileForm.username.trim() } as any)
    }
    await usersApi.updateProfile({
      nickname: profileForm.nickname,
      signature: profileForm.signature,
      email: profileForm.email
    })
    await userStore.refreshUser()
    profileForm.username = userStore.currentUser?.username || ''
    ElMessage.success('资料保存成功')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.error?.message || '保存失败')
  } finally {
    profileSaving.value = false
  }
}

async function savePrivacy() {
  try {
    await usersApi.updatePrivacy({ ...privacyForm })
    ElMessage.success('隐私设置已保存')
  } catch {
    ElMessage.error('保存隐私设置失败')
  }
}

async function savePassword() {
  if (!passwordForm.old_password || !passwordForm.new_password) {
    ElMessage.warning('请填写完整密码信息')
    return
  }
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    ElMessage.error('两次输入的新密码不一致')
    return
  }
  if (passwordForm.new_password.length < 6) {
    ElMessage.error('新密码不能少于6位')
    return
  }
  passwordSaving.value = true
  try {
    await usersApi.changePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    })
    ElMessage.success('密码修改成功，请重新登录')
    await userStore.logout()
    await router.push('/login')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.error?.message || '密码修改失败')
  } finally {
    passwordSaving.value = false
  }
}

async function handleRedeemCode() {
  const code = redeemCode.value.trim().toUpperCase()
  if (!code || code.length !== 8) {
    ElMessage.warning('请输入有效的 8 位内测码')
    return
  }
  redeemLoading.value = true
  try {
    await usersApi.redeemInviteCode(code)
    ElMessage.success('内测码兑换成功')
    redeemCode.value = ''
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.error?.message || '兑换失败，内测码无效或已被使用')
  } finally {
    redeemLoading.value = false
  }
}

// ==================== 文件拖拽移动 ====================

function handleKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'z' && moveHistory.value.length > 0) {
    e.preventDefault()
    undoLastMove()
  }
}

function onFileDragStart(e: DragEvent, file: FileItem) {
  draggingFile.value = file
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('application/vaultshare-file', String(file.id))
  }
}

function onFileDragEnd() {
  draggingFile.value = null
  dragOverFolderId.value = null
  if (folderHoverTimer) { clearTimeout(folderHoverTimer); folderHoverTimer = null }
}

async function moveFileTo(file: FileItem, targetGroupId: number | null) {
  const prevGroupId = file.group_id ?? null
  if (prevGroupId === targetGroupId) return
  try {
    await filesApi.updateGroup(file.id, targetGroupId)
    moveHistory.value.push({ fileId: file.id, prevGroupId })
    // 从当前筛选视图中移除（如果当前在某文件夹内且目标不是该文件夹）
    if (currentFolderId.value !== null && currentFolderId.value > 0 && targetGroupId !== currentFolderId.value) {
      allFiles.value = allFiles.value.filter(f => f.id !== file.id)
    }
    await loadSubFolders()
    ElMessage.success('已移动，Ctrl+Z 可撤销')
  } catch {
    ElMessage.error('移动失败')
  }
}

async function undoLastMove() {
  const last = moveHistory.value.pop()
  if (!last) return
  try {
    await filesApi.updateGroup(last.fileId, last.prevGroupId)
    ElMessage.success('已撤销')
    await loadFiles()
  } catch {
    ElMessage.error('撤销失败')
  }
}

// ==================== 文件夹拖拽移动 ====================

function onFolderDragStart(e: DragEvent, folder: FileGroup) {
  draggingFolder.value = folder
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('application/vaultshare-folder', String(folder.id))
  }
}

function onFolderDragEnd() {
  draggingFolder.value = null
  dragOverFolderId.value = null
  if (folderHoverTimer) { clearTimeout(folderHoverTimer); folderHoverTimer = null }
}

// 文件夹编辑对话框
const folderEditDialogVisible = ref(false)
const folderEditLoading = ref(false)
const editFolderTarget = ref<FileGroup | null>(null)
const editFolderForm = reactive({ name: '', targetParentId: undefined as number | undefined })

function openFolderEdit(folder: FileGroup) {
  editFolderTarget.value = folder
  editFolderForm.name = folder.name
  editFolderForm.targetParentId = undefined
  loadFolderTree()
  folderEditDialogVisible.value = true
}

async function handleFolderEdit() {
  const folder = editFolderTarget.value
  if (!folder) return
  const name = editFolderForm.name.trim()
  if (!name) { ElMessage.warning('名称不能为空'); return }
  folderEditLoading.value = true
  try {
    if (name !== folder.name) {
      await groupsApi.rename(folder.id, name)
      const crumbIdx = breadcrumb.value.findIndex(c => c.id === folder.id)
      if (crumbIdx >= 0) breadcrumb.value[crumbIdx].name = name
    }
    if (editFolderForm.targetParentId !== undefined) {
      const newParent = editFolderForm.targetParentId === -1 ? null : editFolderForm.targetParentId
      await groupsApi.move(folder.id, newParent)
    }
    folderEditDialogVisible.value = false
    ElMessage.success('已保存')
    await Promise.all([loadRootGroups(), loadSubFolders()])
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.error?.message || '操作失败')
  } finally {
    folderEditLoading.value = false
  }
}

async function deleteFolderWithCheck(folder: FileGroup) {
  const hasContent = folder.file_count > 0 || folder.children_count > 0
  const msg = hasContent
    ? `文件夹「${folder.name}」包含 ${folder.file_count} 个文件和 ${folder.children_count} 个子文件夹，确认删除将一并递归删除所有内容，此操作不可撤销。`
    : `确认删除文件夹「${folder.name}」？`
  try {
    await ElMessageBox.confirm(msg, '删除文件夹', {
      confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning',
    })
  } catch { return }
  try {
    await groupsApi.delete(folder.id, hasContent)  // 有内容时 force=true，递归删除
    if (breadcrumb.value.some(c => c.id === folder.id)) {
      await navigateToAll()
    } else {
      await Promise.all([loadSubFolders(), loadFiles()])
    }
    await loadRootGroups()
  } catch {
    ElMessage.error('删除文件夹失败')
  }
}

// ==================== 侧边栏快捷入口拖放 ====================

function onSidebarDragEnter(e: DragEvent) {
  if (draggingFile.value || draggingFolder.value) {
    e.preventDefault()
    isSidebarDragOver.value = true
  }
}

function onSidebarDragOver(e: DragEvent) {
  if (draggingFile.value || draggingFolder.value) {
    e.preventDefault()
    if (e.dataTransfer) e.dataTransfer.dropEffect = 'link'
  }
}

function onSidebarDragLeave(e: DragEvent) {
  const related = e.relatedTarget as Node | null
  if (!(e.currentTarget as HTMLElement).contains(related)) {
    isSidebarDragOver.value = false
  }
}

function onSidebarDrop(e: DragEvent) {
  e.preventDefault()
  isSidebarDragOver.value = false
  if (draggingFile.value) {
    addShortcut('file', draggingFile.value.id, draggingFile.value.title)
    draggingFile.value = null
  } else if (draggingFolder.value) {
    addShortcut('folder', draggingFolder.value.id, draggingFolder.value.name)
    draggingFolder.value = null
  }
}

// 拖拽悬浮在子文件夹上：0.6s 后自动导航进入（spring-load）
function onFolderDragEnter(e: DragEvent, folder: FileGroup) {
  const isFileDrag = !!draggingFile.value
  const isFolderDrag = !!draggingFolder.value
  const isDiskDrag = e.dataTransfer?.types.includes('Files') ?? false
  if (!isFileDrag && !isFolderDrag && !isDiskDrag) return
  e.preventDefault()
  dragOverFolderId.value = folder.id
  if (folderHoverTimer) clearTimeout(folderHoverTimer)
  folderHoverTimer = setTimeout(async () => {
    folderHoverTimer = null
    await navigateDeep(folder)
  }, 600)
}

function onFolderDragOver(e: DragEvent) {
  if (draggingFile.value || draggingFolder.value || e.dataTransfer?.types.includes('Files')) {
    e.preventDefault()
    if (e.dataTransfer) e.dataTransfer.dropEffect = 'move'
  }
}

function onFolderDragLeave(e: DragEvent) {
  const related = e.relatedTarget as Node | null
  if ((e.currentTarget as HTMLElement).contains(related)) return
  if (folderHoverTimer) { clearTimeout(folderHoverTimer); folderHoverTimer = null }
  dragOverFolderId.value = null
}

async function onFolderDrop(e: DragEvent, folder: FileGroup) {
  e.stopPropagation()
  e.preventDefault()
  if (folderHoverTimer) { clearTimeout(folderHoverTimer); folderHoverTimer = null }
  dragOverFolderId.value = null

  // 文件夹拖拽 → 将源文件夹移动到目标文件夹内
  if (draggingFolder.value) {
    const sourceFolder = draggingFolder.value
    draggingFolder.value = null
    if (sourceFolder.id === folder.id) return
    try {
      await groupsApi.move(sourceFolder.id, folder.id)
      await Promise.all([loadRootGroups(), loadSubFolders()])
      ElMessage.success('文件夹已移动')
    } catch (err: any) {
      ElMessage.error(err?.response?.data?.error?.message || '移动失败')
    }
    return
  }

  if (draggingFile.value) {
    // 文件列表拖拽 → 移动到该文件夹
    const file = draggingFile.value
    draggingFile.value = null
    await moveFileTo(file, folder.id)
    return
  }

  if (e.dataTransfer?.types.includes('Files')) {
    // 磁盘文件拖拽 → 导航到该文件夹再上传
    isDragOver.value = false
    dragCounter.value = 0
    await navigateDeep(folder)
    const items = e.dataTransfer.items
    if (!items || items.length === 0) return
    const files: File[] = []
    await Promise.all(Array.from(items).map(item => {
      const entry = item.webkitGetAsEntry?.()
      if (entry) return collectEntryFiles(entry, files)
      const f = item.getAsFile()
      if (f) files.push(f)
      return Promise.resolve()
    }))
    if (files.length > 0) startBatchUpload(files)
  }
}

// ==================== 拖拽上传处理 ====================

function onDragEnter(e: DragEvent) {
  if (isStorageFull.value) return
  if (e.dataTransfer?.types.includes('Files')) {
    dragCounter.value++
    isDragOver.value = true
  }
}

function onDragLeave() {
  dragCounter.value--
  if (dragCounter.value <= 0) {
    dragCounter.value = 0
    isDragOver.value = false
  }
}

async function onDrop(e: DragEvent) {
  isDragOver.value = false
  dragCounter.value = 0

  // 文件列表拖拽 → 移动到当前文件夹
  if (draggingFile.value) {
    const file = draggingFile.value
    draggingFile.value = null
    if (currentFolderId.value !== null && currentFolderId.value > 0) {
      await moveFileTo(file, currentFolderId.value)
    }
    return
  }

  if (isStorageFull.value) { ElMessage.warning('存储空间已满，无法上传'); return }

  const items = e.dataTransfer?.items
  if (!items || items.length === 0) return

  const files: File[] = []
  await Promise.all(
    Array.from(items).map(item => {
      const entry = item.webkitGetAsEntry?.()
      if (entry) return collectEntryFiles(entry, files)
      const f = item.getAsFile()
      if (f) files.push(f)
      return Promise.resolve()
    })
  )

  if (files.length === 0) return
  startBatchUpload(files)
}

function collectEntryFiles(entry: FileSystemEntry, files: File[]): Promise<void> {
  if (entry.isFile) {
    return new Promise(resolve => {
      (entry as FileSystemFileEntry).file(f => { files.push(f); resolve() }, () => resolve())
    })
  }
  if (entry.isDirectory) {
    const reader = (entry as FileSystemDirectoryEntry).createReader()
    return new Promise(resolve => {
      const read = () => {
        reader.readEntries(async entries => {
          if (entries.length === 0) { resolve(); return }
          await Promise.all(entries.map(e => collectEntryFiles(e, files)))
          read()   // readEntries 可能分批返回，需循环直到空
        }, () => resolve())
      }
      read()
    })
  }
  return Promise.resolve()
}

async function startBatchUpload(files: File[]) {
  // 重名检测：对比当前已加载的文件列表
  const existingNames = new Set(allFiles.value.map(f => f.file_name || f.title))
  const duplicates = files.filter(f => existingNames.has(f.name))

  let overwriteAll = false
  let skipAll = false

  if (duplicates.length > 0) {
    try {
      const action = await ElMessageBox.confirm(
        `以下 ${duplicates.length} 个文件已存在同名文件：\n${duplicates.slice(0, 5).map(f => f.name).join('\n')}${duplicates.length > 5 ? `\n...（共 ${duplicates.length} 个）` : ''}\n\n选择"覆盖"将重新上传，选择"跳过"将跳过这些文件。`,
        '发现同名文件',
        {
          distinguishCancelAndClose: true,
          confirmButtonText: '覆盖',
          cancelButtonText: '跳过',
          type: 'warning',
        }
      )
      overwriteAll = action === 'confirm'
    } catch (action) {
      if (action === 'cancel') skipAll = true
      else return // Close = cancel all
    }
  }

  const filesToUpload = skipAll
    ? files.filter(f => !existingNames.has(f.name))
    : files

  if (filesToUpload.length === 0) {
    ElMessage.info('没有需要上传的文件')
    return
  }

  const tasks: UploadTask[] = filesToUpload.map((file, i) => ({
    id: `${Date.now()}-${i}`,
    file,
    progress: 0,
    status: 'pending',
  }))
  uploadTasks.value = tasks
  showUploadPanel.value = true
  batchUploading.value = true

  const errorTypes = new Map<string, number>() // errorType → count

  for (const task of uploadTasks.value) {
    task.status = 'uploading'
    try {
      const fd = new FormData()
      fd.append('file', task.file)
      fd.append('title', task.file.name.replace(/\.[^.]+$/, ''))
      fd.append('category', detectCategory(task.file))
      fd.append('visibility', 'private')
      if (currentFolderId.value && currentFolderId.value > 0) {
        fd.append('group_id', String(currentFolderId.value))
      }
      await filesApi.uploadWithProgress(fd, p => { task.progress = p })
      task.status = 'done'
      task.progress = 100
    } catch (err: any) {
      task.status = 'error'
      // 提取错误类型，按类型去重
      const errMsg = err?.response?.data?.error?.message || err?.message || '上传失败'
      const errKey = errMsg.includes('类型') || errMsg.includes('format') || errMsg.includes('extension')
        ? '不支持的文件类型'
        : errMsg.includes('大小') || errMsg.includes('size') || errMsg.includes('large')
        ? '文件超出大小限制'
        : errMsg.includes('空间') || errMsg.includes('quota') || errMsg.includes('storage')
        ? '存储空间不足'
        : '上传失败'
      errorTypes.set(errKey, (errorTypes.get(errKey) || 0) + 1)
    }
  }

  batchUploading.value = false

  // 汇总错误提示（每种错误类型只展示一次）
  if (errorTypes.size > 0) {
    const summary = [...errorTypes.entries()]
      .map(([type, count]) => `${type}：${count} 个文件`)
      .join('；')
    ElMessage.warning(`部分文件上传失败 — ${summary}`)
  }

  await loadFiles()
  loadOverview()
  setTimeout(() => { if (!batchUploading.value) closeBatchPanel() }, 3000)
}

function closeBatchPanel() {
  if (batchUploading.value) return
  showUploadPanel.value = false
  uploadTasks.value = []
}

// ==================== 头像上传 ====================

function triggerAvatarUpload() {
  avatarInputRef.value?.click()
}

async function handleAvatarChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  try {
    await usersApi.uploadAvatar(formData)
    await userStore.refreshUser()
    avatarTimestamp.value = Date.now()
    ElMessage.success('头像上传成功')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.error?.message || '头像上传失败')
  } finally {
    input.value = ''
  }
}

// ==================== 初始化 ====================

onMounted(async () => {
  document.addEventListener('keydown', handleKeydown)
  await Promise.all([loadFiles(), loadRootGroups(), loadOverview()])
  initSettingsForms()
  loadShortcuts()
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  if (folderHoverTimer) clearTimeout(folderHoverTimer)
})
</script>

<style scoped lang="scss">
.space-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

.space-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: $spacing-lg $spacing-md $spacing-3xl;
  width: 100%;
  display: flex;
  flex-direction: column;
}

.loading-container {
  padding: $spacing-xl;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

// ==================== 用户卡片 ====================

.user-card {
  background: var(--el-bg-color);
  border-radius: $radius-xl;
  overflow: hidden;
  box-shadow: $shadow-md;
  margin-bottom: $spacing-lg;
}

.user-cover {
  height: 200px;
  background: linear-gradient(135deg, $color-primary 0%, $color-secondary 100%);
}

.user-info-section {
  padding: 0 $spacing-xl $spacing-lg;
  margin-top: -50px;
}

.avatar-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: $spacing-md;
}

.avatar-upload-area {
  position: relative;
  cursor: pointer;
  border-radius: 50%;
  display: inline-block;

  &:hover .avatar-overlay {
    opacity: 1;
  }
}

.user-avatar {
  border: 4px solid var(--el-bg-color);
  font-size: 40px;
  font-weight: bold;
  background: linear-gradient(135deg, $color-primary, $color-secondary);
  color: white;
  display: block;
}

.avatar-overlay {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: white;
  font-size: $font-xs;
  opacity: 0;
  transition: opacity $transition-base;
  border: 4px solid transparent;

  .el-icon {
    font-size: 20px;
  }
}

.user-details {
  text-align: center;
}

.user-header {
  margin-bottom: $spacing-sm;
}

.user-name {
  font-size: $font-2xl;
  font-weight: 700;
  margin: 0 0 4px;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-username {
  font-size: $font-sm;
  color: var(--el-text-color-secondary);
  margin: 0 0 $spacing-sm;
}

.user-signature {
  font-size: $font-sm;
  color: var(--el-text-color-secondary);
  margin: 0;
  line-height: 1.6;
}

.user-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-md;
  padding: $spacing-sm 0 $spacing-md;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;

  &.clickable {
    cursor: pointer;
    transition: color $transition-fast;

    &:hover .stat-value {
      color: $color-primary;
    }
  }
}

.stat-value {
  font-size: $font-xl;
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1;
}

.stat-label {
  font-size: $font-xs;
  color: var(--el-text-color-secondary);
  line-height: 1;
}

.stat-divider {
  width: 1px;
  height: 24px;
  background: var(--el-border-color-light);
}

// ==================== 区域 Tab ====================

.zone-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
  border-bottom: 1px solid var(--el-border-color-light);
  margin-bottom: $spacing-lg;
  scroll-margin-top: 64px;
}

.zone-tab {
  display: inline-flex;
  align-items: center;
  gap: $spacing-xs;
  padding: $spacing-sm $spacing-lg;
  font-size: $font-base;
  font-weight: 500;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color $transition-fast, border-color $transition-fast;

  &:hover {
    color: var(--el-text-color-primary);
  }

  &.active {
    color: $color-primary;
    border-bottom-color: $color-primary;
  }

  .el-icon {
    font-size: 16px;
  }
}

.zone-content {
  // min-height: 100vh 确保任意区域页面总高度足够触发滚动（scrollTo 才能到达目标位置）
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.files-area {
  // 填充剩余空间，保证内容区足够高
  flex: 1;
  min-height: 520px;
  position: relative;
}

// ==================== 文件区 ====================

// 两栏布局
.files-layout {
  display: flex;
  gap: $spacing-md;
  align-items: flex-start;
  flex: 1;
  min-height: 0;
}

// 左侧分组侧边栏
.groups-sidebar {
  width: 160px;
  flex-shrink: 0;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: $radius-lg;
  padding: $spacing-xs;
  position: sticky;
  top: 76px; // 64px header + 12px breathing room
  overflow: hidden;
  max-height: calc(100vh - 88px);
  overflow-y: auto;
}

.group-item {
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  padding: 6px $spacing-sm;
  border-radius: $radius-md;
  cursor: pointer;
  font-size: $font-sm;
  color: var(--el-text-color-secondary);
  transition: background $transition-fast, color $transition-fast;
  user-select: none;

  &:hover {
    background: var(--el-fill-color-light);
    color: var(--el-text-color-primary);
  }

  &.active {
    background: rgba(99, 102, 241, 0.08);
    color: $color-primary;
  }

  .el-icon {
    font-size: 14px;
    flex-shrink: 0;
  }
}

.group-name {
  flex: 1;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  min-width: 0;
}


.group-more-icon {
  font-size: 14px;
  cursor: pointer;
  color: var(--el-text-color-secondary);
  opacity: 0;
  transition: opacity $transition-fast;
  flex-shrink: 0;

  &:hover {
    color: var(--el-text-color-primary);
  }
}

.group-item:hover .group-more-icon,
.group-item.active .group-more-icon {
  opacity: 1;
}

.groups-divider {
  height: 1px;
  background: var(--el-border-color-lighter);
  margin: $spacing-xs $spacing-sm;
}

.rename-input {
  flex: 1;
  min-width: 0;
  border: 1px solid $color-primary;
  border-radius: $radius-sm;
  padding: 2px 6px;
  font-size: $font-xs;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  outline: none;
}

.new-group-area {
  margin-top: $spacing-xs;
  padding: 2px $spacing-xs;
}

.new-group-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100%;
  padding: 6px $spacing-sm;
  border: none;
  background: transparent;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  font-size: $font-xs;
  border-radius: $radius-md;
  transition: background $transition-fast, color $transition-fast;

  &:hover {
    background: var(--el-fill-color-light);
    color: $color-primary;
  }

  .el-icon {
    font-size: 12px;
  }
}

// 右侧内容区
.files-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

// 工具栏
.files-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: $spacing-md;
  margin-bottom: $spacing-lg;
  flex-wrap: wrap;
}

.content-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
  border-bottom: 1px solid var(--el-border-color-light);

  .tab-item {
    display: inline-flex;
    align-items: center;
    gap: $spacing-xs;
    padding: $spacing-sm $spacing-md;
    font-size: $font-sm;
    color: var(--el-text-color-secondary);
    cursor: pointer;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
    transition: color $transition-fast, border-color $transition-fast;
    white-space: nowrap;

    &:hover {
      color: var(--el-text-color-primary);
    }

    &.active {
      color: $color-primary;
      border-bottom-color: $color-primary;
      font-weight: 500;
    }
  }
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  flex-shrink: 0;
}

// 视图切换单按钮
// 统一图标按钮基类（视图切换 / 可见性 / 上传 / 编辑）
.icon-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
  color: var(--el-text-color-secondary);
  cursor: pointer;
  border-radius: $radius-md;
  transition: background $transition-fast, color $transition-fast, border-color $transition-fast;
  flex-shrink: 0;

  &:hover {
    border-color: $color-primary;
    color: $color-primary;
  }

  &.active {
    border-color: $color-primary;
    background: rgba(99, 102, 241, 0.08);
    color: $color-primary;
  }

  // CSS tooltip —— 按钮正下方居中浮出
  &[data-tip]::after {
    content: attr(data-tip);
    position: absolute;
    top: calc(100% + 6px);
    left: 50%;
    translate: -50% 0;
    z-index: 9999;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11.5px;
    font-weight: 450;
    line-height: 1.4;
    white-space: nowrap;
    pointer-events: none;
    opacity: 0;
    transform: translateY(-4px) scale(0.96);
    transform-origin: top center;
    transition: opacity 0.12s ease, transform 0.12s ease;
    transition-delay: 0.06s;
    background: rgba(22, 24, 30, 0.82);
    color: rgba(255, 255, 255, 0.92);
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.22);
    border: 1px solid rgba(255, 255, 255, 0.07);
  }

  &[data-tip]:hover::after {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

// 暗色模式 tooltip 适配
:global(html.dark) .icon-btn[data-tip]::after {
  background: rgba(48, 51, 62, 0.90);
  color: rgba(222, 225, 232, 0.92);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.40);
  border-color: rgba(255, 255, 255, 0.10);
}

// 上传按钮变体（主色 / 危险色）
.upload-btn {
  background: $color-primary;
  border-color: $color-primary;
  color: #fff;

  &:hover {
    background: rgba(99, 102, 241, 0.82);
    border-color: $color-primary;
    color: #fff;
  }

  &.is-full {
    background: var(--el-color-danger);
    border-color: var(--el-color-danger);

    &:hover {
      background: var(--el-color-danger-light-3);
      border-color: var(--el-color-danger-light-3);
    }
  }
}

// 批量操作栏
.toolbar-left {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.batch-count {
  font-size: $font-xs;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
  flex-shrink: 0;
}

.toolbar-sep {
  width: 1px;
  height: 18px;
  background: var(--el-border-color-light);
  flex-shrink: 0;
  margin: 0 2px;
}

.batch-action-btn {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  height: 24px;
  border: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
  color: var(--el-text-color-regular);
  cursor: pointer;
  border-radius: $radius-sm;
  font-size: $font-xs;
  transition: all $transition-fast;
  flex-shrink: 0;

  &:hover {
    border-color: $color-primary;
    color: $color-primary;
  }

  &.danger:hover {
    border-color: var(--el-color-danger);
    color: var(--el-color-danger);
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
    &:hover {
      border-color: var(--el-border-color-light);
      color: var(--el-text-color-regular);
    }
  }
}

// 复选框列
.col-check {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  flex-shrink: 0;
}

// 选中状态高亮
.hub-file-item.is-selected {
  :deep(.file-card) {
    box-shadow: 0 0 0 2px $color-primary;
  }
}

.list-row.is-selected {
  background: rgba(99, 102, 241, 0.06) !important;
  outline: 1px solid rgba(99, 102, 241, 0.3);
}

.folder-card.is-selected {
  box-shadow: 0 0 0 2px $color-primary;
}

// 列表视图含复选框列时的网格列
.list-header.with-check,
.list-row.with-check {
  grid-template-columns: 32px 44px 1fr 40px 70px 100px 100px;
}

// 编辑模式下，网格卡片的复选框
.item-checkbox {
  position: absolute;
  top: 7px;
  left: 7px;
  z-index: 10;
  cursor: pointer;
}

// SVG 圆形复选框
.check-circle {
  display: block;
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
  transition: all 0.15s ease;
  filter: drop-shadow(0 1px 2px rgba(0,0,0,0.18));

  circle {
    stroke: rgba(150, 155, 170, 0.9);
    stroke-width: 1.5;
    fill: rgba(255,255,255,0.85);
  }
  polyline {
    stroke: transparent;
    stroke-width: 2;
  }

  &.checked {
    circle {
      fill: $color-primary;
      stroke: $color-primary;
    }
    polyline {
      stroke: #fff;
    }
  }

  :global(html.dark) & {
    circle {
      fill: rgba(30, 35, 50, 0.85);
    }
  }
}

// ==================== 列表视图 ====================

.file-list {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: $radius-lg;
  overflow: hidden;
  margin-bottom: $spacing-lg;
}

.list-header {
  display: grid;
  grid-template-columns: 44px 1fr 40px 70px 100px 100px;
  gap: $spacing-sm;
  align-items: center;
  padding: $spacing-sm $spacing-md;
  background: var(--el-fill-color-light);
  border-bottom: 1px solid var(--el-border-color-light);
  font-size: $font-xs;
  font-weight: 500;
  color: var(--el-text-color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.list-row {
  display: grid;
  grid-template-columns: 44px 1fr 40px 70px 100px 100px;
  gap: $spacing-sm;
  align-items: center;
  padding: $spacing-sm $spacing-md;
  border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: background $transition-fast;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: var(--el-fill-color-light);
  }
}

.col-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  .list-thumb {
    width: 36px;
    height: 36px;
    border-radius: $radius-sm;
    overflow: hidden;
    background: var(--el-fill-color);
    display: flex;
    align-items: center;
    justify-content: center;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }
}

.col-name {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;

  .row-title {
    font-size: $font-sm;
    font-weight: 500;
    color: var(--el-text-color-primary);
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  .row-desc {
    font-size: $font-xs;
    color: var(--el-text-color-secondary);
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }
}

.col-visibility,
.col-size,
.col-time {
  font-size: $font-xs;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

// 可见性切换按钮（锁图标）
.vis-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  padding: 0;
  border: none;
  border-radius: $radius-sm;
  background: transparent;
  cursor: pointer;
  transition: background $transition-fast, color $transition-fast;
  // 私有（锁）：极浅灰，暗/亮均可辨
  color: var(--el-text-color-disabled);

  &.is-public {
    // 公开（开锁）：绿色显示，清晰标识
    color: #22c55e;
  }

  &:hover:not(:disabled) {
    background: var(--el-fill-color);
    color: var(--el-text-color-regular);
  }

  &:disabled {
    opacity: 0.35;
    cursor: not-allowed;
  }

  .el-icon {
    font-size: 13px;
  }
}

.col-visibility {
  display: flex;
  align-items: center;
  justify-content: center;
}

.col-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}

.hide-mobile {
  @media (max-width: $breakpoint-md) {
    display: none;
  }
}

.file-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: $spacing-sm;
}

// 列表排序容器（VueDraggable 包装）
.list-sortable {
  display: contents;
}

.hub-file-item {
  position: relative;
  border-radius: $radius-lg;
  overflow: hidden;

  &:hover :deep(.file-card) {
    box-shadow: $shadow-lg;
  }

  // 去掉 FileCard 自身的 hover 动画，由 hub-file-item 统一管理
  :deep(.file-card) {
    border-radius: $radius-lg;
    transition: box-shadow $transition-base;

    &:hover {
      transform: none;
    }
  }

  // 隐藏卡片描述，空间紧凑
  :deep(.card-desc) {
    display: none;
  }
}

.card-actions {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 2px;
  padding: 4px 6px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(6px);
  opacity: 0;
  transition: opacity 0.15s;

  html.dark & {
    background: rgba(15, 23, 42, 0.9);
  }
}

.hub-file-item:hover .card-actions {
  opacity: 1;
}


.empty-state {
  padding: $spacing-3xl $spacing-lg;
}

// ==================== 概况区 ====================

.settings-card {
  background: var(--el-bg-color);
  border-radius: $radius-lg;
  padding: $spacing-lg;
  box-shadow: $shadow-sm;
  margin-bottom: $spacing-md;
}

.card-title {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  font-size: $font-base;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: $spacing-md;

  .el-icon {
    font-size: 18px;
    color: $color-primary;
  }
}

.storage-info {
  .storage-bar-wrap {
    height: 8px;
    background: var(--el-fill-color);
    border-radius: $radius-full;
    overflow: hidden;
    margin-bottom: $spacing-sm;
  }

  .storage-bar {
    height: 100%;
    background: linear-gradient(90deg, $color-primary 0%, $color-secondary 100%);
    border-radius: $radius-full;
    transition: width 0.6s ease;
    min-width: 2px;
  }

  .storage-text {
    font-size: $font-sm;
    color: var(--el-text-color-secondary);
    margin: 0;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $spacing-md;
  text-align: center;
}

.stats-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-xs;
  padding: $spacing-md;
  background: var(--el-fill-color-light);
  border-radius: $radius-lg;
}

.stats-icon {
  font-size: 28px;

  &.image-icon { color: #6366f1; }
  &.resource-icon { color: #f59e0b; }
  &.post-icon { color: #10b981; }
}

.stats-num {
  font-size: $font-2xl;
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1;
}

.stats-label {
  font-size: $font-xs;
  color: var(--el-text-color-secondary);
}

.social-stats {
  display: flex;
  align-items: center;
  gap: $spacing-xl;
}

.social-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;

  &.clickable {
    cursor: pointer;

    &:hover .social-num {
      color: $color-primary;
    }
  }
}

.social-num {
  font-size: $font-2xl;
  font-weight: 700;
  color: var(--el-text-color-primary);
  transition: color $transition-fast;
}

.social-label {
  font-size: $font-sm;
  color: var(--el-text-color-secondary);
}

.social-divider {
  width: 1px;
  height: 40px;
  background: var(--el-border-color-light);
}

// ==================== 设置区 ====================

.settings-form {
  max-width: 480px;
}

.field-hint {
  font-size: 12px;
  color: var(--el-color-warning);
  margin-top: 4px;
}

.privacy-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.privacy-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-sm 0;
  border-bottom: 1px solid var(--el-border-color-lighter);

  &:last-child {
    border-bottom: none;
  }
}

.privacy-label {
  display: flex;
  flex-direction: column;
  gap: 2px;

  span:first-child {
    font-size: $font-sm;
    font-weight: 500;
    color: var(--el-text-color-primary);
  }
}

.privacy-hint {
  font-size: $font-xs !important;
  color: var(--el-text-color-secondary) !important;
  font-weight: 400 !important;
}

// ==================== 响应式 ====================

// ==================== 拖拽上传 ====================

.files-main {
  position: relative;   // 让 drop-overlay 相对此容器定位

  &.drag-active {
    outline: 2px dashed $color-primary;
    outline-offset: -4px;
    border-radius: $radius-lg;
  }
}

.drop-overlay {
  position: absolute;
  inset: 0;
  z-index: 50;
  background: rgba(99, 102, 241, 0.08);
  border-radius: $radius-lg;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.drop-overlay-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-sm;
  color: $color-primary;

  svg { opacity: 0.85; }

  p {
    font-size: $font-xl;
    font-weight: 600;
    margin: 0;
    color: $color-primary;
  }

  span {
    font-size: $font-sm;
    color: var(--el-text-color-secondary);
  }
}

// 批量上传面板（右下角浮层）
.batch-upload-panel {
  position: fixed;
  bottom: $spacing-xl;
  right: $spacing-xl;
  z-index: 2000;
  width: 320px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: $radius-lg;
  box-shadow: $shadow-lg;
  overflow: hidden;
}

.batch-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-sm $spacing-md;
  background: var(--el-fill-color-light);
  border-bottom: 1px solid var(--el-border-color-lighter);
  font-size: $font-sm;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.batch-panel-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: none;
  background: transparent;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  border-radius: $radius-sm;
  transition: background $transition-fast;

  &:hover:not(:disabled) { background: var(--el-fill-color); }
  &:disabled { opacity: 0.4; cursor: not-allowed; }
}

.batch-panel-list {
  max-height: 280px;
  overflow-y: auto;
  padding: $spacing-xs $spacing-sm;
}

.batch-task-row {
  display: grid;
  grid-template-columns: 1fr 100px 32px;
  align-items: center;
  gap: $spacing-xs;
  padding: 5px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);

  &:last-child { border-bottom: none; }
}

.batch-task-name {
  font-size: $font-xs;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  color: var(--el-text-color-primary);
}

.batch-task-bar {
  height: 4px;
  background: var(--el-fill-color);
  border-radius: $radius-full;
  overflow: hidden;
}

.batch-task-fill {
  height: 100%;
  border-radius: $radius-full;
  transition: width 0.2s;
  background: $color-primary;

  &.done { background: var(--el-color-success); }
  &.error { background: var(--el-color-danger); }
}

.batch-task-status {
  font-size: 11px;
  text-align: right;
  color: var(--el-text-color-secondary);

  &:has(.done) { color: var(--el-color-success); }
}

// 面板出入动画
.upload-panel-enter-active,
.upload-panel-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.upload-panel-enter-from,
.upload-panel-leave-to {
  opacity: 0;
  transform: translateY(12px);
}

// ==================== 收藏夹 & 快捷入口 ====================

.favorites-item {
  .group-icon-wrap svg {
    color: #f59e0b; // 琥珀色星形图标
  }
}

.sidebar-section {
  margin: $spacing-xs 0 2px;
  padding-top: $spacing-xs;
  border-top: 1px solid var(--el-border-color-lighter);
}

.shortcut-item {
  color: var(--el-text-color-secondary);
}

.shortcut-remove {
  font-size: 14px;
  line-height: 1;
  width: 16px;
  height: 16px;
  display: none;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-placeholder);
  cursor: pointer;
  flex-shrink: 0;
  border-radius: 3px;
  transition: color $transition-fast, background $transition-fast;

  &:hover {
    color: var(--el-color-danger);
    background: var(--el-color-danger-light-9);
  }
}

.shortcut-item:hover .shortcut-remove {
  display: flex;
}

// 侧边栏拖放区域高亮
.new-group-area.sidebar-drop-active {
  background: rgba(99, 102, 241, 0.06);
  border: 1px dashed $color-primary;
  border-radius: $radius-md;
}

.sidebar-drop-hint {
  font-size: 10px;
  color: $color-primary;
  text-align: center;
  padding: 2px 0;
  margin-top: 2px;
}

// ==================== 文件夹卡片操作按钮 ====================

.folder-card-actions {
  display: none;
  position: absolute;
  top: 4px;
  right: 4px;
  gap: 2px;
  align-items: center;
}

.folder-card:hover .folder-card-actions {
  display: flex;
}

.folder-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: none;
  border-radius: $radius-sm;
  background: var(--el-bg-color);
  cursor: pointer;
  color: var(--el-text-color-secondary);
  transition: background $transition-fast, color $transition-fast;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);

  &:hover {
    background: var(--el-fill-color);
    color: var(--el-text-color-primary);
  }

  &.danger:hover {
    background: var(--el-color-danger-light-9);
    color: var(--el-color-danger);
  }
}

// 被拖拽的文件夹半透明
.is-dragging-folder {
  opacity: 0.4;
  cursor: grabbing;
}

// 列表视图排序拖拽手柄
.sort-handle {
  cursor: grab;
  color: var(--el-text-color-placeholder);
  transition: color $transition-fast;

  &:hover {
    color: var(--el-text-color-secondary);
  }

  &:active {
    cursor: grabbing;
  }
}

// ==================== 侧边栏标题 & 计数 ====================

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px $spacing-sm 2px;
  margin-bottom: 2px;
}

.sidebar-title {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--el-text-color-placeholder);
}

.group-counter {
  font-size: 10px;
  color: var(--el-text-color-placeholder);

  &.warn { color: var(--el-color-warning); }
  &.full { color: var(--el-color-danger); }
}

// ==================== 侧边栏图标淡入淡出 ====================

.group-icon-wrap {
  position: relative;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;

  svg {
    position: absolute;
    transition: opacity 0.15s;
  }

  .icon-folder { opacity: 1; }
  .icon-handle { opacity: 0; cursor: grab; &:active { cursor: grabbing; } }
}

.group-item:hover .group-icon-wrap .icon-folder { opacity: 0; }
.group-item:hover .group-icon-wrap .icon-handle { opacity: 1; }

// 拖拽列表包装
.draggable-list {
  display: flex;
  flex-direction: column;
}

// ==================== 面包屑导航 ====================

.breadcrumb-bar {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 5px $spacing-sm;
  margin-top: 3px;
  margin-bottom: $spacing-sm;
  background: var(--el-fill-color-light);
  border-radius: $radius-md;
  overflow: hidden;
  flex-wrap: nowrap;
}

.crumb-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  border: none;
  background: transparent;
  font-size: $font-sm;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  border-radius: $radius-sm;
  transition: background $transition-fast, color $transition-fast;
  white-space: nowrap;

  &.crumb-home {
    padding: 2px 5px;
    color: var(--el-text-color-placeholder);

    &:hover {
      color: $color-primary;
    }
  }

  &:hover:not(.crumb-current) {
    background: var(--el-fill-color);
    color: var(--el-text-color-primary);
  }

  &.crumb-current {
    color: var(--el-text-color-primary);
    font-weight: 500;
    cursor: default;
  }
}

.crumb-sep {
  color: var(--el-text-color-placeholder);
  flex-shrink: 0;
}

.crumb-spacer {
  flex: 1;
  min-width: $spacing-xs;
}

.new-subfolder-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
  color: var(--el-text-color-secondary);
  border-radius: $radius-sm;
  cursor: pointer;
  flex-shrink: 0;
  transition: border-color $transition-fast, color $transition-fast;

  &:hover {
    border-color: $color-primary;
    color: $color-primary;
  }

  // tooltip 复用 icon-btn 同款样式（正下方居中）
  &[data-tip]::after {
    content: attr(data-tip);
    position: absolute;
    top: calc(100% + 6px);
    left: 50%;
    translate: -50% 0;
    z-index: 9999;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11.5px;
    font-weight: 450;
    line-height: 1.4;
    white-space: nowrap;
    pointer-events: none;
    opacity: 0;
    transform: translateY(-4px) scale(0.96);
    transform-origin: top center;
    transition: opacity 0.12s ease, transform 0.12s ease;
    transition-delay: 0.06s;
    background: rgba(22, 24, 30, 0.82);
    color: rgba(255, 255, 255, 0.92);
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.22);
    border: 1px solid rgba(255, 255, 255, 0.07);
  }

  &[data-tip]:hover::after {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

// ==================== 子文件夹区域 ====================

.subfolders-section {
  margin-bottom: $spacing-md;
  position: relative;
  min-height: 20px;
}

.new-subfolder-form {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  padding: 6px $spacing-sm;
  margin-bottom: $spacing-sm;
  background: var(--el-fill-color-light);
  border-radius: $radius-md;

  .subfolder-name-input {
    flex: 1;
    max-width: 200px;
  }

  .subfolder-hint {
    font-size: 11px;
    color: var(--el-text-color-placeholder);
    white-space: nowrap;
  }
}

.subfolders-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: $spacing-sm;
}

.folder-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: $spacing-md $spacing-sm $spacing-sm;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: $radius-lg;
  cursor: pointer;
  transition: border-color $transition-fast, box-shadow $transition-fast, background $transition-fast;
  position: relative;
  text-align: center;
  min-height: 72px;
  user-select: none;

  &:hover {
    border-color: rgba(99, 102, 241, 0.35);
    box-shadow: $shadow-sm;
  }

  &:hover .folder-card-more {
    opacity: 1;
  }
}

.folder-card-icon {
  color: $color-primary;
  opacity: 0.8;
  display: flex;
  align-items: center;
  justify-content: center;
}

.folder-card-info {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 2px;
  align-items: center;
}

.folder-card-name {
  font-size: $font-sm;
  font-weight: 500;
  color: var(--el-text-color-primary);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  width: 100%;
  text-align: center;
}

.folder-card-meta {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  white-space: nowrap;
}

// 拖拽 hover 目标文件夹高亮
.folder-card.drag-over {
  border-color: $color-primary;
  background: rgba(99, 102, 241, 0.06);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.25);
}

.list-row.folder-row.drag-over {
  background: rgba(99, 102, 241, 0.06);
  outline: 1px solid $color-primary;
  outline-offset: -1px;
}

// 被拖拽的网格卡片半透明
.hub-file-item.is-dragging {
  opacity: 0.4;
  cursor: grabbing;
}

// 列表视图文件夹行
.list-row.folder-row {
  cursor: pointer;
  font-weight: 500;
}

.folder-card-more {
  position: absolute;
  top: 5px;
  right: 5px;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: $radius-sm;
  cursor: pointer;
  opacity: 0;
  transition: opacity $transition-fast, background $transition-fast;
  font-size: 13px;
  color: var(--el-text-color-secondary);

  &:hover {
    background: var(--el-fill-color);
    color: var(--el-text-color-primary);
  }
}

// ==================== 统一内容网格（文件夹 + 文件同等尺寸） ====================

.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: $spacing-sm;
}

// 文件夹网格卡片 — 与 FileCard 一致的视觉风格
.folder-grid-card {
  background: var(--el-bg-color);
  border-radius: $radius-lg;
  border: 1px solid var(--el-border-color-light);
  box-shadow: $shadow-sm;
  cursor: pointer;
  overflow: hidden;
  transition: transform $transition-base, box-shadow $transition-base;
  user-select: none;
  position: relative;

  &:hover {
    transform: translateY(-2px);
    box-shadow: $shadow-lg;
  }

  &.drag-over {
    box-shadow: 0 0 0 2px $color-primary;
    background: rgba(99, 102, 241, 0.04);
    transform: none;
  }

  &.is-selected {
    box-shadow: 0 0 0 2px $color-primary;
    background: rgba(99, 102, 241, 0.05);
  }

  &.is-dragging-folder {
    opacity: 0.4;
    cursor: grabbing;
  }

  .card-body {
    padding: $spacing-md;
  }

  .card-title {
    margin: 0 0 $spacing-xs;
    font-size: $font-sm;
    font-weight: 600;
    color: var(--el-text-color-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .card-desc {
    margin: 0;
    font-size: $font-xs;
    color: var(--el-text-color-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

// 文件夹缩略图区域（16:9 比例，与 FileCard .thumbnail-wrap 等高等宽）
.folder-thumb-area {
  position: relative;
  padding-top: 56.25%;
  overflow: hidden;
  background: var(--el-fill-color);

  & > svg {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
  }
}

// 文件夹卡片悬浮操作覆层（编辑/删除）
.folder-actions-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 2px;
  padding: 4px 6px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(6px);
  opacity: 0;
  transition: opacity 0.15s;

  html.dark & {
    background: rgba(15, 23, 42, 0.9);
  }

  .folder-grid-card:hover & {
    opacity: 1;
  }
}

// 覆层中的单个操作按钮
.overlay-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border: none;
  border-radius: $radius-sm;
  background: transparent;
  cursor: pointer;
  color: var(--el-text-color-secondary);
  transition: background $transition-fast, color $transition-fast;

  &:hover {
    background: var(--el-fill-color);
    color: var(--el-text-color-primary);
  }

  &.danger:hover {
    background: var(--el-color-danger-light-9);
    color: var(--el-color-danger);
  }
}

// 添加快捷入口按钮（侧边栏，比新建文件夹更暗淡）
.add-shortcut-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100%;
  padding: 6px $spacing-sm;
  border: none;
  background: transparent;
  color: var(--el-text-color-placeholder);
  cursor: pointer;
  font-size: $font-xs;
  border-radius: $radius-md;
  transition: background $transition-fast, color $transition-fast;
  margin-top: 2px;

  &:hover {
    background: var(--el-fill-color-light);
    color: $color-primary;
  }

  .el-icon {
    font-size: 12px;
  }
}

// 收藏夹内容区
.collections-area {
  padding: $spacing-md;
  min-height: 200px;
}

.collections-header {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  margin-bottom: $spacing-md;
  padding-bottom: $spacing-sm;
  border-bottom: 1px solid var(--el-border-color-light);
}

.collections-title {
  font-size: $font-base;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.collections-count {
  font-size: $font-xs;
  color: var(--el-text-color-secondary);
}

.load-more-wrap {
  display: flex;
  justify-content: center;
  padding-top: $spacing-md;
}

// ==================== 响应式 ====================

@media (max-width: $breakpoint-md) {
  .space-container {
    padding: $spacing-sm;
  }

  .user-info-section {
    padding: 0 $spacing-md $spacing-md;
  }

  .user-stats {
    gap: $spacing-md;
  }

  .stat-value {
    font-size: $font-lg;
  }

  // 移动端：侧边栏改为顶部横向滚动
  .files-layout {
    flex-direction: column;
  }

  .groups-sidebar {
    width: 100%;
    display: flex;
    flex-direction: row;
    overflow-x: auto;
    position: static;
    padding: $spacing-xs;
    gap: $spacing-xs;
    border-radius: $radius-md;

    .sidebar-header { display: none; }

    .group-item {
      flex-shrink: 0;
      white-space: nowrap;
    }

    .groups-divider {
      width: 1px;
      height: auto;
      margin: $spacing-xs 0;
    }

    .new-group-area {
      flex-shrink: 0;
      margin-top: 0;
      padding: 0;
    }

    .draggable-list {
      flex-direction: row;
    }
  }

  .file-grid,
  .content-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: $spacing-sm;
  }

  .list-header,
  .list-row {
    grid-template-columns: 44px 1fr 90px 140px;
  }

  .stats-grid {
    gap: $spacing-sm;
  }

  .subfolders-grid {
    grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  }

  .breadcrumb-bar {
    overflow-x: auto;
  }
}
</style>
