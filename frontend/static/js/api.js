// API 工具类
class API {
    constructor() {
        this.baseURL = '';
        this.token = localStorage.getItem('access_token');
    }

    async request(url, options = {}) {
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (this.token) {
            config.headers['Authorization'] = `Bearer ${this.token}`;
        }

        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(this.baseURL + url, config);
            
            // 检查响应状态
            if (response.status === 401) {
                // Token过期或无效，清除本地存储并跳转登录
                this.logout();
                if (window.location.pathname !== '/login') {
                    window.location.href = '/login';
                }
                throw new Error('登录已过期，请重新登录');
            }
            
            if (response.status === 403) {
                throw new Error('权限不足');
            }
            
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `请求失败 (${response.status})`);
            }

            return data;
        } catch (error) {
            // 网络错误或其他异常
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('网络连接失败，请检查网络状态');
            }
            throw error;
        }
    }

    async get(url, params = {}) {
        const searchParams = new URLSearchParams(params);
        const queryString = searchParams.toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        
        return this.request(fullUrl, {
            method: 'GET'
        });
    }

    async post(url, data = {}) {
        return this.request(url, {
            method: 'POST',
            body: data
        });
    }

    async put(url, data = {}) {
        return this.request(url, {
            method: 'PUT',
            body: data
        });
    }

    async delete(url) {
        return this.request(url, {
            method: 'DELETE'
        });
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('access_token', token);
    }

    logout() {
        this.token = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
    }

    // 验证token是否有效
    async verifyToken() {
        if (!this.token) {
            return false;
        }
        
        try {
            const response = await this.get('/api/auth/verify-token');
            return response.valid;
        } catch (error) {
            // Token无效或过期
            this.logout();
            return false;
        }
    }

    // 更新token
    updateToken() {
        this.token = localStorage.getItem('access_token');
    }

    // 认证相关 API
    async login(username, password) {
        const response = await this.post('/api/auth/login', { username, password });
        if (response.access_token) {
            this.setToken(response.access_token);
            localStorage.setItem('user', JSON.stringify(response.user));
        }
        return response;
    }

    async register(userData) {
        return this.post('/api/auth/register', userData);
    }

    async getProfile() {
        return this.get('/api/auth/profile');
    }

    async changePassword(oldPassword, newPassword) {
        return this.post('/api/auth/change-password', {
            old_password: oldPassword,
            new_password: newPassword
        });
    }

    async verifyToken() {
        return this.get('/api/auth/verify-token');
    }

    // 管理员 API
    async getUsers(page = 1, perPage = 20, search = '') {
        return this.get('/api/admin/users', { page, per_page: perPage, search });
    }

    async createUser(userData) {
        return this.post('/api/admin/users', userData);
    }

    async deleteUser(userId) {
        return this.delete(`/api/admin/users/${userId}`);
    }

    async resetUserPassword(userId, newPassword) {
        return this.put(`/api/admin/users/${userId}/password`, { new_password: newPassword });
    }

    async importUsers(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const config = {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`
                // 不设置 Content-Type，让浏览器自动设置 multipart/form-data
            },
            body: formData
        };

        try {
            const response = await fetch(this.baseURL + '/api/admin/users/import', config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '请求失败');
            }

            return data;
        } catch (error) {
            if (error.message.includes('401') || error.message.includes('token')) {
                this.logout();
                window.location.href = '/login';
            }
            throw error;
        }
    }

    async getBuildings() {
        return this.get('/api/admin/buildings');
    }

    async createBuilding(buildingData) {
        return this.post('/api/admin/buildings', buildingData);
    }

    async deleteBuilding(buildingId) {
        return this.delete(`/api/admin/buildings/${buildingId}`);
    }

    async getRooms(buildingId = null, roomType = null) {
        const params = {};
        if (buildingId) params.building_id = buildingId;
        if (roomType) params.room_type = roomType;
        return this.get('/api/admin/rooms', params);
    }

    async createRoom(roomData) {
        return this.post('/api/admin/rooms', roomData);
    }

    async updateRoom(roomId, roomData) {
        return this.put(`/api/admin/rooms/${roomId}`, roomData);
    }

    async deleteRoom(roomId) {
        return this.delete(`/api/admin/rooms/${roomId}`);
    }

    async importRooms(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const config = {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`
            },
            body: formData
        };

        try {
            const response = await fetch(this.baseURL + '/api/admin/rooms/import', config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '请求失败');
            }

            return data;
        } catch (error) {
            if (error.message.includes('401') || error.message.includes('token')) {
                this.logout();
                window.location.href = '/login';
            }
            throw error;
        }
    }

    async getAllocations(page = 1, perPage = 20) {
        return this.get('/api/admin/allocations', { page, per_page: perPage });
    }

    async createAllocation(allocationData) {
        return this.post('/api/admin/allocations', allocationData);
    }

    async getUnallocatedUsers(page = 1, perPage = 20, search = '') {
        return this.get('/api/admin/unallocated-users', { page, per_page: perPage, search });
    }

    // 寝室类型分配 API
    async getRoomTypeAllocations(page = 1, perPage = 20, search = '') {
        return this.get('/api/admin/room-type-allocations', { page, per_page: perPage, search });
    }

    async createRoomTypeAllocation(allocationData) {
        return this.post('/api/admin/room-type-allocations', allocationData);
    }

    async updateRoomTypeAllocation(allocationId, data) {
        return this.put(`/api/admin/room-type-allocations/${allocationId}`, data);
    }

    async deleteRoomTypeAllocation(allocationId) {
        return this.delete(`/api/admin/room-type-allocations/${allocationId}`);
    }

    async getUnallocatedRoomTypeUsers(page = 1, perPage = 20, search = '') {
        return this.get('/api/admin/unallocated-room-type-users', { page, per_page: perPage, search });
    }

    async updateAllocation(allocationId, data) {
        return this.put(`/api/admin/allocations/${allocationId}`, data);
    }

    async deleteAllocation(allocationId) {
        return this.delete(`/api/admin/allocations/${allocationId}`);
    }

    async getAllocationHistory(page = 1, perPage = 20) {
        return this.get('/api/admin/allocation-history', { page, per_page: perPage });
    }

    // 抽签管理 API
    async quickLotteryDraw(lotteryData) {
        return this.post('/api/admin/lottery/quick-draw', lotteryData);
    }

    async publishLotteryResults(lotteryId) {
        return this.post(`/api/admin/lottery/${lotteryId}/publish`);
    }

    async deleteLotteryResults(lotteryId) {
        return this.delete(`/api/admin/lottery/${lotteryId}`);
    }

    async getAllLotteryResults(page = 1, perPage = 20, lotteryId = null) {
        const params = { page, per_page: perPage };
        if (lotteryId) params.lottery_id = lotteryId;
        return this.get('/api/admin/lottery/results', params);
    }

    // 抽签 API
    async getLotterySettings() {
        return this.get('/api/lottery/settings');
    }

    async createLotterySetting(settingData) {
        return this.post('/api/lottery/settings', settingData);
    }

    async publishLottery(settingId, roomCounts = {}) {
        return this.post(`/api/lottery/settings/${settingId}/publish`, roomCounts);
    }

    async getLotteryResults(lotteryId = null) {
        const params = lotteryId ? { lottery_id: lotteryId } : {};
        return this.get('/api/lottery/results', params);
    }

    async updateLotteryResult(resultId, data) {
        return this.put(`/api/admin/lottery/results/${resultId}`, data);
    }

    async getAvailableRooms(roomType = null, buildingId = null) {
        const params = {};
        if (roomType) params.room_type = roomType;
        if (buildingId) params.building_id = buildingId;
        return this.get('/api/lottery/rooms/available', params);
    }

    async getBuildingsForSelection() {
        return this.get('/api/lottery/buildings');
    }

    async getMySelection() {
        return this.get('/api/lottery/my-selection');
    }

    // 宿舍选择 API
    async selectRoom(bedId) {
        return this.post('/api/room-selection/select', { bed_id: bedId });
    }

    async cancelSelection() {
        return this.post('/api/room-selection/cancel');
    }

    async confirmSelection() {
        return this.post('/api/room-selection/confirm');
    }

    async changeSelection(newBedId) {
        return this.post('/api/room-selection/change', { new_bed_id: newBedId });
    }

    async getSelectionStatistics() {
        return this.get('/api/room-selection/statistics');
    }

    // 详细统计 API
    async getDetailedStatistics() {
        return this.get('/api/admin/detailed-statistics');
    }

    async exportAllocations() {
        const config = {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${this.token}`
            }
        };

        try {
            const response = await fetch(this.baseURL + '/api/admin/export-allocations', config);
            
            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || '导出失败');
            }

            // 获取文件名
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = '用户分配统计.xlsx';
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1].replace(/['"]/g, '');
                }
            }

            // 创建下载链接
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            return { success: true, message: '文件已开始下载' };
        } catch (error) {
            if (error.message.includes('401') || error.message.includes('token')) {
                this.logout();
                window.location.href = '/login';
            }
            throw error;
        }
    }
}

// 全局 API 实例
const api = new API();

// 工具函数
function showAlert(message, type = 'info') {
    const alertsContainer = document.getElementById('alerts') || document.body;
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    
    alertsContainer.appendChild(alert);
    
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

function showLoading(button) {
    const originalText = button.textContent;
    button.innerHTML = '<span class="loading"></span> 处理中...';
    button.disabled = true;
    
    return () => {
        button.textContent = originalText;
        button.disabled = false;
    };
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

function getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}

function isAdmin() {
    const user = getCurrentUser();
    return user && user.is_admin;
}

function requireAuth() {
    if (!api.token) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

async function requireAdmin() {
    if (!requireAuth()) {
        return false;
    }
    
    // 先检查本地存储的用户信息
    if (isAdmin()) {
        return true;
    }
    
    // 如果本地检查失败，尝试从服务器重新获取用户信息
    try {
        const response = await api.getProfile();
        if (response.user) {
            // 更新本地存储的用户信息
            localStorage.setItem('user', JSON.stringify(response.user));
            
            if (response.user.is_admin) {
                return true;
            }
        }
    } catch (error) {
        console.error('获取用户信息失败:', error);
    }
    
    showAlert('需要管理员权限', 'error');
    setTimeout(() => {
        window.location.href = '/login';
    }, 2000);
    return false;
}