#!/bin/bash

# Script de rollback du correctif réseau
# Restaure la version précédente de api.js
# Auteur: GMAO Iris
# Date: 2025-01-11

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  🔙 Rollback du correctif réseau                        ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Trouver la dernière sauvegarde
BACKUP_DIR=$(ls -td /app/backups/network_fix_* 2>/dev/null | head -1)

if [ -z "$BACKUP_DIR" ]; then
    log_error "Aucune sauvegarde trouvée dans /app/backups/"
    exit 1
fi

log_info "Sauvegarde trouvée: $BACKUP_DIR"

# Restaurer le fichier
if [ -f "$BACKUP_DIR/api.js.backup" ]; then
    log_info "Restauration de api.js..."
    cp "$BACKUP_DIR/api.js.backup" /app/frontend/src/services/api.js
    log_success "Fichier restauré"
else
    log_error "Fichier de sauvegarde introuvable: $BACKUP_DIR/api.js.backup"
    exit 1
fi

# Redémarrer le frontend
log_info "Redémarrage du frontend..."
sudo supervisorctl restart frontend
log_success "Frontend redémarré"

echo ""
log_success "Rollback effectué avec succès!"
log_info "Configuration réseau restaurée à l'état précédent"
echo ""
