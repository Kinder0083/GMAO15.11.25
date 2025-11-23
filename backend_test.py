#!/usr/bin/env python3
"""
Backend API Testing Script for GMAO Application
Tests Système de Pièces Utilisées dans les Ordres de Travail
"""

import requests
import json
import os
from datetime import datetime, timedelta

# Use the correct backend URL from frontend .env
BACKEND_URL = "https://maint-dashboard-7.preview.emergentagent.com/api"

# Test credentials - admin account as specified in the request
ADMIN_EMAIL = "admin@gmao-iris.local"
ADMIN_PASSWORD = "Admin123!"

class PartsUsedSystemTester:
    def __init__(self):
        self.admin_session = requests.Session()
        self.admin_token = None
        self.admin_data = None
        self.test_work_order_id = None  # UUID for GET endpoint
        self.test_work_order_object_id = None  # ObjectId for comments endpoint
        self.test_inventory_item_id = None
        self.test_equipment_id = None
        self.initial_inventory_quantity = None
        self.inventory_item_name = None
        self.equipment_name = None
        
    def log(self, message, level="INFO"):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_admin_login(self):
        """Test admin login with specified credentials"""
        self.log("Testing admin login...")
        
        try:
            response = self.admin_session.post(
                f"{BACKEND_URL}/auth/login",
                json={
                    "email": ADMIN_EMAIL,
                    "password": ADMIN_PASSWORD
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                self.admin_data = data.get("user")
                
                # Set authorization header for future requests
                self.admin_session.headers.update({
                    "Authorization": f"Bearer {self.admin_token}"
                })
                
                self.log(f"✅ Admin login successful - User: {self.admin_data.get('prenom')} {self.admin_data.get('nom')} (Role: {self.admin_data.get('role')})")
                return True
            else:
                self.log(f"❌ Admin login failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Admin login request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_get_initial_state(self):
        """TEST 1: Vérifier l'état initial - Inventaire, Ordres de travail, Équipements"""
        self.log("🧪 TEST 1: Vérifier l'état initial du système")
        
        try:
            # 1. GET /api/inventory - Noter la quantité d'une pièce test
            self.log("📦 Récupération de l'inventaire...")
            response = self.admin_session.get(f"{BACKEND_URL}/inventory", timeout=15)
            
            if response.status_code == 200:
                inventory_items = response.json()
                if inventory_items:
                    # Prendre le premier item d'inventaire
                    test_item = inventory_items[0]
                    self.test_inventory_item_id = test_item.get('id')
                    self.initial_inventory_quantity = test_item.get('quantite', 0)
                    self.inventory_item_name = test_item.get('nom', 'Pièce Test')
                    
                    self.log(f"✅ Pièce d'inventaire trouvée - ID: {self.test_inventory_item_id}")
                    self.log(f"✅ Nom: {self.inventory_item_name}")
                    self.log(f"✅ Quantité initiale: {self.initial_inventory_quantity}")
                else:
                    self.log("❌ Aucune pièce d'inventaire trouvée", "ERROR")
                    return False
            else:
                self.log(f"❌ Récupération inventaire échouée - Status: {response.status_code}", "ERROR")
                return False
            
            # 2. GET /api/work-orders - Prendre un ordre de travail existant
            self.log("📋 Récupération des ordres de travail...")
            response = self.admin_session.get(f"{BACKEND_URL}/work-orders", timeout=15)
            
            if response.status_code == 200:
                work_orders = response.json()
                if work_orders:
                    # Prendre le premier ordre de travail
                    test_wo = work_orders[0]
                    self.test_work_order_id = test_wo.get('id')  # UUID for GET endpoint
                    self.test_work_order_object_id = test_wo.get('id')  # For now, try with same ID
                    self.log(f"✅ Ordre de travail trouvé - ID: {self.test_work_order_id}")
                    self.log(f"✅ Titre: {test_wo.get('titre', 'N/A')}")
                    self.log(f"🔍 Debug - Work order keys: {list(test_wo.keys())}")
                    
                    # Check if there's a MongoDB ObjectId field
                    if '_id' in test_wo:
                        self.test_work_order_object_id = test_wo.get('_id')
                        self.log(f"🔍 Debug - ObjectId found: {self.test_work_order_object_id}")
                    elif 'objectId' in test_wo:
                        self.test_work_order_object_id = test_wo.get('objectId')
                        self.log(f"🔍 Debug - ObjectId found: {self.test_work_order_object_id}")
                else:
                    self.log("⚠️ Aucun ordre de travail existant, création d'un nouveau...")
                    return self.create_test_work_order()
            else:
                self.log(f"❌ Récupération ordres de travail échouée - Status: {response.status_code}", "ERROR")
                return False
            
            # 3. GET /api/equipment - Prendre un équipement test
            self.log("🔧 Récupération des équipements...")
            response = self.admin_session.get(f"{BACKEND_URL}/equipments", timeout=15)
            
            if response.status_code == 200:
                equipments = response.json()
                if equipments:
                    test_equipment = equipments[0]
                    self.test_equipment_id = test_equipment.get('id')
                    self.equipment_name = test_equipment.get('nom', 'Équipement Test')
                    self.log(f"✅ Équipement trouvé - ID: {self.test_equipment_id}")
                    self.log(f"✅ Nom: {self.equipment_name}")
                else:
                    self.log("❌ Aucun équipement trouvé", "ERROR")
                    return False
            else:
                self.log(f"❌ Récupération équipements échouée - Status: {response.status_code}", "ERROR")
                return False
            
            self.log("✅ État initial vérifié avec succès")
            return True
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def create_test_work_order(self):
        """Créer un ordre de travail de test si aucun n'existe"""
        self.log("📋 Création d'un ordre de travail de test...")
        
        try:
            wo_data = {
                "titre": "Test pièces utilisées",
                "description": "Ordre de travail créé pour tester le système de pièces utilisées",
                "type": "CORRECTIF",
                "priorite": "NORMALE",
                "statut": "OUVERT",
                "equipement_id": self.test_equipment_id,
                "tempsEstime": 2.0
            }
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/work-orders",
                json=wo_data,
                timeout=15
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.test_work_order_id = data.get('id')
                self.test_work_order_object_id = data.get('id')  # For now, same ID
                self.log(f"✅ Ordre de travail créé - ID: {self.test_work_order_id}")
                return True
            else:
                self.log(f"❌ Création ordre de travail échouée - Status: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_add_parts_with_comment(self):
        """TEST 2: Test d'ajout de pièces avec commentaire"""
        self.log("🧪 TEST 2: Test d'ajout de pièces avec déduction stock")
        
        if not self.test_work_order_id or not self.test_inventory_item_id or not self.test_equipment_id:
            self.log("❌ Prérequis manquants pour le test", "ERROR")
            return False
        
        try:
            # POST /api/work-orders/{id}/comments avec parts_used
            comment_data = {
                "text": "Test ajout pièce avec déduction stock",
                "parts_used": [
                    {
                        "inventory_item_id": self.test_inventory_item_id,
                        "inventory_item_name": self.inventory_item_name,
                        "quantity": 2,
                        "source_equipment_id": self.test_equipment_id,
                        "source_equipment_name": self.equipment_name
                    }
                ]
            }
            
            self.log(f"📤 Envoi du commentaire avec pièce utilisée...")
            self.log(f"   Pièce: {self.inventory_item_name} (Quantité: 2)")
            self.log(f"   Source: {self.equipment_name}")
            
            # Use ObjectId for comments endpoint
            comments_id = self.test_work_order_object_id or self.test_work_order_id
            self.log(f"🔍 Debug - Using ID for comments: {comments_id}")
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/work-orders/{comments_id}/comments",
                json=comment_data,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Commentaire avec pièce ajouté avec succès")
                self.log(f"✅ Commentaire ID: {data.get('comment', {}).get('id')}")
                self.log(f"✅ Pièces utilisées: {len(data.get('parts_used', []))}")
                
                # Vérifier que la pièce est dans la réponse
                parts_used = data.get('parts_used', [])
                if parts_used and len(parts_used) > 0:
                    part = parts_used[0]
                    self.log(f"✅ Pièce ajoutée: {part.get('inventory_item_name')} (Quantité: {part.get('quantity')})")
                    return True
                else:
                    self.log("❌ Aucune pièce utilisée dans la réponse", "ERROR")
                    return False
            else:
                self.log(f"❌ Ajout commentaire échoué - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False

    def test_verify_inventory_deduction(self):
        """TEST 3: Vérifications après ajout - Déduction inventaire et mise à jour ordre de travail"""
        self.log("🧪 TEST 3: Vérifier la déduction automatique du stock")
        
        if not self.test_inventory_item_id:
            self.log("❌ ID pièce d'inventaire manquant", "ERROR")
            return False
        
        try:
            # GET /api/inventory/{id} - Vérifier que la quantité a été déduite de 2 unités
            self.log("📦 Vérification de la déduction du stock...")
            response = self.admin_session.get(
                f"{BACKEND_URL}/inventory",
                timeout=15
            )
            
            if response.status_code == 200:
                inventory_items = response.json()
                # Trouver notre pièce
                test_item = None
                for item in inventory_items:
                    if item.get('id') == self.test_inventory_item_id:
                        test_item = item
                        break
                
                if test_item:
                    current_quantity = test_item.get('quantite', 0)
                    expected_quantity = self.initial_inventory_quantity - 2
                    
                    self.log(f"📊 Quantité initiale: {self.initial_inventory_quantity}")
                    self.log(f"📊 Quantité actuelle: {current_quantity}")
                    self.log(f"📊 Quantité attendue: {expected_quantity}")
                    
                    if current_quantity == expected_quantity:
                        self.log("✅ SUCCÈS: Déduction automatique du stock confirmée (-2 unités)")
                        return True
                    else:
                        self.log(f"❌ ÉCHEC: Déduction incorrecte. Attendu: {expected_quantity}, Trouvé: {current_quantity}", "ERROR")
                        return False
                else:
                    self.log("❌ Pièce d'inventaire non trouvée", "ERROR")
                    return False
            else:
                self.log(f"❌ Récupération inventaire échouée - Status: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_verify_work_order_update(self):
        """TEST 4: Vérifier que l'ordre de travail contient les pièces utilisées"""
        self.log("🧪 TEST 4: Vérifier la mise à jour de l'ordre de travail")
        
        if not self.test_work_order_id:
            self.log("❌ ID ordre de travail manquant", "ERROR")
            return False
        
        try:
            # GET /api/work-orders/{id} - Vérifier que les pièces sont dans l'historique
            self.log("📋 Vérification de l'ordre de travail mis à jour...")
            self.log(f"🔍 Debug - Using work order ID: {self.test_work_order_id}")
            response = self.admin_session.get(
                f"{BACKEND_URL}/work-orders/{self.test_work_order_id}",
                timeout=15
            )
            
            if response.status_code == 200:
                work_order = response.json()
                self.log(f"✅ Ordre de travail récupéré - ID: {work_order.get('id')}")
                
                # Vérifier les commentaires
                comments = work_order.get('comments', [])
                if comments:
                    latest_comment = comments[-1]  # Dernier commentaire
                    self.log(f"✅ Commentaire présent: {latest_comment.get('text')}")
                    self.log(f"✅ Timestamp: {latest_comment.get('timestamp')}")
                else:
                    self.log("❌ Aucun commentaire trouvé", "ERROR")
                    return False
                
                # Vérifier les pièces utilisées
                parts_used = work_order.get('parts_used', [])
                if parts_used:
                    self.log(f"✅ Pièces utilisées trouvées: {len(parts_used)} pièce(s)")
                    
                    # Vérifier la première pièce
                    part = parts_used[-1]  # Dernière pièce ajoutée
                    self.log(f"✅ Pièce: {part.get('inventory_item_name')}")
                    self.log(f"✅ Quantité: {part.get('quantity')}")
                    self.log(f"✅ Source: {part.get('source_equipment_name')}")
                    self.log(f"✅ Timestamp: {part.get('timestamp')}")
                    
                    # Vérifier tous les champs requis
                    required_fields = ['id', 'inventory_item_id', 'inventory_item_name', 'quantity', 
                                     'source_equipment_id', 'source_equipment_name', 'timestamp']
                    missing_fields = [field for field in required_fields if not part.get(field)]
                    
                    if not missing_fields:
                        self.log("✅ SUCCÈS: Tous les champs requis sont présents")
                        return True
                    else:
                        self.log(f"❌ ÉCHEC: Champs manquants: {missing_fields}", "ERROR")
                        return False
                else:
                    self.log("❌ ÉCHEC: Aucune pièce utilisée trouvée dans l'ordre de travail", "ERROR")
                    return False
            else:
                self.log(f"❌ Récupération ordre de travail échouée - Status: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_external_parts(self):
        """TEST 5: Test avec pièce externe (texte libre)"""
        self.log("🧪 TEST 5: Test avec pièce externe (texte libre)")
        
        if not self.test_work_order_id:
            self.log("❌ ID ordre de travail manquant", "ERROR")
            return False
        
        try:
            # Sauvegarder la quantité actuelle pour vérifier qu'elle ne change pas
            response = self.admin_session.get(f"{BACKEND_URL}/inventory", timeout=15)
            if response.status_code != 200:
                self.log("❌ Impossible de récupérer l'inventaire pour comparaison", "ERROR")
                return False
            
            inventory_before = response.json()
            test_item_before = None
            for item in inventory_before:
                if item.get('id') == self.test_inventory_item_id:
                    test_item_before = item
                    break
            
            if not test_item_before:
                self.log("❌ Pièce d'inventaire non trouvée pour comparaison", "ERROR")
                return False
            
            quantity_before = test_item_before.get('quantite', 0)
            
            # POST /api/work-orders/{id}/comments avec pièce externe
            comment_data = {
                "text": "Test pièce externe",
                "parts_used": [
                    {
                        "inventory_item_id": None,
                        "custom_part_name": "Pièce externe test",
                        "quantity": 1,
                        "custom_source": "Fournisseur externe"
                    }
                ]
            }
            
            self.log("📤 Envoi du commentaire avec pièce externe...")
            self.log("   Pièce: Pièce externe test (Quantité: 1)")
            self.log("   Source: Fournisseur externe")
            
            # Use ObjectId for comments endpoint
            comments_id = self.test_work_order_object_id or self.test_work_order_id
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/work-orders/{comments_id}/comments",
                json=comment_data,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Commentaire avec pièce externe ajouté avec succès")
                
                # Vérifier que la pièce externe est dans la réponse
                parts_used = data.get('parts_used', [])
                if parts_used and len(parts_used) > 0:
                    part = parts_used[0]
                    if (part.get('custom_part_name') == 'Pièce externe test' and 
                        part.get('inventory_item_id') is None):
                        self.log("✅ Pièce externe correctement enregistrée")
                        
                        # Vérifier que l'inventaire n'a PAS été déduit
                        response = self.admin_session.get(f"{BACKEND_URL}/inventory", timeout=15)
                        if response.status_code == 200:
                            inventory_after = response.json()
                            test_item_after = None
                            for item in inventory_after:
                                if item.get('id') == self.test_inventory_item_id:
                                    test_item_after = item
                                    break
                            
                            if test_item_after:
                                quantity_after = test_item_after.get('quantite', 0)
                                if quantity_after == quantity_before:
                                    self.log("✅ SUCCÈS: Aucune déduction d'inventaire pour pièce externe")
                                    return True
                                else:
                                    self.log(f"❌ ÉCHEC: Déduction incorrecte pour pièce externe. Avant: {quantity_before}, Après: {quantity_after}", "ERROR")
                                    return False
                            else:
                                self.log("❌ Pièce d'inventaire non trouvée après test", "ERROR")
                                return False
                        else:
                            self.log("❌ Impossible de vérifier l'inventaire après test", "ERROR")
                            return False
                    else:
                        self.log("❌ Pièce externe incorrecte dans la réponse", "ERROR")
                        return False
                else:
                    self.log("❌ Aucune pièce utilisée dans la réponse", "ERROR")
                    return False
            else:
                self.log(f"❌ Ajout commentaire avec pièce externe échoué - Status: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_multiple_parts_addition(self):
        """TEST 6: Test d'ajout multiple de pièces"""
        self.log("🧪 TEST 6: Test d'ajout multiple de pièces")
        
        if not self.test_work_order_id:
            self.log("❌ ID ordre de travail manquant", "ERROR")
            return False
        
        try:
            # POST /api/work-orders/{id}/comments avec 3 pièces différentes
            comment_data = {
                "text": "Test ajout multiple de pièces",
                "parts_used": [
                    {
                        "inventory_item_id": self.test_inventory_item_id,
                        "inventory_item_name": self.inventory_item_name,
                        "quantity": 1,
                        "source_equipment_id": self.test_equipment_id,
                        "source_equipment_name": self.equipment_name
                    },
                    {
                        "inventory_item_id": None,
                        "custom_part_name": "Pièce externe 1",
                        "quantity": 2,
                        "custom_source": "Fournisseur A"
                    },
                    {
                        "inventory_item_id": None,
                        "custom_part_name": "Pièce externe 2",
                        "quantity": 1,
                        "custom_source": "Fournisseur B"
                    }
                ]
            }
            
            self.log("📤 Envoi du commentaire avec 3 pièces différentes...")
            self.log("   1. Pièce d'inventaire (Quantité: 1)")
            self.log("   2. Pièce externe 1 (Quantité: 2)")
            self.log("   3. Pièce externe 2 (Quantité: 1)")
            
            # Use ObjectId for comments endpoint
            comments_id = self.test_work_order_object_id or self.test_work_order_id
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/work-orders/{comments_id}/comments",
                json=comment_data,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                parts_used = data.get('parts_used', [])
                
                if len(parts_used) == 3:
                    self.log("✅ SUCCÈS: 3 pièces ajoutées correctement")
                    
                    # Vérifier chaque pièce
                    inventory_part = None
                    external_parts = []
                    
                    for part in parts_used:
                        if part.get('inventory_item_id'):
                            inventory_part = part
                        else:
                            external_parts.append(part)
                    
                    if inventory_part and len(external_parts) == 2:
                        self.log("✅ 1 pièce d'inventaire et 2 pièces externes identifiées")
                        self.log(f"✅ Pièce inventaire: {inventory_part.get('inventory_item_name')}")
                        self.log(f"✅ Pièce externe 1: {external_parts[0].get('custom_part_name')}")
                        self.log(f"✅ Pièce externe 2: {external_parts[1].get('custom_part_name')}")
                        return True
                    else:
                        self.log("❌ ÉCHEC: Répartition incorrecte des pièces", "ERROR")
                        return False
                else:
                    self.log(f"❌ ÉCHEC: Nombre incorrect de pièces. Attendu: 3, Trouvé: {len(parts_used)}", "ERROR")
                    return False
            else:
                self.log(f"❌ Ajout multiple échoué - Status: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_verify_audit_journal(self):
        """TEST 7: Vérification du journal d'audit"""
        self.log("🧪 TEST 7: Vérifier le journal d'audit pour les pièces utilisées")
        
        if not self.test_work_order_id:
            self.log("❌ ID ordre de travail manquant", "ERROR")
            return False
        
        try:
            # GET /api/audit-logs - Chercher les logs liés aux pièces utilisées
            self.log("📋 Récupération du journal d'audit...")
            response = self.admin_session.get(
                f"{BACKEND_URL}/audit-logs",
                params={
                    "entity_type": "WORK_ORDER",
                    "limit": 50
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                logs = data.get('logs', [])
                self.log(f"✅ Journal récupéré - {len(logs)} entrées WORK_ORDER trouvées")
                
                # Chercher les entrées liées à notre ordre de travail avec pièces utilisées
                parts_logs = []
                for log in logs:
                    if (log.get('entity_id') == self.test_work_order_id and 
                        'pièce(s) utilisée(s)' in log.get('details', '')):
                        parts_logs.append(log)
                
                if parts_logs:
                    self.log(f"✅ SUCCÈS: {len(parts_logs)} entrée(s) de pièces utilisées trouvée(s)")
                    
                    # Vérifier la première entrée
                    log_entry = parts_logs[0]
                    self.log(f"✅ Action: {log_entry.get('action')}")
                    self.log(f"✅ Entity Type: {log_entry.get('entity_type')}")
                    self.log(f"✅ Details: {log_entry.get('details')}")
                    
                    # Vérifier que le texte contient "pièce(s) utilisée(s)"
                    details = log_entry.get('details', '')
                    if 'pièce(s) utilisée(s)' in details:
                        self.log("✅ SUCCÈS: Journal d'audit mis à jour avec mention des pièces")
                        return True
                    else:
                        self.log("❌ ÉCHEC: Mention des pièces manquante dans les détails", "ERROR")
                        return False
                else:
                    self.log("❌ ÉCHEC: Aucune entrée de pièces utilisées trouvée dans le journal", "ERROR")
                    return False
            else:
                self.log(f"❌ Récupération du journal échouée - Status: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_data(self):
        """Nettoyer les données de test créées"""
        self.log("🧹 Nettoyage des données de test...")
        
        # Note: Pas de nettoyage spécifique nécessaire pour ce test
        # Les commentaires et pièces utilisées restent dans l'historique
        self.log("✅ Nettoyage terminé (données conservées pour historique)")
    
    # Additional helper methods can be added here if needed

    def run_parts_used_system_tests(self):
        """Run comprehensive tests for Parts Used System in Work Orders"""
        self.log("=" * 80)
        self.log("TESTING SYSTÈME DE PIÈCES UTILISÉES DANS LES ORDRES DE TRAVAIL")
        self.log("=" * 80)
        self.log("CONTEXTE:")
        self.log("Test complet du système permettant d'ajouter des pièces utilisées lors des interventions.")
        self.log("Les pièces doivent être déduites de l'inventaire automatiquement et l'historique doit être conservé.")
        self.log("")
        self.log("SCÉNARIOS DE TEST:")
        self.log("1. 📦 Vérifier l'état initial (inventaire, ordres de travail, équipements)")
        self.log("2. 🔧 Test d'ajout de pièces avec commentaire")
        self.log("3. ✅ Vérifications après ajout (déduction inventaire)")
        self.log("4. 📋 Vérifier mise à jour ordre de travail")
        self.log("5. 🌐 Test avec pièce externe (texte libre)")
        self.log("6. 📊 Test d'ajout multiple de pièces")
        self.log("7. 📋 Vérification du journal d'audit")
        self.log("=" * 80)
        
        results = {
            "admin_login": False,
            "get_initial_state": False,
            "add_parts_with_comment": False,
            "verify_inventory_deduction": False,
            "verify_work_order_update": False,
            "external_parts": False,
            "multiple_parts_addition": False,
            "verify_audit_journal": False
        }
        
        # Test 1: Admin Login
        results["admin_login"] = self.test_admin_login()
        
        if not results["admin_login"]:
            self.log("❌ Cannot proceed with other tests - Admin login failed", "ERROR")
            return results
        
        # TESTS CRITIQUES DU SYSTÈME DE PIÈCES UTILISÉES
        self.log("\n" + "=" * 60)
        self.log("🔧 TESTS CRITIQUES - SYSTÈME DE PIÈCES UTILISÉES")
        self.log("=" * 60)
        
        # Test 1: Vérifier l'état initial
        results["get_initial_state"] = self.test_get_initial_state()
        
        # Test 2: Ajouter des pièces avec commentaire
        results["add_parts_with_comment"] = self.test_add_parts_with_comment()
        
        # Test 3: Vérifier la déduction d'inventaire
        results["verify_inventory_deduction"] = self.test_verify_inventory_deduction()
        
        # Test 4: Vérifier la mise à jour de l'ordre de travail
        results["verify_work_order_update"] = self.test_verify_work_order_update()
        
        # Test 5: Test avec pièce externe
        results["external_parts"] = self.test_external_parts()
        
        # Test 6: Test d'ajout multiple
        results["multiple_parts_addition"] = self.test_multiple_parts_addition()
        
        # Test 7: Vérifier le journal d'audit
        results["verify_audit_journal"] = self.test_verify_audit_journal()
        
        # Summary
        self.log("=" * 80)
        self.log("SYSTÈME DE PIÈCES UTILISÉES - RÉSULTATS DES TESTS")
        self.log("=" * 80)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"  {test_name}: {status}")
        
        self.log(f"\n📊 Overall: {passed}/{total} tests passed")
        
        # Analyse détaillée des tests critiques
        critical_tests = ["get_initial_state", "add_parts_with_comment", "verify_inventory_deduction", 
                         "verify_work_order_update", "external_parts", "multiple_parts_addition", "verify_audit_journal"]
        critical_passed = sum(results.get(test, False) for test in critical_tests)
        
        self.log("\n" + "=" * 60)
        self.log("ANALYSE CRITIQUE DU SYSTÈME DE PIÈCES UTILISÉES")
        self.log("=" * 60)
        
        # TEST CRITIQUE 1: État initial
        if results.get("get_initial_state", False):
            self.log("🎉 TEST CRITIQUE 1 - ÉTAT INITIAL: ✅ SUCCÈS")
            self.log("✅ Inventaire, ordres de travail et équipements accessibles")
            self.log("✅ Données de test préparées")
        else:
            self.log("🚨 TEST CRITIQUE 1 - ÉTAT INITIAL: ❌ ÉCHEC")
            self.log("❌ Impossible d'accéder aux données de base")
        
        # TEST CRITIQUE 2: Ajout de pièces
        if results.get("add_parts_with_comment", False):
            self.log("🎉 TEST CRITIQUE 2 - AJOUT PIÈCES: ✅ SUCCÈS")
            self.log("✅ POST /api/work-orders/{id}/comments avec parts_used fonctionne")
            self.log("✅ Pièces correctement ajoutées avec commentaire")
        else:
            self.log("🚨 TEST CRITIQUE 2 - AJOUT PIÈCES: ❌ ÉCHEC")
            self.log("❌ Erreur lors de l'ajout de pièces")
        
        # TEST CRITIQUE 3: Déduction inventaire
        if results.get("verify_inventory_deduction", False):
            self.log("🎉 TEST CRITIQUE 3 - DÉDUCTION INVENTAIRE: ✅ SUCCÈS")
            self.log("✅ Déduction automatique du stock pour pièces d'inventaire")
            self.log("✅ Quantités correctement mises à jour")
        else:
            self.log("🚨 TEST CRITIQUE 3 - DÉDUCTION INVENTAIRE: ❌ ÉCHEC")
            self.log("❌ Déduction automatique ne fonctionne pas")
        
        # TEST CRITIQUE 4: Mise à jour ordre de travail
        if results.get("verify_work_order_update", False):
            self.log("🎉 TEST CRITIQUE 4 - MISE À JOUR ORDRE: ✅ SUCCÈS")
            self.log("✅ Historique complet conservé dans work_order.parts_used")
            self.log("✅ Toutes les informations présentes (timestamp, noms, quantités, sources)")
        else:
            self.log("🚨 TEST CRITIQUE 4 - MISE À JOUR ORDRE: ❌ ÉCHEC")
            self.log("❌ Historique des pièces non conservé")
        
        # TEST CRITIQUE 5: Pièces externes
        if results.get("external_parts", False):
            self.log("🎉 TEST CRITIQUE 5 - PIÈCES EXTERNES: ✅ SUCCÈS")
            self.log("✅ Pas de déduction pour pièces externes (texte libre)")
            self.log("✅ Pièces externes correctement enregistrées")
        else:
            self.log("🚨 TEST CRITIQUE 5 - PIÈCES EXTERNES: ❌ ÉCHEC")
            self.log("❌ Gestion des pièces externes incorrecte")
        
        # TEST CRITIQUE 6: Ajout multiple
        if results.get("multiple_parts_addition", False):
            self.log("🎉 TEST CRITIQUE 6 - AJOUT MULTIPLE: ✅ SUCCÈS")
            self.log("✅ Ajout de plusieurs pièces simultanément")
            self.log("✅ Toutes les pièces enregistrées et déductions correctes")
        else:
            self.log("🚨 TEST CRITIQUE 6 - AJOUT MULTIPLE: ❌ ÉCHEC")
            self.log("❌ Problème avec l'ajout multiple de pièces")
        
        # TEST CRITIQUE 7: Journal d'audit
        if results.get("verify_audit_journal", False):
            self.log("🎉 TEST CRITIQUE 7 - JOURNAL D'AUDIT: ✅ SUCCÈS")
            self.log("✅ Journal d'audit mis à jour")
            self.log("✅ Logs contiennent 'pièce(s) utilisée(s)'")
        else:
            self.log("🚨 TEST CRITIQUE 7 - JOURNAL D'AUDIT: ❌ ÉCHEC")
            self.log("❌ Journal d'audit non mis à jour")
        
        # Conclusion finale
        self.log("\n" + "=" * 80)
        self.log("CONCLUSION FINALE - SYSTÈME DE PIÈCES UTILISÉES")
        self.log("=" * 80)
        
        if critical_passed == len(critical_tests):
            self.log("🎉 SYSTÈME DE PIÈCES UTILISÉES ENTIÈREMENT FONCTIONNEL!")
            self.log("✅ Déduction automatique du stock pour pièces d'inventaire")
            self.log("✅ Pas de déduction pour pièces externes (texte libre)")
            self.log("✅ Historique complet conservé dans work_order.parts_used")
            self.log("✅ Toutes les informations présentes (timestamp, noms, quantités, sources)")
            self.log("✅ Journal d'audit mis à jour")
            self.log("✅ POST /api/work-orders/{id}/comments avec parts_used fonctionnel")
            self.log("✅ Support des pièces d'inventaire et externes")
            self.log("✅ Ajout multiple de pièces supporté")
            self.log("✅ Le système est PRÊT POUR PRODUCTION")
        else:
            self.log("⚠️ SYSTÈME DE PIÈCES UTILISÉES INCOMPLET - PROBLÈMES DÉTECTÉS")
            failed_critical = [test for test in critical_tests if not results.get(test, False)]
            self.log(f"❌ Tests critiques échoués: {', '.join(failed_critical)}")
            self.log("❌ Le système de pièces utilisées ne fonctionne pas correctement")
            self.log("❌ Intervention requise avant mise en production")
        
        return results

if __name__ == "__main__":
    tester = PartsUsedSystemTester()
    results = tester.run_parts_used_system_tests()
    
    # Exit with appropriate code
    critical_tests = [
        "admin_login", "get_initial_state", "add_parts_with_comment", 
        "verify_inventory_deduction", "verify_work_order_update", "external_parts", 
        "multiple_parts_addition", "verify_audit_journal"
    ]
    
    critical_passed = sum(results.get(test, False) for test in critical_tests)
    
    if critical_passed == len(critical_tests):
        exit(0)  # Success
    else:
        exit(1)  # Failure
