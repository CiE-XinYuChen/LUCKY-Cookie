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

    async deleteUser(userId) {
        return this.delete(`/api/admin/users/${userId}`);
    }

    async resetUserPassword(userId, newPassword) {
        return this.put(`/api/admin/users/${userId}/password`, { new_password: newPassword });
    }

    async importUsers(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        return this.request('/api/admin/users/import', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`
            },
            body: formData
        });
    }

    async getBuildings() {
        return this.get('/api/admin/buildings');
    }

    async createBuilding(buildingData) {
        return this.post('/api/admin/buildings', buildingData);
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

    async getAllocations(page = 1, perPage = 20) {
        return this.get('/api/admin/allocations', { page, per_page: perPage });
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

    // 抽签 API
    async getLotterySettings() {
        return this.get('/api/lottery/settings');
    }

    async createLotterySetting(settingData) {
        return this.post('/api/lottery/settings', settingData);
    }

    async publishLottery(settingId) {
        return this.post(`/api/lottery/settings/${settingId}/publish`);
    }

    async getLotteryResults(lotteryId = null) {
        const params = lotteryId ? { lottery_id: lotteryId } : {};
        return this.get('/api/lottery/results', params);
    }

    async updateLotteryResult(resultId, data) {
        return this.put(`/api/lottery/results/${resultId}`, data);
    }

    async getAvailableRooms(roomType = null, buildingId = null) {
        const params = {};
        if (roomType) params.room_type = roomType;
        if (buildingId) params.building_id = buildingId;
        return this.get('/api/lottery/rooms/available', params);
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

function requireAdmin() {
    if (!requireAuth() || !isAdmin()) {
        showAlert('需要管理员权限', 'error');
        return false;
    }
    return true;
}