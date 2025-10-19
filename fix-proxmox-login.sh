#!/bin/bash

###############################################################################
# Script de Correction Urgente - Problème de Login GMAO Iris sur Proxmox
# 
# Ce script diagnostique et corrige le problème de connexion
# Usage: ./fix-proxmox-login.sh
###############################################################################

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "  DIAGNOSTIC ET CORRECTION - GMAO IRIS LOGIN PROXMOX"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Vérifier si on est dans le container
if [ ! -d "/opt/gmao-iris" ]; then
    echo "❌ ERREUR: Ce script doit être exécuté DANS le container LXC"
    echo "   Utilisez: pct enter <CTID> puis exécutez ce script"
    exit 1
fi

echo "✅ Détection du container OK"
echo ""

# Étape 1: Vérifier la configuration
echo "📋 ÉTAPE 1: Vérification de la configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "/opt/gmao-iris/backend/.env" ]; then
    echo "✅ Fichier .env trouvé"
    source /opt/gmao-iris/backend/.env
    echo "   MONGO_URL: $MONGO_URL"
    echo "   DB_NAME: ${DB_NAME:-gmao_iris}"
else
    echo "❌ Fichier .env non trouvé!"
    exit 1
fi

DB_NAME=${DB_NAME:-gmao_iris}
echo ""

# Étape 2: Vérifier MongoDB
echo "📋 ÉTAPE 2: Vérification de MongoDB"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if systemctl is-active --quiet mongod; then
    echo "✅ MongoDB est actif"
else
    echo "❌ MongoDB n'est pas actif"
    echo "   Démarrage de MongoDB..."
    systemctl start mongod
    sleep 3
fi

# Lister les bases de données
echo ""
echo "Bases de données MongoDB disponibles:"
mongosh --quiet --eval "db.adminCommand('listDatabases').databases.forEach(function(db){ print('  - ' + db.name); })"
echo ""

# Étape 3: Vérifier les utilisateurs
echo "📋 ÉTAPE 3: Vérification des utilisateurs dans la base $DB_NAME"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

USER_COUNT=$(mongosh --quiet "$DB_NAME" --eval "db.users.countDocuments({})")
echo "Nombre d'utilisateurs dans $DB_NAME: $USER_COUNT"

if [ "$USER_COUNT" -gt 0 ]; then
    echo ""
    echo "Utilisateurs existants:"
    mongosh --quiet "$DB_NAME" --eval "db.users.find({}, {email: 1, role: 1, statut: 1}).forEach(function(u){ print('  - ' + u.email + ' (' + u.role + ') - ' + (u.statut || 'NO STATUS')); })"
else
    echo "⚠️  Aucun utilisateur trouvé dans la base $DB_NAME"
fi

echo ""
echo ""

# Étape 4: Proposition de correction
echo "📋 ÉTAPE 4: Création/Réinitialisation du compte administrateur"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

read -p "Voulez-vous créer/réinitialiser un compte administrateur ? (y/n): " CONFIRM
if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
    echo "Opération annulée"
    exit 0
fi

echo ""
read -p "Email de l'administrateur [admin@gmao-iris.local]: " ADMIN_EMAIL
ADMIN_EMAIL=${ADMIN_EMAIL:-admin@gmao-iris.local}

read -sp "Mot de passe (min 8 caractères) [Admin2024!]: " ADMIN_PASS
echo ""
ADMIN_PASS=${ADMIN_PASS:-Admin2024!}

read -p "Prénom [Admin]: " ADMIN_FIRSTNAME
ADMIN_FIRSTNAME=${ADMIN_FIRSTNAME:-Admin}

read -p "Nom [System]: " ADMIN_LASTNAME
ADMIN_LASTNAME=${ADMIN_LASTNAME:-System}

echo ""
echo "Création du compte administrateur..."
echo ""

# Créer le script Python
cat > /tmp/fix_admin.py <<'EOPYTHON'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime
import sys
import uuid
import os

async def create_admin():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'gmao_iris')
    
    email = sys.argv[1]
    password = sys.argv[2]
    prenom = sys.argv[3]
    nom = sys.argv[4]
    
    print(f"🔧 Connexion à MongoDB...")
    print(f"   URL: {mongo_url}")
    print(f"   Base de données: {db_name}")
    print("")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    hashed_password = pwd_context.hash(password)
    
    # Vérifier si l'utilisateur existe
    existing_user = await db.users.find_one({'email': email})
    
    admin_user = {
        'id': str(uuid.uuid4()),
        'email': email,
        'password': hashed_password,
        'prenom': prenom,
        'nom': nom,
        'role': 'ADMIN',
        'telephone': '',
        'service': None,
        'statut': 'actif',
        'dateCreation': datetime.utcnow(),
        'derniereConnexion': datetime.utcnow(),
        'permissions': {
            'dashboard': {'view': True, 'edit': True, 'delete': True},
            'workOrders': {'view': True, 'edit': True, 'delete': True},
            'assets': {'view': True, 'edit': True, 'delete': True},
            'preventiveMaintenance': {'view': True, 'edit': True, 'delete': True},
            'inventory': {'view': True, 'edit': True, 'delete': True},
            'locations': {'view': True, 'edit': True, 'delete': True},
            'vendors': {'view': True, 'edit': True, 'delete': True},
            'reports': {'view': True, 'edit': True, 'delete': True}
        }
    }
    
    if existing_user:
        admin_user['id'] = existing_user.get('id', str(uuid.uuid4()))
        await db.users.update_one(
            {'email': email},
            {'$set': admin_user}
        )
        print(f"✅ Compte administrateur mis à jour: {email}")
    else:
        await db.users.insert_one(admin_user)
        print(f"✅ Compte administrateur créé: {email}")
    
    print("")
    print("Détails du compte:")
    print(f"  📧 Email:     {email}")
    print(f"  👤 Nom:       {prenom} {nom}")
    print(f"  🔑 Rôle:      ADMIN")
    print(f"  ✓  Statut:    actif")
    
    client.close()

asyncio.run(create_admin())
EOPYTHON

# Exécuter le script
cd /opt/gmao-iris/backend
source venv/bin/activate
export MONGO_URL="$MONGO_URL"
export DB_NAME="$DB_NAME"
python3 /tmp/fix_admin.py "$ADMIN_EMAIL" "$ADMIN_PASS" "$ADMIN_FIRSTNAME" "$ADMIN_LASTNAME"

# Nettoyer
rm -f /tmp/fix_admin.py

echo ""
echo ""

# Étape 5: Redémarrer le backend
echo "📋 ÉTAPE 5: Redémarrage du backend"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

supervisorctl restart gmao-iris-backend
sleep 3

if supervisorctl status gmao-iris-backend | grep -q RUNNING; then
    echo "✅ Backend redémarré avec succès"
else
    echo "⚠️  Le backend ne s'est pas redémarré correctement"
    echo "   Vérifiez les logs: tail -f /var/log/gmao-iris-backend.err.log"
fi

echo ""
echo ""

# Résumé final
echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ CORRECTION TERMINÉE"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "🔐 Compte créé/mis à jour:"
echo "   Email:        $ADMIN_EMAIL"
echo "   Mot de passe: [masqué]"
echo "   Rôle:         ADMIN"
echo ""
echo "🌐 Accédez à l'application et essayez de vous connecter"
echo ""
echo "📋 Si le problème persiste, vérifiez:"
echo "   1. Les logs backend: tail -f /var/log/gmao-iris-backend.out.log"
echo "   2. Les logs d'erreur: tail -f /var/log/gmao-iris-backend.err.log"
echo "   3. Configuration Nginx: nginx -t"
echo ""
echo "═══════════════════════════════════════════════════════════════"
