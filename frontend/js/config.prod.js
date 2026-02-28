/**
 * 生产环境配置文件
 * 部署时替换 config.js 使用
 */

// 根据域名自动判断环境
const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';

// API基础URL
const API_BASE_URL = isProduction
    ? window.location.origin + '/api/v1'  // 生产环境：使用同域名
    : 'http://localhost:5000/api/v1';     // 开发环境

// 上传文件访问URL
const UPLOAD_BASE_URL = isProduction
    ? window.location.origin + '/uploads' // 生产环境
    : 'http://localhost:5000/uploads';    // 开发环境

// 分页配置
const PAGINATION = {
    posts: 10,
    resources: 12,
    media: 12
};

// 调试输出
console.log('环境配置:', {
    isProduction,
    API_BASE_URL,
    UPLOAD_BASE_URL,
    hostname: window.location.hostname
});
