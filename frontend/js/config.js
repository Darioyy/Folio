/**
 * 配置文件
 * 学习要点：API地址配置、环境切换
 */


// API基础URL - 远程服务器专用（不带端口）
// 使用 window 对象确保全局可访问
window.API_BASE_URL = '/api/v1';
window.UPLOAD_BASE_URL = '/uploads';

// 分页配置
window.PAGINATION = {
    posts: 10,
    resources: 12,
    media: 12
};
