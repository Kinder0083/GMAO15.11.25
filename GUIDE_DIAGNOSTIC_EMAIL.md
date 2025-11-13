# Guide de diagnostic et correction du service email

## 🎯 Problème
Les invitations par email fonctionnent sur l'environnement de développement Emergent mais pas sur votre container Proxmox.

## 📋 Scripts créés

J'ai créé 3 scripts de diagnostic et correction, similaires à ceux d'hier pour MongoDB :

### 1. `check-email-service.sh` - Script de diagnostic
Vérifie tous les aspects du service email

### 2. `test-backend-email.py` - Test d'envoi Python
Teste l'envoi d'email via le code Python (comme le backend)

### 3. `fix-email-service.sh` - Script de correction automatique
Corrige automatiquement les problèmes détectés

---

## 🔍 ÉTAPE 1 : Copier les scripts sur votre container

Sur votre **machine locale**, copiez les scripts vers le container :

```bash
# Depuis votre machine locale
scp /chemin/vers/check-email-service.sh root@VOTRE_IP_PROXMOX:/opt/gmao-iris/
scp /chemin/vers/test-backend-email.py root@VOTRE_IP_PROXMOX:/opt/gmao-iris/
scp /chemin/vers/fix-email-service.sh root@VOTRE_IP_PROXMOX:/opt/gmao-iris/
```

**OU** créez-les directement sur le container :

```bash
# Connectez-vous au container
ssh root@VOTRE_IP_PROXMOX

# Les scripts sont dans /app/ sur Emergent, copiez-les vers /opt/gmao-iris/
```

---

## 🔍 ÉTAPE 2 : Diagnostic complet

Sur votre **container Proxmox**, exécutez le script de diagnostic :

```bash
cd /opt/gmao-iris
bash check-email-service.sh
```

### Ce que le script vérifie :

1. ✅ **Installation de Postfix** : Est-il installé ?
2. ✅ **Service Postfix actif** : Est-il en cours d'exécution ?
3. ✅ **Auto-démarrage** : Démarre-t-il au boot ?
4. ✅ **Port SMTP 25** : Est-il en écoute ?
5. ✅ **Variables d'environnement** : Le fichier .env contient-il les configs SMTP ?
6. ✅ **Logs Postfix** : Y a-t-il des erreurs ?
7. ✅ **File d'attente** : Des emails sont-ils bloqués ?
8. ✅ **Test d'envoi simple** : Peut-on envoyer un email ?
9. ✅ **Configuration Postfix** : Les paramètres sont-ils corrects ?

### Résultat attendu :

Le script vous donnera un résumé comme :
```
✅ Aucun problème critique détecté
```

**OU**

```
❌ 3 problème(s) détecté(s)
❌ Service Postfix arrêté
❌ Port SMTP 25 non en écoute
❌ Fichier .env backend manquant
```

---

## 🔧 ÉTAPE 3 : Correction automatique

Si des problèmes sont détectés, exécutez le script de correction :

```bash
cd /opt/gmao-iris
sudo bash fix-email-service.sh
```

### Ce que fait le script de correction :

1. **Installe Postfix** (si nécessaire)
2. **Configure Postfix** pour envoi local
3. **Redémarre le service**
4. **Active le démarrage automatique**
5. **Vérifie les permissions des logs**
6. **Nettoie la file d'attente**
7. **Ajoute les variables SMTP au .env** (si manquantes)
8. **Teste l'envoi d'un email**

### Après la correction :

```bash
# Redémarrer le backend pour prendre en compte les nouvelles configs
sudo supervisorctl restart backend

# Attendre 3 secondes
sleep 3

# Vérifier que le backend a bien redémarré
sudo supervisorctl status backend
```

---

## 🧪 ÉTAPE 4 : Test d'envoi Python

Testez l'envoi d'email exactement comme le fait le backend :

```bash
cd /opt/gmao-iris
python3 test-backend-email.py
```

### Ce que fait le script :

1. **Charge les variables .env** du backend
2. **Vérifie toutes les variables SMTP**
3. **Teste la connexion au serveur SMTP**
4. **Envoie un email de test** (vous demande l'adresse)

### Exemple d'exécution :

```
============================================================
1. VÉRIFICATION VARIABLES D'ENVIRONNEMENT
============================================================
✅ SMTP_HOST = localhost
✅ SMTP_PORT = 25
✅ SMTP_FROM = noreply@gmao-iris.local
✅ SMTP_FROM_NAME = GMAO IRIS
✅ APP_URL = http://100.105.2.113

============================================================
2. TEST CONNEXION SERVEUR SMTP
============================================================
   Connexion à localhost:25...
✅ Connexion établie avec localhost:25

============================================================
3. ENVOI EMAIL DE TEST
============================================================
Entrez l'adresse email pour le test (ou Enter pour test@example.com) :
Email: votre.email@example.com
   Envoi à votre.email@example.com...
✅ Email envoyé avec succès à votre.email@example.com
   Vérifiez la boîte de réception (et les spams)
```

---

## 🔎 ÉTAPE 5 : Vérifier les logs

Si l'email n'arrive toujours pas, vérifiez les logs :

### Logs Postfix (temps réel) :
```bash
tail -f /var/log/mail.log
```

### Logs backend (temps réel) :
```bash
tail -f /var/log/supervisor/backend.err.log
```

### Logs système :
```bash
journalctl -u postfix -n 50
```

### File d'attente des emails :
```bash
mailq
```

---

## 🧰 Problèmes courants et solutions

### Problème 1 : "Service Postfix arrêté"
```bash
sudo systemctl start postfix
sudo systemctl enable postfix
sudo systemctl status postfix
```

### Problème 2 : "Port 25 non en écoute"
```bash
# Vérifier si un autre processus utilise le port
sudo netstat -tuln | grep :25
sudo lsof -i :25

# Redémarrer Postfix
sudo systemctl restart postfix
```

### Problème 3 : "Permission denied" sur les logs
```bash
sudo chmod 644 /var/log/mail.log
sudo chown syslog:adm /var/log/mail.log
```

### Problème 4 : "Variables SMTP manquantes dans .env"
```bash
# Éditer le fichier
nano /opt/gmao-iris/backend/.env

# Ajouter ces lignes :
SMTP_HOST=localhost
SMTP_PORT=25
SMTP_FROM=noreply@gmao-iris.local
SMTP_FROM_NAME=GMAO IRIS
APP_URL=http://VOTRE_IP_TAILSCALE

# Redémarrer le backend
sudo supervisorctl restart backend
```

### Problème 5 : "Emails bloqués dans la file d'attente"
```bash
# Voir la file d'attente
mailq

# Vider la file d'attente
sudo postsuper -d ALL

# Relancer l'envoi
sudo postqueue -f
```

---

## 🧪 Test final avec l'application

Une fois tout corrigé, testez l'invitation depuis l'application :

1. Connectez-vous à GMAO IRIS en tant qu'admin
2. Allez dans **Équipes**
3. Cliquez sur **"Inviter un membre"**
4. Remplissez le formulaire :
   - Nom : Test
   - Prénom : Email
   - Email : **votre.email@example.com**
   - Rôle : VISUALISEUR
5. Cliquez sur **"Envoyer l'invitation"**

### Vérifications :

1. **Message de succès** dans l'interface
2. **Log backend** : `Email envoyé avec succès à votre.email@example.com`
3. **Email reçu** (vérifier les spams)
4. **Lien d'invitation** fonctionnel

---

## 📊 Checklist de validation

- [ ] Script de diagnostic exécuté
- [ ] Aucun problème critique détecté (ou corrigé)
- [ ] Service Postfix actif
- [ ] Port 25 en écoute
- [ ] Variables SMTP dans .env
- [ ] Test Python réussi
- [ ] Email de test reçu
- [ ] Invitation depuis l'app fonctionnelle
- [ ] Email d'invitation reçu
- [ ] Lien d'invitation fonctionnel

---

## 🆘 Si rien ne fonctionne

Exécutez cette commande et envoyez-moi le résultat complet :

```bash
cd /opt/gmao-iris
bash check-email-service.sh > diagnostic-email.txt 2>&1
python3 test-backend-email.py >> diagnostic-email.txt 2>&1
cat diagnostic-email.txt
```

Cela nous permettra de voir exactement où se situe le problème.

---

## 📝 Notes importantes

- **Postfix** fonctionne en mode **"local only"** pour éviter d'être un relais SMTP ouvert
- Les emails sont envoyés depuis **localhost** vers des destinations externes
- Si votre FAI bloque le port 25, les emails peuvent ne pas sortir (vérifier avec votre FAI)
- Les emails peuvent atterrir dans les **spams** lors des premiers envois

---

**Tous les scripts sont prêts ! Exécutez-les sur votre container Proxmox pour diagnostiquer et corriger le problème d'envoi d'emails. 🚀**
