# 🔧 Correctif de Connexion Réseau - GMAO Iris

## 📋 Problème résolu

Ce correctif résout le problème de connexion "Email ou mot de passe incorrect" lorsque vous accédez à l'application via:
- **Tailscale** (IP 100.x.x.x)
- **Réseau local** (IP 192.168.x.x ou 10.x.x.x)
- **Redirection de port** depuis votre box Internet

## 🚀 Application du correctif

### Méthode automatique (recommandée)

```bash
cd /app
./apply_network_fix.sh
```

Ce script va:
1. ✅ Créer une sauvegarde automatique
2. ✅ Modifier le fichier `/app/frontend/src/services/api.js`
3. ✅ Redémarrer le frontend
4. ✅ Vérifier que tout fonctionne

**Durée**: ~15 secondes

### Méthode manuelle

Si vous préférez appliquer manuellement:

1. **Sauvegarder l'ancien fichier**:
```bash
cp /app/frontend/src/services/api.js /app/frontend/src/services/api.js.backup
```

2. **Modifier le fichier** `/app/frontend/src/services/api.js`:
   - Remplacer les 4 premières lignes par le code de détection automatique
   - Voir le contenu dans `apply_network_fix.sh`

3. **Redémarrer le frontend**:
```bash
sudo supervisorctl restart frontend
```

## 🔄 Rollback (annuler les modifications)

Si vous souhaitez revenir à l'ancienne configuration:

```bash
cd /app
./rollback_network_fix.sh
```

## ✅ Vérification

Après l'application du correctif:

1. **Accédez à l'application** via votre IP (Tailscale ou réseau local):
   - Exemple: `http://100.105.2.113`
   - Ou: `http://192.168.1.100`

2. **Ouvrez la console du navigateur** (F12):
   - Vous devriez voir: `🔗 Backend URL configurée: http://[votre-ip]:8001`

3. **Connectez-vous**:
   - Email: `admin@gmao-iris.local`
   - Mot de passe: `Admin123!`

## 🎯 Comment ça fonctionne

Le correctif ajoute une **détection automatique intelligente** de l'URL backend:

| Mode d'accès | URL Backend utilisée |
|--------------|---------------------|
| `http://100.x.x.x` (Tailscale) | `http://100.x.x.x:8001` |
| `http://192.168.x.x` (LAN) | `http://192.168.x.x:8001` |
| `http://10.x.x.x` (LAN) | `http://10.x.x.x:8001` |
| `http://localhost` | `http://localhost:8001` |
| Domaine public | `https://github-auth-issue-1.preview.emergentagent.com` |

**Avantages**:
- ✅ Pas de configuration manuelle
- ✅ Fonctionne automatiquement quel que soit le mode d'accès
- ✅ Pas de problèmes de CORS ou Mixed Content
- ✅ Performance optimale (connexion directe en local)

## 📁 Sauvegardes

Les sauvegardes sont créées dans:
```
/app/backups/network_fix_YYYYMMDD_HHMMSS/
```

Chaque sauvegarde contient:
- `api.js.backup` - Version originale du fichier

## 🔍 Dépannage

### Le script échoue

1. Vérifiez les permissions:
```bash
ls -la /app/*.sh
```

2. Rendez les scripts exécutables:
```bash
chmod +x /app/apply_network_fix.sh
chmod +x /app/rollback_network_fix.sh
```

### La connexion ne fonctionne toujours pas

1. **Vérifiez le port 8001**:
```bash
netstat -tuln | grep 8001
```
   Vous devriez voir: `0.0.0.0:8001`

2. **Vérifiez les logs du backend**:
```bash
tail -50 /var/log/supervisor/backend.out.log
```

3. **Vérifiez la console du navigateur** (F12):
   - Cherchez des erreurs en rouge
   - Vérifiez l'URL backend affichée

4. **Redirection de ports**:
   Si vous utilisez une redirection de port sur votre box:
   - Port 3000 → Frontend
   - Port 8001 → Backend (important!)

### Le frontend ne redémarre pas

```bash
# Voir les logs
tail -50 /var/log/supervisor/frontend.err.log

# Redémarrer manuellement
sudo supervisorctl restart frontend

# Vérifier le statut
sudo supervisorctl status frontend
```

## 📞 Support

Pour toute question:
- Documentation: `/app/NETWORK_FIX_README.md`
- Logs backend: `/var/log/supervisor/backend.out.log`
- Logs frontend: `/var/log/supervisor/frontend.err.log`

## 📝 Notes techniques

**Fichier modifié**: `/app/frontend/src/services/api.js`

**Fonction ajoutée**: `getBackendURL()`
- Détecte l'hostname depuis `window.location.hostname`
- Compare avec des patterns d'IP locales (regex)
- Retourne l'URL appropriée

**Pas de modifications backend**: Le backend reste inchangé

**Compatibilité**: React 18+, Axios
