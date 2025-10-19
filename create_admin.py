#!/usr/bin/env python3
"""
Script pour créer un utilisateur administrateur dans GMAO Iris
Usage: python3 create_admin.py
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime
import uuid
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
ROOT_DIR = Path(__file__).parent / 'backend'
load_dotenv(ROOT_DIR / '.env')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin():
    """Créer un utilisateur administrateur"""
    
    # Configuration MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'gmao_iris')
    
    print("=" * 60)
    print("CRÉATION D'UN UTILISATEUR ADMINISTRATEUR - GMAO Iris")
    print("=" * 60)
    print()
    
    # Demander les informations
    email = input("Email de l'administrateur: ").strip()
    if not email or '@' not in email:
        print("❌ Email invalide")
        sys.exit(1)
    
    password = input("Mot de passe (min 8 caractères): ").strip()
    if len(password) < 8:
        print("❌ Le mot de passe doit contenir au moins 8 caractères")
        sys.exit(1)
    
    prenom = input("Prénom: ").strip() or "Admin"
    nom = input("Nom: ").strip() or "User"
    telephone = input("Téléphone (optionnel): ").strip() or ""
    service = input("Service (optionnel): ").strip() or None
    
    print()
    print(f"Connexion à MongoDB: {mongo_url}")
    print(f"Base de données: {db_name}")
    print()
    
    try:
        # Connexion à MongoDB
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = await db.users.find_one({'email': email})
        
        # Hasher le mot de passe
        hashed_password = pwd_context.hash(password)
        
        # Créer le document utilisateur
        admin_user = {
            'id': str(uuid.uuid4()),
            'email': email,
            'password': hashed_password,
            'prenom': prenom,
            'nom': nom,
            'role': 'ADMIN',
            'telephone': telephone,
            'service': service,
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
            # Mettre à jour l'utilisateur existant en gardant son id
            admin_user['id'] = existing_user.get('id', str(uuid.uuid4()))
            await db.users.update_one(
                {'email': email},
                {'$set': admin_user}
            )
            print(f"✅ Utilisateur administrateur mis à jour: {email}")
        else:
            # Créer un nouvel utilisateur
            await db.users.insert_one(admin_user)
            print(f"✅ Utilisateur administrateur créé: {email}")
        
        print()
        print("Détails du compte:")
        print(f"  Email:    {email}")
        print(f"  Nom:      {prenom} {nom}")
        print(f"  Role:     ADMIN")
        print(f"  Statut:   actif")
        if service:
            print(f"  Service:  {service}")
        print()
        print("=" * 60)
        
        client.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'administrateur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(create_admin())
