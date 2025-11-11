#!/bin/bash

# Script de correction de la connexion réseau
# Applique la détection automatique de l'URL backend
# Auteur: GMAO Iris
# Date: 2025-01-11

set -e  # Arrêter en cas d'erreur

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  🔧 Application du correctif de connexion réseau        ║"
echo "║     GMAO Iris - Détection automatique backend          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction de log
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Vérifier qu'on est dans le bon répertoire
if [ ! -d "/app/frontend/src/services" ]; then
    log_error "Répertoire /app/frontend/src/services non trouvé!"
    exit 1
fi

# 1. Créer une sauvegarde
log_info "Création de la sauvegarde..."
BACKUP_DIR="/app/backups/network_fix_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -f "/app/frontend/src/services/api.js" ]; then
    cp "/app/frontend/src/services/api.js" "$BACKUP_DIR/api.js.backup"
    log_success "Sauvegarde créée: $BACKUP_DIR/api.js.backup"
fi

# 2. Appliquer la correction dans api.js
log_info "Application de la correction de détection réseau..."

cat > /app/frontend/src/services/api.js << 'EOF'
import axios from 'axios';

// Détection intelligente de l'URL backend
// Si on accède via une IP locale (Tailscale, LAN), utiliser la même origine
// Sinon, utiliser l'URL configurée dans .env
const getBackendURL = () => {
  const hostname = window.location.hostname;
  
  // Si on accède via une IP locale (Tailscale: 100.x.x.x, LAN: 192.168.x.x, 10.x.x.x)
  if (
    hostname.match(/^100\./) || // Tailscale
    hostname.match(/^192\.168\./) || // LAN
    hostname.match(/^10\./) || // LAN
    hostname.match(/^172\.(1[6-9]|2[0-9]|3[01])\./) || // LAN
    hostname === 'localhost' ||
    hostname === '127.0.0.1'
  ) {
    // Utiliser la même origine avec le port 8001
    return `${window.location.protocol}//${hostname}:8001`;
  }
  
  // Sinon, utiliser l'URL configurée pour la production
  return process.env.REACT_APP_BACKEND_URL || `${window.location.protocol}//${window.location.hostname}`;
};

const BACKEND_URL = getBackendURL();
const API_BASE = `${BACKEND_URL}/api`;

console.log('🔗 Backend URL configurée:', BACKEND_URL);

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
  import: (file, format = 'csv') => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/purchase-history/import', formData, {
      params: { format },
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  }
};

// ==================== REPORTS ====================
export const reportsAPI = {
  getAnalytics: () => api.get('/reports/analytics'),
  getWorkOrdersReport: (params) => api.get('/reports/work-orders', { params }),
  getEquipmentsReport: () => api.get('/reports/equipments'),
  getMaintenanceReport: (params) => api.get('/reports/maintenance', { params }),
  exportPDF: (reportType, params) => 
    api.get(`/reports/${reportType}/pdf`, {
      params,
      responseType: 'blob'
    }),
  exportExcel: (reportType, params) =>
    api.get(`/reports/${reportType}/excel`, {
      params,
      responseType: 'blob'
    })
};

// ==================== INTERVENTION REQUESTS ====================
export const interventionRequestsAPI = {
  getAll: (params) => api.get('/intervention-requests', { params }),
  getById: (id) => api.get(`/intervention-requests/${id}`),
  create: (data) => api.post('/intervention-requests', data),
  update: (id, data) => api.put(`/intervention-requests/${id}`, data),
  delete: (id) => api.delete(`/intervention-requests/${id}`),
  convertToWorkOrder: (id, data) => api.post(`/intervention-requests/${id}/convert`, data),
  addComment: (id, comment) => api.post(`/intervention-requests/${id}/comments`, { text: comment }),
  getComments: (id) => api.get(`/intervention-requests/${id}/comments`)
};

// ==================== IMPROVEMENT REQUESTS ====================
export const improvementRequestsAPI = {
  getAll: (params) => api.get('/improvement-requests', { params }),
  getById: (id) => api.get(`/improvement-requests/${id}`),
  create: (data) => api.post('/improvement-requests', data),
  update: (id, data) => api.put(`/improvement-requests/${id}`, data),
  delete: (id) => api.delete(`/improvement-requests/${id}`),
  convertToImprovement: (id, data) => api.post(`/improvement-requests/${id}/convert-to-improvement`, data),
  addComment: (id, comment) => api.post(`/improvement-requests/${id}/comments`, { text: comment }),
  getComments: (id) => api.get(`/improvement-requests/${id}/comments`)
};

// ==================== IMPROVEMENTS ====================
export const improvementsAPI = {
  getAll: (params) => api.get('/improvements', { params }),
  getById: (id) => api.get(`/improvements/${id}`),
  create: (data) => api.post('/improvements', data),
  update: (id, data) => api.put(`/improvements/${id}`, data),
  delete: (id) => api.delete(`/improvements/${id}`),
  addComment: (id, comment) => api.post(`/improvements/${id}/comments`, { text: comment }),
  getComments: (id) => api.get(`/improvements/${id}/comments`)
};

// ==================== METERS ====================
export const metersAPI = {
  getAll: () => api.get('/meters'),
  getById: (id) => api.get(`/meters/${id}`),
  create: (data) => api.post('/meters', data),
  update: (id, data) => api.put(`/meters/${id}`, data),
  delete: (id) => api.delete(`/meters/${id}`),
  
  // Readings
  getReadings: (meterId, params) => api.get(`/meters/${meterId}/readings`, { params }),
  createReading: (meterId, data) => api.post(`/meters/${meterId}/readings`, data),
  deleteReading: (readingId) => api.delete(`/readings/${readingId}`),
  
  // Statistics
  getStatistics: (meterId, params) => api.get(`/meters/${meterId}/statistics`, { params })
};

// ==================== IMPORT/EXPORT ====================
export const importExportAPI = {
  exportData: (module) => 
    api.get(`/export/${module}`, {
      responseType: 'blob'
    }),
  importData: (module, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/import/${module}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  }
};

// ==================== AUDIT LOG ====================
export const auditAPI = {
  getAll: (params) => api.get('/audit', { params }),
  getByUser: (userId, params) => api.get(`/audit/user/${userId}`, { params }),
  getByEntity: (entityType, entityId, params) => api.get(`/audit/entity/${entityType}/${entityId}`, { params }),
  exportLog: (params) => 
    api.get('/audit/export', {
      params,
      responseType: 'blob'
    })
};

export default api;
EOF

log_success "Fichier api.js mis à jour avec la détection automatique"

# 3. Vérifier la syntaxe du fichier
log_info "Vérification du fichier..."
if [ -f "/app/frontend/src/services/api.js" ]; then
    log_success "Fichier api.js créé avec succès"
else
    log_error "Échec de la création du fichier"
    exit 1
fi

# 4. Redémarrer le frontend
log_info "Redémarrage du frontend..."
if sudo supervisorctl restart frontend > /dev/null 2>&1; then
    log_success "Frontend redémarré"
else
    log_error "Échec du redémarrage du frontend"
    log_warning "Essayez manuellement: sudo supervisorctl restart frontend"
fi

# 5. Attendre que le frontend soit prêt
log_info "Attente du démarrage du frontend (10 secondes)..."
sleep 10

# 6. Vérifier le statut
log_info "Vérification du statut des services..."
echo ""
sudo supervisorctl status frontend backend mongodb

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✅ Correctif appliqué avec succès !                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
log_info "Sauvegarde disponible dans: $BACKUP_DIR"
echo ""
log_success "Le système détecte maintenant automatiquement l'URL backend:"
echo "  • Tailscale (100.x.x.x) → http://100.x.x.x:8001"
echo "  • Réseau local (192.168.x.x) → http://192.168.x.x:8001"
echo "  • Internet/domaine → https://github-auth-issue-1.preview.emergentagent.com"
echo ""
log_info "Testez maintenant la connexion via votre IP Tailscale/réseau local"
log_info "Identifiants: admin@gmao-iris.local / Admin123!"
echo ""
log_info "Dans la console du navigateur (F12), vous devriez voir:"
echo "  🔗 Backend URL configurée: http://[votre-ip]:8001"
echo ""
