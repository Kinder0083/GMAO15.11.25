# 🚨 CORRECTION URGENTE - Problème de Login Proxmox

## ⚠️ PROBLÈME IDENTIFIÉ

Le script d'installation Proxmox avait un **BUG CRITIQUE** :
- Les utilisateurs étaient créés dans une base de données (`gmao_iris` EN DUR)
- L'application les cherchait dans une autre base (variable `DB_NAME`)
- **Résultat:** Impossible de se connecter même avec des identifiants valides

## ✅ SOLUTION IMMÉDIATE

### Étape 1: Entrer dans votre container Proxmox

Depuis votre serveur Proxmox (shell):

```bash
pct enter <VOTRE_CTID>
```

Remplacez `<VOTRE_CTID>` par l'ID de votre container (par exemple: 100, 101, etc.)

### Étape 2: Exécuter le script de correction

**Option A: Script Complet (Recommandé)**

```bash
# Télécharger le script
wget https://raw.githubusercontent.com/votreuser/gmao-iris/main/fix-proxmox-login.sh

# Rendre exécutable
chmod +x fix-proxmox-login.sh

# Exécuter
./fix-proxmox-login.sh
```

Ce script va:
1. ✅ Diagnostiquer votre installation
2. ✅ Afficher les bases de données MongoDB
3. ✅ Lister les utilisateurs existants
4. ✅ Créer/réinitialiser un compte admin
5. ✅ Redémarrer le backend

**Option B: Script Rapide**

```bash
# Télécharger
wget https://raw.githubusercontent.com/votreuser/gmao-iris/main/quick-create-admin.sh

# Rendre exécutable
chmod +x quick-create-admin.sh

# Exécuter
./quick-create-admin.sh
```

### Étape 3: Créer votre compte admin

Le script vous demandera:
- **Email** (par défaut: admin@gmao-iris.local)
- **Mot de passe** (par défaut: Admin2024!)

Vous pouvez utiliser les valeurs par défaut ou entrer les vôtres.

### Étape 4: Tester la connexion

1. Ouvrez votre navigateur
2. Allez sur l'URL de votre application
3. Connectez-vous avec les identifiants que vous venez de créer

## 🔧 Si ça ne fonctionne toujours pas

### Vérification 1: Le backend fonctionne-t-il ?

```bash
supervisorctl status gmao-iris-backend
```

Si pas `RUNNING`:
```bash
supervisorctl restart gmao-iris-backend
tail -f /var/log/gmao-iris-backend.err.log
```

### Vérification 2: MongoDB fonctionne-t-il ?

```bash
systemctl status mongod
```

Si pas actif:
```bash
systemctl start mongod
```

### Vérification 3: Vérifier manuellement les utilisateurs

```bash
mongosh gmao_iris --eval "db.users.find({}, {email: 1, role: 1, statut: 1})"
```

Cela devrait afficher votre utilisateur avec:
- email: votre email
- role: ADMIN
- statut: actif

### Vérification 4: Les logs backend

```bash
tail -100 /var/log/gmao-iris-backend.out.log
tail -100 /var/log/gmao-iris-backend.err.log
```

## 📝 Création manuelle d'un admin (méthode alternative)

Si les scripts ne fonctionnent pas, utilisez le script Python directement:

```bash
cd /opt/gmao-iris
python3 create_admin.py
```

Suivez les instructions interactives.

## 🔄 Réinstallation complète (dernier recours)

Si rien ne fonctionne, vous pouvez réinstaller avec le **script corrigé**:

1. **Sauvegarder vos données importantes** (si vous en avez)
2. **Détruire l'ancien container:**
   ```bash
   pct stop <CTID>
   pct destroy <CTID>
   ```

3. **Installer avec le script corrigé:**
   ```bash
   wget -qO - https://raw.githubusercontent.com/votreuser/gmao-iris/main/gmao-iris-proxmox.sh | bash
   ```

Le nouveau script créera correctement les utilisateurs dans la bonne base de données.

## 📞 Support

Si vous rencontrez toujours des problèmes après avoir suivi ces étapes:

1. **Collectez les informations suivantes:**
   ```bash
   # Dans le container
   echo "=== Configuration ==="
   cat /opt/gmao-iris/backend/.env
   
   echo "=== Bases MongoDB ==="
   mongosh --quiet --eval "db.adminCommand('listDatabases')"
   
   echo "=== Utilisateurs ==="
   mongosh --quiet gmao_iris --eval "db.users.countDocuments({})"
   
   echo "=== Backend Status ==="
   supervisorctl status gmao-iris-backend
   
   echo "=== Derniers logs ==="
   tail -20 /var/log/gmao-iris-backend.err.log
   ```

2. **Partagez ces informations** pour obtenir de l'aide

---

## ✅ Résumé

**Le problème:** Script d'installation avec base de données hardcodée  
**La solution:** Scripts de correction qui créent les utilisateurs dans la bonne base  
**Après correction:** Vous pourrez vous connecter normalement

**Compte par défaut après correction:**
- Email: admin@gmao-iris.local (ou celui que vous avez choisi)
- Mot de passe: Admin2024! (ou celui que vous avez choisi)
- Rôle: ADMIN avec tous les droits
