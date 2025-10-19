#!/usr/bin/env bash

#######################################################################
# GMAO Iris - Script d'installation pour Proxmox VE
# Version: 1.0.0
# Utilisation: bash -c "$(curl -fsSL https://raw.githubusercontent.com/VOTRE_USER/gmao-iris/main/ct/gmao-iris.sh)"
#######################################################################

# Couleurs
YW="\033[33m"
BL="\033[36m"
RD="\033[01;31m"
BGN="\033[4;92m"
GN="\033[1;92m"
DGN="\033[32m"
CL="\033[m"
BFR="\\r\\033[K"
HOLD="-"
CM="${GN}✓${CL}"
CROSS="${RD}✗${CL}"

# Variables de configuration par défaut
APP="GMAO-Iris"
var_cpu="2"
var_ram="2048"
var_disk="20"
var_os="debian"
var_version="12"

# Fonction d'en-tête
header_info() {
    clear
    cat <<"EOF"
   _____  __  __          ____    _____      _     
  / ____||  \/  |   /\   / __ \  |_   _|    (_)    
 | |  __ | \  / |  /  \ | |  | |   | |  _ __ _ ___ 
 | | |_ || |\/| | / /\ \| |  | |   | | | '__| / __|
 | |__| || |  | |/ ____ \ |__| |  _| |_| |  | \__ \
  \_____||_|  |_/_/    \_\____/  |_____|_|  |_|___/
                                                    
EOF
}

# Fonction pour afficher les messages
msg_info() {
    echo -ne "${HOLD} ${YW}$1${CL}"
}

msg_ok() {
    echo -e "${BFR} ${CM} ${GN}$1${CL}"
}

msg_error() {
    echo -e "${BFR} ${CROSS} ${RD}$1${CL}"
}

# Vérifications préliminaires
check_root() {
    if [[ "$(id -u)" -ne 0 ]]; then
        msg_error "Ce script doit être exécuté en tant que root sur le host Proxmox"
        exit 1
    fi
}

check_proxmox() {
    if ! command -v pveversion >/dev/null 2>&1; then
        msg_error "Ce script doit être exécuté sur un host Proxmox VE"
        exit 1
    fi
}

# Fonction de configuration interactive
configure() {
    header_info
    echo -e "${BL}Configuration de l'installation GMAO Iris${CL}"
    echo ""
    
    # CT ID
    while true; do
        read -p "ID du container (100-999, défaut: prochain disponible): " CTID
        CTID=${CTID:-$(pvesh get /cluster/nextid)}
        if [[ "$CTID" =~ ^[0-9]+$ ]] && [ "$CTID" -ge 100 ] && [ "$CTID" -le 999 ]; then
            if pct status $CTID &>/dev/null; then
                msg_error "Le CT ID $CTID existe déjà"
            else
                break
            fi
        else
            msg_error "CT ID invalide"
        fi
    done
    
    # Hostname
    read -p "Nom du container (défaut: gmao-iris): " CT_HOSTNAME
    CT_HOSTNAME=${CT_HOSTNAME:-gmao-iris}
    
    # RAM
    read -p "RAM en Mo (défaut: 2048): " CT_RAM
    CT_RAM=${CT_RAM:-$var_ram}
    
    # Disk
    read -p "Taille du disque en Go (défaut: 20): " CT_DISK
    CT_DISK=${CT_DISK:-$var_disk}
    
    # CPU
    read -p "Nombre de CPUs (défaut: 2): " CT_CPU
    CT_CPU=${CT_CPU:-$var_cpu}
    
    # Storage
    msg_info "Détection des storages disponibles..."
    VALID_STORAGES=$(pvesm status -content rootdir | awk 'NR>1 {print $1}')
    echo -e "${BFR}${CM} Storages disponibles: $VALID_STORAGES"
    read -p "Storage à utiliser (défaut: local-lvm): " CT_STORAGE
    CT_STORAGE=${CT_STORAGE:-local-lvm}
    
    # Réseau
    echo ""
    echo -e "${BL}Configuration réseau${CL}"
    read -p "Bridge réseau (défaut: vmbr0): " CT_BRIDGE
    CT_BRIDGE=${CT_BRIDGE:-vmbr0}
    
    read -p "DHCP ou IP statique? (dhcp/static, défaut: dhcp): " NET_TYPE
    NET_TYPE=${NET_TYPE:-dhcp}
    
    if [[ "$NET_TYPE" == "static" ]]; then
        read -p "Adresse IP (ex: 192.168.1.100/24): " CT_IP
        read -p "Gateway (ex: 192.168.1.1): " CT_GW
        NET_CONFIG="ip=$CT_IP,gw=$CT_GW"
    else
        NET_CONFIG="ip=dhcp"
    fi
    
    # Password
    echo ""
    read -sp "Mot de passe root du container: " CT_PASSWORD
    echo
    
    # Configuration application
    echo ""
    echo -e "${BL}Configuration de l'application${CL}"
    
    # GitHub
    echo "1) Dépôt GitHub public"
    echo "2) Dépôt GitHub privé (avec token)"
    read -p "Type de dépôt [1-2] (défaut: 1): " REPO_TYPE
    REPO_TYPE=${REPO_TYPE:-1}
    
    read -p "URL du dépôt GitHub: " GITHUB_URL
    GITHUB_URL=${GITHUB_URL:-https://github.com/votreuser/gmao-iris.git}
    
    if [[ "$REPO_TYPE" == "2" ]]; then
        read -p "Token GitHub: " GITHUB_TOKEN
        GITHUB_URL=$(echo $GITHUB_URL | sed "s|https://|https://${GITHUB_TOKEN}@|")
    fi
    
    # Admin
    read -p "Email administrateur (défaut: admin@gmao-iris.local): " ADMIN_EMAIL
    ADMIN_EMAIL=${ADMIN_EMAIL:-admin@gmao-iris.local}
    
    read -sp "Mot de passe administrateur: " ADMIN_PASS
    echo
    ADMIN_PASS=${ADMIN_PASS:-Admin123!}
    
    read -p "Prénom administrateur (défaut: System): " ADMIN_FIRSTNAME
    ADMIN_FIRSTNAME=${ADMIN_FIRSTNAME:-System}
    
    read -p "Nom administrateur (défaut: Admin): " ADMIN_LASTNAME
    ADMIN_LASTNAME=${ADMIN_LASTNAME:-Admin}
    
    # Domaine
    read -p "Nom de domaine (optionnel, ex: gmao.example.com): " DOMAIN_NAME
    
    if [[ ! -z "$DOMAIN_NAME" ]]; then
        echo "Options SSL:"
        echo "1) HTTP uniquement"
        echo "2) HTTPS avec Let's Encrypt"
        echo "3) HTTPS avec certificat manuel"
        read -p "Choix [1-3] (défaut: 1): " SSL_OPTION
        SSL_OPTION=${SSL_OPTION:-1}
    else
        SSL_OPTION=1
    fi
    
    # Résumé
    echo ""
    echo -e "${GN}═══════════════════════════════════════════${CL}"
    echo -e "${GN}         RÉSUMÉ DE LA CONFIGURATION        ${CL}"
    echo -e "${GN}═══════════════════════════════════════════${CL}"
    echo ""
    echo "Container:"
    echo "  CT ID:        $CTID"
    echo "  Hostname:     $CT_HOSTNAME"
    echo "  RAM:          $CT_RAM Mo"
    echo "  Disk:         $CT_DISK Go"
    echo "  CPU:          $CT_CPU core(s)"
    echo "  Storage:      $CT_STORAGE"
    echo "  Network:      $CT_BRIDGE ($NET_TYPE)"
    echo ""
    echo "Application:"
    echo "  GitHub:       ${GITHUB_URL//\@*/***}"
    echo "  Admin:        $ADMIN_EMAIL"
    echo "  Domaine:      ${DOMAIN_NAME:-Aucun (IP locale)}"
    echo "  SSL:          $([ $SSL_OPTION -eq 1 ] && echo 'HTTP' || echo 'HTTPS')"
    echo ""
    echo -e "${GN}═══════════════════════════════════════════${CL}"
    echo ""
    
    read -p "Confirmer l'installation ? (y/n): " CONFIRM
    if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
        msg_error "Installation annulée"
        exit 0
    fi
}

# Création du container
create_container() {
    msg_info "Création du container LXC"
    
    # Télécharger le template Debian 12 si nécessaire
    TEMPLATE="debian-12-standard_12.7-1_amd64.tar.zst"
    if ! pveam list $CT_STORAGE | grep -q $TEMPLATE; then
        msg_info "Téléchargement du template Debian 12..."
        pveam download $CT_STORAGE $TEMPLATE >/dev/null 2>&1
    fi
    
    # Créer le container
    pct create $CTID \
        $CT_STORAGE:vztmpl/$TEMPLATE \
        -arch amd64 \
        -cores $CT_CPU \
        -hostname $CT_HOSTNAME \
        -memory $CT_RAM \
        -net0 name=eth0,bridge=$CT_BRIDGE,$NET_CONFIG \
        -onboot 1 \
        -ostype debian \
        -password "$CT_PASSWORD" \
        -rootfs $CT_STORAGE:$CT_DISK \
        -unprivileged 1 \
        -features nesting=1 >/dev/null 2>&1
    
    msg_ok "Container créé (ID: $CTID)"
}

# Démarrage du container
start_container() {
    msg_info "Démarrage du container"
    pct start $CTID
    sleep 5
    msg_ok "Container démarré"
}

# Installation dans le container
install_in_container() {
    msg_info "Installation des dépendances système"
    
    # Mise à jour et installation des paquets de base
    pct exec $CTID -- bash -c "apt update && apt upgrade -y" >/dev/null 2>&1
    pct exec $CTID -- bash -c "apt install -y curl wget git gnupg ca-certificates apt-transport-https software-properties-common supervisor nginx ufw" >/dev/null 2>&1
    
    msg_ok "Dépendances système installées"
    
    # Node.js
    msg_info "Installation de Node.js 20.x"
    pct exec $CTID -- bash -c "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -" >/dev/null 2>&1
    pct exec $CTID -- bash -c "apt install -y nodejs" >/dev/null 2>&1
    pct exec $CTID -- bash -c "npm install -g yarn" >/dev/null 2>&1
    msg_ok "Node.js installé"
    
    # Python
    msg_info "Installation de Python"
    pct exec $CTID -- bash -c "apt install -y python3 python3-pip python3-venv" >/dev/null 2>&1
    msg_ok "Python installé"
    
    # MongoDB
    msg_info "Installation de MongoDB 7.0"
    pct exec $CTID -- bash -c "curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor" >/dev/null 2>&1
    pct exec $CTID -- bash -c "echo 'deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] http://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main' | tee /etc/apt/sources.list.d/mongodb-org-7.0.list" >/dev/null 2>&1
    pct exec $CTID -- bash -c "apt update && apt install -y mongodb-org" >/dev/null 2>&1
    pct exec $CTID -- bash -c "systemctl start mongod && systemctl enable mongod" >/dev/null 2>&1
    msg_ok "MongoDB installé"
    
    # Cloner le dépôt
    msg_info "Clonage du dépôt GitHub"
    pct exec $CTID -- bash -c "mkdir -p /opt/gmao-iris && cd /opt/gmao-iris && git clone $GITHUB_URL ." >/dev/null 2>&1
    msg_ok "Dépôt cloné"
    
    # Configuration .env
    msg_info "Configuration des variables d'environnement"
    
    # Backend .env
    pct exec $CTID -- bash -c "cat > /opt/gmao-iris/backend/.env <<EOF
MONGO_URL=mongodb://localhost:27017/gmao_iris
SECRET_KEY=\$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
PORT=8001
HOST=0.0.0.0
EOF"
    
    # Frontend .env - Obtenir l'IP du container
    CONTAINER_IP=$(pct exec $CTID -- hostname -I | awk '{print $1}')
    BACKEND_URL="http://${CONTAINER_IP}:8001"
    
    if [[ ! -z "$DOMAIN_NAME" ]]; then
        if [[ $SSL_OPTION -eq 1 ]]; then
            BACKEND_URL="http://${DOMAIN_NAME}"
        else
            BACKEND_URL="https://${DOMAIN_NAME}"
        fi
    fi
    
    pct exec $CTID -- bash -c "cat > /opt/gmao-iris/frontend/.env <<EOF
REACT_APP_BACKEND_URL=$BACKEND_URL
NODE_ENV=production
EOF"
    
    msg_ok "Variables d'environnement configurées"
    
    # Installation des dépendances de l'application
    msg_info "Installation des dépendances de l'application (cela peut prendre plusieurs minutes)"
    
    # Backend
    pct exec $CTID -- bash -c "cd /opt/gmao-iris/backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt" >/dev/null 2>&1
    
    # Frontend
    pct exec $CTID -- bash -c "cd /opt/gmao-iris/frontend && yarn install --production=false && yarn build" >/dev/null 2>&1
    
    msg_ok "Dépendances de l'application installées"
    
    # Création de l'utilisateur admin
    msg_info "Création du compte administrateur"
    
    pct exec $CTID -- bash -c "cd /opt/gmao-iris/backend && source venv/bin/activate && python3 <<'EOPY'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime

async def create_admin():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.gmao_iris
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    hashed_password = pwd_context.hash('$ADMIN_PASS')
    
    admin_user = {
        'email': '$ADMIN_EMAIL',
        'password': hashed_password,
        'prenom': '$ADMIN_FIRSTNAME',
        'nom': '$ADMIN_LASTNAME',
        'role': 'ADMIN',
        'telephone': '',
        'dateCreation': datetime.utcnow(),
        'derniereConnexion': None,
        'actif': True,
        'permissions': {
            'dashboard': {'view': True, 'edit': True, 'delete': True},
            'workOrders': {'view': True, 'edit': True, 'delete': True},
            'assets': {'view': True, 'edit': True, 'delete': True},
            'preventiveMaintenance': {'view': True, 'edit': True, 'delete': True},
            'inventory': {'view': True, 'edit': True, 'delete': True},
            'locations': {'view': True, 'edit': True, 'delete': True},
            'vendors': {'view': True, 'edit': True, 'delete': True},
            'reports': {'view': True, 'edit': True, 'delete': True}
        }
    }
    
    await db.users.update_one(
        {'email': '$ADMIN_EMAIL'},
        {'\$set': admin_user},
        upsert=True
    )

asyncio.run(create_admin())
EOPY
" >/dev/null 2>&1
    
    msg_ok "Compte administrateur créé"
    
    # Configuration Supervisor
    msg_info "Configuration de Supervisor"
    
    pct exec $CTID -- bash -c "cat > /etc/supervisor/conf.d/gmao-iris-backend.conf <<EOF
[program:gmao-iris-backend]
directory=/opt/gmao-iris/backend
command=/opt/gmao-iris/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/gmao-iris-backend.err.log
stdout_logfile=/var/log/gmao-iris-backend.out.log
environment=PYTHONUNBUFFERED=1
EOF"
    
    pct exec $CTID -- bash -c "supervisorctl reread && supervisorctl update && supervisorctl start gmao-iris-backend" >/dev/null 2>&1
    
    msg_ok "Supervisor configuré"
    
    # Configuration Nginx
    msg_info "Configuration de Nginx"
    
    pct exec $CTID -- bash -c "rm -f /etc/nginx/sites-enabled/default"
    
    pct exec $CTID -- bash -c "cat > /etc/nginx/sites-available/gmao-iris <<'EOF'
server {
    listen 80;
    server_name ${DOMAIN_NAME:-_};
    
    location / {
        root /opt/gmao-iris/frontend/build;
        try_files \$uri \$uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF"
    
    pct exec $CTID -- bash -c "ln -sf /etc/nginx/sites-available/gmao-iris /etc/nginx/sites-enabled/"
    pct exec $CTID -- bash -c "nginx -t && systemctl reload nginx" >/dev/null 2>&1
    
    msg_ok "Nginx configuré"
    
    # Let's Encrypt si nécessaire
    if [[ $SSL_OPTION -eq 2 ]] && [[ ! -z "$DOMAIN_NAME" ]]; then
        msg_info "Configuration de Let's Encrypt"
        pct exec $CTID -- bash -c "apt install -y certbot python3-certbot-nginx" >/dev/null 2>&1
        pct exec $CTID -- bash -c "certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos -m $ADMIN_EMAIL" >/dev/null 2>&1
        msg_ok "Let's Encrypt configuré"
    fi
    
    # Firewall
    msg_info "Configuration du firewall"
    pct exec $CTID -- bash -c "ufw --force enable && ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp && ufw reload" >/dev/null 2>&1
    msg_ok "Firewall configuré"
}

# Résumé final
show_summary() {
    CONTAINER_IP=$(pct exec $CTID -- hostname -I | awk '{print $1}')
    
    echo ""
    echo -e "${GN}═══════════════════════════════════════════${CL}"
    echo -e "${GN}   INSTALLATION TERMINÉE AVEC SUCCÈS !    ${CL}"
    echo -e "${GN}═══════════════════════════════════════════${CL}"
    echo ""
    echo -e "📍 ${BL}Accès à l'application:${CL}"
    
    if [[ ! -z "$DOMAIN_NAME" ]]; then
        if [[ $SSL_OPTION -eq 1 ]]; then
            echo -e "   🌐 ${BGN}http://${DOMAIN_NAME}${CL}"
        else
            echo -e "   🔒 ${BGN}https://${DOMAIN_NAME}${CL}"
        fi
    fi
    
    echo -e "   🏠 ${BGN}http://${CONTAINER_IP}${CL}"
    echo ""
    echo -e "👤 ${BL}Compte Administrateur:${CL}"
    echo -e "   Email:        ${GN}$ADMIN_EMAIL${CL}"
    echo -e "   Mot de passe: ${GN}$ADMIN_PASS${CL}"
    echo ""
    echo -e "🔧 ${BL}Gestion du container:${CL}"
    echo -e "   Entrer:       ${YW}pct enter $CTID${CL}"
    echo -e "   Arrêter:      ${YW}pct stop $CTID${CL}"
    echo -e "   Démarrer:     ${YW}pct start $CTID${CL}"
    echo -e "   Redémarrer:   ${YW}pct reboot $CTID${CL}"
    echo ""
    echo -e "${GN}═══════════════════════════════════════════${CL}"
}

# Fonction principale
main() {
    header_info
    check_root
    check_proxmox
    
    configure
    
    echo ""
    echo -e "${BL}Début de l'installation...${CL}"
    echo ""
    
    create_container
    start_container
    install_in_container
    
    show_summary
}

# Exécution
main "$@"
