/**
 * 主应用逻辑
 * 学习要点：DOM操作、事件处理、异步数据加载
 */

// 应用状态
const AppState = {
    currentTab: 'home',
    mediaType: 'image',
    stats: {}
};

/**
 * 页面导航
 */
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.section');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');

            // 如果是外部链接（如upload.html），不拦截
            if (!href.startsWith('#')) {
                return; // 让默认导航发生
            }

            e.preventDefault();

            // 更新导航状态
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            // 切换页面
            const targetId = href.substring(1);
            sections.forEach(s => s.classList.remove('active'));
            document.getElementById(targetId)?.classList.add('active');

            AppState.currentTab = targetId;

            // 加载对应数据
            loadSectionData(targetId);

            // 移动端：点击菜单项后关闭菜单
            if (window.innerWidth < 768) {
                closeMobileMenu();
            }
        });
    });

    // 初始化汉堡菜单
    initHamburger();
}

/**
 * 汉堡菜单（移动端）
 */
function initHamburger() {
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('navMenu');

    if (!hamburger || !navMenu) return;

    // 切换菜单
    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        navMenu.classList.toggle('active');
    });

    // 点击菜单外部关闭
    document.addEventListener('click', (e) => {
        if (!hamburger.contains(e.target) && !navMenu.contains(e.target)) {
            closeMobileMenu();
        }
    });
}

/**
 * 关闭移动端菜单
 */
function closeMobileMenu() {
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('navMenu');

    if (hamburger) hamburger.classList.remove('active');
    if (navMenu) navMenu.classList.remove('active');
}

/**
 * 根据当前页面加载数据
 */
function loadSectionData(section) {
    switch (section) {
        case 'about':
            loadSystemInfo();
            break;
        case 'posts':
            loadPosts();
            break;
        case 'resources':
            loadResources();
            break;
        case 'media':
            loadMedia();
            break;
    }
}

/**
 * 加载系统信息（关于我页面）
 */
async function loadSystemInfo() {
    try {
        const response = await SystemAPI.getInfo();

        // 更新统计数字
        document.getElementById('post-count').textContent = response.data.database_stats.posts || 0;
        document.getElementById('resource-count').textContent = response.data.database_stats.resources || 0;
        document.getElementById('media-count').textContent = response.data.database_stats.media || 0;

    } catch (error) {
        console.error('加载系统信息失败:', error);
        document.getElementById('post-count').textContent = '0';
        document.getElementById('resource-count').textContent = '0';
        document.getElementById('media-count').textContent = '0';
    }
}

/**
 * 加载文章列表
 */
async function loadPosts() {
    const container = document.getElementById('posts-list');
    container.innerHTML = '<p class="loading">加载中...</p>';

    try {
        const response = await PostAPI.getPosts({
            page: 1,
            limit: window.PAGINATION.posts,
            status: 'published'
        });

        if (response.data.length === 0) {
            container.innerHTML = '<p class="empty">暂无文章</p>';
            return;
        }

        container.innerHTML = response.data.map(post => `
            <article class="post-card" onclick="viewPost(${post.id})">
                <h3>${escapeHtml(post.title)}</h3>
                <div class="post-meta">
                    <span>${post.category_name || '未分类'}</span>
                    <span> · </span>
                    <span>${post.author_name || '匿名'}</span>
                    <span> · </span>
                    <span>${formatDate(post.created_at)}</span>
                    <span> · </span>
                    <span>${post.view_count} 次浏览</span>
                </div>
                <p class="post-summary">${escapeHtml(post.summary || post.content.substring(0, 100))}...</p>
            </article>
        `).join('');

    } catch (error) {
        container.innerHTML = `<p class="error">加载失败: ${error.message}</p>`;
    }
}

/**
 * 加载学习资料列表
 */
async function loadResources() {
    const container = document.getElementById('resources-list');
    container.innerHTML = '<p class="loading">加载中...</p>';

    try {
        const response = await ResourceAPI.getResources({
            page: 1,
            limit: window.PAGINATION.resources
        });

        if (response.data.length === 0) {
            container.innerHTML = '<p class="empty">暂无资料</p>';
            return;
        }

        container.innerHTML = response.data.map(resource => `
            <div class="resource-card">
                <div class="resource-icon">📄</div>
                <h3>${escapeHtml(resource.title)}</h3>
                <p class="resource-meta">${formatFileSize(resource.file_size)}</p>
                <p class="resource-meta">${resource.download_count} 次下载</p>
                <button class="btn" onclick="ResourceAPI.downloadResource(${resource.id})">
                    下载
                </button>
            </div>
        `).join('');

    } catch (error) {
        container.innerHTML = `<p class="error">加载失败: ${error.message}</p>`;
    }
}

/**
 * 加载媒体文件
 */
async function loadMedia() {
    const container = document.getElementById('media-list');
    container.innerHTML = '<p class="loading">加载中...</p>';

    try {
        const response = await MediaAPI.getMedia({
            page: 1,
            limit: window.PAGINATION.media,
            type: AppState.mediaType
        });

        if (response.data.length === 0) {
            container.innerHTML = '<p class="empty">暂无媒体</p>';
            return;
        }

        if (AppState.mediaType === 'image') {
            // 显示图片网格
            container.innerHTML = response.data.map(media => `
                <div class="media-card" data-media-id="${media.id}" data-media-type="image">
                    <img src="${MediaAPI.getViewUrl(media.id)}"
                         alt="${escapeHtml(media.title)}"
                         class="media-image"
                         loading="lazy"
                         onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2216%22 height=%229%22%3E%3Crect fill=%22%23ddd%22 width=%2216%22 height=%229%22/%3E%3C/svg%3E'">
                    <div class="media-info">
                        <h4>${escapeHtml(media.title)}</h4>
                    </div>
                </div>
            `).join('');

            // 添加点击事件监听
            container.querySelectorAll('.media-card').forEach(card => {
                card.addEventListener('click', () => {
                    const id = parseInt(card.dataset.mediaId);
                    const type = card.dataset.mediaType;
                    viewMedia(id, type);
                });
            });
        } else {
            // 显示视频列表（使用封面图）
            container.innerHTML = response.data.map(media => {
                // 如果有封面图就显示封面，否则显示默认图标
                // JavaScript获取文件名（替代Python的os.path.basename）
                const getBasename = (path) => path.split(/[\\/]/).pop();
                const imageUrl = media.thumbnail_path
                    ? `${window.UPLOAD_BASE_URL}/media/thumbnails/${getBasename(media.thumbnail_path)}`
                    : '';

                if (imageUrl) {
                    return `
                        <div class="media-card" data-media-id="${media.id}" data-media-type="video">
                            <div class="media-image-wrapper">
                                <img src="${imageUrl}" alt="${escapeHtml(media.title)}" class="media-image" loading="lazy"
                                     onerror="this.parentElement.innerHTML='<span class=video-icon>&#9658;</span>'">
                                <span class="play-overlay">▶</span>
                            </div>
                            <div class="media-info">
                                <h4>${escapeHtml(media.title)}</h4>
                            </div>
                        </div>
                    `;
                } else {
                    return `
                        <div class="media-card" data-media-id="${media.id}" data-media-type="video">
                            <div class="media-image-wrapper">
                                <span class="video-icon">🎬</span>
                            </div>
                            <div class="media-info">
                                <h4>${escapeHtml(media.title)}</h4>
                            </div>
                        </div>
                    `;
                }
            }).join('');

            // 添加点击事件监听
            container.querySelectorAll('.media-card').forEach(card => {
                card.addEventListener('click', () => {
                    const id = parseInt(card.dataset.mediaId);
                    const type = card.dataset.mediaType;
                    viewMedia(id, type);
                });
            });
        }

    } catch (error) {
        container.innerHTML = `<p class="error">加载失败: ${error.message}</p>`;
    }
}

/**
 * 媒体类型切换
 */
function initMediaTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            AppState.mediaType = btn.dataset.type;
            loadMedia();
        });
    });
}

/**
 * 工具函数：转义HTML，防止XSS攻击
 * 学习要点：安全编码，永远不要直接输出用户输入
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 工具函数：格式化日期
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

/**
 * 工具函数：格式化文件大小
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

/**
 * 查看媒体文件（打开预览模态框）
 */
function viewMedia(id, type) {
    const modal = document.getElementById('previewModal');
    const container = document.getElementById('previewContainer');
    const url = MediaAPI.getViewUrl(id);

    if (type === 'image') {
        container.innerHTML = `<img src="${url}" alt="预览">`;
    } else if (type === 'video') {
        container.innerHTML = `<video src="${url}" controls autoplay></video>`;
    }

    modal.classList.add('active');
}

/**
 * 关闭预览模态框
 */
function closePreview(event) {
    if (event && event.target.id !== 'previewModal') return;
    const modal = document.getElementById('previewModal');
    const container = document.getElementById('previewContainer');
    modal.classList.remove('active');
    container.innerHTML = '';
}

/**
 * 查看文章详情
 */
function viewPost(id) {
    // 简单实现：直接跳转
    // 完整实现应该打开模态框或新页面
    alert(`查看文章 ${id} - 待实现详情页`);
}

/**
 * 应用初始化
 */
function init() {
    console.log('应用初始化...');

    // 初始化导航
    initNavigation();

    // 初始化媒体标签
    initMediaTabs();

    // 加载初始数据（关于我页面）
    loadSystemInfo();

    console.log('应用初始化完成');
}

// DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', init);
