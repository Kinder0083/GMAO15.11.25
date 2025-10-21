#!/bin/bash
###############################################################################
# Configuration automatique de Postfix pour GMAO Iris
# Ce script installe et configure Postfix comme serveur SMTP local
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"; }
error() { echo -e "${RED}[$(date +'%H:%M:%S')] ERREUR:${NC} $1"; }
warn() { echo -e "${YELLOW}[$(date +'%H:%M:%S')] ATTENTION:${NC} $1"; }
info() { echo -e "${BLUE}[$(date +'%H:%M:%S')] INFO:${NC} $1"; }

clear
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Configuration Automatique Postfix - GMAO Iris             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Vérifier qu'on est root
if [ "$EUID" -ne 0 ]; then 
    error "Ce script doit être exécuté en tant que root"
    exit 1
fi

log "📧 Installation et configuration de Postfix..."

# Déterminer le hostname
HOSTNAME=$(hostname)
DOMAIN="${HOSTNAME}.local"

info "Hostname: $HOSTNAME"
info "Domain: $DOMAIN"

# Préparer les réponses pour l'installation non-interactive
export DEBIAN_FRONTEND=noninteractive

# Préconfigurer Postfix
log "Préconfiguration de Postfix..."
debconf-set-selections <<< "postfix postfix/mailname string $DOMAIN"
debconf-set-selections <<< "postfix postfix/main_mailer_type string 'Internet Site'"

# Installer Postfix et mailutils
log "Installation de Postfix et mailutils..."
apt-get update -qq
apt-get install -y -qq postfix mailutils libsasl2-2 ca-certificates libsasl2-modules

# Créer une sauvegarde de la config existante
if [ -f /etc/postfix/main.cf ]; then
    log "Sauvegarde de la configuration existante..."
    cp /etc/postfix/main.cf /etc/postfix/main.cf.backup.$(date +%Y%m%d_%H%M%S)
fi

# Configuration de base de Postfix
log "Configuration de Postfix..."
cat > /etc/postfix/main.cf << EOF
# Configuration Postfix pour GMAO Iris
# Générée automatiquement le $(date)

# Paramètres de base
smtpd_banner = \$myhostname ESMTP \$mail_name
biff = no
append_dot_mydomain = no
readme_directory = no

# Compatibilité TLS
compatibility_level = 2

# Nom du serveur
myhostname = $HOSTNAME
mydomain = $DOMAIN
myorigin = \$mydomain

# Interfaces réseau
inet_interfaces = loopback-only
inet_protocols = ipv4

# Destinations acceptées
mydestination = \$myhostname, localhost.\$mydomain, localhost
relayhost = 
mynetworks = 127.0.0.0/8 [::ffff:127.0.0.0]/104 [::1]/128

# Limitations de taille
mailbox_size_limit = 0
message_size_limit = 52428800
recipient_delimiter = +

# Configuration alias
alias_maps = hash:/etc/aliases
alias_database = hash:/etc/aliases

# Paramètres de livraison locale
home_mailbox = Maildir/
mailbox_command = 

# Sécurité et relais
smtpd_relay_restrictions = permit_mynetworks, permit_sasl_authenticated, defer_unauth_destination

# Timeouts
smtp_connection_cache_time_limit = 4s
EOF

# Mettre à jour les aliases
log "Configuration des aliases..."
if ! grep -q "root:" /etc/aliases; then
    echo "root: admin" >> /etc/aliases
fi
newaliases

# Démarrer Postfix
log "Démarrage de Postfix..."
postfix start 2>/dev/null || postfix reload

# Vérifier que Postfix fonctionne
sleep 2
if postfix status > /dev/null 2>&1; then
    log "✅ Postfix démarré avec succès"
else
    error "Échec du démarrage de Postfix"
    exit 1
fi

# Configuration du backend GMAO Iris
log "Configuration du backend GMAO Iris..."

BACKEND_ENV="/app/backend/.env"

if [ -f "$BACKEND_ENV" ]; then
    # Sauvegarder l'ancien .env
    cp "$BACKEND_ENV" "${BACKEND_ENV}.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Mettre à jour les paramètres SMTP
    sed -i 's|^SMTP_SERVER=.*|SMTP_SERVER="localhost"|' "$BACKEND_ENV"
    sed -i 's|^SMTP_PORT=.*|SMTP_PORT="25"|' "$BACKEND_ENV"
    sed -i 's|^SMTP_USERNAME=.*|SMTP_USERNAME=""|' "$BACKEND_ENV"
    sed -i 's|^SMTP_PASSWORD=.*|SMTP_PASSWORD=""|' "$BACKEND_ENV"
    sed -i 's|^SMTP_USE_TLS=.*|SMTP_USE_TLS="false"|' "$BACKEND_ENV"
    
    # Si les variables n'existent pas, les ajouter
    if ! grep -q "^SMTP_SERVER=" "$BACKEND_ENV"; then
        echo 'SMTP_SERVER="localhost"' >> "$BACKEND_ENV"
    fi
    if ! grep -q "^SMTP_PORT=" "$BACKEND_ENV"; then
        echo 'SMTP_PORT="25"' >> "$BACKEND_ENV"
    fi
    if ! grep -q "^SMTP_USE_TLS=" "$BACKEND_ENV"; then
        echo 'SMTP_USE_TLS="false"' >> "$BACKEND_ENV"
    fi
    
    log "✅ Configuration backend mise à jour"
else
    error "Fichier .env du backend non trouvé : $BACKEND_ENV"
    exit 1
fi

# Adapter email_service.py pour supporter Postfix local
log "Adaptation du service email..."

EMAIL_SERVICE="/app/backend/email_service.py"

if [ -f "$EMAIL_SERVICE" ]; then
    # Créer une sauvegarde
    cp "$EMAIL_SERVICE" "${EMAIL_SERVICE}.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Créer la nouvelle version
    cat > "$EMAIL_SERVICE" << 'PYEOF'
"""
Service d'envoi d'emails pour GMAO Iris
Support SMTP local (Postfix) et externe (Gmail, SendGrid, etc.)
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Configuration depuis .env
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'localhost')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '25'))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_SENDER_EMAIL = os.environ.get('SMTP_SENDER_EMAIL', 'noreply@gmao-iris.com')
SMTP_FROM_NAME = os.environ.get('SMTP_FROM_NAME', 'GMAO Iris')
SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'false').lower() == 'true'
APP_URL = os.environ.get('APP_URL', 'http://localhost')


def send_email(to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
    """
    Envoie un email via SMTP (local ou externe)
    
    Args:
        to_email: Email du destinataire
        subject: Sujet de l'email
        html_content: Contenu HTML de l'email
        text_content: Contenu texte alternatif (optionnel)
    
    Returns:
        bool: True si envoi réussi, False sinon
    """
    try:
        # Créer le message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{SMTP_FROM_NAME} <{SMTP_SENDER_EMAIL}>"
        msg['To'] = to_email
        
        # Ajouter version texte si fournie
        if text_content:
            part_text = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(part_text)
        
        # Ajouter version HTML
        part_html = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part_html)
        
        # Déterminer le mode de connexion
        is_local = SMTP_SERVER in ['localhost', '127.0.0.1']
        needs_auth = bool(SMTP_USERNAME and SMTP_PASSWORD)
        
        logger.info(f"📧 Envoi email via {SMTP_SERVER}:{SMTP_PORT} (Local: {is_local}, Auth: {needs_auth})")
        
        # Connexion SMTP
        if is_local:
            # Postfix local : connexion simple sans TLS ni authentification
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
            server.send_message(msg)
            server.quit()
        elif SMTP_USE_TLS:
            # SMTP externe avec TLS (port 587)
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()
            if needs_auth:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
        else:
            # SMTP externe avec SSL (port 465)
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10)
            if needs_auth:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
        
        logger.info(f"✅ Email envoyé avec succès à {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"❌ Erreur d'authentification SMTP: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"❌ Erreur SMTP lors de l'envoi à {to_email}: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Erreur inattendue lors de l'envoi à {to_email}: {e}")
        return False
PYEOF
    
    # Garder les fonctions d'envoi d'invitation et de compte
    cat >> "$EMAIL_SERVICE" << 'PYEOF'


def send_invitation_email(to_email: str, token: str, role: str) -> bool:
    """
    Envoie un email d'invitation à rejoindre GMAO Iris
    
    Args:
        to_email: Email du destinataire
        token: Token d'invitation JWT
        role: Rôle attribué (ADMIN, TECHNICIEN, VISUALISEUR)
    
    Returns:
        bool: True si envoi réussi
    """
    invitation_link = f"{APP_URL}/inscription?token={token}"
    
    role_labels = {
        "ADMIN": "Administrateur",
        "TECHNICIEN": "Technicien",
        "VISUALISEUR": "Visualiseur"
    }
    role_label = role_labels.get(role, role)
    
    subject = "Invitation à rejoindre GMAO Iris"
    
    # Version HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #2563eb;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 8px 8px 0 0;
            }}
            .content {{
                background-color: #f9fafb;
                padding: 30px;
                border-radius: 0 0 8px 8px;
            }}
            .button {{
                display: inline-block;
                padding: 12px 30px;
                background-color: #2563eb;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                margin: 20px 0;
            }}
            .footer {{
                margin-top: 20px;
                text-align: center;
                font-size: 12px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔧 GMAO Iris</h1>
            </div>
            <div class="content">
                <h2>Bonjour,</h2>
                <p>Vous avez été invité(e) à rejoindre <strong>GMAO Iris</strong> en tant que <strong>{role_label}</strong>.</p>
                
                <p>Pour compléter votre inscription, cliquez sur le bouton ci-dessous :</p>
                
                <div style="text-align: center;">
                    <a href="{invitation_link}" class="button">Compléter mon inscription</a>
                </div>
                
                <p style="font-size: 12px; color: #666;">
                    Si le bouton ne fonctionne pas, copiez et collez ce lien dans votre navigateur :<br>
                    <a href="{invitation_link}">{invitation_link}</a>
                </p>
                
                <p><strong>⚠️ Important :</strong> Ce lien expire dans 7 jours.</p>
                
                <p>Cordialement,<br>L'équipe GMAO Iris</p>
            </div>
            <div class="footer">
                <p>Ceci est un email automatique, merci de ne pas y répondre.</p>
                <p>© 2025 GMAO Iris - Tous droits réservés</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Version texte
    text_content = f"""
Bonjour,

Vous avez été invité(e) à rejoindre GMAO Iris en tant que {role_label}.

Pour compléter votre inscription, cliquez sur le lien ci-dessous :
{invitation_link}

Ce lien expire dans 7 jours.

Cordialement,
L'équipe GMAO Iris

---
Ceci est un email automatique, merci de ne pas y répondre.
© 2025 GMAO Iris - Tous droits réservés
    """
    
    return send_email(to_email, subject, html_content, text_content)


def send_account_created_email(to_email: str, temp_password: str, prenom: str) -> bool:
    """
    Envoie un email avec les identifiants temporaires
    
    Args:
        to_email: Email du destinataire
        temp_password: Mot de passe temporaire
        prenom: Prénom de l'utilisateur
    
    Returns:
        bool: True si envoi réussi
    """
    subject = "Votre compte GMAO Iris a été créé"
    
    # Version HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #2563eb;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 8px 8px 0 0;
            }}
            .content {{
                background-color: #f9fafb;
                padding: 30px;
                border-radius: 0 0 8px 8px;
            }}
            .credentials {{
                background-color: white;
                padding: 15px;
                border-left: 4px solid #2563eb;
                margin: 20px 0;
            }}
            .button {{
                display: inline-block;
                padding: 12px 30px;
                background-color: #2563eb;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                margin: 20px 0;
            }}
            .footer {{
                margin-top: 20px;
                text-align: center;
                font-size: 12px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔧 GMAO Iris</h1>
            </div>
            <div class="content">
                <h2>Bonjour {prenom},</h2>
                <p>Votre compte GMAO Iris a été créé avec succès !</p>
                
                <div class="credentials">
                    <p><strong>Vos identifiants de connexion :</strong></p>
                    <p>Email : <strong>{to_email}</strong></p>
                    <p>Mot de passe temporaire : <strong>{temp_password}</strong></p>
                </div>
                
                <p><strong>⚠️ Important :</strong> Vous devrez changer votre mot de passe lors de votre première connexion.</p>
                
                <div style="text-align: center;">
                    <a href="{APP_URL}" class="button">Se connecter</a>
                </div>
                
                <p>Cordialement,<br>L'équipe GMAO Iris</p>
            </div>
            <div class="footer">
                <p>Ceci est un email automatique, merci de ne pas y répondre.</p>
                <p>© 2025 GMAO Iris - Tous droits réservés</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Version texte
    text_content = f"""
Bonjour {prenom},

Votre compte GMAO Iris a été créé avec succès !

Vos identifiants de connexion :
Email : {to_email}
Mot de passe temporaire : {temp_password}

⚠️ Important : Vous devrez changer votre mot de passe lors de votre première connexion.

Connectez-vous sur : {APP_URL}

Cordialement,
L'équipe GMAO Iris

---
Ceci est un email automatique, merci de ne pas y répondre.
© 2025 GMAO Iris - Tous droits réservés
    """
    
    return send_email(to_email, subject, html_content, text_content)
PYEOF

    log "✅ Service email mis à jour"
else
    error "Fichier email_service.py non trouvé"
    exit 1
fi

# Redémarrer le backend
log "Redémarrage du backend GMAO Iris..."
supervisorctl restart backend 2>/dev/null || true
sleep 3

# Test d'envoi d'email
log "Test d'envoi d'email..."

cat > /tmp/test_email.py << 'PYEOF'
import sys
sys.path.insert(0, '/app/backend')

from email_service import send_email

result = send_email(
    to_email="test@example.com",
    subject="Test Postfix GMAO Iris",
    html_content="<h1>Test réussi</h1><p>Postfix fonctionne correctement</p>",
    text_content="Test réussi - Postfix fonctionne correctement"
)

print(f"Résultat: {'✅ Succès' if result else '❌ Échec'}")
PYEOF

cd /app/backend
python3 /tmp/test_email.py

# Informations finales
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              ✅ CONFIGURATION TERMINÉE !                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
log "📧 Postfix installé et configuré"
log "⚙️  Backend GMAO Iris configuré pour utiliser Postfix local"
log "✉️  Les emails seront envoyés depuis: $SMTP_SENDER_EMAIL"
echo ""
info "Pour tester l'envoi d'email depuis l'application :"
info "  1. Connectez-vous en tant qu'admin"
info "  2. Allez dans 'Équipes'"
info "  3. Cliquez 'Inviter un membre'"
info "  4. L'email sera envoyé via Postfix local"
echo ""
info "Pour vérifier les logs Postfix :"
info "  tail -f /var/log/mail.log"
echo ""
info "Pour vérifier les logs backend :"
info "  tail -f /var/log/supervisor/backend.err.log"
echo ""
warn "⚠️  IMPORTANT : Configuration DNS/SPF"
info "Pour éviter que vos emails soient marqués comme SPAM :"
info "  1. Configurez un reverse DNS (PTR) pour votre IP"
info "  2. Ajoutez un enregistrement SPF dans votre DNS"
info "  3. Pour la production, utilisez un relay SMTP (SendGrid, etc.)"
echo ""
log "🎉 Configuration terminée avec succès !"
echo ""
