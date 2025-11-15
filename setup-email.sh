#!/bin/bash

# Script de configuration SMTP pour GMAO IRIS
# Ce script configure l'envoi d'emails pour l'application

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "======================================"
echo "  CONFIGURATION SMTP - GMAO IRIS"
echo "======================================"
echo -e "${NC}"

# Déterminer le chemin du backend
if [ -d "/opt/gmao-iris/backend" ]; then
    BACKEND_DIR="/opt/gmao-iris/backend"
else
    BACKEND_DIR="./backend"
fi

ENV_FILE="$BACKEND_DIR/.env"

echo -e "${YELLOW}Ce script va configurer l'envoi d'emails pour GMAO IRIS.${NC}"
echo ""
echo "Options SMTP disponibles :"
echo "  1. Gmail (smtp.gmail.com) - Gratuit, fiable"
echo "  2. SendGrid (smtp.sendgrid.net) - Service professionnel"
echo "  3. Serveur SMTP personnalisé"
echo "  4. Serveur local (nécessite Postfix)"
echo ""

read -p "Choisissez une option (1-4) : " smtp_choice

case $smtp_choice in
    1)
        echo -e "${GREEN}Configuration Gmail sélectionnée${NC}"
        SMTP_SERVER="smtp.gmail.com"
        SMTP_PORT="587"
        SMTP_USE_TLS="true"
        
        echo ""
        echo -e "${YELLOW}Pour Gmail, vous devez créer un mot de passe d'application :${NC}"
        echo "1. Allez sur : https://myaccount.google.com/apppasswords"
        echo "2. Créez un nouveau mot de passe d'application"
        echo "3. Copiez le mot de passe généré (16 caractères)"
        echo ""
        
        read -p "Votre adresse Gmail : " gmail_address
        read -s -p "Votre mot de passe d'application Gmail : " gmail_password
        echo ""
        
        SMTP_USERNAME="$gmail_address"
        SMTP_PASSWORD="$gmail_password"
        SMTP_SENDER_EMAIL="$gmail_address"
        SMTP_FROM="$gmail_address"
        ;;
    
    2)
        echo -e "${GREEN}Configuration SendGrid sélectionnée${NC}"
        SMTP_SERVER="smtp.sendgrid.net"
        SMTP_PORT="587"
        SMTP_USE_TLS="true"
        
        read -p "Votre adresse email SendGrid : " sendgrid_email
        read -s -p "Votre clé API SendGrid : " sendgrid_key
        echo ""
        
        SMTP_USERNAME="apikey"
        SMTP_PASSWORD="$sendgrid_key"
        SMTP_SENDER_EMAIL="$sendgrid_email"
        SMTP_FROM="$sendgrid_email"
        ;;
    
    3)
        echo -e "${GREEN}Configuration serveur SMTP personnalisé${NC}"
        
        read -p "Hôte SMTP : " custom_host
        read -p "Port SMTP (défaut 587) : " custom_port
        custom_port=${custom_port:-587}
        read -p "Utiliser TLS ? (y/n, défaut y) : " use_tls
        use_tls=${use_tls:-y}
        
        if [[ $use_tls == "y" || $use_tls == "Y" ]]; then
            SMTP_USE_TLS="true"
        else
            SMTP_USE_TLS="false"
        fi
        
        read -p "Nom d'utilisateur SMTP : " smtp_user
        read -s -p "Mot de passe SMTP : " smtp_pass
        echo ""
        read -p "Adresse email d'envoi : " smtp_from
        
        SMTP_SERVER="$custom_host"
        SMTP_PORT="$custom_port"
        SMTP_USERNAME="$smtp_user"
        SMTP_PASSWORD="$smtp_pass"
        SMTP_SENDER_EMAIL="$smtp_from"
        SMTP_FROM="$smtp_from"
        ;;
    
    4)
        echo -e "${GREEN}Configuration serveur local sélectionnée${NC}"
        echo -e "${YELLOW}Note : Vous devez avoir Postfix installé et configuré${NC}"
        
        SMTP_SERVER="localhost"
        SMTP_PORT="25"
        SMTP_USE_TLS="false"
        SMTP_USERNAME=""
        SMTP_PASSWORD=""
        
        read -p "Adresse email d'envoi (ex: noreply@gmao-iris.local) : " local_from
        SMTP_SENDER_EMAIL="$local_from"
        SMTP_FROM="$local_from"
        ;;
    
    *)
        echo -e "${RED}Option invalide${NC}"
        exit 1
        ;;
esac

echo ""
read -p "Nom de l'expéditeur (ex: GMAO Iris) : " from_name
SMTP_FROM_NAME="${from_name:-GMAO Iris}"

read -p "URL de l'application (ex: http://192.168.1.104) : " app_url
APP_URL="${app_url:-http://localhost:3000}"

echo ""
echo -e "${BLUE}Configuration SMTP :${NC}"
echo "  Serveur : $SMTP_SERVER:$SMTP_PORT"
echo "  TLS : $SMTP_USE_TLS"
echo "  Email : $SMTP_FROM"
echo "  Nom : $SMTP_FROM_NAME"
echo "  URL App : $APP_URL"
echo ""

read -p "Confirmer la configuration ? (y/n) : " confirm
if [[ $confirm != "y" && $confirm != "Y" ]]; then
    echo -e "${RED}Configuration annulée${NC}"
    exit 1
fi

# Mettre à jour le fichier .env
echo -e "${BLUE}Mise à jour du fichier .env...${NC}"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}Fichier .env non trouvé, création depuis .env.example${NC}"
    cp "$BACKEND_DIR/.env.example" "$ENV_FILE"
fi

# Fonction pour mettre à jour ou ajouter une variable
update_env_var() {
    local key=$1
    local value=$2
    
    if grep -q "^$key=" "$ENV_FILE"; then
        # Variable existe, la mettre à jour
        sed -i "s|^$key=.*|$key=$value|" "$ENV_FILE"
    else
        # Variable n'existe pas, l'ajouter
        echo "$key=$value" >> "$ENV_FILE"
    fi
}

# Mettre à jour les variables SMTP
update_env_var "SMTP_SERVER" "$SMTP_SERVER"
update_env_var "SMTP_HOST" "$SMTP_SERVER"
update_env_var "SMTP_PORT" "$SMTP_PORT"
update_env_var "SMTP_USERNAME" "$SMTP_USERNAME"
update_env_var "SMTP_PASSWORD" "$SMTP_PASSWORD"
update_env_var "SMTP_SENDER_EMAIL" "$SMTP_SENDER_EMAIL"
update_env_var "SMTP_FROM" "$SMTP_FROM"
update_env_var "SMTP_FROM_NAME" "$SMTP_FROM_NAME"
update_env_var "SMTP_USER" "$SMTP_USERNAME"
update_env_var "SMTP_USE_TLS" "$SMTP_USE_TLS"
update_env_var "APP_URL" "$APP_URL"

echo -e "${GREEN}✅ Fichier .env mis à jour${NC}"

# Redémarrer le backend si supervisor est configuré
if command -v supervisorctl &> /dev/null; then
    echo -e "${BLUE}Redémarrage du backend...${NC}"
    
    # Chercher le nom du processus backend
    if supervisorctl status | grep -q "gmao-iris-backend"; then
        sudo supervisorctl restart gmao-iris-backend
        echo -e "${GREEN}✅ Backend redémarré${NC}"
    elif supervisorctl status | grep -q "backend"; then
        sudo supervisorctl restart backend
        echo -e "${GREEN}✅ Backend redémarré${NC}"
    else
        echo -e "${YELLOW}⚠️  Processus backend non trouvé dans supervisor${NC}"
        echo "   Redémarrez manuellement le backend"
    fi
else
    echo -e "${YELLOW}⚠️  Supervisor non trouvé${NC}"
    echo "   Redémarrez manuellement le backend"
fi

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  CONFIGURATION SMTP TERMINÉE${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo "Pour tester l'envoi d'emails :"
echo "  1. Connectez-vous à l'application en tant qu'admin"
echo "  2. Allez dans Équipes → Inviter un membre"
echo "  3. Envoyez une invitation à une adresse email de test"
echo ""
echo "Les logs backend se trouvent dans :"
echo "  /var/log/gmao-iris-backend.out.log (succès)"
echo "  /var/log/gmao-iris-backend.err.log (erreurs)"
echo ""
