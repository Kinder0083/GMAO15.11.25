# 🚀 Installation GMAO Iris - Nouveau Serveur

Guide complet pour déployer GMAO Iris sur un nouveau serveur (Proxmox LXC, VPS, VM, etc.)

---

## 📋 Prérequis

### Logiciels requis :
- ✅ Python 3.11+
- ✅ Node.js 16+ / Yarn
- ✅ MongoDB 5.0+
- ✅ Nginx
- ✅ Supervisor
- ✅ Git

### Ports à ouvrir :
- `80` (HTTP) ou `443` (HTTPS)
- `8001` (Backend API - en interne uniquement)

---

## 🔧 Installation Étape par Étape

### 1. Préparation du système

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation des dépendances
sudo apt install -y python3 python3-pip python3-venv \
    nodejs npm nginx supervisor git mongodb curl

# Installation de Yarn
sudo npm install -g yarn

# Vérifier les versions
python3 --version  # 3.11+
node --version     # v16+
yarn --version
mongod --version   # 5.0+
```

---

### 2. Clone du projet

```bash
# Créer le répertoire
sudo mkdir -p /opt/gmao-iris
cd /opt/gmao-iris

# Cloner depuis GitHub
sudo git clone https://github.com/Kinder0083/GMAO.git .

# Vérifier que tout est là
ls -la
# Vous devez voir: backend/ frontend/ README.md etc.
```

---

### 3. Configuration Backend

```bash
cd /opt/gmao-iris/backend

# Créer l'environnement virtuel
python3 -m venv venv

# Activer le venv
source venv/bin/activate

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt

# Créer le fichier .env
cat > .env << 'EOF'
MONGO_URL=mongodb://localhost:27017
DB_NAME=gmao_iris
PORT=8001
HOST=0.0.0.0

# Configuration SMTP (à remplir plus tard via l'interface)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_FROM_NAME=GMAO Iris
SMTP_USE_TLS=true

# Secret pour JWT
JWT_SECRET_KEY=$(openssl rand -hex 32)
EOF

# Créer l'utilisateur admin initial
python3 create_admin_manual.py
# Suivre les instructions à l'écran
```

---

### 4. Configuration Frontend

```bash
cd /opt/gmao-iris/frontend

# Installer les dépendances
yarn install

# Créer le fichier .env
cat > .env << 'EOF'
# Laisser vide pour détection automatique (recommandé)
REACT_APP_BACKEND_URL=

# Configuration WebSocket (mode dev)
WDS_SOCKET_PORT=443

# Options
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
EOF

# Builder le frontend
yarn build

# Vérifier que le build est créé
ls -la build/
```

---

### 5. Configuration Supervisor

```bash
# Créer le fichier de configuration
sudo nano /etc/supervisor/conf.d/gmao-iris-backend.conf
```

Contenu du fichier :

```ini
[program:gmao-iris-backend]
directory=/opt/gmao-iris/backend
command=/opt/gmao-iris/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/gmao-iris-backend.err.log
stdout_logfile=/var/log/gmao-iris-backend.out.log
environment=PYTHONUNBUFFERED=1
```

Puis :

```bash
# Recharger Supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Démarrer le backend
sudo supervisorctl start gmao-iris-backend

# Vérifier le statut
sudo supervisorctl status gmao-iris-backend
# Doit afficher: RUNNING

# Vérifier les logs
tail -f /var/log/gmao-iris-backend.err.log
# Doit afficher: "Application startup complete"
```

---

### 6. Configuration Nginx

```bash
# Créer la configuration
sudo nano /etc/nginx/sites-available/gmao-iris
```

Contenu du fichier :

```nginx
server {
    listen 80;
    server_name _;  # Remplacer par votre domaine si vous en avez un

    # Frontend (fichiers statiques React)
    location / {
        root /opt/gmao-iris/frontend/build;
        try_files $uri $uri/ /index.html;
        
        # Cache pour les assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts pour les longues requêtes
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }

    # Taille max upload (pour fichiers)
    client_max_body_size 50M;
}
```

Puis :

```bash
# Activer le site
sudo ln -s /etc/nginx/sites-available/gmao-iris /etc/nginx/sites-enabled/

# Désactiver le site par défaut (optionnel)
sudo rm /etc/nginx/sites-enabled/default

# Tester la configuration
sudo nginx -t

# Redémarrer Nginx
sudo systemctl restart nginx

# Vérifier le statut
sudo systemctl status nginx
```

---

### 7. Configuration MongoDB

```bash
# Démarrer MongoDB
sudo systemctl start mongodb
sudo systemctl enable mongodb

# Vérifier qu'il tourne
sudo systemctl status mongodb

# Se connecter à MongoDB (optionnel)
mongo
> show dbs
> use gmao_iris
> show collections
> exit
```

---

### 8. Première connexion

```bash
# Trouver votre IP (si vous ne la connaissez pas)
ip addr show | grep "inet " | grep -v 127.0.0.1

# Ou votre IP publique
curl ifconfig.me
```

**Accéder à l'application :**
- **Local :** `http://VOTRE_IP_LOCALE`
- **Distant :** `http://VOTRE_IP_PUBLIQUE`
- **Domaine :** `http://votre-domaine.com`

**Connexion avec le compte admin créé à l'étape 3.**

---

## ⚙️ Configuration Post-Installation

### 1. Configurer SMTP (envoi d'emails)

1. Se connecter en tant qu'admin
2. Aller dans **Paramètres spéciaux**
3. Section **Configuration SMTP**
4. Remplir les informations (ex: Gmail avec mot de passe d'application)
5. **Sauvegarder**
6. **Tester** l'envoi

**Pour Gmail :**
- Serveur : `smtp.gmail.com`
- Port : `587`
- Utilisateur : `votre-email@gmail.com`
- Mot de passe : Créer un "Mot de passe d'application" sur https://myaccount.google.com/security
- TLS : ✓ Coché

---

### 2. Configurer les utilisateurs

1. Aller dans **Paramètres spéciaux** → **Gestion des utilisateurs**
2. Créer les comptes utilisateurs
3. Définir les permissions (admin, technicien, etc.)
4. Les utilisateurs recevront un email pour définir leur mot de passe

---

### 3. Configurer le timeout de session

1. Aller dans **Paramètres spéciaux**
2. Section **Déconnexion automatique**
3. Ajuster le temps d'inactivité (défaut : 15 minutes)
4. **Sauvegarder**

---

## 🔄 Mises à jour

### Via l'interface (recommandé) :

1. Se connecter en tant qu'admin
2. Aller dans **Mises à jour** (icône en haut à droite)
3. Cliquer sur **Vérifier les mises à jour**
4. Si disponible, cliquer sur **Appliquer la mise à jour**
5. Gérer les conflits Git si nécessaire (3 options proposées)
6. Attendre la fin de la mise à jour
7. Recharger la page

### Manuellement (si problème) :

```bash
cd /opt/gmao-iris

# Récupérer les modifications
git pull origin main

# Mettre à jour le backend
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Mettre à jour et builder le frontend
cd ../frontend
yarn install
yarn build

# Redémarrer les services
sudo supervisorctl restart gmao-iris-backend
sudo systemctl reload nginx

# Vider cache navigateur : Ctrl + Shift + R
```

---

## 🔐 Sécurité

### Recommandations :

1. **HTTPS (SSL/TLS) :**
```bash
# Avec Certbot (Let's Encrypt)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d votre-domaine.com
```

2. **Firewall :**
```bash
# Installer UFW
sudo apt install ufw

# Autoriser SSH, HTTP, HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Activer
sudo ufw enable
```

3. **Sauvegardes automatiques :**
- Configurer des sauvegardes quotidiennes de MongoDB
- Utiliser la fonction de backup intégrée dans l'application

---

## 🆘 Dépannage

### Backend ne démarre pas :

```bash
# Vérifier les logs
tail -f /var/log/gmao-iris-backend.err.log

# Vérifier supervisor
sudo supervisorctl status gmao-iris-backend

# Redémarrer
sudo supervisorctl restart gmao-iris-backend
```

### Frontend ne s'affiche pas :

```bash
# Vérifier que le build existe
ls -la /opt/gmao-iris/frontend/build/

# Rebuilder si nécessaire
cd /opt/gmao-iris/frontend
yarn build

# Redémarrer nginx
sudo systemctl restart nginx

# Vider cache navigateur : Ctrl + Shift + R
```

### Modifications ne s'appliquent pas :

```bash
# Rebuilder le frontend
cd /opt/gmao-iris/frontend
yarn build

# Redémarrer nginx
sudo systemctl reload nginx

# Vider cache navigateur
```

### MongoDB ne démarre pas :

```bash
# Vérifier les logs
sudo tail -f /var/log/mongodb/mongodb.log

# Redémarrer
sudo systemctl restart mongodb
```

---

## 📊 Monitoring

### Vérifier l'état des services :

```bash
# Supervisor
sudo supervisorctl status

# Nginx
sudo systemctl status nginx

# MongoDB
sudo systemctl status mongodb

# Logs en temps réel
tail -f /var/log/gmao-iris-backend.err.log
tail -f /var/log/nginx/access.log
```

### Vérifier l'espace disque :

```bash
df -h
du -sh /opt/gmao-iris/*
```

---

## 📝 Checklist Installation

- [ ] Prérequis installés (Python, Node, MongoDB, Nginx, Supervisor)
- [ ] Projet cloné depuis GitHub
- [ ] Backend configuré (.env, venv, dépendances)
- [ ] Admin initial créé
- [ ] Frontend buildé
- [ ] Supervisor configuré et backend démarre
- [ ] Nginx configuré et fonctionne
- [ ] MongoDB actif
- [ ] Application accessible via navigateur
- [ ] Connexion admin réussie
- [ ] SMTP configuré et testé
- [ ] Utilisateurs créés
- [ ] Firewall configuré (si production)
- [ ] HTTPS configuré (si production)
- [ ] Sauvegardes automatiques configurées (si production)

---

**Version du guide :** 1.0  
**Dernière mise à jour :** 17 novembre 2025  
**Testé sur :** Ubuntu 22.04 LTS, Debian 11/12
