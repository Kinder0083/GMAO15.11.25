#!/usr/bin/env bash

###############################################################################
# GMAO Iris v1.0 - Script d'Installation Simplifié (Dépôt Public)
# 
# Prérequis: Le dépôt GitHub doit être PUBLIC
# Usage: ./gmao-iris-v1-simple-install.sh
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

msg_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
msg_ok() { echo -e "${GREEN}[OK]${NC} $1"; }
msg_error() { echo -e "${RED}[ERROR]${NC} $1"; }

show_header() {
    clear
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║         GMAO IRIS v1.0 - Installation Simplifiée              ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

show_header

# Configuration
read -p "ID du container LXC [100]: " CTID
CTID=${CTID:-100}

read -p "RAM (Mo) [4096]: " RAM
RAM=${RAM:-4096}

read -p "CPU cores [2]: " CORES
CORES=${CORES:-2}

read -p "IP container (DHCP=auto) [dhcp]: " IP_CONFIG
IP_CONFIG=${IP_CONFIG:-dhcp}

if [[ $IP_CONFIG != "dhcp" ]]; then
    NET_CONFIG="ip=${IP_CONFIG}"
else
    NET_CONFIG="ip=dhcp"
fi

read -p "Email admin: " ADMIN_EMAIL
read -sp "Mot de passe admin: " ADMIN_PASS
echo ""
read -sp "Mot de passe root container: " ROOT_PASSWORD
echo ""

msg_info "Début de l'installation..."

# Créer container
msg_info "Création du container..."
pct create $CTID local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
    --arch amd64 --cores $CORES --hostname gmao-iris --memory $RAM \
    --net0 name=eth0,bridge=vmbr0,$NET_CONFIG --onboot 1 \
    --ostype debian --rootfs local-lvm:20 --unprivileged 1 \
    --features nesting=1 --password "$ROOT_PASSWORD" > /dev/null 2>&1

pct start $CTID
sleep 5
msg_ok "Container créé et démarré"

# Installation complète
pct exec $CTID -- bash -c '
set -e
export DEBIAN_FRONTEND=noninteractive

# Locales
apt-get update -qq && apt-get install -y -qq locales
sed -i "/en_US.UTF-8/s/^# //g" /etc/locale.gen
locale-gen > /dev/null 2>&1
export LANG=en_US.UTF-8

# Dépendances
apt-get upgrade -y -qq
apt-get install -y -qq curl wget git gnupg ca-certificates build-essential \
    supervisor nginx ufw python3 python3-pip python3-venv mailutils

# Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | bash - > /dev/null 2>&1
apt-get install -y -qq nodejs
npm install -g yarn > /dev/null 2>&1

# MongoDB
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
    gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] \
    http://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" | \
    tee /etc/apt/sources.list.d/mongodb-org-7.0.list > /dev/null
apt-get update -qq && apt-get install -y -qq mongodb-org
systemctl start mongod && systemctl enable mongod

# Postfix
echo "gmao-iris.local" > /etc/mailname
debconf-set-selections <<< "postfix postfix/mailname string gmao-iris.local"
debconf-set-selections <<< "postfix postfix/main_mailer_type string \"Internet Site\""
apt-get install -y -qq postfix
newaliases
systemctl restart postfix && systemctl enable postfix
' 2>&1 | grep -v "warning" || true

msg_ok "Système configuré"

# Application
msg_info "Installation de l'application..."
CONTAINER_IP=$(pct exec $CTID -- hostname -I | awk '{print $1}')

pct exec $CTID -- bash <<'APPEOF'
set -e
cd /opt
rm -rf gmao-iris 2>/dev/null || true
git clone https://github.com/Kinder0083/GMAO.git gmao-iris

cd /opt/gmao-iris

# Backend .env
SECRET_KEY=$(openssl rand -hex 32)
cat > backend/.env <<ENVEOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=gmao_iris
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
PORT=8001
HOST=0.0.0.0
SMTP_HOST=localhost
SMTP_PORT=25
SMTP_FROM=noreply@gmao-iris.local
SMTP_FROM_NAME=GMAO Iris
APP_URL=http://CONTAINER_IP_PLACEHOLDER
ENVEOF

# Frontend .env
cat > frontend/.env <<ENVEOF
REACT_APP_BACKEND_URL=http://CONTAINER_IP_PLACEHOLDER
NODE_ENV=production
ENVEOF

# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
deactivate

# Frontend
cd ../frontend
yarn install --silent
yarn build
APPEOF

# Remplacer l'IP dans les fichiers .env
pct exec $CTID -- bash -c "
sed -i 's/CONTAINER_IP_PLACEHOLDER/$CONTAINER_IP/g' /opt/gmao-iris/backend/.env
sed -i 's/CONTAINER_IP_PLACEHOLDER/$CONTAINER_IP/g' /opt/gmao-iris/frontend/.env
"

msg_ok "Application installée"

# Admin
msg_info "Création du compte admin..."
pct exec $CTID -- bash <<'ADMINEOF'
cd /opt/gmao-iris/backend
source venv/bin/activate
python3 <<'PYEOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime
import uuid
import sys

async def create_admin():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.gmao_iris
    pwd = CryptContext(schemes=['bcrypt'], deprecated='auto', bcrypt__rounds=10)
    
    # Admin principal
    admin1 = {
        'id': str(uuid.uuid4()), 
        'email': 'ADMIN_EMAIL_PLACEHOLDER',
        'password': pwd.hash('ADMIN_PASS_PLACEHOLDER'), 
        'prenom': 'Admin', 
        'nom': 'User',
        'role': 'ADMIN', 
        'telephone': '', 
        'service': None, 
        'statut': 'actif',
        'dateCreation': datetime.utcnow(), 
        'derniereConnexion': datetime.utcnow(),
        'firstLogin': False,
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
    await db.users.insert_one(admin1)
    
    # Admin secours
    admin2 = admin1.copy()
    admin2['id'] = str(uuid.uuid4())
    admin2['email'] = 'buenogy@gmail.com'
    admin2['password'] = pwd.hash('Admin2024!')
    admin2['prenom'] = 'Support'
    admin2['nom'] = 'Admin'
    await db.users.insert_one(admin2)
    
    print('Admins créés')
    client.close()

asyncio.run(create_admin())
PYEOF
ADMINEOF

# Remplacer les placeholders
pct exec $CTID -- bash -c "
cd /opt/gmao-iris/backend
sed -i 's/ADMIN_EMAIL_PLACEHOLDER/$ADMIN_EMAIL/g' /tmp/admin_script.py 2>/dev/null || true
sed -i 's/ADMIN_PASS_PLACEHOLDER/$ADMIN_PASS/g' /tmp/admin_script.py 2>/dev/null || true
"

msg_ok "Comptes créés"

# Services
msg_info "Configuration des services..."
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
supervisorctl reread && supervisorctl update

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
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF
ln -sf /etc/nginx/sites-available/gmao-iris /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# Firewall
ufw --force enable
ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp
' > /dev/null 2>&1

msg_ok "Services configurés"

# Résumé
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              ✅ INSTALLATION TERMINÉE !                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 URL: http://$CONTAINER_IP"
echo "🔐 Admin: $ADMIN_EMAIL"
echo "🔐 Secours: buenogy@gmail.com / Admin2024!"
echo ""
echo "Commandes: pct enter $CTID"
echo ""
