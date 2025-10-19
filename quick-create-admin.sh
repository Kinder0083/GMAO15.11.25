#!/bin/bash

###############################################################################
# Script Rapide de Création d'Admin - GMAO Iris
# À exécuter DANS le container Proxmox
###############################################################################

echo "════════════════════════════════════════════════════════"
echo "  CRÉATION RAPIDE D'UN COMPTE ADMINISTRATEUR"
echo "════════════════════════════════════════════════════════"
echo ""

# Charger les variables d'environnement
cd /opt/gmao-iris/backend
source .env 2>/dev/null || true

MONGO_URL=${MONGO_URL:-mongodb://localhost:27017}
DB_NAME=${DB_NAME:-gmao_iris}

echo "Configuration:"
echo "  MongoDB: $MONGO_URL"
echo "  Base de données: $DB_NAME"
echo ""

# Informations du compte
read -p "Email [admin@gmao-iris.local]: " EMAIL
EMAIL=${EMAIL:-admin@gmao-iris.local}

read -sp "Mot de passe [Admin2024!]: " PASSWORD
echo ""
PASSWORD=${PASSWORD:-Admin2024!}

echo ""
echo "Création du compte $EMAIL..."

# Script Python inline
source venv/bin/activate
export MONGO_URL="$MONGO_URL"
export DB_NAME="$DB_NAME"

python3 - <<PYTHON
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime
import uuid
import os

async def main():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    
    admin = {
        'id': str(uuid.uuid4()),
        'email': '$EMAIL',
        'password': pwd_context.hash('$PASSWORD'),
        'prenom': 'Admin',
        'nom': 'User',
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
    
    existing = await db.users.find_one({'email': '$EMAIL'})
    if existing:
        admin['id'] = existing.get('id', str(uuid.uuid4()))
        await db.users.update_one({'email': '$EMAIL'}, {'\$set': admin})
        print('✅ Compte mis à jour')
    else:
        await db.users.insert_one(admin)
        print('✅ Compte créé')

asyncio.run(main())
PYTHON

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ TERMINÉ"
echo ""
echo "Compte: $EMAIL"
echo "Mot de passe: [masqué]"
echo ""
echo "Redémarrez le backend: supervisorctl restart gmao-iris-backend"
echo "════════════════════════════════════════════════════════"
