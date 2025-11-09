#!/usr/bin/env bash

###############################################################################
# GMAO Iris v1.1.2 - Installation Auto-Détection (Proxmox 9.0 / Debian 12)
# 
# CORRECTIFS v1.1.2:
# - Auto-détection du template Debian disponible
# - Auto-détection du storage (local-lvm, local, etc.)
# - Choix du bridge réseau (vmbr0, vmbr1, etc.)
# - Configuration automatique du DNS
# - Gestion des erreurs améliorée
# - Compatible Proxmox 9.0
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

msg() { echo -e "${BLUE}▶${NC} $1"; }
ok() { echo -e "${GREEN}✓${NC} $1"; }
err() { echo -e "${RED}✗${NC} $1"; exit 1; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }

clear
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   GMAO IRIS v1.1.2 - Installation Auto (Proxmox 9.0 Ready)    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Vérifier qu'on est sur Proxmox
if ! command -v pct &> /dev/null; then
    err "Ce script doit être exécuté sur un serveur Proxmox"
fi

msg "Détection de la configuration Proxmox..."
PVE_VERSION=$(pveversion | head -1)
echo "  $PVE_VERSION"
echo ""

# Auto-détection du template Debian 12
msg "Recherche du template Debian 12..."
TEMPLATE=$(ls /var/lib/vz/template/cache/*debian-12*.tar.* 2>/dev/null | head -1 | xargs basename 2>/dev/null)

if [[ -z "$TEMPLATE" ]]; then
    warn "Aucun template Debian 12 trouvé !"
    echo ""
    echo "Téléchargement du template (cela peut prendre quelques minutes)..."
    pveam update >/dev/null 2>&1
    
    # Chercher le template disponible
    TEMPLATE_NAME=$(pveam available --section system | grep "debian-12.*amd64" | awk '{print $2}' | head -1)
    
    if [[ -z "$TEMPLATE_NAME" ]]; then
        err "Impossible de trouver un template Debian 12 disponible"
    fi
    
    pveam download local "$TEMPLATE_NAME" || err "Échec du téléchargement du template"
    TEMPLATE="$TEMPLATE_NAME"
    ok "Template téléchargé: $TEMPLATE"
else
    ok "Template trouvé: $TEMPLATE"
fi
echo ""

# Auto-détection du storage
msg "Détection du storage disponible..."
STORAGE=""

# Priorité: local-lvm > local > premier storage disponible
if pvesm status | grep -q "local-lvm"; then
    STORAGE="local-lvm"
elif pvesm status | grep -q "^local "; then
    STORAGE="local"
else
    STORAGE=$(pvesm status | awk 'NR==2 {print $1}')
fi

if [[ -z "$STORAGE" ]]; then
    err "Aucun storage disponible trouvé"
fi

ok "Storage sélectionné: $STORAGE"
echo ""

# Détection des bridges réseau disponibles
msg "Détection des bridges réseau..."
echo ""
echo "Bridges réseau disponibles:"
BRIDGES=$(ip link show | grep -E '^[0-9]+: vmbr' | awk -F': ' '{print $2}' | sed 's/@.*//')

if [[ -z "$BRIDGES" ]]; then
    err "Aucun bridge réseau détecté"
fi

# Afficher la liste numérotée
i=1
declare -A BRIDGE_MAP
while IFS= read -r bridge; do
    # Obtenir l'état et l'IP si disponible
    STATE=$(ip link show $bridge | grep -o "state [A-Z]*" | awk '{print $2}')
    IP=$(ip addr show $bridge 2>/dev/null | grep "inet " | awk '{print $2}' | head -1)
    
    echo "  $i) $bridge - État: $STATE"
    if [[ -n "$IP" ]]; then
        echo "     IP: $IP"
    fi
    
    BRIDGE_MAP[$i]=$bridge
    ((i++))
done <<< "$BRIDGES"

echo ""
read -p "Choisissez le numéro du bridge à utiliser [1]: " BRIDGE_CHOICE
BRIDGE_CHOICE=${BRIDGE_CHOICE:-1}

SELECTED_BRIDGE=${BRIDGE_MAP[$BRIDGE_CHOICE]}

if [[ -z "$SELECTED_BRIDGE" ]]; then
    err "Choix de bridge invalide"
fi

ok "Bridge sélectionné: $SELECTED_BRIDGE"
echo ""

# GitHub Token
warn "Vous avez besoin d'un Personal Access Token GitHub"
echo "1. Allez sur: https://github.com/settings/tokens"
echo "2. Cliquez: Generate new token (classic)"
echo "3. Cochez: repo (Full control of private repositories)"
echo "4. Copiez le token généré"
echo ""
read -sp "Collez votre GitHub Token: " GITHUB_TOKEN
echo ""
[[ -z "$GITHUB_TOKEN" ]] && err "Token requis"

# Informations GitHub
read -p "Votre username GitHub [Kinder0083]: " GITHUB_USER
GITHUB_USER=${GITHUB_USER:-Kinder0083}

read -p "Nom du dépôt [GMAO]: " REPO_NAME
REPO_NAME=${REPO_NAME:-GMAO}

read -p "Branche [main]: " BRANCH
BRANCH=${BRANCH:-main}

echo ""
msg "Configuration du container..."

# Trouver un ID libre
CTID=100
while pct status $CTID >/dev/null 2>&1; do
    ((CTID++))
done

read -p "ID container [$CTID]: " CUSTOM_CTID
CTID=${CUSTOM_CTID:-$CTID}

# Vérifier que l'ID est libre
if pct status $CTID >/dev/null 2>&1; then
    err "Container ID $CTID existe déjà"
fi

read -p "RAM (Mo) [4096]: " RAM
RAM=${RAM:-4096}

read -p "CPU cores [2]: " CORES
CORES=${CORES:-2}

read -p "Taille disque (Go) [20]: " DISK_SIZE
DISK_SIZE=${DISK_SIZE:-20}

echo ""
msg "Configuration réseau du container..."
echo ""

# Détecter la config du bridge sélectionné
BRIDGE_IP=$(ip addr show $SELECTED_BRIDGE | grep "inet " | awk '{print $2}' | cut -d'/' -f1)
BRIDGE_CIDR=$(ip addr show $SELECTED_BRIDGE | grep "inet " | awk '{print $2}' | cut -d'/' -f2)
BRIDGE_GW=$(ip route | grep "default.*$SELECTED_BRIDGE" | awk '{print $3}')

if [[ -z "$BRIDGE_GW" ]]; then
    BRIDGE_GW=$BRIDGE_IP
fi

echo "Configuration détectée sur $SELECTED_BRIDGE:"
echo "  IP Proxmox: $BRIDGE_IP/$BRIDGE_CIDR"
echo "  Gateway: $BRIDGE_GW"
echo ""

# Proposer IP statique ou DHCP
NETWORK_PREFIX=$(echo $BRIDGE_IP | cut -d'.' -f1-3)
SUGGESTED_IP="${NETWORK_PREFIX}.150"

echo "Choisissez le mode de configuration réseau:"
echo "  1) IP Statique (recommandé si pas de serveur DHCP)"
echo "  2) DHCP (nécessite un serveur DHCP fonctionnel)"
echo ""
read -p "Votre choix [1]: " NET_MODE
NET_MODE=${NET_MODE:-1}

if [[ "$NET_MODE" == "1" ]]; then
    # IP Statique
    read -p "Adresse IP du container [$SUGGESTED_IP]: " CONTAINER_IP
    CONTAINER_IP=${CONTAINER_IP:-$SUGGESTED_IP}
    
    read -p "Masque CIDR [/$BRIDGE_CIDR]: " CONTAINER_CIDR
    CONTAINER_CIDR=${CONTAINER_CIDR:-$BRIDGE_CIDR}
    
    read -p "Gateway [$BRIDGE_GW]: " CONTAINER_GW
    CONTAINER_GW=${CONTAINER_GW:-$BRIDGE_GW}
    
    IP_CONFIG="${CONTAINER_IP}/${CONTAINER_CIDR}"
    NET="ip=${IP_CONFIG},gw=${CONTAINER_GW}"
else
    # DHCP
    warn "Mode DHCP sélectionné - un serveur DHCP doit être disponible sur $SELECTED_BRIDGE"
    IP_CONFIG="dhcp"
    NET="ip=dhcp"
    CONTAINER_IP="dhcp"
fi

echo ""
msg "Configuration administrateur..."

read -p "Email admin: " ADMIN_EMAIL
[[ -z "$ADMIN_EMAIL" ]] && err "Email requis"

read -sp "Mot de passe admin (min 8 car): " ADMIN_PASS
echo ""
[[ ${#ADMIN_PASS} -lt 8 ]] && err "Mot de passe trop court"

read -sp "Mot de passe root container: " ROOT_PASS
echo ""
[[ ${#ROOT_PASS} -lt 8 ]] && err "Mot de passe root trop court"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Résumé:"
echo "  Proxmox: $PVE_VERSION"
echo "  Template: $TEMPLATE"
echo "  Storage: $STORAGE"
echo "  Bridge réseau: $SELECTED_BRIDGE"
echo "  Container: $CTID (${RAM}Mo, ${CORES} cores, ${DISK_SIZE}Go)"
echo "  Réseau: $IP_CONFIG"
echo "  GitHub: ${GITHUB_USER}/${REPO_NAME} (branche: $BRANCH)"
echo "  Admin: $ADMIN_EMAIL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Confirmer l'installation ? (y/n): " CONFIRM
[[ ! $CONFIRM =~ ^[Yy]$ ]] && err "Installation annulée"

# Construction de l'URL Git avec token
GIT_URL="https://${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${REPO_NAME}.git"

echo ""
msg "Création du container..."

# Nettoyer les variables (enlever espaces)
CONTAINER_IP=$(echo "$CONTAINER_IP" | tr -d ' ')
CONTAINER_CIDR=$(echo "$CONTAINER_CIDR" | tr -d ' ')
CONTAINER_GW=$(echo "$CONTAINER_GW" | tr -d ' ')

# Commande de création adaptée avec le bridge choisi
if [[ "$NET_MODE" == "1" ]]; then
    # IP Statique
    PCT_CREATE_CMD="pct create $CTID local:vztmpl/$TEMPLATE \
  --arch amd64 \
  --cores $CORES \
  --hostname gmao-iris \
  --memory $RAM \
  --net0 name=eth0,bridge=$SELECTED_BRIDGE,ip=${CONTAINER_IP}/${CONTAINER_CIDR},gw=${CONTAINER_GW} \
  --onboot 1 \
  --ostype debian \
  --rootfs ${STORAGE}:${DISK_SIZE} \
  --unprivileged 1 \
  --features nesting=1 \
  --password '$ROOT_PASS'"
else
    # DHCP
    PCT_CREATE_CMD="pct create $CTID local:vztmpl/$TEMPLATE \
  --arch amd64 \
  --cores $CORES \
  --hostname gmao-iris \
  --memory $RAM \
  --net0 name=eth0,bridge=$SELECTED_BRIDGE,ip=dhcp \
  --onboot 1 \
  --ostype debian \
  --rootfs ${STORAGE}:${DISK_SIZE} \
  --unprivileged 1 \
  --features nesting=1 \
  --password '$ROOT_PASS'"
fi

# Debug: afficher la commande
echo ""
echo "DEBUG - Commande qui sera exécutée:"
echo "$PCT_CREATE_CMD"
echo ""
read -p "Appuyez sur Entrée pour continuer..."

# Exécuter avec gestion d'erreur détaillée
if ! eval "$PCT_CREATE_CMD" 2>&1 | tee /tmp/pct_create_error.log; then
    echo ""
    echo "Erreur lors de la création. Détails:"
    cat /tmp/pct_create_error.log
    exit 1
fi

sleep 2
pct start $CTID || err "Impossible de démarrer le container"
sleep 5

# CORRECTION: Configurer le DNS immédiatement
msg "Configuration du réseau..."
pct exec $CTID -- bash -c 'cat > /etc/resolv.conf <<EOF
nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 1.1.1.1
EOF'

# Vérifier la connectivité Internet
msg "Vérification de la connectivité Internet..."
if ! pct exec $CTID -- ping -c 3 8.8.8.8 >/dev/null 2>&1; then
    err "Le container n'a pas de connexion Internet. Vérifiez:
    1. La configuration réseau de Proxmox
    2. Le bridge $SELECTED_BRIDGE est correctement configuré
    3. Le firewall Proxmox (pve-firewall status)
    
Pour diagnostic, exécutez:
    pct enter $CTID
    ip addr show
    ip route
    ping 8.8.8.8"
fi

ok "Container $CTID créé et réseau configuré"

msg "Installation du système (5-7 min)..."
pct exec $CTID -- bash -c 'export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq locales
echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
locale-gen >/dev/null 2>&1
export LANG=en_US.UTF-8

apt-get upgrade -y -qq
apt-get install -y -qq curl wget git gnupg ca-certificates build-essential \
  supervisor nginx ufw python3 python3-pip python3-venv

# Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | bash - >/dev/null 2>&1
apt-get install -y -qq nodejs
npm install -g yarn >/dev/null 2>&1

# MongoDB
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
  gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
echo "deb [signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg] http://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" > /etc/apt/sources.list.d/mongodb-org-7.0.list
apt-get update -qq
apt-get install -y -qq mongodb-org
systemctl start mongod
systemctl enable mongod >/dev/null 2>&1

# Postfix
apt-get install -y -qq mailutils
echo "gmao-iris.local" > /etc/mailname
debconf-set-selections <<< "postfix postfix/mailname string gmao-iris.local"
debconf-set-selections <<< "postfix postfix/main_mailer_type string Internet Site"
apt-get install -y -qq postfix
systemctl start postfix
systemctl enable postfix >/dev/null 2>&1
' 2>&1 | grep -iE "(error|fatal)" || true

ok "Système installé"

# Obtenir IP du container
if [[ "$CONTAINER_IP" == "dhcp" ]]; then
    CONTAINER_IP=$(pct exec $CTID -- hostname -I | awk '{print $1}')
    
    if [[ -z "$CONTAINER_IP" || "$CONTAINER_IP" == "127.0.0.1" ]]; then
        warn "Le DHCP n'a pas attribué d'IP. Configuration manuelle nécessaire."
        CONTAINER_IP="AUCUNE_IP"
    else
        ok "IP du container (DHCP): $CONTAINER_IP"
    fi
else
    ok "IP du container (Statique): $CONTAINER_IP"
fi

msg "Clonage de l'application depuis GitHub..."

# Créer le script Python pour les admins (VERSION 1.1 - CORRIGÉE)
cat > /tmp/create_admins_${CTID}.py <<'PYEOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime
import sys

async def main():
    admin_email = sys.argv[1]
    admin_pass = sys.argv[2]
    
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.gmao_iris
    pwd = CryptContext(schemes=['bcrypt'], deprecated='auto', bcrypt__rounds=10)
    
    print("🔐 Création des comptes administrateurs...")
    
    # Admin principal - STRUCTURE CORRIGÉE v1.1
    admin1 = {
        'email': admin_email,
        'hashed_password': pwd.hash(admin_pass),
        'nom': 'Admin',
        'prenom': 'Principal',
        'role': 'ADMIN',
        'telephone': None,
        'service': None,
        'statut': 'actif',
        'dateCreation': datetime.now(),
        'derniereConnexion': None,
        'firstLogin': False,
        'permissions': {
            module: {'view': True, 'edit': True, 'delete': True}
            for module in ['dashboard', 'workOrders', 'assets', 'preventiveMaintenance', 
                          'inventory', 'locations', 'vendors', 'reports', 'purchaseHistory',
                          'people', 'planning', 'improvementRequests', 'improvements',
                          'interventionRequests', 'equipments', 'meters', 'importExport', 'journal']
        }
    }
    
    # Vérifier si l'email existe déjà
    existing = await db.users.find_one({'email': admin_email})
    if existing:
        await db.users.update_one({'email': admin_email}, {'$set': admin1})
        print(f'✅ Admin mis à jour: {admin_email}')
    else:
        await db.users.insert_one(admin1)
        print(f'✅ Admin créé: {admin_email}')
    
    # Admin de secours (TOUJOURS créé)
    admin2 = {
        'email': 'buenogy@gmail.com',
        'hashed_password': pwd.hash('Admin2024!'),
        'nom': 'Support',
        'prenom': 'Admin',
        'role': 'ADMIN',
        'telephone': None,
        'service': None,
        'statut': 'actif',
        'dateCreation': datetime.now(),
        'derniereConnexion': None,
        'firstLogin': False,
        'permissions': {
            module: {'view': True, 'edit': True, 'delete': True}
            for module in ['dashboard', 'workOrders', 'assets', 'preventiveMaintenance', 
                          'inventory', 'locations', 'vendors', 'reports', 'purchaseHistory',
                          'people', 'planning', 'improvementRequests', 'improvements',
                          'interventionRequests', 'equipments', 'meters', 'importExport', 'journal']
        }
    }
    
    existing_backup = await db.users.find_one({'email': 'buenogy@gmail.com'})
    if existing_backup:
        await db.users.update_one({'email': 'buenogy@gmail.com'}, {'$set': admin2})
        print('✅ Admin de secours mis à jour: buenogy@gmail.com')
    else:
        await db.users.insert_one(admin2)
        print('✅ Admin de secours créé: buenogy@gmail.com / Admin2024!')
    
    count = await db.users.count_documents({'role': 'ADMIN'})
    print(f'✅ Total admins dans la base: {count}')
    
    client.close()

asyncio.run(main())
PYEOF

# Uploader le script dans le container
pct push $CTID /tmp/create_admins_${CTID}.py /tmp/create_admins.py

# Cloner et installer l'application
pct exec $CTID -- bash <<APPEOF
set -e
cd /opt
rm -rf gmao-iris 2>/dev/null || true

# Cloner avec le token
echo "Clonage du dépôt GitHub..."
git clone -b $BRANCH $GIT_URL gmao-iris >/dev/null 2>&1 || {
    echo "❌ Erreur: Impossible de cloner le dépôt"
    echo "Vérifications:"
    echo "  1. Le token a-t-il les permissions 'repo' ?"
    echo "  2. Le dépôt ${GITHUB_USER}/${REPO_NAME} existe-t-il ?"
    echo "  3. La branche '$BRANCH' existe-t-elle ?"
    exit 1
}

cd gmao-iris

# Backend .env
SECRET_KEY=\$(openssl rand -hex 32)
cat > backend/.env <<BEOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=gmao_iris
SECRET_KEY=\${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
PORT=8001
HOST=0.0.0.0
SMTP_HOST=localhost
SMTP_PORT=25
SMTP_FROM=noreply@gmao-iris.local
SMTP_FROM_NAME=GMAO Iris
APP_URL=http://${CONTAINER_IP}
BEOF

# Frontend .env
cat > frontend/.env <<FEOF
REACT_APP_BACKEND_URL=http://${CONTAINER_IP}
NODE_ENV=production
FEOF

# Backend installation
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Créer les admins
python3 /tmp/create_admins.py "${ADMIN_EMAIL}" "${ADMIN_PASS}"

deactivate

# Frontend build
cd ../frontend
echo "Build du frontend (cela peut prendre 3-5 minutes)..."
yarn install --silent 2>/dev/null
yarn build 2>/dev/null
APPEOF

# Nettoyer
rm /tmp/create_admins_${CTID}.py

ok "Application installée"

msg "Configuration des services..."
pct exec $CTID -- bash -c '
# Supervisor
cat > /etc/supervisor/conf.d/gmao-iris-backend.conf <<EOF
[program:gmao-iris-backend]
directory=/opt/gmao-iris/backend
command=/opt/gmao-iris/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/gmao-iris-backend.err.log
stdout_logfile=/var/log/gmao-iris-backend.out.log
environment=PYTHONUNBUFFERED=1
EOF
supervisorctl reread >/dev/null
supervisorctl update >/dev/null
sleep 3

# Nginx
rm -f /etc/nginx/sites-enabled/default
cat > /etc/nginx/sites-available/gmao-iris <<EOF
server {
    listen 80;
    server_name _;
    client_max_body_size 25M;
    
    location / {
        root /opt/gmao-iris/frontend/build;
        try_files \$uri \$uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection upgrade;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF
ln -sf /etc/nginx/sites-available/gmao-iris /etc/nginx/sites-enabled/
nginx -t >/dev/null 2>&1
systemctl reload nginx

# Firewall
ufw --force enable >/dev/null 2>&1
ufw allow 22/tcp >/dev/null 2>&1
ufw allow 80/tcp >/dev/null 2>&1
ufw allow 443/tcp >/dev/null 2>&1
' >/dev/null 2>&1

ok "Services démarrés"

# Vérifier que le backend tourne
sleep 2
BACKEND_STATUS=$(pct exec $CTID -- supervisorctl status gmao-iris-backend | grep RUNNING || echo "NOT_RUNNING")

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              ✅ INSTALLATION TERMINÉE !                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Accès à l'application"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 URL:     http://${CONTAINER_IP}"
echo ""
echo "🔐 Compte principal:"
echo "   Email:        ${ADMIN_EMAIL}"
echo "   Mot de passe: [celui que vous avez défini]"
echo ""
echo "🔐 Compte de secours:"
echo "   Email:        buenogy@gmail.com"
echo "   Mot de passe: Admin2024!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Statut des services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [[ "$BACKEND_STATUS" == *"RUNNING"* ]]; then
    ok "Backend: RUNNING"
    echo ""
    echo "✅ Tout est opérationnel !"
    echo ""
    echo "Testez la connexion:"
    echo "  curl http://${CONTAINER_IP}/api/health"
else
    warn "Backend: Vérifier les logs"
    echo ""
    echo "Pour diagnostiquer:"
    echo "  pct enter $CTID"
    echo "  supervisorctl status"
    echo "  tail -f /var/log/gmao-iris-backend.err.log"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Commandes utiles"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Entrer dans le container:"
echo "  pct enter $CTID"
echo ""
echo "Arrêter/Démarrer le container:"
echo "  pct stop $CTID"
echo "  pct start $CTID"
echo ""
