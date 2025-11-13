#!/bin/bash

# Script de configuration GMAO Iris pour Tailscale
# Version: 1.0

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║       Configuration GMAO Iris - Accès Tailscale        ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; }

if [ "$EUID" -ne 0 ]; then 
    log_error "Ce script doit être exécuté en tant que root"
    exit 1
fi

if [ ! -d "/opt/gmao-iris/frontend" ]; then
    log_error "Le répertoire /opt/gmao-iris/frontend n'existe pas!"
    exit 1
fi

echo "Configuration de GMAO Iris pour Tailscale"
echo ""

while true; do
    read -p "Entrez l'adresse IP Tailscale (ex: 100.105.2.113): " TAILSCALE_IP
    
    if [[ $TAILSCALE_IP =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        echo ""
        log_info "IP Tailscale: $TAILSCALE_IP"
        read -p "Est-ce correct? (o/n): " confirm
        if [[ $confirm == "o" || $confirm == "O" ]]; then
            break
        fi
    else
        log_error "Format d'IP invalide. Exemple: 100.105.2.113"
    fi
done

echo ""
log_info "Démarrage de la configuration..."
echo ""

log_info "[1/7] Vérification de MongoDB..."
if ! systemctl is-active --quiet mongod; then
    log_warning "MongoDB arrêté. Correction..."
    chown -R mongodb:mongodb /var/lib/mongodb 2>/dev/null || true
    chown -R mongodb:mongodb /var/log/mongodb 2>/dev/null || true
    rm -f /var/lib/mongodb/mongod.lock 2>/dev/null || true
    systemctl restart mongod
    sleep 3
    
    if systemctl is-active --quiet mongod; then
        log_success "MongoDB démarré"
    else
        log_error "Impossible de démarrer MongoDB"
        exit 1
    fi
else
    log_success "MongoDB actif"
fi

log_info "[2/7] Sauvegarde..."
BACKUP_DIR="/opt/gmao-iris/backups/config_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
if [ -f "/opt/gmao-iris/frontend/.env" ]; then
    cp /opt/gmao-iris/frontend/.env "$BACKUP_DIR/.env.backup"
    log_success "Sauvegarde: $BACKUP_DIR"
fi

log_info "[3/7] Configuration du frontend..."
cat > /opt/gmao-iris/frontend/.env << EOF
NODE_ENV=production
REACT_APP_BACKEND_URL=http://${TAILSCALE_IP}
EOF
log_success "Fichier .env configuré"

log_info "[4/7] Vérification de Yarn..."
if ! command -v yarn &> /dev/null; then
    log_error "Yarn non installé!"
    exit 1
fi
log_success "Yarn disponible"

log_info "[5/7] Recompilation du frontend (1-2 minutes)..."
cd /opt/gmao-iris/frontend
if yarn build > /tmp/yarn-build.log 2>&1; then
    log_success "Frontend recompilé"
else
    log_error "Erreur compilation. Logs: /tmp/yarn-build.log"
    exit 1
fi

log_info "[6/7] Redémarrage des services..."
systemctl restart nginx 2>/dev/null && log_success "Nginx redémarré"
supervisorctl restart gmao-iris-backend >/dev/null 2>&1 && log_success "Backend redémarré"
sleep 3

log_info "[7/7] Vérifications finales..."
systemctl is-active --quiet mongod && log_success "MongoDB: OK" || log_error "MongoDB: KO"
systemctl is-active --quiet nginx && log_success "Nginx: OK" || log_error "Nginx: KO"
supervisorctl status gmao-iris-backend | grep -q RUNNING && log_success "Backend: OK" || log_warning "Backend: Vérifier"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║              ✅ Configuration terminée !                ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
log_success "URL d'accès: http://${TAILSCALE_IP}"
echo ""
echo "Testez maintenant et videz le cache (Ctrl+F5)"
echo ""
