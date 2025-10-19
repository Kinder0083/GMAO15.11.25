#!/usr/bin/env bash

###############################################################################
# GMAO Iris v1.0 - Installation Ultra-Simplifiée
# Pour dépôts publics uniquement - Installation en 10 minutes
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

msg() { echo -e "${BLUE}▶${NC} $1"; }
ok() { echo -e "${GREEN}✓${NC} $1"; }
err() { echo -e "${RED}✗${NC} $1"; exit 1; }

clear
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         GMAO IRIS v1.0 - Installation Rapide                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Config
read -p "ID container [100]: " CTID; CTID=${CTID:-100}
read -p "RAM Mo [4096]: " RAM; RAM=${RAM:-4096}
read -p "CPU [2]: " CORES; CORES=${CORES:-2}
read -p "IP [dhcp]: " IP; IP=${IP:-dhcp}
[[ $IP == "dhcp" ]] && NET="ip=dhcp" || NET="ip=$IP"
read -p "Email admin: " ADMIN_EMAIL
read -sp "Password admin: " ADMIN_PASS; echo ""
read -sp "Password root container: " ROOT_PASS; echo ""

msg "Création container..."
pct create $CTID local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
  --arch amd64 --cores $CORES --hostname gmao-iris --memory $RAM \
  --net0 name=eth0,bridge=vmbr0,$NET --onboot 1 --ostype debian \
  --rootfs local-lvm:20 --unprivileged 1 --features nesting=1 \
  --password "$ROOT_PASS" >/dev/null 2>&1 || err "Échec création"
pct start $CTID && sleep 5
ok "Container $CTID créé"

msg "Installation système (5-7 min)..."
pct exec $CTID -- bash -c 'export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq locales
echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
locale-gen >/dev/null 2>&1
export LANG=en_US.UTF-8
apt-get upgrade -y -qq
apt-get install -y -qq curl wget git gnupg ca-certificates build-essential \
  supervisor nginx ufw python3 python3-pip python3-venv mailutils

curl -fsSL https://deb.nodesource.com/setup_20.x | bash - >/dev/null 2>&1
apt-get install -y -qq nodejs
npm install -g yarn >/dev/null 2>&1

curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
  gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
echo "deb [signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg] http://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" > /etc/apt/sources.list.d/mongodb-org-7.0.list
apt-get update -qq
apt-get install -y -qq mongodb-org
systemctl start mongod
systemctl enable mongod >/dev/null 2>&1

echo "gmao-iris.local" > /etc/mailname
debconf-set-selections <<< "postfix postfix/mailname string gmao-iris.local"
debconf-set-selections <<< "postfix postfix/main_mailer_type string Internet Site"
apt-get install -y -qq postfix
systemctl start postfix
systemctl enable postfix >/dev/null 2>&1' 2>&1 | grep -i error || true
ok "Système installé"

IP=$(pct exec $CTID -- hostname -I | awk '{print $1}')
msg "Installation app..."

# Créer script Python pour admin
cat > /tmp/create_admins_$CTID.py <<EOF
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime
import uuid

async def main():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.gmao_iris
    pwd = CryptContext(schemes=['bcrypt'], deprecated='auto', bcrypt__rounds=10)
    
    admin = {
        'id': str(uuid.uuid4()),
        'email': '${ADMIN_EMAIL}',
        'password': pwd.hash('${ADMIN_PASS}'),
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
            m: {'view': True, 'edit': True, 'delete': True}
            for m in ['dashboard', 'workOrders', 'assets', 'preventiveMaintenance', 
                     'inventory', 'locations', 'vendors', 'reports']
        }
    }
    await db.users.insert_one(admin)
    
    admin2 = admin.copy()
    admin2['id'] = str(uuid.uuid4())
    admin2['email'] = 'buenogy@gmail.com'
    admin2['password'] = pwd.hash('Admin2024!')
    admin2['prenom'] = 'Support'
    admin2['nom'] = 'Admin'
    await db.users.insert_one(admin2)
    
    client.close()

asyncio.run(main())
EOF

pct push $CTID /tmp/create_admins_$CTID.py /tmp/create_admins.py

pct exec $CTID -- bash -c '
cd /opt
git clone -q https://github.com/Kinder0083/GMAO.git gmao-iris

cd gmao-iris

cat > backend/.env <<BEOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=gmao_iris
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
PORT=8001
HOST=0.0.0.0
SMTP_HOST=localhost
SMTP_PORT=25
SMTP_FROM=noreply@gmao-iris.local
SMTP_FROM_NAME=GMAO Iris
APP_URL=http://'$IP'
BEOF

cat > frontend/.env <<FEOF
REACT_APP_BACKEND_URL=http://'$IP'
NODE_ENV=production
FEOF

cd backend
python3 -m venv venv
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
python3 /tmp/create_admins.py
deactivate

cd ../frontend
yarn install --silent 2>/dev/null
yarn build 2>/dev/null
' || err "Échec installation app"

rm /tmp/create_admins_$CTID.py
ok "Application installée"

msg "Configuration services..."
pct exec $CTID -- bash -c '
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

ufw --force enable >/dev/null 2>&1
ufw allow 22/tcp >/dev/null 2>&1
ufw allow 80/tcp >/dev/null 2>&1
ufw allow 443/tcp >/dev/null 2>&1
' >/dev/null 2>&1
ok "Services configurés"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              ✅ INSTALLATION TERMINÉE !                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 URL:     http://$IP"
echo "🔐 Admin:   $ADMIN_EMAIL"
echo "🔐 Secours: buenogy@gmail.com / Admin2024!"
echo ""
echo "📋 Commandes utiles:"
echo "   pct enter $CTID"
echo "   tail -f /var/log/gmao-iris-backend.err.log"
echo ""
