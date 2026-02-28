/**
 * 配置文件
 * 学习要点：API地址配置、环境切换
 */

// API基础URL - 开发环境使用本地地址
const API_BASE_URL = 'http://localhost:5000/api/v1';

// 上传文件访问URL - 用于图片/视频显示
const UPLOAD_BASE_URL = 'http://localhost:5000/uploads';

// 分页配置
const PAGINATION = {
    posts: 10,
    resources: 12,
    media: 12
};
