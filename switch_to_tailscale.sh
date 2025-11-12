#!/bin/bash

# Script de configuration pour accès via Tailscale
# Configure l'application pour utiliser l'IP Tailscale
# Auteur: GMAO Iris
# Date: 2025-01-11

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  🔧 Configuration pour accès via Tailscale              ║"
echo "║     IP: 100.105.2.113                                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

# 1. Sauvegarder l'ancien fichier
log_info "Création de la sauvegarde..."
BACKUP_DIR="/app/backups/env_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp /app/frontend/.env "$BACKUP_DIR/.env.backup"
log_success "Sauvegarde créée: $BACKUP_DIR/.env.backup"

# 2. Afficher l'ancienne configuration
echo ""
log_info "Configuration actuelle:"
grep "REACT_APP_BACKEND_URL" /app/frontend/.env

# 3. Créer le nouveau fichier .env
log_info "Application de la nouvelle configuration..."
cat > /app/frontend/.env << 'EOF'
REACT_APP_BACKEND_URL=http://100.105.2.113:8001
WDS_SOCKET_PORT=443
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
EOF

log_success "Fichier .env modifié"

# 4. Afficher la nouvelle configuration
echo ""
log_info "Nouvelle configuration:"
grep "REACT_APP_BACKEND_URL" /app/frontend/.env

# 5. Redémarrer le frontend
echo ""
log_info "Redémarrage du frontend..."
sudo supervisorctl restart frontend

# 6. Attendre le démarrage
log_info "Attente du démarrage (15 secondes)..."
sleep 15

# 7. Vérifier le statut
sudo supervisorctl status frontend

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✅ Configuration appliquée avec succès !               ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
log_success "Vous pouvez maintenant accéder à l'application via:"
echo "  👉 http://100.105.2.113"
echo ""
log_info "Identifiants:"
echo "  • Email: admin@gmao-iris.local"
echo "  • Mot de passe: Admin123!"
echo ""
log_warning "Note: Cette configuration fonctionne UNIQUEMENT via Tailscale"
log_warning "Pour accéder via Internet/domaine public, exécutez: ./switch_to_public.sh"
echo ""
