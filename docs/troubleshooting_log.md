# 问题解决学习日志

## 项目信息
- **项目名称**: Web Dev & Server Deployment Practice
- **日期**: 2024-02-28
- **学习目标**: 全栈开发、数据库操作、服务器部署

---

## 问题记录与解决方案

### 问题1: 数据库初始化失败

**错误信息**:
```
ERROR 1364 (HY000) at line 108: Field 'password_hash' doesn't have a default value
```

**问题分析**:
1. `init.sql` 中插入用户时只提供了 `username` 和 `email` 字段
2. 但 `users` 表的 `password_hash` 字段定义为 `NOT NULL`
3. MySQL要求 NOT NULL字段必须有值

**原始代码** (database/init.sql:108-109):
```sql
INSERT INTO users (username, email) VALUES
('admin', 'admin@example.com');
```

**解决方案**:
1. 计算密码哈希值
2. 在INSERT语句中包含password_hash字段

**修复后代码**:
```sql
-- 使用Python计算哈希值
import hashlib
hashlib.sha256(b"admin123ai_web_dev_salt_2024").hexdigest()
# 结果: d60ee70b3fde10ec3a0d5789d39e6071999ed5e5ed1955c511e5e51fd7cc1861

INSERT INTO users (username, password_hash, email) VALUES
('admin', 'd60ee70b3fde10ec3a0d5789d39e6071999ed5e5ed1955c511e5e51fd7cc1861', 'admin@example.com');
```

**学习要点**:
- 数据库NOT NULL约束必须遵守
- 密码永远不要明文存储，使用哈希+盐
- 初始化SQL脚本需要考虑字段完整性

---

### 问题2: Windows终端emoji乱码

**错误信息**:
```
UnicodeEncodeError: 'gbk' codec can't encode character '\U0001f680' in position 0
```

**问题分析**:
1. Windows CMD默认使用GBK编码
2. GBK编码不支持emoji字符
3. Flask启动代码中使用了emoji：🚀、✓、✗

**原始代码** (backend/app.py:130):
```python
print("🚀 启动 Flask 开发服务器")
print(f"✓ 数据库连接成功: {database}")
print(f"✗ 数据库连接失败: {e}")
```

**解决方案**:
移除emoji字符，改用文本标识

**修复后代码**:
```python
print("启动 Flask 开发服务器")
print(f"[OK] 数据库连接成功: {database}")
print(f"[ERROR] 数据库连接失败: {e}")
```

**学习要点**:
- 开发时注意跨平台编码兼容性
- Windows使用GBK，Linux/Mac使用UTF-8
- 生产环境日志应避免使用emoji
- 使用文本标识 `[OK]` `[ERROR]` 更可靠

---

### 问题3: 缺少flask-cors模块

**错误信息**:
```
ModuleNotFoundError: No module named 'flask_cors'
```

**问题分析**:
1. `backend/app.py` 中引入了 `flask_cors`
2. 但 `requirements.txt` 中没有包含该依赖
3. 前端访问后端API需要CORS支持

**原始代码** (backend/app.py:8):
```python
from flask_cors import CORS
```

**requirements.txt** (缺失):
```txt
Flask==3.0.0
Werkzeug==3.0.1
PyMySQL==1.1.0
# 缺少 Flask-Cors
```

**解决方案**:
1. 在requirements.txt中添加Flask-Cors
2. 安装依赖

**修复后**:
```txt
Flask==3.0.0
Flask-Cors==4.0.0    # 新增
Werkzeug==3.0.1
```

```bash
pip install -r requirements.txt
```

**学习要点**:
- 依赖管理要完整，requirements.txt应包含所有依赖
- CORS (Cross-Origin Resource Sharing) 是前后端分离开发必需
- 使用 `pip freeze > requirements.txt` 可以生成完整依赖列表

---

### 问题4: 主页缺少上传入口

**问题描述**:
用户无法从主页找到上传功能

**问题分析**:
导航栏中没有上传链接

**解决方案**:
在导航栏添加上传链接

**修复代码** (frontend/index.html:22):
```html
<ul class="nav-menu">
    <li><a href="#home" class="nav-link active">首页</a></li>
    <li><a href="#about" class="nav-link">关于我</a></li>
    <li><a href="#posts" class="nav-link">文章</a></li>
    <li><a href="#resources" class="nav-link">学习资料</a></li>
    <li><a href="#media" class="nav-link">游戏媒体</a></li>
    <li><a href="upload.html" class="nav-link">上传</a></li>  <!-- 新增 -->
</ul>
```

**学习要点**:
- 用户界面需要清晰的导航
- 功能入口应该显而易见

---

### 问题5: 上传后文件无法访问

**问题描述**:
上传成功但前端无法显示文件

**问题分析**:
1. 文件路径不规范，包含 `backend\..\` 相对路径
2. 缺少静态文件服务路由

**原始代码** (backend/api/media.py:170-191):
```python
upload_dir = os.path.join(Config.UPLOAD_FOLDER, 'media', media_type + 's')
# upload_dir = "D:\...\backend\..\uploads\media\videos"

file_path = os.path.join(upload_dir, unique_filename)
file.save(file_path)

# 保存到数据库时路径不规范
normalized_path = os.path.normpath(file_path)
# 结果: "D:\...\backend\..\uploads\media\videos\xxx.mp4"
```

**解决方案**:
1. 使用绝对路径和规范化路径
2. 添加静态文件服务路由

**修复后代码** (backend/api/media.py):
```python
# 使用绝对路径
upload_dir = os.path.abspath(upload_dir)
os.makedirs(upload_dir, exist_ok=True)

# 保存文件
file_path = os.path.join(upload_dir, unique_filename)
file.save(file_path)

# 规范化路径后存入数据库
normalized_path = os.path.normpath(file_path)
```

**添加静态文件服务** (backend/app.py):
```python
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """提供上传文件的访问"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    uploads_dir = os.path.join(project_root, 'uploads')
    return send_from_directory(uploads_dir, filename)
```

**学习要点**:
- 相对路径 `..\` 在不同环境下可能出问题
- 使用 `os.path.abspath()` 获取绝对路径
- 使用 `os.path.normpath()` 规范化路径
- Flask需要专门的静态文件服务才能访问uploads目录

---

### 问题6: 点击上传链接页面空白

**问题描述**:
从首页点击"上传"链接后页面无变化

**问题分析**:
JavaScript拦截了所有导航链接，对于非锚点链接（如upload.html）也进行了拦截

**原始代码** (frontend/js/main.js:20-37):
```python
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();  // 所有链接都被拦截！

            const targetId = link.getAttribute('href').substring(1);
            // ...
        });
    });
}
```

**解决方案**:
检查链接类型，只拦截锚点链接

**修复后代码**:
```javascript
link.addEventListener('click', (e) => {
    const href = link.getAttribute('href');

    // 如果不是锚点链接（不以#开头），不拦截
    if (!href.startsWith('#')) {
        return;  // 让默认导航发生
    }

    e.preventDefault();
    // ...处理锚点导航
});
```

**学习要点**:
- 区分锚点导航（`#section`）和页面跳转（`page.html`）
- `preventDefault()` 会阻止默认行为
- 条件判断很重要，需要根据场景处理不同类型的链接

---

### 问题7: API路由需要斜杠

**错误信息**:
```
GET /api/v1/media?type=video → 301重定向到 /api/v1/media/?type=video
```

**问题描述**:
Flask路由规则要求以斜杠结尾，否则会重定向，导致查询参数丢失

**原始代码** (frontend/js/api.js:133):
```javascript
getMedia: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/media?${query}`);  // 缺少斜杠
}
```

**解决方案**:
在URL末尾添加斜杠

**修复后代码**:
```javascript
getMedia: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/media/?${query}`);  // 添加斜杠
}
```

**同样修复**:
- `/posts?${query}` → `/posts/?${query}`
- `/resources?${query}` → `/resources/?${query}`
- `/users?${query}` → `/users/?${query}`

**学习要点**:
- Flask路由 `/path` 和 `/path/` 是不同的
- 没有斜杠的路径会被重定向到有斜杠的版本
- 重定向可能导致查询参数丢失
- 前端API调用应统一使用带斜杠的URL

---

### 问题8: getMedia函数重复定义

**错误信息**:
```
Access to fetch at 'http://localhost:5000/api/v1/media/[object%20Object]/'
```

**问题描述**:
`MediaAPI` 对象中 `getMedia` 被定义了两次，第二次覆盖了第一次

**原始代码** (frontend/js/api.js:129-137):
```javascript
const MediaAPI = {
    // 第一次定义 - 获取列表
    getMedia: (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiRequest(`/media/?${query}`);
    },

    // 第二次定义 - 获取详情（同名覆盖！）
    getMedia: (id) => apiRequest(`/media/${id}/`),  // 错误！
}
```

**问题分析**:
调用 `MediaAPI.getMedia({type: 'video'})` 时，实际调用的是第二次定义的函数，参数 `{type: 'video'}` 被当作 `id` 参数，URL变成了 `/media/[object Object]/`

**解决方案**:
重命名第二个函数

**修复后代码**:
```javascript
const MediaAPI = {
    // 获取媒体列表
    getMedia: (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiRequest(`/media/?${query}`);
    },

    // 获取媒体详情（重命名）
    getMediaDetail: (id) => apiRequest(`/media/${id}/`),  // 修复
}
```

**学习要点**:
- JavaScript对象中不能有重复的键，后者会覆盖前者
- 函数命名要清晰，避免冲突
- `getList` / `getDetail` 是常见的命名模式

---

### 问题9: 文件名乱码

**问题描述**:
中文文件名在数据库中显示为乱码：`测试视频` → `����Ƶ`

**问题分析**:
使用 `secure_filename()` 会过滤掉中文字符

**原始代码** (backend/api/media.py:191):
```python
from werkzeug.utils import secure_filename

# ...
secure_filename(file.filename)  # "测试.mp4" → ".mp4" （中文丢失）
```

**解决方案**:
保留原始文件名，只使用UUID作为实际存储文件名

**修复后代码**:
```python
# 数据库中存储原始文件名
cursor.execute("""
    INSERT INTO media (title, description, file_path, file_name, ...)
    VALUES (%s, %s, %s, %s, ...)
""", (
    title,
    description,
    normalized_path,
    file.filename,  # 保留原始文件名，不使用secure_filename
    ...
))
```

**学习要点**:
- `secure_filename()` 会移除非ASCII字符，导致中文丢失
- 实际存储使用UUID避免文件名冲突
- 数据库中保存原始文件名用于显示
- 下载时使用原始文件名

---

### 问题10: 删除功能缺失

**问题描述**:
用户无法删除已上传的文件

**解决方案**:
1. 后端已有删除API
2. 前端添加删除按钮和函数

**添加删除按钮** (frontend/js/main.js:191):
```javascript
<button class="btn-delete" onclick="deleteMedia(${media.id}, '${escapeHtml(media.title)}')">删除</button>
```

**删除函数**:
```javascript
async function deleteMedia(id, title) {
    if (!confirm(`确定要删除 "${title}" 吗？`)) {
        return;
    }

    try {
        await MediaAPI.deleteMedia(id);
        alert('删除成功！');
        loadMedia(); // 重新加载列表
    } catch (error) {
        alert(`删除失败: ${error.message}`);
    }
}
```

**CSS样式**:
```css
.btn-delete {
    padding: 0.25rem 0.75rem;
    background: #ef4444;
    color: white;
    border: none;
    border-radius: 0.375rem;
    cursor: pointer;
}
```

**学习要点**:
- 删除操作需要二次确认
- 删除成功后刷新列表
- 使用 `escapeHtml()` 防止XSS攻击

---

### 问题11: 上传后 "e is not defined" 错误

**错误信息**:
```
Uncaught ReferenceError: e is not defined
```

**问题描述**:
上传成功后尝试重置表单时出错

**原始代码** (frontend/upload.html:239):
```javascript
async function uploadFile(endpoint, data, resultId) {
    // ...
    if (result.success) {
        resultEl.textContent = `上传成功！${result.message}`;
        resultEl.classList.add('success');
        e.target.reset();  // 错误！'e' 在这个作用域中不存在
    }
}

// 调用处
document.getElementById('videoForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    await uploadFile('media', {...}, 'videoResult');
});
```

**问题分析**:
事件对象 `e` 只存在于事件监听器函数的作用域中，在 `uploadFile` 函数中无法访问

**解决方案**:
1. 将表单ID作为参数传递
2. 在uploadFile函数中使用表单ID重置

**修复后代码**:
```javascript
// 调用处传递表单ID
document.getElementById('videoForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    await uploadFile('media', {...}, 'videoResult', 'videoForm');  // 传递表单ID
});

// uploadFile函数接收表单ID
async function uploadFile(endpoint, data, resultId, formId) {
    // ...
    if (result.success) {
        resultEl.textContent = `上传成功！${result.message}`;
        resultEl.classList.add('success');
        if (formId) {
            document.getElementById(formId).reset();  // 使用表单ID重置
        }
        await loadUploadedFiles();  // 自动刷新列表
    }
}
```

**学习要点**:
- JavaScript作用域问题：事件对象只在事件处理函数中可用
- 将需要的元素ID或引用作为参数传递
- 表单重置：`form.reset()` 或 `document.getElementById(id).reset()`

---

### 问题12: 上传界面拥挤

**问题描述**:
视频、图片、资料上传都挤在同一个页面，页面很长

**解决方案**:
使用标签页切换，每次只显示一种类型

**修复前结构**:
```html
<div class="upload-section">
    <h2>上传视频</h2>
    <!-- 表单 -->
</div>

<div class="upload-section">
    <h2>上传图片</h2>
    <!-- 表单 -->
</div>

<div class="upload-section">
    <h2>上传资料</h2>
    <!-- 表单 -->
</div>
```

**修复后结构** (frontend/upload.html):
```html
<!-- 标签页 -->
<div class="tabs">
    <button class="tab-btn active" data-tab="video">视频</button>
    <button class="tab-btn" data-tab="image">图片</button>
    <button class="tab-btn" data-tab="resource">学习资料</button>
</div>

<!-- 标签内容（默认隐藏） -->
<div class="tab-content active" id="videoTab">
    <!-- 视频上传表单 -->
</div>

<div class="tab-content" id="imageTab">
    <!-- 图片上传表单 -->
</div>

<div class="tab-content" id="resourceTab">
    <!-- 资料上传表单 -->
</div>

<script>
// 标签切换逻辑
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;

        // 更新按钮状态
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // 更新内容显示
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        document.getElementById(tab + 'Tab').classList.add('active');
    });
});
</script>

<style>
.tab-content {
    display: none;
}
.tab-content.active {
    display: block;
}
.tab-btn.active {
    color: #007bff;
    border-bottom-color: #007bff;
}
</style>
```

**学习要点**:
- 使用标签页减少页面高度
- 激活状态通过CSS类控制
- `data-*` 属性存储元素数据

---

### 问题13: 已上传文件列表过长

**问题描述**:
已上传文件直接显示，导致页面很长

**解决方案**:
使用折叠面板，默认隐藏，点击展开

**实现代码** (frontend/upload.html):
```html
<!-- 折叠按钮 -->
<div class="uploaded-toggle" onclick="toggleUploaded('video')">
    <div>
        <span class="toggle-text">已上传的视频</span>
        <span class="toggle-count" id="videoCount">0</span>
    </div>
    <span class="toggle-icon">▼</span>
</div>

<!-- 折叠内容（默认隐藏） -->
<div class="uploaded-content" id="videoContent">
    <div class="uploaded-list" id="uploadedVideos">
        <!-- 文件列表 -->
    </div>
</div>

<script>
function toggleUploaded(type) {
    const toggle = document.querySelector(`#${type}Content`).previousElementSibling;
    const content = document.getElementById(type + 'Content');
    toggle.classList.toggle('expanded');
    content.classList.toggle('expanded');
}
</script>

<style>
.uploaded-content {
    display: none;  /* 默认隐藏 */
}
.uploaded-content.expanded {
    display: block;  /* 展开时显示 */
}
.uploaded-toggle.expanded .toggle-icon {
    transform: rotate(180deg);  /* 箭头旋转 */
}
</style>
```

**学习要点**:
- 折叠面板改善用户体验
- CSS类切换控制显示/隐藏
- 使用CSS transform实现动画效果

---

### 问题14: 500内部服务器错误

**错误信息**:
```
GET /api/v1/system/info 500 INTERNAL SERVER ERROR
{"error": "(0, '')", "success": false}
```

**问题描述**:
数据库连接可能断开，导致查询失败

**问题分析**:
1. 长时间运行后数据库连接可能超时断开
2. 错误 `(0, '')` 是pymysql的连接错误
3. 没有连接重试机制

**解决方案**:
添加连接检查和重试机制

**修复后代码** (backend/api/system.py):
```python
@system_bp.route('/info', methods=['GET'])
def get_system_info():
    try:
        conn = get_db_connection()
        # 确保连接有效
        conn.ping(reconnect=True)  # 新增：检查并重连

        with conn.cursor() as cursor:
            # 获取各表记录数（添加异常处理）
            tables = ['users', 'categories', 'posts', 'resources', 'media']
            stats = {}
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    result = cursor.fetchone()
                    stats[table] = result['count']
                except Exception:
                    stats[table] = 0  # 失败时设为0

            # 获取数据库大小（可能失败）
            try:
                cursor.execute("""
                    SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'size_mb'
                    FROM information_schema.tables
                    WHERE table_schema = 'ai_web_dev'
                """)
                db_size = cursor.fetchone()
                database_size_mb = db_size['size_mb'] if db_size else 0
            except Exception:
                database_size_mb = 0  # 失败时设为0

        return jsonify({
            'success': True,
            'data': {
                'version': '1.0.0',
                'database_stats': stats,
                'database_size_mb': database_size_mb
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

**学习要点**:
- 数据库连接可能超时断开
- 使用 `conn.ping(reconnect=True)` 检查并重连
- 关键操作添加try-catch容错
- 部分失败不应导致整个请求失败

---

### 问题15: upload.html中MediaAPI未定义

**错误信息**:
```
ReferenceError: MediaAPI is not defined
```

**问题描述**:
upload.html中使用了 `MediaAPI.getViewUrl()` 但未引入api.js

**原始代码** (frontend/upload.html:425, 570):
```html
<script src="js/config.js"></script>
<script>
    // ...
    <img src="${MediaAPI.getViewUrl(img.id)}">  <!-- 错误：MediaAPI未定义 -->
</script>
```

**解决方案**:
直接在upload.html中定义getViewUrl函数

**修复后代码**:
```html
<script src="js/config.js"></script>
<script>
    // 定义获取媒体查看URL的函数
    function getMediaViewUrl(id) {
        return `${API_BASE_URL}/media/${id}/view`;
    }

    // 使用时
    <img src="${getMediaViewUrl(img.id)}">
</script>
```

**学习要点**:
- JavaScript需要先引入才能使用
- 可以选择引入完整文件或只定义需要的函数
- 模块化开发需要注意依赖关系

---

### 问题16: 游戏媒体的图片/视频无法点击查看

**问题描述**:
主页游戏媒体页面显示图片/视频，但无法点击查看大图或播放

**解决方案**:
1. 添加预览模态框
2. 为媒体卡片添加点击事件
3. 实现viewMedia和closePreview函数

**实现代码**:

**HTML模态框** (frontend/index.html):
```html
<!-- 预览模态框 -->
<div class="preview-modal" id="previewModal" onclick="closePreview(event)">
    <div class="preview-content">
        <button class="preview-close" onclick="closePreview()">&times;</button>
        <div id="previewContainer"></div>
    </div>
</div>
```

**CSS样式** (frontend/css/style.css):
```css
.preview-modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.9);
    z-index: 1000;
    align-items: center;
    justify-content: center;
}

.preview-modal.active {
    display: flex;
}

.preview-content img {
    max-width: 100%;
    max-height: 90vh;
    border-radius: 8px;
}

.preview-close {
    position: absolute;
    color: white;
    font-size: 36px;
    cursor: pointer;
}
```

**JavaScript逻辑** (frontend/js/main.js):
```javascript
// 修改loadMedia，添加点击事件
if (AppState.mediaType === 'image') {
    container.innerHTML = response.data.map(media => `
        <div class="media-card" onclick="viewMedia(${media.id}, 'image')">
            <img src="${MediaAPI.getViewUrl(media.id)}">
            <div class="media-info">
                <h4>${escapeHtml(media.title)}</h4>
                <button class="btn-delete" onclick="event.stopPropagation(); deleteMedia(...)">
                    删除
                </button>
            </div>
        </div>
    `).join('');
}

// 查看媒体函数
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

// 关闭预览函数
function closePreview(event) {
    if (event && event.target.id !== 'previewModal') return;
    const modal = document.getElementById('previewModal');
    const container = document.getElementById('previewContainer');
    modal.classList.remove('active');
    container.innerHTML = '';
}
```

**事件冒泡处理**:
```javascript
// 删除按钮需要阻止事件冒泡，否则会触发预览
<button onclick="event.stopPropagation(); deleteMedia(...)">删除</button>
```

**学习要点**:
- 模态框（Modal）是常用的UI组件
- 事件冒泡：子元素点击会触发父元素的点击事件
- `stopPropagation()` 阻止事件冒泡
- 点击模态框背景关闭是一个常见交互模式

---

### 问题17: JavaScript中使用Python代码导致 "os is not defined"

**错误信息**:
```
加载失败: os is not defined
```

**问题描述**:
在JavaScript代码中使用了Python的 `os.path.basename()` 函数

**原始代码** (frontend/js/main.js:208-210):
```javascript
const imageUrl = media.thumbnail_path
    ? `${API_BASE_URL}/uploads/media/thumbnails/${os.path.basename(media.thumbnail_path)}`
    : '';
```

**问题分析**:
1. `os.path.basename()` 是Python标准库函数
2. JavaScript中没有 `os` 模块
3. 前端代码不能使用后端语言函数

**解决方案**:
使用JavaScript实现相同功能

**修复后代码**:
```javascript
// JavaScript获取文件名（替代Python的os.path.basename）
const getBasename = (path) => path.split(/[\\/]/).pop();
const imageUrl = media.thumbnail_path
    ? `${API_BASE_URL}/uploads/media/thumbnails/${getBasename(media.thumbnail_path)}`
    : '';
```

**代码解析**:
- `path.split(/[\\/]/)` - 用正则表达式按 `/` 或 `\` 分割路径
- `.pop()` - 取数组最后一个元素（文件名）
- Windows使用 `\`，Unix使用 `/`，所以正则需要匹配两种

**示例**:
| 输入路径 | 输出文件名 |
|---------|-----------|
| `D:\uploads\video.mp4` | `video.mp4` |
| `/home/user/image.jpg` | `image.jpg` |
| `folder\subfolder\file.png` | `file.png` |

**学习要点**:
- 前端和后端使用不同的编程语言，不能混用
- JavaScript字符串操作使用 `split()`, `pop()` 等数组方法
- 正则表达式 `[\\/]` 匹配两种路径分隔符
- 路径处理要考虑跨平台兼容性

---

### 问题18: 视频缩略图404错误

**错误信息**:
```
GET http://localhost:8080/favicon.ico 404 (File not found)
视频封面无法显示
```

**问题描述**:
视频缩略图无法加载，浏览器提示404错误

**问题分析**:
1. Flask的 `/uploads/` 路由位于根路径: `http://localhost:5000/uploads/`
2. 但代码中使用了 `API_BASE_URL` = `http://localhost:5000/api/v1`
3. 结果URL变成: `http://localhost:5000/api/v1/uploads/...` (错误)
4. 前端服务器在8080端口，后端在5000端口，可能混淆

**原始代码** (frontend/js/main.js:211):
```javascript
const imageUrl = media.thumbnail_path
    ? `${API_BASE_URL}/uploads/media/thumbnails/${getBasename(media.thumbnail_path)}`
    : '';  // 结果: http://localhost:5000/api/v1/uploads/... ❌
```

**Flask路由** (backend/app.py:126):
```python
@app.route('/uploads/<path:filename>')  # 注意：不是 /api/v1/uploads/
def serve_upload(filename):
    # ...
```

**解决方案**:
添加专门的 `UPLOAD_BASE_URL` 常量

**修复后代码** (frontend/js/config.js):
```javascript
// API基础URL - 用于API调用
const API_BASE_URL = 'http://localhost:5000/api/v1';

// 上传文件访问URL - 用于图片/视频显示（新增）
const UPLOAD_BASE_URL = 'http://localhost:5000/uploads';
```

**修复后代码** (frontend/js/main.js:211):
```javascript
const imageUrl = media.thumbnail_path
    ? `${UPLOAD_BASE_URL}/media/thumbnails/${getBasename(media.thumbnail_path)}`
    : '';  // 结果: http://localhost:5000/uploads/media/thumbnails/... ✅
```

**URL对比**:
| 类型 | URL示例 |
|------|---------|
| API调用 | `http://localhost:5000/api/v1/media/` |
| 文件访问 | `http://localhost:5000/uploads/media/thumbnails/xxx.jpg` |
| 视频播放 | `http://localhost:5000/api/v1/media/123/view` |

**学习要点**:
- API路由和静态文件路由是分开的
- Flask Blueprint (`/api/v1/`) 和根路由 (`/uploads/`) 不同
- 前端需要区分API调用URL和资源访问URL
- 端口混淆：前端8080，后端5000，资源访问要走后端端口
- 模块化配置：使用独立的常量管理不同类型的URL

---

## 总结与关键知识点

### 1. 数据库操作
| 要点 | 说明 |
|------|------|
| NOT NULL约束 | 必须提供值，否则插入失败 |
| 密码存储 | 永远使用哈希+盐，不要明文存储 |
| 事务管理 | 确保数据一致性 |

### 2. 跨平台兼容
| 要点 | 说明 |
|------|------|
| 字符编码 | Windows GBK，Linux/Mac UTF-8 |
| 避免emoji | 日志使用文本标识 |
| 路径处理 | 使用 `os.path` 模块，避免硬编码分隔符 |

### 3. Web开发
| 要点 | 说明 |
|------|------|
| CORS | 前后端分离必需，使用Flask-CORS |
| URL路由 | Flask中 `/path` 和 `/path/` 不同 |
| 静态文件 | 需要专门路由提供uploads目录访问 |

### 4. JavaScript
| 要点 | 说明 |
|------|------|
| 作用域 | 事件对象只在事件处理函数中可用 |
| 对象键 | 重复定义会覆盖，注意命名冲突 |
| 事件冒泡 | `stopPropagation()` 阻止传播 |

### 5. 用户体验
| 要点 | 说明 |
|------|------|
| 标签页 | 减少页面高度，分类展示内容 |
| 折叠面板 | 隐藏次要信息，按需展开 |
| 模态框 | 图片预览、表单对话框等场景 |
| 二次确认 | 删除等危险操作需要确认 |

### 6. 错误处理
| 要点 | 说明 |
|------|------|
| 连接检查 | `conn.ping(reconnect=True)` |
| 分层try-catch | 关键操作单独处理 |
| 降级策略 | 部分失败不影响整体 |

---

## 调试技巧总结

### 1. 查看错误信息
```bash
# 后端错误
curl -v http://localhost:5000/api/endpoint

# 浏览器Console
F12 → Console → 查看红色错误

# Network标签
F12 → Network → 查看请求/响应
```

### 2. 逐步排查
1. 确认后端API正常（curl测试）
2. 确认前端能访问API
3. 检查数据格式是否匹配
4. 检查JavaScript错误

### 3. 常用命令
```bash
# 检查端口占用
netstat -ano | grep ":5000"

# 检查进程
taskkill /F /PID [pid]

# 强制刷新
Ctrl + Shift + R
```

---

## 文件清单

### 后端
- `backend/app.py` - Flask主入口
- `backend/config.py` - 配置管理
- `backend/api/system.py` - 系统信息API
- `backend/api/media.py` - 媒体API

### 前端
- `frontend/index.html` - 主页
- `frontend/upload.html` - 上传页面
- `frontend/js/main.js` - 主逻辑
- `frontend/js/api.js` - API调用
- `frontend/css/style.css` - 样式

### 数据库
- `database/init.sql` - 初始化脚本

---

**文档创建时间**: 2024-02-28
**最后更新**: 2024-02-28 23:35
**问题总数**: 18个
**状态**: 已完成所有问题修复，视频缩略图功能正常
