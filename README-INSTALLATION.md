# 📘 Guide d'Installation GMAO Iris v1.1.1

## 📋 Table des matières

1. [Prérequis](#prérequis)
2. [Avant l'installation](#avant-linstallation)
3. [Installation](#installation)
4. [Première connexion](#première-connexion)
5. [Dépannage](#dépannage)
6. [Commandes utiles](#commandes-utiles)
7. [Mise à jour](#mise-à-jour)

---

## 🔧 Prérequis

### Serveur Proxmox
- **Version** : Proxmox VE 9.0 ou supérieur
- **OS** : Basé sur Debian 12 (Bookworm)
- **RAM** : Minimum 8 Go recommandé (4 Go pour le container)
- **Disque** : 30 Go d'espace libre minimum
- **Réseau** : Connexion Internet active

### GitHub (Dépôt privé)
Vous devez créer un **Personal Access Token** :

1. Allez sur : https://github.com/settings/tokens
2. Cliquez sur : **Generate new token (classic)**
3. Donnez un nom : `GMAO Iris Installation`
4. Cochez : **`repo`** (Full control of private repositories)
5. Générez et **copiez le token** (vous ne pourrez plus le voir après)

---

## 🔍 Avant l'installation

### Étape 1 : Télécharger les scripts

Connectez-vous en SSH sur votre serveur Proxmox et exécutez :

```bash
cd /root
wget https://raw.githubusercontent.com/VOTRE_USER/VOTRE_REPO/main/diagnose-proxmox.sh
wget https://raw.githubusercontent.com/VOTRE_USER/VOTRE_REPO/main/gmao-iris-v1.1.1-install-auto.sh
chmod +x *.sh
```

> **💡 Astuce** : Si les fichiers sont dans un dépôt privé, vous devrez les transférer via SCP/SFTP ou les copier manuellement.

### Étape 2 : Exécuter le diagnostic

```bash
./diagnose-proxmox.sh
```

Ce script vérifie automatiquement :
- ✅ Version de Proxmox
- ✅ Templates Debian 12 disponibles
- ✅ Storages disponibles (local-lvm, local, etc.)
- ✅ IDs de container libres
- ✅ Espace disque disponible

**Exemple de sortie :**

```
╔════════════════════════════════════════════════════════════════╗
║         Diagnostic Proxmox pour GMAO Iris v1.1                ║
╚════════════════════════════════════════════════════════════════╝

[1/6] Version Proxmox
pve-manager/9.0.1 (running kernel: 6.8.12-1-pve)

[2/6] Templates CT disponibles
debian-12-standard_12.7-1_amd64.tar.zst

[3/6] Storages disponibles
Name         Type     Status  Total      Used       Available
local-lvm    lvmthin  active  500.00GiB  120.00GiB  380.00GiB
local        dir      active  100.00GiB  45.00GiB   55.00GiB

[4/6] Vérification du storage 'local-lvm'
✓ local-lvm est disponible

[5/6] Vérification de l'ID container 100
✓ ID 100 est disponible

[6/6] Espace disque disponible
/dev/sda1  100G   45G   55G   45% /
```

### Étape 3 : Corriger les problèmes (si nécessaire)

#### ❌ Si le template Debian 12 est manquant :

```bash
pveam update
pveam download local debian-12-standard_12.7-1_amd64.tar.zst
```

#### ❌ Si l'ID 100 est déjà utilisé :

Le nouveau script détecte automatiquement un ID libre, mais vous pouvez le choisir manuellement pendant l'installation.

---

## 🚀 Installation

### Lancer le script d'installation

```bash
./gmao-iris-v1.1.1-install-auto.sh
```

### Questions posées pendant l'installation

Le script vous demandera les informations suivantes :

#### 1️⃣ **GitHub Token**
```
Collez votre GitHub Token: ghp_xxxxxxxxxxxxxxxxxxxx
```

#### 2️⃣ **Informations GitHub**
```
Votre username GitHub [Kinder0083]: VotreUsername
Nom du dépôt [GMAO]: GMAO
Branche [main]: main
```

#### 3️⃣ **Configuration du container**
```
ID container [100]: 100
RAM (Mo) [4096]: 4096
CPU cores [2]: 2
Taille disque (Go) [20]: 20
IP [dhcp]: dhcp
```

> **💡 Choix de l'IP :**
> - `dhcp` : Attribution automatique par votre routeur
> - `192.168.1.50/24,gw=192.168.1.1` : IP fixe (adaptez à votre réseau)

#### 4️⃣ **Compte administrateur**
```
Email admin: admin@votre-entreprise.fr
Mot de passe admin (min 8 car): ********
Mot de passe root container: ********
```

#### 5️⃣ **Confirmation**

Le script affiche un résumé :

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Résumé:
  Proxmox: pve-manager/9.0.1
  Template: debian-12-standard_12.7-1_amd64.tar.zst
  Storage: local-lvm
  Container: 100 (4096Mo, 2 cores, 20Go)
  GitHub: VotreUser/GMAO (branche: main)
  Admin: admin@votre-entreprise.fr
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Confirmer l'installation ? (y/n):
```

Tapez `y` pour continuer.

### Durée de l'installation

⏱️ **Temps estimé : 10-15 minutes**

Le script effectue automatiquement :
1. ✅ Création du container LXC
2. ✅ Installation de Debian 12
3. ✅ Installation de Node.js 20, Python 3.11, MongoDB 7.0
4. ✅ Installation de Nginx, Supervisor, Postfix
5. ✅ Clonage du dépôt GitHub
6. ✅ Installation des dépendances backend/frontend
7. ✅ Build de l'application React
8. ✅ Configuration des services
9. ✅ Création des comptes administrateurs

### Fin de l'installation

```
╔════════════════════════════════════════════════════════════════╗
║              ✅ INSTALLATION TERMINÉE !                        ║
╚════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Accès à l'application
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌐 URL:     http://192.168.1.100

🔐 Compte principal:
   Email:        admin@votre-entreprise.fr
   Mot de passe: [celui que vous avez défini]

🔐 Compte de secours:
   Email:        buenogy@gmail.com
   Mot de passe: Admin2024!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Statut des services
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Backend: RUNNING
```

---

## 🔑 Première connexion

### 1. Accéder à l'application

Ouvrez votre navigateur et allez sur l'URL affichée :

```
http://[IP_DU_CONTAINER]
```

### 2. Se connecter

Utilisez les identifiants que vous avez créés :

**Compte principal :**
- Email : `admin@votre-entreprise.fr`
- Mot de passe : Celui que vous avez défini

**Compte de secours (toujours disponible) :**
- Email : `buenogy@gmail.com`
- Mot de passe : `Admin2024!`

### 3. Première utilisation

Une fois connecté, vous accédez au **Dashboard** avec toutes les fonctionnalités :

- 📊 **Dashboard** : Vue d'ensemble
- 🔧 **Ordres de travail** : Gestion des interventions
- 📝 **Demandes d'intervention** : Requêtes internes
- 💡 **Améliorations** : Suivi des améliorations
- 📦 **Équipements** : Inventaire des équipements
- 📍 **Zones** : Gestion des emplacements
- 📈 **Compteurs** : Relevés et suivi
- 📊 **Rapports** : Analyse et statistiques
- 🛒 **Historique d'achat** : Graphiques mensuels
- 👥 **Équipe** : Gestion des utilisateurs
- 📅 **Planning** : Calendrier des tâches
- 🔄 **Maintenance préventive** : Planification
- 📥 **Import/Export** : Gestion des données
- 📜 **Journal** : Audit et logs

---

## 🔧 Dépannage

### Problème : Le backend ne démarre pas

**Symptôme :**
```
⚠ Backend: Vérifier les logs
```

**Solution :**

```bash
# Entrer dans le container
pct enter 100

# Vérifier les logs d'erreur
tail -f /var/log/gmao-iris-backend.err.log

# Vérifier le statut
supervisorctl status

# Redémarrer le backend
supervisorctl restart gmao-iris-backend
```

**Erreurs courantes :**

#### ❌ MongoDB ne démarre pas

```bash
systemctl status mongod
systemctl start mongod
```

#### ❌ Erreur "Module not found"

```bash
cd /opt/gmao-iris/backend
source venv/bin/activate
pip install -r requirements.txt
deactivate
supervisorctl restart gmao-iris-backend
```

### Problème : Page blanche ou 502 Bad Gateway

**Causes possibles :**
1. Backend non démarré
2. Frontend mal build
3. Nginx mal configuré

**Diagnostic :**

```bash
pct enter 100

# Vérifier tous les services
systemctl status nginx
systemctl status mongod
supervisorctl status

# Tester l'API directement
curl http://localhost:8001/api/health

# Vérifier les logs Nginx
tail -f /var/log/nginx/error.log
```

**Rebuild du frontend si nécessaire :**

```bash
cd /opt/gmao-iris/frontend
yarn install
yarn build
systemctl reload nginx
```

### Problème : Impossible de se connecter

**Vérification 1 : Les utilisateurs existent**

```bash
pct enter 100

# Se connecter à MongoDB
mongosh

use gmao_iris
db.users.find({}, {email: 1, role: 1})
exit
```

**Vérification 2 : Recréer l'utilisateur admin**

```bash
cd /opt/gmao-iris/backend
source venv/bin/activate

python3 << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime

async def main():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.gmao_iris
    pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')
    
    admin = {
        'email': 'admin@test.fr',
        'hashed_password': pwd.hash('password123'),
        'nom': 'Admin',
        'prenom': 'Test',
        'role': 'ADMIN',
        'telephone': None,
        'service': None,
        'statut': 'actif',
        'dateCreation': datetime.now(),
        'derniereConnexion': None,
        'firstLogin': False,
        'permissions': {
            m: {'view': True, 'edit': True, 'delete': True}
            for m in ['dashboard', 'workOrders', 'reports', 'people', 
                      'purchaseHistory', 'improvementRequests', 'improvements']
        }
    }
    
    await db.users.delete_one({'email': 'admin@test.fr'})
    await db.users.insert_one(admin)
    print('✅ Admin créé: admin@test.fr / password123')
    client.close()

asyncio.run(main())
EOF

deactivate
```

### Problème : Le container ne démarre pas

```bash
# Vérifier le statut
pct status 100

# Démarrer manuellement
pct start 100

# Voir les logs du container
pct enter 100
journalctl -xe
```

---

## 📝 Commandes utiles

### Gestion du container

```bash
# Entrer dans le container
pct enter 100

# Arrêter le container
pct stop 100

# Démarrer le container
pct start 100

# Redémarrer le container
pct restart 100

# Voir les ressources utilisées
pct status 100

# Modifier la RAM (à chaud)
pct set 100 -memory 8192

# Modifier les CPU cores
pct set 100 -cores 4
```

### Gestion des services (dans le container)

```bash
# Statut de tous les services
supervisorctl status

# Redémarrer le backend
supervisorctl restart gmao-iris-backend

# Voir les logs en direct
supervisorctl tail -f gmao-iris-backend

# Redémarrer Nginx
systemctl restart nginx

# Redémarrer MongoDB
systemctl restart mongod
```

### Logs

```bash
# Backend
tail -f /var/log/gmao-iris-backend.out.log
tail -f /var/log/gmao-iris-backend.err.log

# Nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# MongoDB
journalctl -u mongod -f
```

### Base de données

```bash
# Se connecter à MongoDB
mongosh

# Utiliser la base gmao_iris
use gmao_iris

# Lister les collections
show collections

# Compter les utilisateurs
db.users.countDocuments()

# Voir tous les admins
db.users.find({role: 'ADMIN'}, {email: 1, nom: 1, prenom: 1})

# Supprimer un utilisateur
db.users.deleteOne({email: 'user@example.com'})

# Quitter
exit
```

### Backup / Restore

```bash
# Backup de la base de données
mongodump --db=gmao_iris --out=/root/backup-$(date +%Y%m%d)

# Restore
mongorestore --db=gmao_iris /root/backup-YYYYMMDD/gmao_iris

# Backup du container complet (depuis Proxmox)
vzdump 100 --mode stop --dumpdir /var/lib/vz/dump
```

---

## 🔄 Mise à jour

### Mise à jour de l'application

```bash
pct enter 100
cd /opt/gmao-iris

# Sauvegarder les .env
cp backend/.env /tmp/backend.env.backup
cp frontend/.env /tmp/frontend.env.backup

# Mettre à jour depuis Git
git pull origin main

# Restaurer les .env
cp /tmp/backend.env.backup backend/.env
cp /tmp/frontend.env.backup frontend/.env

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
deactivate

# Frontend
cd ../frontend
yarn install
yarn build

# Redémarrer
supervisorctl restart gmao-iris-backend
systemctl reload nginx
```

### Mise à jour de Proxmox

```bash
# Sur le serveur Proxmox
apt update
apt dist-upgrade
reboot
```

---

## 📞 Support

### Logs à fournir en cas de problème

```bash
# Depuis Proxmox
pct enter 100

# Collecter les informations
cat > /tmp/diagnostic.txt <<EOF
=== Statut des services ===
$(supervisorctl status)

=== Backend logs (dernières 50 lignes) ===
$(tail -50 /var/log/gmao-iris-backend.err.log)

=== Nginx error logs (dernières 50 lignes) ===
$(tail -50 /var/log/nginx/error.log)

=== MongoDB status ===
$(systemctl status mongod)

=== Versions ===
Node: $(node --version)
Python: $(python3 --version)
MongoDB: $(mongod --version | head -1)
EOF

cat /tmp/diagnostic.txt
```

### Contact

- 📧 Email : buenogy@gmail.com
- 📦 GitHub : https://github.com/Kinder0083/GMAO

---

## 🎉 Fonctionnalités v1.1.1

### Nouveautés de cette version

✅ **Système d'authentification corrigé**
- Champs `hashed_password`, `nom`, `prenom` correctement structurés
- Rôles en majuscules (ADMIN, TECHNICIEN, etc.)
- Permissions granulaires par module

✅ **Section Historique d'achat opérationnelle**
- Graphique de l'évolution mensuelle des achats (HTML/CSS pur)
- Affichage groupé des commandes
- Détails dépliables des articles
- Bouton "Supprimer tout" pour les admins
- Import/Export CSV/Excel

✅ **Nouvelles sections**
- Demandes d'amélioration
- Améliorations

✅ **Installation simplifiée**
- Auto-détection du template Debian 12
- Auto-détection du storage Proxmox
- Détection automatique d'ID libre
- Compatible Proxmox 9.0 / Debian 12

---

## 📄 Licence

Ce projet est sous licence privée. Tous droits réservés.

© 2025 GMAO Iris - Grégoire
