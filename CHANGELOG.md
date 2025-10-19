# GMAO Iris - Notes de Version

## Version 1.0.1 - CORRECTION CRITIQUE (Octobre 2025)

### 🔴 CORRECTION CRITIQUE - BUG LOGIN PROXMOX

**Problème Identifié:**
Le script Proxmox (`gmao-iris-proxmox.sh`) contenait une **erreur critique** qui empêchait la connexion sur les installations Proxmox :
- Ligne 344: `db = client.gmao_iris` (nom de base de données EN DUR)
- L'application utilisait `db = client[os.environ.get('DB_NAME')]`
- **Résultat:** Les utilisateurs étaient créés dans une base mais l'application les cherchait dans une autre

### ✅ Solutions Appliquées

#### 1. **Script Proxmox Corrigé** (`gmao-iris-proxmox.sh`)
- ✅ Remplacement de `db = client.gmao_iris` par `db = client[db_name]`
- ✅ Ajout du chargement des variables d'environnement
- ✅ Export explicite de `MONGO_URL` et `DB_NAME` lors de l'exécution
- ✅ Utilisation cohérente de la configuration

#### 2. **Scripts de Réparation Créés**
- ✅ `fix-proxmox-login.sh` : Diagnostic complet et correction
- ✅ `quick-create-admin.sh` : Création rapide d'admin

#### 3. **Utilisation des Scripts de Réparation**

**Sur votre serveur Proxmox, depuis le HOST:**
```bash
# Entrer dans le container
pct enter <CTID>

# Télécharger et exécuter le script de correction
wget https://raw.githubusercontent.com/votreuser/gmao-iris/main/fix-proxmox-login.sh
chmod +x fix-proxmox-login.sh
./fix-proxmox-login.sh
```

**OU version rapide:**
```bash
pct enter <CTID>
wget https://raw.githubusercontent.com/votreuser/gmao-iris/main/quick-create-admin.sh
chmod +x quick-create-admin.sh
./quick-create-admin.sh
```

### 🔍 Diagnostic
Le script de correction effectue:
1. Vérification de la configuration (.env)
2. Vérification de MongoDB et des bases de données
3. Comptage des utilisateurs existants
4. Création/réinitialisation du compte admin
5. Redémarrage du backend

---

## Version 1.0.0 - Corrections Critiques Login & Proxmox (Octobre 2025)

### 🔧 Corrections Critiques

#### 1. **Correction de la Création d'Utilisateurs**
- **Problème:** Les utilisateurs créés via le script Proxmox n'avaient pas tous les champs requis
- **Solution:** 
  - Ajout du champ `id` (UUID) obligatoire
  - Ajout du champ `statut` avec valeur "actif" (remplace `actif: True`)
  - Ajout du champ `service` (nullable)
  - Correction de `derniereConnexion` pour utiliser datetime au lieu de None
  
#### 2. **Configuration MongoDB**
- **Problème:** MONGO_URL contenait le nom de la base de données
- **Solution:**
  - Séparation de `MONGO_URL` et `DB_NAME` dans `.env`
  - `MONGO_URL=mongodb://localhost:27017`
  - `DB_NAME=gmao_iris`

#### 3. **Script Proxmox (`gmao-iris-proxmox.sh`)**
- Correction de la création d'utilisateurs avec tous les champs requis
- Ajout de la gestion des IDs avec UUID
- Correction du format des permissions
- Meilleure gestion des utilisateurs existants (mise à jour vs création)
- Création automatique d'un compte de secours:
  - Email: `buenogy@gmail.com`
  - Mot de passe: `Admin2024!`

#### 4. **Fichiers Backend**
- `server.py`: Ajout de logs de débogage pour le login (temporaires)
- `models.py`: Vérification des modèles Pydantic
- `.env.example`: Création d'un template pour la configuration

#### 5. **Fichiers Frontend**
- `.env.example`: Création d'un template pour la configuration
- `Login.jsx`: Interface mise à jour avec branding "GMAO Iris"

### 📝 Nouveaux Scripts

#### `create_admin.py` (Racine du projet)
Script interactif pour créer des administrateurs manuellement:
```bash
python3 create_admin.py
```

Fonctionnalités:
- Création interactive d'administrateurs
- Validation des emails et mots de passe
- Gestion des utilisateurs existants (mise à jour)
- Compatible avec la structure MongoDB complète

### 📚 Documentation

#### `INSTALLATION_PROXMOX_COMPLET.md`
Guide complet d'installation incluant:
- Installation automatique via script
- Installation manuelle étape par étape
- Configuration SSL avec Let's Encrypt
- Gestion et maintenance du container
- Dépannage et résolution de problèmes
- Procédures de sauvegarde

### ✅ Tests Validés

1. **Création d'utilisateurs:** ✅
   - Via script Proxmox
   - Via `create_admin.py`
   - Via l'interface web

2. **Login:** ✅
   - Authentification backend
   - Authentification frontend
   - Stockage du token
   - Navigation après login

3. **MongoDB:** ✅
   - Connexion correcte
   - Base de données `gmao_iris`
   - Structure des documents utilisateurs

### 🔐 Sécurité

**Important:** Après l'installation Proxmox:
1. Changez le mot de passe du compte de secours `buenogy@gmail.com`
2. Ou supprimez ce compte si non nécessaire
3. Générez une nouvelle `SECRET_KEY` en production:
   ```bash
   openssl rand -hex 32
   ```

### 🚀 Déploiement

#### Proxmox
```bash
wget -qO - https://raw.githubusercontent.com/votreuser/gmao-iris/main/gmao-iris-proxmox.sh | bash
```

#### Docker (À venir)
Documentation Docker à compléter dans une prochaine version.

### 📋 Structure de la Base de Données

#### Collection `users`
```javascript
{
  "_id": ObjectId("..."),
  "id": "uuid-string",           // UUID v4
  "email": "user@example.com",
  "password": "bcrypt-hash",
  "prenom": "John",
  "nom": "Doe",
  "role": "ADMIN|TECHNICIEN|VISUALISEUR",
  "telephone": "+33612345678",
  "service": "IT",               // Nullable
  "statut": "actif|inactif",
  "dateCreation": ISODate("..."),
  "derniereConnexion": ISODate("..."),
  "permissions": {
    "dashboard": {"view": true, "edit": true, "delete": true},
    "workOrders": {"view": true, "edit": true, "delete": true},
    "assets": {"view": true, "edit": true, "delete": true},
    "preventiveMaintenance": {"view": true, "edit": true, "delete": true},
    "inventory": {"view": true, "edit": true, "delete": true},
    "locations": {"view": true, "edit": true, "delete": true},
    "vendors": {"view": true, "edit": true, "delete": true},
    "reports": {"view": true, "edit": true, "delete": true}
  }
}
```

### 🐛 Bugs Connus

Aucun bug critique connu à ce jour.

### 📞 Support

Pour toute question:
1. Consultez `INSTALLATION_PROXMOX_COMPLET.md`
2. Vérifiez les logs: `/var/log/gmao-iris-backend.*.log`
3. Ouvrez une issue sur GitHub

---

## Versions Précédentes

### Version 0.9
- Interface utilisateur complète
- Gestion des ordres de travail
- Gestion des équipements
- Maintenance préventive
- Gestion d'inventaire
- Rapports et analytics

---

**Développé par:** Grèg  
**License:** Propriétaire  
**Contact:** support@gmao-iris.local
