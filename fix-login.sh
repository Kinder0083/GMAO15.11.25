#!/bin/bash

#######################################################################
# GMAO Iris - Script de diagnostic et réparation des comptes admin
# À exécuter DANS le container LXC
#######################################################################

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     GMAO Iris - Diagnostic et Réparation Connexion           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Vérifier qu'on est dans le container
if [ ! -d "/opt/gmao-iris" ]; then
    echo -e "${RED}❌ Ce script doit être exécuté DANS le container LXC${NC}"
    echo "   Utilisez : pct enter VOTRE_CT_ID"
    exit 1
fi

echo "🔍 ÉTAPE 1 : Vérification de MongoDB"
if systemctl is-active --quiet mongod; then
    echo -e "${GREEN}✓${NC} MongoDB est actif"
else
    echo -e "${RED}✗${NC} MongoDB n'est pas actif - Démarrage..."
    systemctl start mongod
    sleep 2
fi

echo ""
echo "🔍 ÉTAPE 2 : Vérification de la base de données"
DB_COUNT=$(mongosh --quiet --eval "db.adminCommand('listDatabases').databases.length")
echo "  Nombre de bases : $DB_COUNT"

USER_COUNT=$(mongosh --quiet gmao_iris --eval "db.users.countDocuments({})")
echo "  Utilisateurs dans gmao_iris : $USER_COUNT"

if [ "$USER_COUNT" -eq "0" ]; then
    echo -e "${YELLOW}⚠${NC} Aucun utilisateur trouvé - Création nécessaire"
fi

echo ""
echo "🔍 ÉTAPE 3 : Vérification du backend"
if supervisorctl status gmao-iris-backend | grep -q RUNNING; then
    echo -e "${GREEN}✓${NC} Backend est actif"
else
    echo -e "${RED}✗${NC} Backend n'est pas actif"
fi

# Vérifier les logs backend pour des erreurs
echo ""
echo "🔍 ÉTAPE 4 : Vérification des logs backend"
if tail -20 /var/log/gmao-iris-backend.err.log | grep -q "error\|Error\|ERROR"; then
    echo -e "${YELLOW}⚠${NC} Erreurs détectées dans les logs :"
    tail -10 /var/log/gmao-iris-backend.err.log
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
read -p "Voulez-vous RÉPARER et créer les comptes admin ? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Arrêt du script"
    exit 0
fi

echo ""
echo "🔧 RÉPARATION EN COURS..."
echo ""

# Arrêter le backend
echo "1️⃣  Arrêt du backend..."
supervisorctl stop gmao-iris-backend >/dev/null 2>&1

# Créer le script Python de réparation
echo "2️⃣  Création du script de réparation..."
cat > /tmp/fix_users.py <<'EOFPY'
import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime

async def fix_users():
    print("   Connexion à MongoDB...")
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.gmao_iris
    
    print("   Suppression des anciens utilisateurs...")
    result = await db.users.delete_many({})
    print(f"   -> {result.deleted_count} utilisateur(s) supprimé(s)")
    
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    
    # Liste des admins à créer
    admins = [
        {
            "email": "admin@gmao-iris.local",
            "password": "Admin123!",
            "prenom": "System",
            "nom": "Admin"
        },
        {
            "email": "buenogy@gmail.com",
            "password": "nmrojvbvgb",
            "prenom": "Support",
            "nom": "Admin"
        }
    ]
    
    print("   Création des comptes administrateurs...")
    for admin_data in admins:
        hashed_password = pwd_context.hash(admin_data["password"])
        
        admin_user = {
            "email": admin_data["email"],
            "password": hashed_password,
            "prenom": admin_data["prenom"],
            "nom": admin_data["nom"],
            "role": "ADMIN",
            "telephone": "",
            "dateCreation": datetime.utcnow(),
            "derniereConnexion": None,
            "actif": True,
            "permissions": {
                "dashboard": {"view": True, "edit": True, "delete": True},
                "workOrders": {"view": True, "edit": True, "delete": True},
                "assets": {"view": True, "edit": True, "delete": True},
                "preventiveMaintenance": {"view": True, "edit": True, "delete": True},
                "inventory": {"view": True, "edit": True, "delete": True},
                "locations": {"view": True, "edit": True, "delete": True},
                "vendors": {"view": True, "edit": True, "delete": True},
                "reports": {"view": True, "edit": True, "delete": True}
            }
        }
        
        result = await db.users.insert_one(admin_user)
        print(f"   ✓ Admin créé : {admin_data['email']}")
        
        # Vérification immédiate
        test_verify = pwd_context.verify(admin_data["password"], hashed_password)
        if test_verify:
            print(f"     -> Mot de passe vérifié : OK")
        else:
            print(f"     -> ERREUR de vérification du mot de passe !")
            sys.exit(1)
    
    # Vérification finale
    final_count = await db.users.count_documents({})
    print(f"\n   Total utilisateurs dans la base : {final_count}")
    
    if final_count >= 2:
        print("\n   ✅ SUCCÈS - Tous les comptes sont créés et vérifiés")
        return True
    else:
        print("\n   ❌ ERREUR - Problème lors de la création")
        return False

try:
    result = asyncio.run(fix_users())
    sys.exit(0 if result else 1)
except Exception as e:
    print(f"\n   ❌ ERREUR : {str(e)}")
    sys.exit(1)
EOFPY

# Exécuter le script Python
echo "3️⃣  Exécution de la réparation..."
cd /opt/gmao-iris/backend
source venv/bin/activate
python3 /tmp/fix_users.py
REPAIR_STATUS=$?

if [ $REPAIR_STATUS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ RÉPARATION RÉUSSIE${NC}"
else
    echo ""
    echo -e "${RED}❌ ERREUR lors de la réparation${NC}"
    exit 1
fi

# Redémarrer le backend
echo ""
echo "4️⃣  Redémarrage du backend..."
supervisorctl start gmao-iris-backend >/dev/null 2>&1
sleep 3

if supervisorctl status gmao-iris-backend | grep -q RUNNING; then
    echo -e "${GREEN}✓${NC} Backend redémarré avec succès"
else
    echo -e "${RED}✗${NC} Erreur lors du redémarrage du backend"
    echo "   Logs :"
    tail -20 /var/log/gmao-iris-backend.err.log
    exit 1
fi

# Vérification finale avec un test de connexion
echo ""
echo "5️⃣  Test de connexion..."
CONTAINER_IP=$(hostname -I | awk '{print $1}')

# Test avec curl
sleep 2
RESPONSE=$(curl -s -X POST "http://localhost:8001/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"buenogy@gmail.com","password":"nmrojvbvgb"}')

if echo "$RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✅ TEST DE CONNEXION RÉUSSI${NC}"
else
    echo -e "${YELLOW}⚠${NC} La connexion backend a retourné :"
    echo "$RESPONSE"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    RÉPARATION TERMINÉE                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 URL de l'application : http://$CONTAINER_IP"
echo ""
echo "👤 Comptes disponibles :"
echo "   1) Email: admin@gmao-iris.local"
echo "      Mot de passe: Admin123!"
echo ""
echo "   2) Email: buenogy@gmail.com"
echo "      Mot de passe: nmrojvbvgb"
echo ""
echo "💡 Essayez de vous connecter maintenant !"
echo ""

# Nettoyer
rm -f /tmp/fix_users.py
