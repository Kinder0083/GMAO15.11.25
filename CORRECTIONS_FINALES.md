# Corrections finales - Scripts d'installation

## ✅ Corrections effectuées

### 1. URL de l'application automatique

**Problème :** L'URL demandée était générique (localhost:3000) au lieu de l'IP du container

**Solution :** 
- Le script d'installation passe maintenant l'IP du container (`CONTAINER_IP`) au script `setup-email.sh`
- Le script `setup-email.sh` utilise automatiquement cette IP comme valeur par défaut

**Avant :**
```
URL de l'application (ex: http://192.168.1.104) : 
# Défaut: http://localhost:3000
```

**Après :**
```
URL de l'application (ex: http://192.168.1.104) [http://192.168.1.105] : 
# Défaut: http://IP_DU_CONTAINER (détectée automatiquement)
```

### 2. Suppression des commandes sudo

**Problème :** Les commandes `sudo` causaient des erreurs car :
- Le script s'exécute déjà en root dans le container
- `sudo` n'est pas installé par défaut dans les containers LXC

**Solution :** 
- Suppression de tous les `sudo` du script `setup-email.sh`

**Modifications :**
```bash
# AVANT
sudo supervisorctl restart gmao-iris-backend

# APRÈS
supervisorctl restart gmao-iris-backend
```

---

## 📦 Fichiers modifiés

1. **`gmao-iris-v1.1.2-install-auto.sh`**
   - Passage de la variable `CONTAINER_IP` au script setup-email.sh
   ```bash
   pct exec $CTID -- bash -c "cd /opt/gmao-iris && CONTAINER_IP=${CONTAINER_IP} bash setup-email.sh"
   ```

2. **`setup-email.sh`**
   - Utilisation de `$CONTAINER_IP` pour l'URL par défaut
   - Suppression de tous les `sudo`

---

## 🧪 Test du comportement

### Scénario 1 : Installation normale

```bash
# 1. Exécuter l'installation
bash gmao-iris-v1.1.2-install-auto.sh

# 2. Container créé avec IP 192.168.1.105

# 3. Configuration SMTP demandée
Voulez-vous configurer le SMTP maintenant ? (y/n) : y

# 4. URL proposée automatiquement
URL de l'application (ex: http://192.168.1.104) [http://192.168.1.105] : 
# ↑ L'IP du container est déjà remplie !
# L'utilisateur appuie juste sur Entrée
```

### Scénario 2 : DHCP sans IP détectée

```bash
# Si DHCP et pas d'IP détectée
URL de l'application (ex: http://192.168.1.104) [http://localhost:3000] : 
# Fallback sur localhost:3000
```

---

## ✅ Avantages

1. **Zéro configuration manuelle** : L'IP est déjà remplie
2. **Pas d'erreur sudo** : Fonctionne dans tous les containers LXC
3. **Expérience utilisateur améliorée** : Moins de questions, plus d'automatisation

---

## 🚀 Prêt pour GitHub

Les corrections sont complètes. Le script est maintenant :
- ✅ 100% automatique pour l'URL
- ✅ Compatible avec tous les containers LXC
- ✅ Sans erreurs sudo
- ✅ Expérience utilisateur optimale

**Prêt à être poussé sur GitHub !**
