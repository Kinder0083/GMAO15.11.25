# GMAO Atlas - Script d'installation Proxmox LXC

Ce script permet d'installer automatiquement l'application GMAO Atlas dans un conteneur LXC Proxmox.

## Prérequis

- Proxmox VE 7.0 ou supérieur
- Accès SSH root à votre serveur Proxmox
- Au moins 2 Go de RAM et 10 Go d'espace disque disponibles

## Installation automatique

### Étape 1 : Se connecter à Proxmox

Connectez-vous en SSH à votre serveur Proxmox :

```bash
ssh root@votre-serveur-proxmox
```

### Étape 2 : Télécharger et exécuter le script

```bash
wget -O install-gmao-atlas.sh https://raw.githubusercontent.com/VOTRE_REPO/gmao-atlas-clone/main/install-gmao-atlas.sh
chmod +x install-gmao-atlas.sh
./install-gmao-atlas.sh
```

Le script va :
1. Créer un nouveau conteneur LXC (Debian 12)
2. Installer toutes les dépendances nécessaires
3. Configurer Docker et Docker Compose
4. Cloner le dépôt de l'application
5. Démarrer tous les services

### Étape 3 : Accéder à l'application

Une fois l'installation terminée, vous pouvez accéder à l'application via :

```
http://IP_DU_CONTENEUR:3000
```

Le script affichera l'adresse IP à la fin de l'installation.

## Connexion par défaut

**Email** : sophie.martin@gmao.fr  
**Mot de passe** : admin123

## Configuration manuelle

Si vous préférez installer manuellement, suivez ces étapes :

### 1. Créer le conteneur LXC

Dans l'interface Proxmox :
- Cliquez sur "Create CT"
- Template : Debian 12
- RAM : 2048 Mo minimum
- Disk : 10 Go minimum
- Network : Bridge avec IP statique ou DHCP

### 2. Se connecter au conteneur

```bash
pct enter VMID
```

### 3. Installer les dépendances

```bash
apt update && apt upgrade -y
apt install -y git curl wget docker.io docker-compose
systemctl enable docker
systemctl start docker
```

### 4. Cloner le dépôt

```bash
cd /opt
git clone https://github.com/VOTRE_REPO/gmao-atlas-clone.git
cd gmao-atlas-clone
```

### 5. Configurer l'environnement

```bash
cp .env.example .env
# Éditez le fichier .env avec vos paramètres
nano .env
```

### 6. Démarrer l'application

```bash
docker-compose up -d
```

### 7. Vérifier le statut

```bash
docker-compose ps
```

## Gestion de l'application

### Arrêter l'application
```bash
cd /opt/gmao-atlas-clone
docker-compose stop
```

### Démarrer l'application
```bash
cd /opt/gmao-atlas-clone
docker-compose start
```

### Redémarrer l'application
```bash
cd /opt/gmao-atlas-clone
docker-compose restart
```

### Voir les logs
```bash
cd /opt/gmao-atlas-clone
docker-compose logs -f
```

### Mettre à jour l'application
```bash
cd /opt/gmao-atlas-clone
git pull
docker-compose down
docker-compose up -d --build
```

## Sauvegarde et restauration

### Sauvegarder la base de données

```bash
docker exec gmao-mongodb mongodump --out /data/backup
docker cp gmao-mongodb:/data/backup ./backup-$(date +%Y%m%d)
```

### Restaurer la base de données

```bash
docker cp ./backup-20250118 gmao-mongodb:/data/restore
docker exec gmao-mongodb mongorestore /data/restore
```

## Dépannage

### L'application ne démarre pas

1. Vérifiez que Docker fonctionne :
   ```bash
   systemctl status docker
   ```

2. Vérifiez les logs :
   ```bash
   docker-compose logs
   ```

3. Vérifiez que les ports ne sont pas déjà utilisés :
   ```bash
   netstat -tulpn | grep -E '3000|8001|27017'
   ```

### Erreur de connexion à la base de données

1. Vérifiez que MongoDB fonctionne :
   ```bash
   docker-compose ps mongodb
   ```

2. Vérifiez les variables d'environnement :
   ```bash
   cat .env | grep MONGO
   ```

### L'interface ne charge pas

1. Vérifiez que le frontend est accessible :
   ```bash
   curl http://localhost:3000
   ```

2. Vérifiez les logs du frontend :
   ```bash
   docker-compose logs frontend
   ```

## Support

Pour toute question ou problème :
- Créez une issue sur GitHub
- Consultez la documentation complète sur https://docs.gmao-atlas.fr

## Licence

Ce projet est sous licence GPL-3.0. Voir le fichier LICENSE pour plus de détails.
