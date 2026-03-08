/**
 * API请求模块
 * 学习要点：fetch API、异步处理、错误处理
 */

/**
 * 通用请求函数
 * @param {string} endpoint - API端点
 * @param {Object} options - 请求选项
 * @returns {Promise} 响应数据
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${window.window.API_BASE_URL}${endpoint}`;

    const defaultOptions = {
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
    };

    const finalOptions = { ...defaultOptions, ...options };

    try {
        const response = await fetch(url, finalOptions);
        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || '请求失败');
        }

        return data;
    } catch (error) {
        console.error(`API请求失败: ${url}`, error);
        throw error;
    }
}

/**
 * 系统相关API
 */
const SystemAPI = {
    // 获取系统信息
    getInfo: () => apiRequest('/system/info'),

    // 获取分类列表
    getCategories: () => apiRequest('/system/categories')
};

/**
 * 文章相关API
 */
const PostAPI = {
    // 获取文章列表
    getPosts: (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiRequest(`/posts/?${query}`);
    },

    // 获取文章详情
    getPost: (id) => apiRequest(`/posts/${id}`),

    // 创建文章
    createPost: (data) => apiRequest('/posts', {
        method: 'POST',
        body: JSON.stringify(data)
    }),

    // 更新文章
    updatePost: (id, data) => apiRequest(`/posts/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data)
    }),

    // 删除文章
    deletePost: (id) => apiRequest(`/posts/${id}`, {
        method: 'DELETE'
    })
};

/**
 * 资源相关API
 */
const ResourceAPI = {
    // 获取资源列表
    getResources: (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiRequest(`/resources/?${query}`);
    },

    // 获取资源详情
    getResource: (id) => apiRequest(`/resources/${id}`),

    // 上传资源
    uploadResource: async (formData) => {
        const url = `${window.API_BASE_URL}/resources/upload`;

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || '上传失败');
            }

            return data;
        } catch (error) {
            console.error('文件上传失败:', error);
            throw error;
        }
    },

    // 下载资源
    downloadResource: (id) => {
        window.open(`${window.API_BASE_URL}/resources/${id}/download`, '_blank');
    },

    // 删除资源
    deleteResource: (id) => apiRequest(`/resources/${id}`, {
        method: 'DELETE'
    })
};

/**
 * 媒体相关API
 */
const MediaAPI = {
    // 获取媒体列表
    getMedia: (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiRequest(`/media/?${query}`);
    },

    // 获取媒体详情
    getMediaDetail: (id) => apiRequest(`/media/${id}/`),

    // 上传媒体
    uploadMedia: async (formData) => {
        const url = `${window.API_BASE_URL}/media/upload`;

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || '上传失败');
            }

            return data;
        } catch (error) {
            console.error('媒体上传失败:', error);
            throw error;
        }
    },

    // 获取媒体查看URL
    getViewUrl: (id) => `${window.API_BASE_URL}/media/${id}/view`,

    // 删除媒体
    deleteMedia: (id) => apiRequest(`/media/${id}`, {
        method: 'DELETE'
    })
};

/**
 * 用户相关API
 */
const UserAPI = {
    // 获取用户列表
    getUsers: (params = {}) => {
        const query = new URLSearchParams(params).toString();
        return apiRequest(`/users/?${query}`);
    },

    // 获取用户详情
    getUser: (id) => apiRequest(`/users/${id}`),

    // 创建用户
    createUser: (data) => apiRequest('/users', {
        method: 'POST',
        body: JSON.stringify(data)
    }),

    // 登录
    login: async (username, password) => {
        const response = await fetch(`${window.API_BASE_URL}/users/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || '登录失败');
        }
        return data;
    },

    // 登出
    logout: async () => {
        const response = await fetch(`${window.API_BASE_URL}/users/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || '登出失败');
        }
        return data;
    },

    // 检查登录状态
    checkAuth: async () => {
        const response = await fetch(`${window.API_BASE_URL}/users/check-auth`, {
            credentials: 'include'
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || '请求失败');
        }
        return data;
    },

    // 获取当前用户
    getMe: async () => {
        const response = await fetch(`${window.API_BASE_URL}/users/me`, {
            credentials: 'include'
        });
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || '请求失败');
        }
        return data;
    }
};
