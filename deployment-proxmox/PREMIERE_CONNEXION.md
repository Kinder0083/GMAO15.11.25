# 🎯 Première Connexion - GMAO Iris sur Proxmox

Guide rapide pour votre première connexion après le déploiement.

---

## 🌐 Accès à l'Application

### URL Frontend
```
http://VOTRE-IP-PUBLIQUE:3000
```

**Exemple :** Si votre IP est `82.66.41.98`
```
http://82.66.41.98:3000
```

---

## 🔐 Identifiants par Défaut

### Compte Administrateur Principal

| Champ | Valeur |
|-------|--------|
| **Email** | `admin@gmao-iris.local` |
| **Mot de passe** | `Admin123!` |
| **Rôle** | Super Admin |

**⚠️ IMPORTANT :** Changez ce mot de passe immédiatement après la première connexion !

---

## 🚀 Première Connexion - Étapes

### 1. Ouvrez votre navigateur

Utilisez Chrome, Firefox, Edge ou Safari (version récente)

### 2. Accédez à l'URL

```
http://VOTRE-IP-PUBLIQUE:3000
```

### 3. Page de connexion

Vous devriez voir la page de connexion **GMAO Iris**

### 4. Entrez les identifiants

- **Email :** `admin@gmao-iris.local`
- **Mot de passe :** `Admin123!`

### 5. Cliquez sur "Se connecter"

Vous serez redirigé vers le **Dashboard**

---

## ✅ Que faire après la première connexion ?

### 1. **Changez le mot de passe admin** ⚠️ PRIORITAIRE

```
Menu → Profil → Modifier le mot de passe
```

Utilisez un mot de passe fort :
- Au moins 12 caractères
- Majuscules, minuscules, chiffres, symboles
- Unique (pas utilisé ailleurs)

### 2. **Créez des utilisateurs**

```
Menu → Utilisateurs → Nouveau Utilisateur
```

Types d'utilisateurs :
- **Admin** : Accès complet
- **User** : Accès limité (voir uniquement)

### 3. **Configurez les Pôles de Service**

```
Menu → Documentations → Nouveau Pôle
```

Exemples :
- Maintenance
- QHSE
- Production
- Qualité

### 4. **Uploadez des documents**

```
Documentations → [Cliquez sur un Pôle] → Upload Document
```

Formats supportés :
- PDF (`.pdf`)
- Word (`.docx`)
- Images (`.jpg`, `.png`)

### 5. **Créez des Bons de Travail**

```
Documentations → [Pôle] → Nouveau Bon de Travail
```

---

## 🔍 Vérifications Post-Installation

### ✅ Checklist de vérification

- [ ] Je peux me connecter avec les identifiants admin
- [ ] Le dashboard s'affiche correctement
- [ ] Je peux naviguer dans les menus
- [ ] Je peux créer un Pôle de Service
- [ ] Je peux uploader un document
- [ ] Je peux créer un Bon de Travail
- [ ] Je peux imprimer un Bon de Travail (PDF)
- [ ] J'ai changé le mot de passe admin par défaut

---

## 🆘 Problèmes Courants

### ❌ "Erreur de connexion au serveur"

**Causes possibles :**
1. Backend pas démarré
2. Ports fermés dans le firewall
3. Mauvaise configuration de `REACT_APP_BACKEND_URL`

**Solutions :**
```bash
# Vérifier que le backend tourne
netstat -tlnp | grep 8001

# Vérifier les logs backend
tail -f /var/log/supervisor/backend.err.log

# Tester l'API directement
curl http://localhost:8001/api/version
```

### ❌ "Invalid credentials" avec les bons identifiants

**Cause :** La base de données n'est pas initialisée avec le compte admin

**Solution :**
```bash
# Vérifier MongoDB
docker exec -it gmao-mongodb mongosh -u admin -p PASSWORD

# Dans mongosh:
use gmao_db
db.users.find({email: "admin@gmao-iris.local"})

# Si vide, créer l'admin manuellement (contactez le support)
```

### ❌ Page blanche / Ne charge pas

**Causes possibles :**
1. Frontend pas démarré
2. Port 3000 fermé
3. Erreur de build

**Solutions :**
```bash
# Vérifier que le frontend tourne
netstat -tlnp | grep 3000

# Vérifier les logs frontend
tail -f /var/log/supervisor/frontend.err.log

# Redémarrer le frontend
sudo supervisorctl restart frontend
```

### ❌ Cannot upload files

**Cause :** Permissions sur le dossier uploads

**Solution :**
```bash
# Créer et donner les permissions
mkdir -p /app/backend/uploads
chmod 755 /app/backend/uploads
chown -R USER:USER /app/backend/uploads
```

---

## 🔧 URLs Utiles

| Service | URL | Utilisation |
|---------|-----|-------------|
| **Frontend** | `http://IP:3000` | Interface utilisateur |
| **Backend API** | `http://IP:8001/api` | API REST |
| **API Docs** | `http://IP:8001/docs` | Documentation Swagger |
| **Health Check** | `http://IP:8001/api/version` | Vérifier que l'API répond |

---

## 📞 Support

### En cas de problème persistant

1. **Consultez la documentation :**
   - `INSTRUCTIONS_PROXMOX.md` (section Dépannage)
   - `DOCKER_DEPLOYMENT.md` (si vous utilisez Docker)

2. **Collectez les informations :**
   ```bash
   # Informations système
   uname -a
   docker --version  # Si Docker
   
   # Status des services
   sudo supervisorctl status
   # ou
   docker-compose ps
   
   # Logs backend
   tail -100 /var/log/supervisor/backend.err.log
   
   # Logs frontend
   tail -100 /var/log/supervisor/frontend.err.log
   
   # Ports ouverts
   netstat -tlnp | grep -E "3000|8001"
   ```

3. **Créez une issue GitHub** avec ces informations

---

## 🎉 Félicitations !

Si vous pouvez vous connecter et naviguer dans l'application, votre installation est réussie !

**Prochaines étapes :**
1. ✅ Changez le mot de passe admin
2. ✅ Créez des utilisateurs
3. ✅ Configurez vos Pôles de Service
4. ✅ Commencez à utiliser l'application !

---

**Bonne utilisation de GMAO Iris !** 🚀

---

**Version :** 1.5.0  
**Date :** 19 Novembre 2025
