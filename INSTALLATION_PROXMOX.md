# GMAO Iris - Installation Proxmox LXC

Ce guide décrit l'installation automatique de GMAO Iris dans un conteneur LXC Proxmox.

## 📋 Prérequis

- **Proxmox VE 7.0 ou supérieur**
- **Accès SSH root** à votre serveur Proxmox
- **Ressources minimales recommandées** :
  - RAM : 2 Go minimum (4 Go recommandé)
  - Disque : 10 Go minimum (20 Go recommandé)
  - CPU : 2 cœurs minimum

## 🚀 Installation automatique (Méthode recommandée)

### Étape 1 : Créer le conteneur LXC dans Proxmox

1. Connectez-vous à l'interface web Proxmox
2. Cliquez sur **"Create CT"** (Créer CT)
3. Configurez le conteneur :

   **Général :**
   - CT ID : Choisir un ID libre (ex: 100)
   - Hostname : `gmao-iris`
   - Password : Définir un mot de passe root
   - Template : **Debian 12 standard**

   **Ressources :**
   - RAM : `2048 MB` (ou plus)
   - Swap : `512 MB`
   - Disque : `20 GB`

   **Réseau :**
   - Bridge : `vmbr0` (ou votre bridge réseau)
   - IPv4 : Choisir entre :
     - **DHCP** (automatique)
     - **IP statique** (ex: 192.168.1.100/24)
   - Gateway : L'adresse de votre routeur (si IP statique)

4. Cliquez sur **"Finish"** pour créer le conteneur
5. **Démarrer** le conteneur

### Étape 2 : Se connecter au conteneur

Depuis votre serveur Proxmox :

```bash
pct enter 100  # Remplacez 100 par votre CT ID
```

Ou via SSH (si vous avez configuré une IP) :

```bash
ssh root@IP_DU_CONTENEUR
```

### Étape 3 : Exécuter le script d'installation

Une seule commande suffit :

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/VOTRE_USER/gmao-iris/main/install-proxmox-lxc.sh)
```

**OU** si vous préférez télécharger d'abord :

```bash
wget https://raw.githubusercontent.com/VOTRE_USER/gmao-iris/main/install-proxmox-lxc.sh
chmod +x install-proxmox-lxc.sh
./install-proxmox-lxc.sh
```

### Étape 4 : Suivre l'assistant d'installation

Le script vous posera plusieurs questions :

#### 1. **Configuration du dépôt GitHub**
```
Configuration du dépôt GitHub
1) Dépôt public (aucune authentification requise)
2) Dépôt privé (nécessite un token GitHub)
Choisissez une option [1-2] (défaut: 1):
```

**Pour un dépôt public :** Choisir `1` et entrer l'URL
**Pour un dépôt privé :** Choisir `2`, entrer l'URL et votre token GitHub

#### 2. **Configuration du compte Administrateur**
```
Email de l'administrateur (défaut: admin@gmao-iris.local): admin@example.com
Mot de passe de l'administrateur: ********
Prénom de l'administrateur (défaut: System): Sophie
Nom de l'administrateur (défaut: Admin): Martin
```

#### 3. **Configuration réseau**
```
Adresse IP détectée: 192.168.1.100
Utiliser cette adresse IP ? (y/n) [défaut: y]: y
Avez-vous un nom de domaine ? (y/n) [défaut: n]: y
Nom de domaine (ex: gmao-iris.votredomaine.com): gmao.example.com
```

#### 4. **Configuration SSL/HTTPS** (si nom de domaine)
```
Configuration SSL/HTTPS
1) HTTP uniquement (pas de SSL)
2) HTTPS avec Let's Encrypt (certificat automatique)
3) HTTPS avec certificat manuel
Choisissez une option [1-3] (défaut: 1):
```

**Option 1 :** HTTP simple (réseau local)
**Option 2 :** HTTPS automatique avec Let's Encrypt (recommandé pour Internet)
**Option 3 :** Vos propres certificats SSL

#### 5. **Configuration des ports**
```
Port du frontend [défaut: 3000]: 3000
Port du backend [défaut: 8001]: 8001
```

#### 6. **Confirmation**
```
═══════════════════════════════════════════════════════════
               RÉSUMÉ DE LA CONFIGURATION
═══════════════════════════════════════════════════════════

  Dépôt GitHub:       https://github.com/user/repo
  Admin Email:        admin@example.com
  IP locale:          192.168.1.100
  Nom de domaine:     gmao.example.com
  SSL:                HTTPS
  Port frontend:      3000
  Port backend:       8001

═══════════════════════════════════════════════════════════

Confirmer l'installation avec ces paramètres ? (y/n):
```

Tapez `y` pour continuer.

### Étape 5 : Attendez la fin de l'installation

Le script va automatiquement :
- ✓ Installer toutes les dépendances système
- ✓ Installer Node.js 20.x et Yarn
- ✓ Installer Python 3 et pip
- ✓ Installer MongoDB 7.0
- ✓ Cloner le dépôt GitHub
- ✓ Configurer les variables d'environnement
- ✓ Installer les dépendances de l'application
- ✓ Créer le compte administrateur
- ✓ Configurer Supervisor pour le backend
- ✓ Configurer Nginx comme reverse proxy
- ✓ Configurer le firewall UFW
- ✓ (Optionnel) Configurer Let's Encrypt pour HTTPS

**Durée estimée :** 10-15 minutes selon votre connexion Internet

### Étape 6 : Accéder à l'application

Une fois l'installation terminée, le script affichera :

```
═══════════════════════════════════════════════════════════
      INSTALLATION TERMINÉE AVEC SUCCÈS !
═══════════════════════════════════════════════════════════

  📍 Accès à l'application:
     🔒 https://gmao.example.com
     🏠 http://192.168.1.100

  👤 Compte Administrateur:
     Email:       admin@example.com
     Mot de passe: ********

  📂 Répertoire d'installation: /opt/gmao-iris

  🔧 Commandes utiles:
     - Redémarrer backend:  supervisorctl restart gmao-iris-backend
     - Voir les logs:       tail -f /var/log/gmao-iris-backend.out.log
     - Redémarrer Nginx:    systemctl restart nginx
     - MongoDB status:      systemctl status mongod

═══════════════════════════════════════════════════════════
```

Ouvrez votre navigateur et accédez à l'une des URLs affichées !

## 🔧 Gestion de l'application

### Commandes Supervisor (Backend)

```bash
# Statut du backend
supervisorctl status gmao-iris-backend

# Redémarrer le backend
supervisorctl restart gmao-iris-backend

# Arrêter le backend
supervisorctl stop gmao-iris-backend

# Démarrer le backend
supervisorctl start gmao-iris-backend

# Voir les logs en temps réel
tail -f /var/log/gmao-iris-backend.out.log

# Voir les erreurs
tail -f /var/log/gmao-iris-backend.err.log
```

### Commandes Nginx (Frontend)

```bash
# Statut de Nginx
systemctl status nginx

# Redémarrer Nginx
systemctl restart nginx

# Recharger la configuration
systemctl reload nginx

# Tester la configuration
nginx -t

# Voir les logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Commandes MongoDB

```bash
# Statut de MongoDB
systemctl status mongod

# Redémarrer MongoDB
systemctl restart mongod

# Se connecter à MongoDB
mongosh

# Sauvegarder la base de données
mongodump --out /root/backup-gmao-$(date +%Y%m%d)

# Restaurer la base de données
mongorestore /root/backup-gmao-20250119
```

## 🔄 Mise à jour de l'application

Pour mettre à jour l'application vers la dernière version :

```bash
cd /opt/gmao-iris

# Arrêter le backend
supervisorctl stop gmao-iris-backend

# Mettre à jour le code
git pull

# Backend : Réinstaller les dépendances si nécessaire
cd backend
source venv/bin/activate
pip install -r requirements.txt
deactivate

# Frontend : Rebuild
cd ../frontend
yarn install
yarn build

# Redémarrer les services
supervisorctl start gmao-iris-backend
systemctl reload nginx
```

## 📊 Sauvegarde et restauration

### Sauvegarde complète

```bash
#!/bin/bash
BACKUP_DIR="/root/backups/gmao-iris-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Sauvegarder MongoDB
mongodump --out "$BACKUP_DIR/mongodb"

# Sauvegarder les fichiers uploadés (si applicable)
cp -r /opt/gmao-iris/uploads "$BACKUP_DIR/" 2>/dev/null || true

# Sauvegarder la configuration
cp /opt/gmao-iris/backend/.env "$BACKUP_DIR/backend.env"
cp /opt/gmao-iris/frontend/.env "$BACKUP_DIR/frontend.env"

echo "Sauvegarde terminée : $BACKUP_DIR"
```

### Restauration

```bash
BACKUP_DIR="/root/backups/gmao-iris-20250119-140530"

# Arrêter les services
supervisorctl stop gmao-iris-backend

# Restaurer MongoDB
mongorestore "$BACKUP_DIR/mongodb"

# Restaurer les fichiers (si applicable)
cp -r "$BACKUP_DIR/uploads" /opt/gmao-iris/ 2>/dev/null || true

# Redémarrer les services
supervisorctl start gmao-iris-backend
```

## 🛠️ Dépannage

### Le backend ne démarre pas

```bash
# Vérifier les logs
tail -n 100 /var/log/gmao-iris-backend.err.log

# Vérifier que MongoDB fonctionne
systemctl status mongod

# Vérifier que le port n'est pas déjà utilisé
netstat -tulpn | grep 8001

# Redémarrer manuellement pour voir les erreurs
cd /opt/gmao-iris/backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001
```

### L'interface ne se charge pas

```bash
# Vérifier que Nginx fonctionne
systemctl status nginx

# Vérifier la configuration Nginx
nginx -t

# Vérifier les logs Nginx
tail -f /var/log/nginx/error.log

# Vérifier que le build frontend existe
ls -la /opt/gmao-iris/frontend/build
```

### Erreur de connexion MongoDB

```bash
# Vérifier que MongoDB écoute
netstat -tulpn | grep 27017

# Vérifier les logs MongoDB
tail -f /var/log/mongodb/mongod.log

# Tester la connexion
mongosh --eval "db.adminCommand('ping')"
```

### Problème de certificat SSL (Let's Encrypt)

```bash
# Renouveler manuellement
certbot renew

# Tester le renouvellement
certbot renew --dry-run

# Vérifier l'expiration
certbot certificates
```

## 🔐 Sécurité

### Recommandations

1. **Changer le mot de passe admin** après la première connexion
2. **Configurer UFW** (fait automatiquement par le script)
3. **Activer HTTPS** avec Let's Encrypt si accessible depuis Internet
4. **Sauvegardes régulières** de MongoDB
5. **Mettre à jour régulièrement** le système et l'application

### Ports ouverts par défaut

- **22** : SSH
- **80** : HTTP
- **443** : HTTPS (si SSL activé)

## 📝 Structure des fichiers

```
/opt/gmao-iris/
├── backend/
│   ├── venv/              # Environnement Python
│   ├── server.py          # API FastAPI
│   ├── models.py          # Modèles Pydantic
│   ├── requirements.txt   # Dépendances Python
│   └── .env              # Variables d'environnement backend
├── frontend/
│   ├── build/            # Build de production
│   ├── src/              # Code source React
│   ├── package.json      # Dépendances Node.js
│   └── .env             # Variables d'environnement frontend
└── install-proxmox-lxc.sh  # Script d'installation

/etc/nginx/
└── sites-available/
    └── gmao-iris         # Configuration Nginx

/etc/supervisor/
└── conf.d/
    └── gmao-iris-backend.conf  # Configuration Supervisor
```

## 📞 Support

Pour toute question ou problème :
- **Issues GitHub** : https://github.com/VOTRE_USER/gmao-iris/issues
- **Documentation** : Consultez ce README

## 📄 Licence

Ce projet est sous licence GPL-3.0. Voir le fichier LICENSE pour plus de détails.

---

**GMAO Iris** - Système de Gestion de Maintenance Assistée par Ordinateur
Version 1.0.0
