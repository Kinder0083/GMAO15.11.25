#!/usr/bin/env python3
"""Script pour créer un utilisateur admin manuellement"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime

async def create_admin_manual():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.gmao_iris
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Supprimer tous les utilisateurs existants
    result = await db.users.delete_many({})
    print(f"Utilisateurs supprimés : {result.deleted_count}")
    
    # Créer les deux admins
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
    
    for admin_data in admins:
        hashed_password = pwd_context.hash(admin_data["password"])
        
        admin_user = {
            "email": admin_data["email"],
            "hashed_password": hashed_password,
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
        print(f"Admin créé : {admin_data['email']} (ID: {result.inserted_id})")
        
        # Tester immédiatement la vérification
        test_verify = pwd_context.verify(admin_data["password"], hashed_password)
        print(f"  -> Vérification du mot de passe : {'OK' if test_verify else 'ERREUR'}")
    
    print("\n✅ Utilisateurs créés avec succès")
    print("\nVous pouvez maintenant vous connecter avec :")
    print("  - admin@gmao-iris.local / Admin123!")
    print("  - buenogy@gmail.com / nmrojvbvgb")

asyncio.run(create_admin_manual())
