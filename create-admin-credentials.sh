#!/usr/bin/env bash

###############################################################################
# Création des identifiants admin pour GMAO Iris
# Container 102
###############################################################################

CTID=102

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Création des identifiants GMAO Iris                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Vérifier que le container existe
if ! pct status $CTID >/dev/null 2>&1; then
    echo -e "${RED}✗${NC} Container $CTID n'existe pas"
    exit 1
fi

# Vérifier que le container est démarré
if ! pct status $CTID | grep -q "running"; then
    echo -e "${BLUE}▶${NC} Démarrage du container..."
    pct start $CTID
    sleep 5
fi

echo -e "${GREEN}✓${NC} Container $CTID actif"
echo ""

# Créer le script Python pour créer les utilisateurs
cat > /tmp/create_admin_users.py <<'PYEOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime

async def main():
    print("🔐 Connexion à MongoDB...")
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.gmao_iris
    pwd = CryptContext(schemes=['bcrypt'], deprecated='auto', bcrypt__rounds=10)
    
    # Supprimer tous les anciens utilisateurs
    print("🗑️  Suppression des anciens utilisateurs...")
    await db.users.delete_many({})
    
    print("➕ Création des comptes administrateurs...")
    
    # Admin 1 : admin@gmao.fr / Admin2024!
    admin1 = {
        'email': 'admin@gmao.fr',
        'hashed_password': pwd.hash('Admin2024!'),
        'nom': 'Admin',
        'prenom': 'Principal',
        'role': 'ADMIN',
        'telephone': None,
        'service': None,
        'statut': 'actif',
        'dateCreation': datetime.now(),
        'derniereConnexion': None,
        'firstLogin': False,
        'permissions': {
            module: {'view': True, 'edit': True, 'delete': True}
            for module in ['dashboard', 'workOrders', 'assets', 'preventiveMaintenance', 
                          'inventory', 'locations', 'vendors', 'reports', 'purchaseHistory',
                          'people', 'planning', 'improvementRequests', 'improvements',
                          'interventionRequests', 'equipments', 'meters', 'importExport', 'journal']
        }
    }
    await db.users.insert_one(admin1)
    print('✅ Compte 1 créé: admin@gmao.fr / Admin2024!')
    
    # Admin 2 : gregoire@iris.fr / password123
    admin2 = {
        'email': 'gregoire@iris.fr',
        'hashed_password': pwd.hash('password123'),
        'nom': 'Admin',
        'prenom': 'Grégoire',
        'role': 'ADMIN',
        'telephone': None,
        'service': None,
        'statut': 'actif',
        'dateCreation': datetime.now(),
        'derniereConnexion': None,
        'firstLogin': False,
        'permissions': {
            module: {'view': True, 'edit': True, 'delete': True}
            for module in ['dashboard', 'workOrders', 'assets', 'preventiveMaintenance', 
                          'inventory', 'locations', 'vendors', 'reports', 'purchaseHistory',
                          'people', 'planning', 'improvementRequests', 'improvements',
                          'interventionRequests', 'equipments', 'meters', 'importExport', 'journal']
        }
    }
    await db.users.insert_one(admin2)
    print('✅ Compte 2 créé: gregoire@iris.fr / password123')
    
    # Admin 3 : buenogy@gmail.com / Admin2024!
    admin3 = {
        'email': 'buenogy@gmail.com',
        'hashed_password': pwd.hash('Admin2024!'),
        'nom': 'Support',
        'prenom': 'Admin',
        'role': 'ADMIN',
        'telephone': None,
        'service': None,
        'statut': 'actif',
        'dateCreation': datetime.now(),
        'derniereConnexion': None,
        'firstLogin': False,
        'permissions': {
            module: {'view': True, 'edit': True, 'delete': True}
            for module in ['dashboard', 'workOrders', 'assets', 'preventiveMaintenance', 
                          'inventory', 'locations', 'vendors', 'reports', 'purchaseHistory',
                          'people', 'planning', 'improvementRequests', 'improvements',
                          'interventionRequests', 'equipments', 'meters', 'importExport', 'journal']
        }
    }
    await db.users.insert_one(admin3)
    print('✅ Compte 3 créé: buenogy@gmail.com / Admin2024!')
    
    # Vérifier
    count = await db.users.count_documents({'role': 'ADMIN'})
    print(f'\n✅ Total: {count} administrateurs créés')
    
    client.close()

asyncio.run(main())
PYEOF

# Copier le script dans le container
echo -e "${BLUE}▶${NC} Transfert du script dans le container..."
pct push $CTID /tmp/create_admin_users.py /tmp/create_admin_users.py

# Exécuter le script dans le container
echo -e "${BLUE}▶${NC} Création des utilisateurs..."
echo ""

pct exec $CTID -- python3 /tmp/create_admin_users.py

# Nettoyer
rm /tmp/create_admin_users.py
pct exec $CTID -- rm /tmp/create_admin_users.py 2>/dev/null || true

# Obtenir l'IP du container
CONTAINER_IP=$(pct exec $CTID -- hostname -I 2>/dev/null | awk '{print $1}')

if [[ -z "$CONTAINER_IP" || "$CONTAINER_IP" == "127.0.0.1" ]]; then
    CONTAINER_IP="192.168.1.200"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              ✅ IDENTIFIANTS CRÉÉS !                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  IDENTIFIANTS DE CONNEXION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 URL: http://${CONTAINER_IP}"
echo ""
echo "👤 COMPTE 1 (Principal):"
echo "   Email:        admin@gmao.fr"
echo "   Mot de passe: Admin2024!"
echo ""
echo "👤 COMPTE 2 (Grégoire):"
echo "   Email:        gregoire@iris.fr"
echo "   Mot de passe: password123"
echo ""
echo "👤 COMPTE 3 (Support):"
echo "   Email:        buenogy@gmail.com"
echo "   Mot de passe: Admin2024!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
