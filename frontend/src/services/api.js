import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

// Axios instance avec intercepteurs
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Intercepteur pour ajouter le token JWT
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Intercepteur pour gérer les erreurs
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ==================== AUTH ====================
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
  updateProfile: (data) => api.put('/auth/me', data),
  changePassword: (data) => api.post('/auth/change-password', data),
  forgotPassword: (data) => api.post('/auth/forgot-password', data),
  resetPassword: (data) => api.post('/auth/reset-password', data),
  validateInvitation: (token) => api.get(`/auth/validate-invitation/${token}`),
  completeRegistration: (data) => api.post('/auth/complete-registration', data),
  changePasswordFirstLogin: (data) => api.post('/auth/change-password-first-login', data)
};

// ==================== WORK ORDERS ====================
export const workOrdersAPI = {
  getAll: (params) => api.get('/work-orders', { params }),
  getById: (id) => api.get(`/work-orders/${id}`),
  create: (data) => api.post('/work-orders', data),
  update: (id, data) => api.put(`/work-orders/${id}`, data),
  delete: (id) => api.delete(`/work-orders/${id}`),
  
  // Attachments
  uploadAttachment: (workOrderId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/work-orders/${workOrderId}/attachments`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  getAttachments: (workOrderId) => api.get(`/work-orders/${workOrderId}/attachments`),
  downloadAttachment: (workOrderId, attachmentId) => {
    return api.get(`/work-orders/${workOrderId}/attachments/${attachmentId}`, {
      responseType: 'blob'
    });
  },
  deleteAttachment: (workOrderId, attachmentId) => {
    return api.delete(`/work-orders/${workOrderId}/attachments/${attachmentId}`);
  }
};

// ==================== EQUIPMENTS ====================
export const equipmentsAPI = {
  getAll: () => api.get('/equipments'),
  getById: (id) => api.get(`/equipments/${id}`),
  create: (data) => api.post('/equipments', data),
  update: (id, data) => api.put(`/equipments/${id}`, data),
  delete: (id) => api.delete(`/equipments/${id}`),
  getChildren: (id) => api.get(`/equipments/${id}/children`),
  getHierarchy: (id) => api.get(`/equipments/${id}/hierarchy`),
  updateStatus: (id, statut) => api.patch(`/equipments/${id}/status`, null, { params: { statut } })
};

// ==================== LOCATIONS ====================
export const locationsAPI = {
  getAll: () => api.get('/locations'),
  getById: (id) => api.get(`/locations/${id}`),
  create: (data) => api.post('/locations', data),
  update: (id, data) => api.put(`/locations/${id}`, data),
  delete: (id) => api.delete(`/locations/${id}`)
};

// ==================== INVENTORY ====================
export const inventoryAPI = {
  getAll: () => api.get('/inventory'),
  getById: (id) => api.get(`/inventory/${id}`),
  create: (data) => api.post('/inventory', data),
  update: (id, data) => api.put(`/inventory/${id}`, data),
  delete: (id) => api.delete(`/inventory/${id}`)
};

// ==================== PREVENTIVE MAINTENANCE ====================
export const preventiveMaintenanceAPI = {
  getAll: () => api.get('/preventive-maintenance'),
  getById: (id) => api.get(`/preventive-maintenance/${id}`),
  create: (data) => api.post('/preventive-maintenance', data),
  update: (id, data) => api.put(`/preventive-maintenance/${id}`, data),
  delete: (id) => api.delete(`/preventive-maintenance/${id}`)
};

// ==================== USERS ====================
export const usersAPI = {
  getAll: () => api.get('/users'),
  getById: (id) => api.get(`/users/${id}`),
  update: (id, data) => api.put(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`),
  invite: (data) => api.post('/users/invite', data),
  inviteMember: (data) => api.post('/users/invite-member', data),
  createMember: (data) => api.post('/users/create-member', data),
  getPermissions: (id) => api.get(`/users/${id}/permissions`),
  updatePermissions: (id, permissions) => api.put(`/users/${id}/permissions`, permissions),
  getDefaultPermissionsByRole: (role) => api.get(`/users/default-permissions/${role}`)
};

// ==================== VENDORS ====================
export const vendorsAPI = {
  getAll: () => api.get('/vendors'),
  getById: (id) => api.get(`/vendors/${id}`),
  create: (data) => api.post('/vendors', data),
  update: (id, data) => api.put(`/vendors/${id}`, data),
  delete: (id) => api.delete(`/vendors/${id}`)
};

// ==================== PURCHASE HISTORY ====================
export const purchaseHistoryAPI = {
  getAll: () => api.get('/purchase-history'),
  getGrouped: () => api.get('/purchase-history/grouped'),
  getStats: () => api.get('/purchase-history/stats'),
  downloadTemplate: (format = 'csv') => 
    api.get('/purchase-history/template', {
      params: { format },
      responseType: 'blob'
    }),
  deleteAll: () => api.delete('/purchase-history/all'),
  create: (data) => api.post('/purchase-history', data),
  update: (id, data) => api.put(`/purchase-history/${id}`, data),
  delete: (id) => api.delete(`/purchase-history/${id}`)
};

// ==================== REPORTS ====================
export const reportsAPI = {
  getAnalytics: () => api.get('/reports/analytics')
};

// ==================== IMPORT/EXPORT ====================
export const importExportAPI = {
  exportData: (module, format = 'xlsx') => 
    api.get(`/export/${module}`, { 
      params: { format },
      responseType: 'blob' 
    }),
  importData: (module, file, mode = 'add') => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/import/${module}`, formData, {
      params: { mode },
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  }
};

// ==================== AUDIT LOGS (JOURNAL) ====================
export const auditAPI = {
  getAuditLogs: async (params) => {
    const response = await api.get('/audit-logs', { params });
    return response.data;
  },
  getEntityHistory: async (entityType, entityId) => {
    const response = await api.get(`/audit-logs/entity/${entityType}/${entityId}`);
    return response.data;
  },
  exportAuditLogs: async (params) => {
    const response = await api.get('/audit-logs/export', {
      params,
      responseType: 'blob'
    });
    
    // Créer un lien de téléchargement
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `audit_logs_${new Date().getTime()}.${params.format || 'csv'}`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    
    return response;
  }
};

// ==================== WORK ORDER COMMENTS ====================
export const commentsAPI = {
  addWorkOrderComment: async (workOrderId, text) => {
    const response = await api.post(`/work-orders/${workOrderId}/comments`, { text });
    return response.data;
  },
  getWorkOrderComments: async (workOrderId) => {
    const response = await api.get(`/work-orders/${workOrderId}/comments`);
    return response.data;
  }
};

// ==================== METERS (COMPTEURS) ====================
export const metersAPI = {
  getAll: () => api.get('/meters'),
  getById: (id) => api.get(`/meters/${id}`),
  create: (data) => api.post('/meters', data),
  update: (id, data) => api.put(`/meters/${id}`, data),
  delete: (id) => api.delete(`/meters/${id}`),
  
  // Readings (Relevés)
  getReadings: (meterId, params) => api.get(`/meters/${meterId}/readings`, { params }),
  createReading: (meterId, data) => api.post(`/meters/${meterId}/readings`, data),
  deleteReading: (readingId) => api.delete(`/readings/${readingId}`),
  getStatistics: (meterId, period = 'month') => api.get(`/meters/${meterId}/statistics`, { params: { period } })
};

// ==================== INTERVENTION REQUESTS (DEMANDES D'INTERVENTION) ====================
export const interventionRequestsAPI = {
  getAll: () => api.get('/intervention-requests'),
  getById: (id) => api.get(`/intervention-requests/${id}`),
  create: (data) => api.post('/intervention-requests', data),
  update: (id, data) => api.put(`/intervention-requests/${id}`, data),
  delete: (id) => api.delete(`/intervention-requests/${id}`),
  convertToWorkOrder: (id, assigneeId, dateLimite) => api.post(`/intervention-requests/${id}/convert-to-work-order`, null, { 
    params: { 
      assignee_id: assigneeId,
      date_limite: dateLimite
    } 
  })
};

// ==================== IMPROVEMENT REQUESTS (DEMANDES D'AMÉLIORATION) ====================
export const improvementRequestsAPI = {
  getAll: () => api.get('/improvement-requests'),
  getById: (id) => api.get(`/improvement-requests/${id}`),
  create: (data) => api.post('/improvement-requests', data),
  update: (id, data) => api.put(`/improvement-requests/${id}`, data),
  delete: (id) => api.delete(`/improvement-requests/${id}`),
  convertToImprovement: (id, assigneeId, dateLimite) => api.post(`/improvement-requests/${id}/convert-to-improvement`, null, { 
    params: { 
      assignee_id: assigneeId,
      date_limite: dateLimite
    } 
  }),
  
  // Attachments
  uploadAttachment: (id, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/improvement-requests/${id}/attachments`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  downloadAttachment: (id, filename) => api.get(`/improvement-requests/${id}/attachments/${filename}`, {
    responseType: 'blob'
  }),
  
  // Comments
  addComment: (id, text) => api.post(`/improvement-requests/${id}/comments`, { text }),
  getComments: (id) => api.get(`/improvement-requests/${id}/comments`)
};

// ==================== IMPROVEMENTS (AMÉLIORATIONS) ====================
export const improvementsAPI = {
  getAll: (params) => api.get('/improvements', { params }),
  getById: (id) => api.get(`/improvements/${id}`),
  create: (data) => api.post('/improvements', data),
  update: (id, data) => api.put(`/improvements/${id}`, data),
  delete: (id) => api.delete(`/improvements/${id}`),
  
  // Attachments
  uploadAttachment: (id, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/improvements/${id}/attachments`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  downloadAttachment: (id, filename) => api.get(`/improvements/${id}/attachments/${filename}`, {
    responseType: 'blob'
  }),
  
  // Comments
  addComment: (id, text) => api.post(`/improvements/${id}/comments`, { text }),
  getComments: (id) => api.get(`/improvements/${id}/comments`)
};

export default api;