# 🚀 Guide de Déploiement - GMAO Iris v1.2.0

## ⚠️ IMPORTANT - À LIRE AVANT DE COMMENCER

Cette version **1.2.0** contient des corrections critiques et de nouvelles fonctionnalités. 

**Changements majeurs :**
- ✅ Authentification externe corrigée
- ✅ Envoi d'emails fonctionnel (Gmail SMTP)
- ✅ Statistiques Historique Achat par utilisateur
- ✅ Notifications auto-refresh (30s)
- ✅ Système de mise à jour amélioré

---

## 📋 Prérequis

- Serveur avec GMAO Iris v1.1.0 ou supérieur
- Accès SSH au serveur
- Accès au dépôt GitHub
- App Password Gmail (pour les emails)

---

## 🔄 Méthode 1 : Mise à jour via l'interface (Recommandée)

### Étape 1 : Pusher sur GitHub

```bash
# Sur votre machine locale (là où vous avez le code)
cd /chemin/vers/GMAO
git add .
git commit -m "Version 1.2.0 - Statistiques + Fixes critiques"
git push origin main
```

### Étape 2 : Mettre à jour via l'interface

1. Connectez-vous sur votre serveur en admin
2. Allez dans **"Mise à jour"** (menu en bas)
3. Cliquez **"Vérifier"**
4. Si une mise à jour est disponible, cliquez **"Mettre à jour maintenant"**
5. Attendez la fin (2-3 minutes)
6. L'application redémarre automatiquement

### Étape 3 : Configuration post-mise à jour

**Sur votre serveur** :

```bash
# Connectez-vous en SSH
ssh root@votre-serveur

# 1. Configurez SMTP Gmail dans .env
nano /opt/gmao-iris/backend/.env

# Ajoutez/Modifiez ces lignes :
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT="587"
SMTP_USERNAME="buenogy@gmail.com"
SMTP_PASSWORD="dvyqotsnqayayobo"
SMTP_SENDER_EMAIL="buenogy@gmail.com"
SMTP_USE_TLS="true"

# Sauvegardez (Ctrl+X, Y, Entrée)

# 2. Redémarrez le backend
supervisorctl restart backend

# 3. Vérifiez que tout fonctionne
supervisorctl status
```

---

## 🔄 Méthode 2 : Mise à jour manuelle complète

### Étape 1 : Sauvegarder

```bash
# Sur votre serveur
cd /opt/gmao-iris
cp -r backend/.env backend/.env.backup
mongodump --db gmao_iris --out /root/backup_v1.1.0_$(date +%Y%m%d)
```

### Étape 2 : Mettre à jour le code

```bash
cd /opt/gmao-iris
git stash  # Sauvegarder les modifications locales
git pull origin main
git stash pop  # Réappliquer les modifications
```

### Étape 3 : Configurer .env

```bash
nano /opt/gmao-iris/backend/.env
```

**Vérifiez que ces lignes existent** :

```bash
# JWT Authentication
SECRET_KEY="votre_secret_key_ici"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES="10080"

# SMTP Gmail
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT="587"
SMTP_USERNAME="buenogy@gmail.com"
SMTP_PASSWORD="dvyqotsnqayayobo"
SMTP_SENDER_EMAIL="buenogy@gmail.com"
SMTP_USE_TLS="true"
```

**Si SECRET_KEY n'existe pas**, générez-en une :

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
# Copiez le résultat dans SECRET_KEY="..."
```

### Étape 4 : Recréer les comptes admins

```bash
cd /opt/gmao-iris/backend
python3 << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admins():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.gmao_iris
    
    # Admin principal
    await db.users.update_one(
        {"email": "admin@gmao.com"},
        {"$set": {
            "hashed_password": pwd.hash("Admin123!"),
            "nom": "Admin",
            "prenom": "Système",
            "role": "ADMIN",
            "statut": "actif",
            "dateCreation": datetime.now(),
            "firstLogin": False,
            "permissions": {
                module: {"view": True, "edit": True, "delete": True}
                for module in ["dashboard", "workOrders", "assets", 
                              "preventiveMaintenance", "inventory", 
                              "locations", "vendors", "reports"]
            }
        }},
        upsert=True
    )
    print("✅ Admin principal créé/mis à jour")
    
    # Admin de secours
    await db.users.update_one(
        {"email": "buenogy@gmail.com"},
        {"$set": {
            "hashed_password": pwd.hash("Admin2024!"),
            "nom": "Support",
            "prenom": "Admin",
            "role": "ADMIN",
            "statut": "actif",
            "dateCreation": datetime.now(),
            "firstLogin": False,
            "permissions": {
                module: {"view": True, "edit": True, "delete": True}
                for module in ["dashboard", "workOrders", "assets", 
                              "preventiveMaintenance", "inventory", 
                              "locations", "vendors", "reports"]
            }
        }},
        upsert=True
    )
    print("✅ Admin de secours créé/mis à jour")
    
    # Vérifier
    count = await db.users.count_documents({"role": "ADMIN"})
    print(f"📊 Total admins: {count}")
    
    client.close()

asyncio.run(create_admins())
EOF
```

### Étape 5 : Redémarrer les services

```bash
supervisorctl restart backend
supervisorctl restart frontend
sleep 5
supervisorctl status
```

---

## ✅ Vérification Post-Déploiement

### 1. Test Connexion Locale

```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@gmao.com","password":"Admin123!"}'

# Devrait retourner un access_token
```

### 2. Test Connexion Interface

- Ouvrez votre navigateur
- Allez sur votre URL
- Connectez-vous : `admin@gmao.com` / `Admin123!`
- ✅ Devrait fonctionner

### 3. Test Envoi Email

- Allez dans **"Équipes"**
- Cliquez **"Inviter un membre"**
- Entrez un email et envoyez
- ✅ Vérifiez la réception de l'email

### 4. Test Notifications

- Créez un ordre de travail
- Assignez-le à un utilisateur
- Attendez 30 secondes
- ✅ Le compteur devrait se mettre à jour automatiquement

### 5. Test Statistiques

- Allez dans **"Historique Achat"**
- Vérifiez les sections :
  - ✅ "Statistiques par Utilisateur"
  - ✅ "Évolution Mensuelle"

---

## 🐛 Dépannage

### Problème : Connexion externe ne fonctionne pas

```bash
# Exécutez le script de diagnostic
bash /opt/gmao-iris/diagnostic-connexion-externe.sh

# Vérifiez que SECRET_KEY est bien défini
grep SECRET_KEY /opt/gmao-iris/backend/.env

# Vérifiez auth.py
grep 'SECRET_KEY = os.environ.get("SECRET_KEY"' /opt/gmao-iris/backend/auth.py
```

### Problème : Emails ne partent pas

```bash
# Vérifiez les logs
tail -f /var/log/supervisor/backend.err.log

# Testez l'envoi manuel
cd /opt/gmao-iris/backend
python3 << 'EOF'
import sys
sys.path.insert(0, '/opt/gmao-iris/backend')
from email_service import send_email

result = send_email(
    to_email="buenogy@gmail.com",
    subject="Test",
    html_content="<h1>Test</h1>",
    text_content="Test"
)
print(f"Résultat: {'✅ Succès' if result else '❌ Échec'}")
EOF
```

### Problème : Statistiques ne s'affichent pas

```bash
# Vérifiez l'endpoint
curl http://localhost:8001/api/purchase-history/stats \
  -H "Authorization: Bearer VOTRE_TOKEN"

# Redémarrez le backend
supervisorctl restart backend
```

---

## 📞 Support

**En cas de problème :**

1. Consultez les logs :
   ```bash
   tail -f /var/log/supervisor/backend.err.log
   tail -f /var/log/supervisor/frontend.err.log
   ```

2. Utilisez le script de diagnostic :
   ```bash
   bash /opt/gmao-iris/diagnostic-connexion-externe.sh
   ```

3. Vérifiez l'état des services :
   ```bash
   supervisorctl status
   ```

---

## 🎉 Version 1.2.0 Déployée !

**Comptes disponibles :**
- Admin principal : `admin@gmao.com` / `Admin123!`
- Admin de secours : `buenogy@gmail.com` / `Admin2024!`

**Nouvelles fonctionnalités :**
- ✅ Statistiques par utilisateur
- ✅ Évolution mensuelle
- ✅ Notifications auto-refresh
- ✅ Emails fonctionnels
- ✅ Connexion externe OK

**Profitez de GMAO Iris v1.2.0 ! 🚀**
