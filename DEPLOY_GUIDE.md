# 🚀 Guide de Déploiement - GMAO Iris

## 📋 Commandes pour sauvegarder sur GitHub

### Depuis l'environnement de développement `/app` :

```bash
cd /app

# 1. Vérifier les modifications
git status

# 2. Ajouter tous les fichiers modifiés
git add .

# 3. Créer un commit avec un message descriptif
git commit -m "feat: Configuration adaptative + Interface SMTP + Gestion conflits Git

- Configuration URL backend adaptative (local + distant)
- Interface complète de configuration SMTP dans Paramètres spéciaux
- Gestion intelligente des conflits Git avant mise à jour
- Correction erreur EntityType.SYSTEM
- Suppression doublon route /api/updates/apply
- Ajout paramètre version dans appel mise à jour
- Documentation complète (.env.example, CHANGELOG)

Fichiers modifiés:
Backend: models.py, server.py, update_service.py, email_service.py
Frontend: 14 fichiers (config.js, pages, composants)
Nouveaux: GitConflictDialog.jsx, config.js, .env.example"

# 4. Pousser vers GitHub
git push origin main
```

---

## 📦 Déploiement sur serveur Proxmox

### Une fois push sur GitHub, sur votre serveur :

```bash
cd /opt/gmao-iris

# 1. Récupérer les dernières modifications
git pull origin main

# 2. Vérifier les changements récupérés
git log --oneline -5

# 3. Mettre à jour les dépendances backend (si nécessaire)
cd backend
source venv/bin/activate  # ou utilisez votre venv
pip install -r requirements.txt

# 4. Mettre à jour et builder le frontend
cd ../frontend
yarn install
yarn build

# 5. Redémarrer les services
sudo supervisorctl restart gmao-iris-backend
sudo systemctl reload nginx

# 6. Vérifier que tout fonctionne
sudo supervisorctl status gmao-iris-backend
sudo nginx -t
sudo systemctl status nginx

# 7. Vider le cache du navigateur
# Dans le navigateur : Ctrl + Shift + R (ou Ctrl + F5)
```

---

## 🔍 Vérification post-déploiement

### 1. Backend
```bash
# Vérifier les logs backend
tail -n 50 /var/log/gmao-iris-backend.err.log

# Tester l'API
curl -X GET http://localhost:8001/api/updates/current
```

### 2. Frontend
```bash
# Vérifier que le build est à jour
ls -lh /opt/gmao-iris/frontend/build/static/js/
# Le fichier main.*.js doit avoir une date/heure récente

# Vérifier nginx
sudo nginx -t
```

### 3. Fonctionnalités
- [ ] Se connecter à l'application
- [ ] Aller dans "Paramètres spéciaux"
- [ ] Vérifier que la section "Configuration SMTP" apparaît
- [ ] Tester une mise à jour (vérifier dialogue des conflits si modifications locales)
- [ ] Tester l'accès depuis l'extérieur avec l'IP publique

---

## ⚠️ Résolution de problèmes courants

### Problème 1 : Les modifications n'apparaissent pas après git pull

**Cause :** Le build frontend n'a pas été régénéré.

**Solution :**
```bash
cd /opt/gmao-iris/frontend
yarn build
sudo systemctl reload nginx
# Vider cache navigateur : Ctrl + Shift + R
```

---

### Problème 2 : Erreur "git pull" - modifications locales

**Cause :** Des modifications locales empêchent le pull.

**Solution 1 - Écraser les modifications locales :**
```bash
cd /opt/gmao-iris
git reset --hard HEAD
git pull origin main
```

**Solution 2 - Sauvegarder les modifications :**
```bash
cd /opt/gmao-iris
git stash
git pull origin main
# Pour restaurer plus tard : git stash pop
```

---

### Problème 3 : L'application n'est pas accessible depuis l'extérieur

**Cause :** Le `.env` du frontend contient une IP locale.

**Solution :**
```bash
cd /opt/gmao-iris/frontend

# Mettre REACT_APP_BACKEND_URL vide (détection auto)
echo "REACT_APP_BACKEND_URL=" > .env

# Rebuilder
yarn build
sudo systemctl reload nginx
```

---

### Problème 4 : Erreurs dans les logs backend

**Vérifier les logs :**
```bash
# Logs d'erreur
tail -f /var/log/gmao-iris-backend.err.log

# Logs de sortie
tail -f /var/log/gmao-iris-backend.out.log

# Redémarrer si nécessaire
sudo supervisorctl restart gmao-iris-backend
```

---

### Problème 5 : Nginx ne démarre pas

**Tester la configuration :**
```bash
# Tester la config nginx
sudo nginx -t

# Si erreur, vérifier les logs
sudo tail -n 50 /var/log/nginx/error.log

# Redémarrer nginx
sudo systemctl restart nginx
```

---

## 🔐 Configuration SMTP (Gmail)

### Créer un mot de passe d'application Gmail :

1. Aller sur : https://myaccount.google.com/security
2. Activer la validation en 2 étapes (si pas déjà fait)
3. Aller dans "Mots de passe des applications"
4. Générer un nouveau mot de passe pour "Mail"
5. Copier le mot de passe généré (16 caractères)

### Configurer dans l'interface :

1. Se connecter en tant qu'admin
2. Aller dans "Paramètres spéciaux"
3. Section "Configuration SMTP"
4. Remplir :
   - Serveur : `smtp.gmail.com`
   - Port : `587`
   - Utilisateur : `votre-email@gmail.com`
   - Mot de passe : le mot de passe d'application (16 caractères)
   - Email expéditeur : `votre-email@gmail.com`
   - TLS : ✓ Coché
5. Sauvegarder
6. Tester l'envoi

---

## 📊 Monitoring

### Vérifier l'état des services :
```bash
# Supervisor
sudo supervisorctl status

# Nginx
sudo systemctl status nginx

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

## 🔄 Rollback (retour arrière)

Si quelque chose ne fonctionne pas après la mise à jour :

```bash
cd /opt/gmao-iris

# 1. Voir l'historique des commits
git log --oneline -10

# 2. Revenir au commit précédent (remplacer COMMIT_ID)
git reset --hard COMMIT_ID

# 3. Rebuilder le frontend
cd frontend
yarn build

# 4. Redémarrer les services
sudo supervisorctl restart gmao-iris-backend
sudo systemctl reload nginx
```

---

## 📝 Checklist de déploiement

### Avant le déploiement :
- [ ] Toutes les modifications sont committées dans `/app`
- [ ] Les tests ont été effectués en développement
- [ ] Le CHANGELOG est à jour
- [ ] Une sauvegarde de la base de données existe

### Pendant le déploiement :
- [ ] `git pull origin main` réussi
- [ ] Dépendances backend mises à jour
- [ ] Dépendances frontend mises à jour
- [ ] `yarn build` réussi
- [ ] Services redémarrés sans erreur

### Après le déploiement :
- [ ] Backend démarre sans erreur
- [ ] Nginx fonctionne correctement
- [ ] L'application est accessible en local
- [ ] L'application est accessible depuis l'extérieur
- [ ] Les nouvelles fonctionnalités sont visibles
- [ ] Test de connexion réussi
- [ ] Test d'une fonctionnalité critique

---

## 🆘 Support

En cas de problème :

1. **Vérifier les logs** (voir section Monitoring)
2. **Consulter ce guide** (section Résolution de problèmes)
3. **Rollback** si nécessaire
4. **Demander de l'aide** avec les logs d'erreur

---

**Version du guide :** 1.0  
**Dernière mise à jour :** 17 novembre 2025
