# GMAO Iris v1.0 - Guide d'Installation Rapide

## 🚀 Installation Automatique sur Proxmox VE

### Prérequis
- Proxmox VE 7.x ou 8.x
- Accès root au serveur Proxmox
- Connexion Internet active
- 4 Go RAM minimum
- 20 Go d'espace disque minimum

### Installation en Une Commande

```bash
wget -qO - https://raw.githubusercontent.com/Kinder0083/GMAO/main/gmao-iris-v1-install.sh | bash
```

**OU** télécharger puis exécuter:

```bash
wget https://raw.githubusercontent.com/Kinder0083/GMAO/main/gmao-iris-v1-install.sh
chmod +x gmao-iris-v1-install.sh
./gmao-iris-v1-install.sh
```

### Processus d'Installation

Le script vous demandera:

1. **Configuration du Container:**
   - ID du container (défaut: 100)
   - RAM (défaut: 4096 Mo)
   - CPU cores (défaut: 2)
   - Disque (défaut: 20 Go)

2. **Configuration Réseau:**
   - DHCP ou IP statique
   - Si statique: IP, masque, passerelle

3. **Repository GitHub:**
   - URL (défaut: https://github.com/Kinder0083/GMAO.git)
   - Branche (défaut: main)

4. **Compte Administrateur:**
   - Email
   - Mot de passe (min 8 caractères)
   - Prénom
   - Nom

### Ce qui est Installé

✅ **Système d'exploitation:** Debian 12  
✅ **Base de données:** MongoDB 7.0  
✅ **Runtime:** Node.js 20.x + Python 3.11  
✅ **Serveur Web:** Nginx  
✅ **Process Manager:** Supervisor  
✅ **Serveur Email:** Postfix (SMTP local)  
✅ **Firewall:** UFW configuré  
✅ **Application:** GMAO Iris v1.0 complète

### Durée d'Installation

⏱️ **Environ 10-15 minutes** selon votre connexion Internet

### Après l'Installation

#### Accès à l'Application

```
http://[IP_DU_CONTAINER]
```

#### Comptes Créés

**1. Votre compte administrateur:**
- Email: [celui que vous avez défini]
- Mot de passe: [celui que vous avez défini]

**2. Compte de secours:**
- Email: buenogy@gmail.com
- Mot de passe: Admin2024!

⚠️ **IMPORTANT:** Changez le mot de passe du compte de secours après la première connexion!

---

## 📧 Configuration Email (Postfix)

Le serveur SMTP est **automatiquement configuré et opérationnel**:

- **Serveur:** localhost (Postfix)
- **Port:** 25
- **From:** noreply@gmao-iris.local
- **Type:** SMTP local sans authentification

### Fonctionnalités Email

✅ Invitations de membres  
✅ Notifications de création de compte  
✅ Emails de réinitialisation de mot de passe

### Tester l'envoi d'email

```bash
pct enter [CTID]
echo "Test email" | mail -s "Test GMAO Iris" root
tail /var/mail/root
```

---

## 🔧 Gestion de l'Application

### Entrer dans le Container

```bash
pct enter [CTID]
```

### Vérifier les Services

```bash
# Status de tous les services
systemctl status mongod
systemctl status nginx
systemctl status postfix
supervisorctl status
```

### Logs

```bash
# Backend
tail -f /var/log/gmao-iris-backend.out.log
tail -f /var/log/gmao-iris-backend.err.log

# Email (Postfix)
tail -f /var/log/mail.log
mailq  # File d'attente des emails
```

### Redémarrer les Services

```bash
# Backend
supervisorctl restart gmao-iris-backend

# Nginx
systemctl restart nginx

# MongoDB
systemctl restart mongod

# Postfix
systemctl restart postfix

# Tout redémarrer
systemctl restart mongod nginx postfix
supervisorctl restart gmao-iris-backend
```

---

## 🆕 Fonctionnalités v1.0

### ✅ Gestion Complète

- 📋 **Ordres de travail** avec multi-fichiers (photos, vidéos, docs)
- 🔧 **Équipements** avec hiérarchie et changement rapide de statut
- ⏰ **Maintenance préventive** planifiée
- 📦 **Inventaire** avec alertes de stock
- 📍 **Localisations** hiérarchiques
- 🛒 **Fournisseurs**
- 👥 **Gestion d'équipe** avancée
- 📊 **Rapports** PDF/Excel/CSV

### ⚡ Nouveau dans v1.0

- ✅ **Système d'invitation** par email
  - Inviter un membre (email avec lien d'inscription)
  - Créer un membre (création directe avec mot de passe temporaire)
  
- ✅ **Changement de mot de passe obligatoire** à la première connexion

- ✅ **Serveur SMTP intégré** (Postfix)
  - Emails d'invitation
  - Emails de création de compte
  - Totalement autonome

- ✅ **Permissions granulaires** par module

- ✅ **Import/Export** de données (Admin uniquement)

- ✅ **Support des domaines locaux** (.local)

---

## 🔄 Mise à Jour

### Mise à jour de l'application

```bash
pct enter [CTID]
cd /opt/gmao-iris

# Sauvegarder les .env
cp backend/.env /tmp/backend.env.backup
cp frontend/.env /tmp/frontend.env.backup

# Mettre à jour le code
git pull origin main

# Restaurer les .env
cp /tmp/backend.env.backup backend/.env
cp /tmp/frontend.env.backup frontend/.env

# Mettre à jour les dépendances
cd backend
source venv/bin/activate
pip install -r requirements.txt
deactivate

cd ../frontend
yarn install
yarn build

# Redémarrer les services
supervisorctl restart gmao-iris-backend
systemctl reload nginx
```

---

## 💾 Sauvegarde

### Sauvegarde MongoDB

```bash
# Dans le container
mongodump --db gmao_iris --out /backup/gmao-$(date +%Y%m%d)

# Restaurer
mongorestore --db gmao_iris /backup/gmao-20250119/gmao_iris
```

### Sauvegarde Complète du Container

```bash
# Depuis le host Proxmox
pct snapshot [CTID] backup-$(date +%Y%m%d)
vzdump [CTID] --mode snapshot --compress zstd --storage local
```

---

## 🆘 Dépannage

### Problème de connexion

```bash
# Vérifier les utilisateurs
pct enter [CTID]
cd /opt/gmao-iris
python3 create_admin.py
```

### Backend ne démarre pas

```bash
tail -50 /var/log/gmao-iris-backend.err.log
supervisorctl restart gmao-iris-backend
```

### Emails ne partent pas

```bash
# Vérifier Postfix
systemctl status postfix
tail -f /var/log/mail.log

# Vérifier la file d'attente
mailq

# Vider la file si nécessaire
postsuper -d ALL
```

### Erreur 502 Bad Gateway

```bash
# Vérifier que le backend écoute
netstat -tlnp | grep 8001

# Redémarrer
supervisorctl restart gmao-iris-backend
nginx -t && systemctl restart nginx
```

---

## 📞 Support

- 📚 **Documentation complète:** `/opt/gmao-iris/INSTALLATION_PROXMOX_COMPLET.md`
- 📋 **Notes de version:** `/opt/gmao-iris/CHANGELOG.md`
- 🐛 **Issues:** Ouvrez une issue sur GitHub

---

## ⚙️ Configuration Avancée

### SSL avec Let's Encrypt

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d votre-domaine.com --non-interactive --agree-tos -m admin@votre-domaine.com
```

### Ajuster les Ressources

```bash
# Depuis le host Proxmox
pct set [CTID] --memory 8192 --cores 4
pct reboot [CTID]
```

### Changer l'URL Backend

```bash
pct enter [CTID]

# Modifier l'URL dans frontend/.env
nano /opt/gmao-iris/frontend/.env
# REACT_APP_BACKEND_URL=http://nouvelle-ip

# Rebuild le frontend
cd /opt/gmao-iris/frontend
yarn build

# Redémarrer Nginx
systemctl reload nginx
```

---

## 📊 Spécifications Techniques

**Stack:**
- Frontend: React 19 + Tailwind CSS + shadcn/ui
- Backend: FastAPI (Python 3.11)
- Base de données: MongoDB 7.0
- Email: Postfix (SMTP)
- Reverse Proxy: Nginx
- Process Manager: Supervisor

**Ports:**
- 80 (HTTP) - Nginx
- 8001 (Internal) - Backend FastAPI
- 25 (Internal) - Postfix SMTP
- 27017 (Internal) - MongoDB

**Ressources Recommandées:**
- RAM: 4 Go (minimum 2 Go)
- CPU: 2 cores
- Disque: 20 Go
- Réseau: 1 Gbps

---

## 📝 License

Propriétaire - © 2025 GMAO Iris

---

## 👨‍💻 Développé par

**Concepteur:** Grèg  
**Version:** 1.0  
**Date:** Octobre 2025

---

**🎉 Profitez de GMAO Iris v1.0 !**
