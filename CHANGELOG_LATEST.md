# 📋 Changelog - Dernières modifications

## Version : Novembre 2025

---

## ✅ Fonctionnalités ajoutées

### 1. 🌐 Configuration URL Backend Adaptative
**Problème résolu :** L'application n'était accessible que depuis le réseau local (IP privée).

**Solution :** Détection automatique de l'URL backend qui fonctionne en local ET à distance.

**Fichiers modifiés :**
- ✅ `frontend/src/utils/config.js` *(nouveau)*
- ✅ `frontend/src/services/api.js`
- ✅ `frontend/src/pages/Login.jsx`
- ✅ `frontend/src/pages/Updates.jsx`
- ✅ `frontend/src/pages/Planning.jsx`
- ✅ `frontend/src/pages/ImportExport.jsx`
- ✅ `frontend/src/components/Common/UpdateNotificationBadge.jsx`
- ✅ `frontend/src/components/Common/RecentUpdatePopup.jsx`
- ✅ `frontend/src/components/Common/ForgotPasswordDialog.jsx`
- ✅ `frontend/src/components/Layout/MainLayout.jsx`
- ✅ `frontend/.env` - REACT_APP_BACKEND_URL vide par défaut
- ✅ `frontend/.env.example` *(nouveau)* - Documentation complète

**Avantages :**
- 🌐 Fonctionne automatiquement en local ET à distance
- 🔄 Pas de reconfiguration lors du changement d'IP
- 📱 Compatible IP locale, IP publique, nom de domaine

---

### 2. 📧 Interface de Configuration SMTP
**Problème résolu :** Configuration SMTP nécessitait des commandes SSH complexes.

**Solution :** Interface complète dans "Paramètres spéciaux" pour gérer la configuration email.

**Fichiers modifiés :**

**Backend :**
- ✅ `backend/models.py` - Modèles `SMTPConfig`, `SMTPConfigUpdate`, `SMTPTestRequest`
- ✅ `backend/server.py` - 3 nouveaux endpoints :
  - `GET /api/smtp/config` - Récupérer la configuration
  - `PUT /api/smtp/config` - Mettre à jour la configuration
  - `POST /api/smtp/test` - Tester l'envoi d'email
- ✅ `backend/email_service.py` - Fonctions :
  - `init_email_service()` - Recharger la configuration
  - `send_test_email()` - Email de test stylisé

**Frontend :**
- ✅ `frontend/src/pages/SpecialSettings.jsx` - Section complète SMTP avec :
  - Formulaire de configuration (serveur, port, identifiants)
  - Guide pour Gmail avec mot de passe d'application
  - Bouton "Tester" pour vérifier la configuration
  - Validation et messages d'erreur

**Fonctionnalités :**
- ⚙️ Configuration directe depuis l'interface
- 📝 Sauvegarde automatique dans `.env`
- ✉️ Test d'envoi avec email stylisé
- 📊 Journalisation dans l'audit

---

### 3. 🔧 Gestion Intelligente des Conflits Git
**Problème résolu :** Les mises à jour échouaient avec erreur "git pull" si modifications locales.

**Solution :** Interface de résolution de conflits avec 3 options claires.

**Fichiers modifiés :**

**Backend :**
- ✅ `backend/update_service.py` - Méthodes :
  - `check_git_conflicts()` - Détecter les modifications locales
  - `resolve_git_conflicts(strategy)` - Résoudre avec stratégie choisie
- ✅ `backend/server.py` - 2 nouveaux endpoints :
  - `GET /api/updates/check-conflicts` - Vérifier les conflits
  - `POST /api/updates/resolve-conflicts` - Résoudre les conflits

**Frontend :**
- ✅ `frontend/src/components/Common/GitConflictDialog.jsx` *(nouveau)* - Dialogue avec 3 options :
  - 🗑️ **Écraser** (git reset --hard)
  - 💾 **Sauvegarder** (git stash)
  - ❌ **Annuler**
- ✅ `frontend/src/pages/Updates.jsx` - Intégration du dialogue
  - Vérification automatique avant mise à jour
  - Affichage des fichiers modifiés

**Fonctionnalités :**
- 🔍 Détection automatique des conflits avant mise à jour
- 🎨 Interface claire avec explications
- 📋 Liste des fichiers modifiés
- 📊 Journalisation des actions

---

### 4. 🔄 Correction du Système de Mise à Jour
**Problèmes résolus :**
1. ❌ Erreur "SYSTEM" - `EntityType.SYSTEM` n'existait pas
2. ❌ Routes dupliquées - 2 définitions de `/api/updates/apply`
3. ❌ Paramètre version manquant - Frontend n'envoyait pas la version

**Solutions :**

**Backend :**
- ✅ `backend/server.py` :
  - Correction `EntityType.SYSTEM` → `EntityType.SETTINGS`
  - Suppression doublon route `/api/updates/apply` (ligne 3661-3675)
- ✅ `backend/update_service.py` :
  - Détection automatique des chemins (fonctionne en `/app` et `/opt/gmao-iris`)
  - Logging détaillé dans `/tmp/update_process.log`

**Frontend :**
- ✅ `frontend/src/pages/Updates.jsx` :
  - Ajout paramètre `version` dans l'appel API
  - Intégration gestion des conflits

---

## 🗂️ Fichiers créés

### Nouveaux fichiers :
1. ✅ `frontend/src/utils/config.js` - Configuration URL adaptative
2. ✅ `frontend/src/components/Common/GitConflictDialog.jsx` - Dialogue conflits Git
3. ✅ `frontend/.env.example` - Documentation configuration
4. ✅ `update_service_FIXED.py` - Version corrigée (temporaire)

---

## 📊 Résumé des modifications

### Backend (4 fichiers)
- `backend/models.py` - Ajout modèles SMTP
- `backend/server.py` - Endpoints SMTP + conflits Git + corrections
- `backend/update_service.py` - Détection chemins + gestion conflits
- `backend/email_service.py` - Init + test SMTP

### Frontend (14 fichiers)
- `frontend/src/utils/config.js` *(nouveau)*
- `frontend/src/services/api.js`
- `frontend/src/pages/Login.jsx`
- `frontend/src/pages/Updates.jsx`
- `frontend/src/pages/Planning.jsx`
- `frontend/src/pages/ImportExport.jsx`
- `frontend/src/pages/SpecialSettings.jsx`
- `frontend/src/components/Common/UpdateNotificationBadge.jsx`
- `frontend/src/components/Common/RecentUpdatePopup.jsx`
- `frontend/src/components/Common/ForgotPasswordDialog.jsx`
- `frontend/src/components/Common/GitConflictDialog.jsx` *(nouveau)*
- `frontend/src/components/Layout/MainLayout.jsx`
- `frontend/.env`
- `frontend/.env.example` *(nouveau)*

### Configuration
- `frontend/yarn.lock` - Dépendances mises à jour

---

## 🚀 Déploiement sur serveur production

### Après avoir push sur GitHub :

```bash
cd /opt/gmao-iris

# 1. Récupérer les modifications
git pull origin main

# 2. Installer les dépendances (si nécessaire)
cd backend
pip install -r requirements.txt

cd ../frontend
yarn install

# 3. Builder le frontend
yarn build

# 4. Redémarrer les services
sudo supervisorctl restart gmao-iris-backend
sudo systemctl reload nginx

# 5. Vérifier
sudo supervisorctl status
```

---

## ⚠️ Notes importantes

### Pour l'accès distant :
- Le fichier `frontend/.env` doit avoir `REACT_APP_BACKEND_URL=` (vide)
- La détection automatique s'occupe du reste
- Fonctionne en local (192.168.x.x) ET distant (IP publique/domaine)

### Pour les mises à jour :
- Toujours vérifier les conflits Git avant mise à jour
- Le système détecte automatiquement et propose 3 options
- Les modifications locales peuvent être sauvegardées avec git stash

### Pour la configuration SMTP :
- Accessible dans "Paramètres spéciaux" (admin uniquement)
- Utiliser un mot de passe d'application pour Gmail
- Tester la configuration avant de l'utiliser en production

---

## 🎯 Tests effectués

✅ Accès local (IP privée)  
✅ Accès distant (IP publique)  
✅ Configuration SMTP avec Gmail  
✅ Test d'envoi d'email  
✅ Mise à jour avec conflits Git (3 scénarios)  
✅ Build frontend et déploiement  
✅ Journalisation audit  

---

## 📝 Prochaines étapes possibles

- [ ] Ajouter support d'autres fournisseurs SMTP (SendGrid, Mailgun, etc.)
- [ ] Interface de visualisation des stash Git
- [ ] Rollback automatique en cas d'échec de mise à jour
- [ ] Notifications email automatiques pour les mises à jour

---

**Date :** 17 novembre 2025  
**Version :** 1.2.0+fixes
