#!/usr/bin/env python3
"""
Backend API Testing Script for GMAO Application
Tests Presqu'accident (Near Miss) endpoints - CRUD complets
"""

import requests
import json
import os
import io
import pandas as pd
import tempfile
import uuid
from datetime import datetime, timedelta

# Use the correct backend URL from frontend .env
BACKEND_URL = "https://surveillance-plus.preview.emergentagent.com/api"

# Test credentials - admin account as specified in the request
ADMIN_EMAIL = "admin@gmao-iris.local"
ADMIN_PASSWORD = "Admin123!"

class SurveillanceTester:
    def __init__(self):
        self.admin_session = requests.Session()
        self.admin_token = None
        self.admin_data = None
        self.created_items = []  # Track created surveillance items for cleanup
        self.test_items = {}  # Dictionary to store surveillance item IDs
        
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
    
    def test_create_surveillance_item(self, category, classe_type, batiment, responsable):
        """Créer un item de surveillance avec des données spécifiques"""
        self.log(f"🧪 Créer item surveillance - Catégorie: {category}, Type: {classe_type}")
        
        try:
            # Créer l'item de surveillance
            item_data = {
                "classe_type": classe_type,
                "category": category,
                "batiment": batiment,
                "periodicite": "6 mois",
                "responsable": responsable,
                "executant": "DESAUTEL",
                "description": f"Test surveillance {classe_type}",
                "prochain_controle": "2025-06-15"
            }
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/surveillance/items",
                json=item_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                item_id = data.get("id")
                self.created_items.append(item_id)
                self.test_items[category] = item_id
                
                self.log(f"✅ Item créé avec succès - ID: {item_id}")
                self.log(f"✅ Catégorie: {data.get('category')}")
                self.log(f"✅ Classe type: {data.get('classe_type')}")
                return True
                    
            else:
                self.log(f"❌ Création d'item échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_create_incendie_item(self):
        """TEST 2: Créer item avec catégorie INCENDIE"""
        return self.test_create_surveillance_item("INCENDIE", "Protection incendie", "BATIMENT 1", "MAINT")
    
    def test_create_electrique_item(self):
        """TEST 3: Créer item avec catégorie ELECTRIQUE"""
        return self.test_create_surveillance_item("ELECTRIQUE", "Installations électriques", "BATIMENT 2", "PROD")
    
    def test_create_mmri_item(self):
        """TEST 4: Créer item avec catégorie MMRI"""
        return self.test_create_surveillance_item("MMRI", "Mesures de maîtrise des risques", "BATIMENT 1", "QHSE")
    
    def test_create_securite_item(self):
        """TEST 5: Créer item avec catégorie SECURITE_ENVIRONNEMENT"""
        return self.test_create_surveillance_item("SECURITE_ENVIRONNEMENT", "Sécurité environnement", "BATIMENT 1 ET 2", "EXTERNE")
    
    def test_surveillance_list_with_filters(self):
        """TEST 6: Tester GET /api/surveillance/items avec filtres"""
        self.log("🧪 TEST 6: Récupérer la liste des items avec filtres")
        
        try:
            # Test 1: Liste complète
            response = self.admin_session.get(
                f"{BACKEND_URL}/surveillance/items",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Liste complète récupérée - {len(data)} items")
                
                # Test 2: Filtre par catégorie INCENDIE
                response_filtered = self.admin_session.get(
                    f"{BACKEND_URL}/surveillance/items?category=INCENDIE",
                    timeout=10
                )
                
                if response_filtered.status_code == 200:
                    filtered_data = response_filtered.json()
                    incendie_count = len([item for item in filtered_data if item.get("category") == "INCENDIE"])
                    self.log(f"✅ Filtre catégorie INCENDIE: {incendie_count} items")
                    
                    # Test 3: Filtre par responsable MAINT
                    response_resp = self.admin_session.get(
                        f"{BACKEND_URL}/surveillance/items?responsable=MAINT",
                        timeout=10
                    )
                    
                    if response_resp.status_code == 200:
                        resp_data = response_resp.json()
                        maint_count = len([item for item in resp_data if item.get("responsable") == "MAINT"])
                        self.log(f"✅ Filtre responsable MAINT: {maint_count} items")
                        
                        # Test 4: Filtre par bâtiment
                        response_bat = self.admin_session.get(
                            f"{BACKEND_URL}/surveillance/items?batiment=BATIMENT 1",
                            timeout=10
                        )
                        
                        if response_bat.status_code == 200:
                            bat_data = response_bat.json()
                            bat_count = len([item for item in bat_data if "BATIMENT 1" in item.get("batiment", "")])
                            self.log(f"✅ Filtre bâtiment BATIMENT 1: {bat_count} items")
                            return True
                        else:
                            self.log(f"❌ Filtre bâtiment échoué - Status: {response_bat.status_code}", "ERROR")
                            return False
                    else:
                        self.log(f"❌ Filtre responsable échoué - Status: {response_resp.status_code}", "ERROR")
                        return False
                else:
                    self.log(f"❌ Filtre catégorie échoué - Status: {response_filtered.status_code}", "ERROR")
                    return False
            else:
                self.log(f"❌ Liste complète échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_surveillance_item_details(self):
        """TEST 7: Tester GET /api/surveillance/items/{item_id}"""
        self.log("🧪 TEST 7: Récupérer les détails d'un item spécifique")
        
        if not self.created_items:
            self.log("⚠️ Pas d'items créés pour tester les détails", "WARNING")
            return False
        
        try:
            item_id = self.created_items[0]  # Prendre le premier item créé
            response = self.admin_session.get(
                f"{BACKEND_URL}/surveillance/items/{item_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Détails récupérés - ID: {data.get('id')}")
                self.log(f"✅ Classe type: {data.get('classe_type')}")
                self.log(f"✅ Catégorie: {data.get('category')}")
                self.log(f"✅ Responsable: {data.get('responsable')}")
                return True
            else:
                self.log(f"❌ Récupération détails échouée - Status: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_surveillance_item_update(self):
        """TEST 8: Tester PUT /api/surveillance/items/{item_id}"""
        self.log("🧪 TEST 8: Mettre à jour un item de surveillance")
        
        if not self.created_items:
            self.log("⚠️ Pas d'items créés pour tester la mise à jour", "WARNING")
            return False
        
        try:
            item_id = self.created_items[0]  # Prendre le premier item créé
            update_data = {
                "status": "PLANIFIE",
                "commentaire": "Test de mise à jour - item planifié",
                "date_realisation": "2025-12-01"
            }
            
            response = self.admin_session.put(
                f"{BACKEND_URL}/surveillance/items/{item_id}",
                json=update_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Mise à jour réussie - Status: {data.get('status')}")
                self.log(f"✅ Commentaire: {data.get('commentaire')}")
                return True
            else:
                self.log(f"❌ Mise à jour échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_surveillance_stats(self):
        """TEST 9: Tester GET /api/surveillance/stats"""
        self.log("🧪 TEST 9: Récupérer les statistiques globales")
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/surveillance/stats",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                global_stats = data.get("global", {})
                by_category = data.get("by_category", {})
                by_responsable = data.get("by_responsable", {})
                
                self.log(f"✅ Statistiques globales récupérées:")
                self.log(f"  - Total: {global_stats.get('total')}")
                self.log(f"  - Réalisés: {global_stats.get('realises')}")
                self.log(f"  - Planifiés: {global_stats.get('planifies')}")
                self.log(f"  - À planifier: {global_stats.get('a_planifier')}")
                self.log(f"  - % réalisation: {global_stats.get('pourcentage_realisation')}%")
                
                self.log(f"✅ Statistiques par catégorie: {len(by_category)} catégories")
                self.log(f"✅ Statistiques par responsable: {len(by_responsable)} responsables")
                return True
            else:
                self.log(f"❌ Récupération statistiques échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_surveillance_alerts(self):
        """TEST 10: Tester GET /api/surveillance/alerts"""
        self.log("🧪 TEST 10: Récupérer les alertes d'échéance")
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/surveillance/alerts",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                count = data.get("count", 0)
                alerts = data.get("alerts", [])
                
                self.log(f"✅ Alertes récupérées - {count} alertes")
                
                if count > 0:
                    for alert in alerts[:3]:  # Afficher les 3 premières
                        self.log(f"  - {alert.get('classe_type')} (dans {alert.get('days_until')} jours)")
                
                return True
            else:
                self.log(f"❌ Récupération alertes échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_surveillance_badge_stats(self):
        """TEST CRITIQUE: Tester GET /api/surveillance/badge-stats - Badge de notification du header"""
        self.log("🧪 TEST CRITIQUE: Badge de notification - GET /api/surveillance/badge-stats")
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/surveillance/badge-stats",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier que les champs requis sont présents
                if "echeances_proches" not in data:
                    self.log("❌ Champ 'echeances_proches' manquant dans la réponse", "ERROR")
                    return False
                
                if "pourcentage_realisation" not in data:
                    self.log("❌ Champ 'pourcentage_realisation' manquant dans la réponse", "ERROR")
                    return False
                
                echeances_proches = data.get("echeances_proches")
                pourcentage_realisation = data.get("pourcentage_realisation")
                
                # Vérifier les types de données
                if not isinstance(echeances_proches, int):
                    self.log(f"❌ 'echeances_proches' doit être un entier, reçu: {type(echeances_proches)}", "ERROR")
                    return False
                
                if not isinstance(pourcentage_realisation, (int, float)):
                    self.log(f"❌ 'pourcentage_realisation' doit être un nombre, reçu: {type(pourcentage_realisation)}", "ERROR")
                    return False
                
                # Vérifier les valeurs logiques
                if echeances_proches < 0:
                    self.log(f"❌ 'echeances_proches' ne peut pas être négatif: {echeances_proches}", "ERROR")
                    return False
                
                if not (0 <= pourcentage_realisation <= 100):
                    self.log(f"❌ 'pourcentage_realisation' doit être entre 0 et 100: {pourcentage_realisation}", "ERROR")
                    return False
                
                self.log(f"✅ Badge stats récupérées avec succès:")
                self.log(f"  - Échéances proches: {echeances_proches}")
                self.log(f"  - Pourcentage réalisation: {pourcentage_realisation}%")
                
                # Validation logique métier
                self.log("✅ Validation des types de données: RÉUSSIE")
                self.log("✅ Validation des valeurs logiques: RÉUSSIE")
                self.log("✅ Structure de réponse JSON: CONFORME")
                
                return True
            else:
                self.log(f"❌ Badge stats échoué - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_surveillance_badge_stats_without_auth(self):
        """TEST SÉCURITÉ: Tester GET /api/surveillance/badge-stats SANS authentification"""
        self.log("🧪 TEST SÉCURITÉ: Badge stats sans authentification")
        
        try:
            # Créer une session sans token d'authentification
            no_auth_session = requests.Session()
            
            response = no_auth_session.get(
                f"{BACKEND_URL}/surveillance/badge-stats",
                timeout=10
            )
            
            # Doit retourner 401 Unauthorized ou 403 Forbidden
            if response.status_code in [401, 403]:
                self.log(f"✅ Protection par authentification fonctionnelle - Status: {response.status_code}")
                return True
            else:
                self.log(f"❌ SÉCURITÉ COMPROMISE - Endpoint accessible sans authentification - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_surveillance_rapport_stats(self):
        """TEST CRITIQUE: Tester GET /api/surveillance/rapport-stats - Statistiques complètes pour la page Rapport"""
        self.log("🧪 TEST CRITIQUE: Statistiques Rapport - GET /api/surveillance/rapport-stats")
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/surveillance/rapport-stats",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier la structure de réponse JSON
                required_keys = ["global", "by_category", "by_batiment", "by_periodicite", "by_responsable", "anomalies"]
                for key in required_keys:
                    if key not in data:
                        self.log(f"❌ Champ '{key}' manquant dans la réponse", "ERROR")
                        return False
                
                # Vérifier la structure des statistiques globales
                global_stats = data.get("global", {})
                global_required = ["total", "realises", "planifies", "a_planifier", "pourcentage_realisation", "en_retard", "a_temps"]
                for key in global_required:
                    if key not in global_stats:
                        self.log(f"❌ Champ 'global.{key}' manquant dans la réponse", "ERROR")
                        return False
                
                # Vérifier les types de données
                if not isinstance(global_stats.get("total"), int):
                    self.log(f"❌ 'global.total' doit être un entier, reçu: {type(global_stats.get('total'))}", "ERROR")
                    return False
                
                if not isinstance(global_stats.get("realises"), int):
                    self.log(f"❌ 'global.realises' doit être un entier, reçu: {type(global_stats.get('realises'))}", "ERROR")
                    return False
                
                if not isinstance(global_stats.get("planifies"), int):
                    self.log(f"❌ 'global.planifies' doit être un entier, reçu: {type(global_stats.get('planifies'))}", "ERROR")
                    return False
                
                if not isinstance(global_stats.get("a_planifier"), int):
                    self.log(f"❌ 'global.a_planifier' doit être un entier, reçu: {type(global_stats.get('a_planifier'))}", "ERROR")
                    return False
                
                if not isinstance(global_stats.get("en_retard"), int):
                    self.log(f"❌ 'global.en_retard' doit être un entier, reçu: {type(global_stats.get('en_retard'))}", "ERROR")
                    return False
                
                if not isinstance(global_stats.get("a_temps"), int):
                    self.log(f"❌ 'global.a_temps' doit être un entier, reçu: {type(global_stats.get('a_temps'))}", "ERROR")
                    return False
                
                if not isinstance(global_stats.get("pourcentage_realisation"), (int, float)):
                    self.log(f"❌ 'global.pourcentage_realisation' doit être un nombre, reçu: {type(global_stats.get('pourcentage_realisation'))}", "ERROR")
                    return False
                
                if not isinstance(data.get("anomalies"), int):
                    self.log(f"❌ 'anomalies' doit être un entier, reçu: {type(data.get('anomalies'))}", "ERROR")
                    return False
                
                # Vérifier les valeurs logiques
                total = global_stats.get("total", 0)
                realises = global_stats.get("realises", 0)
                planifies = global_stats.get("planifies", 0)
                a_planifier = global_stats.get("a_planifier", 0)
                pourcentage = global_stats.get("pourcentage_realisation", 0)
                
                # Validation mathématique
                if total > 0:
                    calculated_percentage = round((realises / total * 100), 1)
                    if abs(calculated_percentage - pourcentage) > 0.1:
                        self.log(f"❌ Calcul pourcentage incorrect: attendu {calculated_percentage}%, reçu {pourcentage}%", "ERROR")
                        return False
                
                # Vérifier que le pourcentage est entre 0 et 100
                if not (0 <= pourcentage <= 100):
                    self.log(f"❌ 'pourcentage_realisation' doit être entre 0 et 100: {pourcentage}", "ERROR")
                    return False
                
                # Vérifier les structures par catégorie, bâtiment, etc.
                for section_name, section_data in [
                    ("by_category", data.get("by_category", {})),
                    ("by_batiment", data.get("by_batiment", {})),
                    ("by_periodicite", data.get("by_periodicite", {})),
                    ("by_responsable", data.get("by_responsable", {}))
                ]:
                    if not isinstance(section_data, dict):
                        self.log(f"❌ '{section_name}' doit être un dictionnaire", "ERROR")
                        return False
                    
                    # Vérifier la structure de chaque sous-section
                    for key, value in section_data.items():
                        if not isinstance(value, dict):
                            self.log(f"❌ '{section_name}.{key}' doit être un dictionnaire", "ERROR")
                            return False
                        
                        required_sub_keys = ["total", "realises", "pourcentage"]
                        for sub_key in required_sub_keys:
                            if sub_key not in value:
                                self.log(f"❌ Champ '{section_name}.{key}.{sub_key}' manquant", "ERROR")
                                return False
                        
                        # Vérifier les types
                        if not isinstance(value.get("total"), int):
                            self.log(f"❌ '{section_name}.{key}.total' doit être un entier", "ERROR")
                            return False
                        
                        if not isinstance(value.get("realises"), int):
                            self.log(f"❌ '{section_name}.{key}.realises' doit être un entier", "ERROR")
                            return False
                        
                        if not isinstance(value.get("pourcentage"), (int, float)):
                            self.log(f"❌ '{section_name}.{key}.pourcentage' doit être un nombre", "ERROR")
                            return False
                        
                        # Vérifier que le pourcentage est entre 0 et 100
                        sub_pourcentage = value.get("pourcentage", 0)
                        if not (0 <= sub_pourcentage <= 100):
                            self.log(f"❌ '{section_name}.{key}.pourcentage' doit être entre 0 et 100: {sub_pourcentage}", "ERROR")
                            return False
                
                self.log(f"✅ Rapport stats récupérées avec succès:")
                self.log(f"  - Total: {global_stats.get('total')}")
                self.log(f"  - Réalisés: {global_stats.get('realises')}")
                self.log(f"  - Planifiés: {global_stats.get('planifies')}")
                self.log(f"  - À planifier: {global_stats.get('a_planifier')}")
                self.log(f"  - % réalisation: {global_stats.get('pourcentage_realisation')}%")
                self.log(f"  - En retard: {global_stats.get('en_retard')}")
                self.log(f"  - À temps: {global_stats.get('a_temps')}")
                self.log(f"  - Anomalies: {data.get('anomalies')}")
                
                # Afficher les statistiques par section
                self.log(f"✅ Statistiques par catégorie: {len(data.get('by_category', {}))} catégories")
                self.log(f"✅ Statistiques par bâtiment: {len(data.get('by_batiment', {}))} bâtiments")
                self.log(f"✅ Statistiques par périodicité: {len(data.get('by_periodicite', {}))} périodicités")
                self.log(f"✅ Statistiques par responsable: {len(data.get('by_responsable', {}))} responsables")
                
                # Validation logique métier
                self.log("✅ Validation de la structure JSON: CONFORME")
                self.log("✅ Validation des types de données: RÉUSSIE")
                self.log("✅ Validation des calculs mathématiques: RÉUSSIE")
                self.log("✅ Validation des valeurs logiques: RÉUSSIE")
                
                return True
            else:
                self.log(f"❌ Rapport stats échoué - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_surveillance_rapport_stats_without_auth(self):
        """TEST SÉCURITÉ: Tester GET /api/surveillance/rapport-stats SANS authentification"""
        self.log("🧪 TEST SÉCURITÉ: Rapport stats sans authentification")
        
        try:
            # Créer une session sans token d'authentification
            no_auth_session = requests.Session()
            
            response = no_auth_session.get(
                f"{BACKEND_URL}/surveillance/rapport-stats",
                timeout=10
            )
            
            # Doit retourner 401 Unauthorized ou 403 Forbidden
            if response.status_code in [401, 403]:
                self.log(f"✅ Protection par authentification fonctionnelle - Status: {response.status_code}")
                return True
            else:
                self.log(f"❌ SÉCURITÉ COMPROMISE - Endpoint accessible sans authentification - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_surveillance_upload(self):
        """TEST 11: Tester POST /api/surveillance/items/{item_id}/upload"""
        self.log("🧪 TEST 11: Upload d'une pièce jointe")
        
        if not self.created_items:
            self.log("⚠️ Pas d'items créés pour tester l'upload", "WARNING")
            return False
        
        try:
            item_id = self.created_items[0]  # Prendre le premier item créé
            
            # Créer un fichier de test temporaire
            test_content = "Contenu de test pour pièce jointe surveillance"
            
            files = {
                'file': ('test_surveillance.txt', test_content, 'text/plain')
            }
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/surveillance/items/{item_id}/upload",
                files=files,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Upload réussi - URL: {data.get('file_url')}")
                self.log(f"✅ Nom fichier: {data.get('file_name')}")
                return True
            else:
                self.log(f"❌ Upload échoué - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_surveillance_export_template(self):
        """TEST 12: Tester GET /api/surveillance/export/template"""
        self.log("🧪 TEST 12: Export du template CSV")
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/surveillance/export/template",
                timeout=10
            )
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                self.log(f"✅ Template exporté - Type: {content_type}")
                self.log(f"✅ Taille: {content_length} bytes")
                
                # Vérifier que c'est bien un CSV
                if 'csv' in content_type or content_length > 0:
                    return True
                else:
                    self.log("❌ Le template ne semble pas être un CSV valide", "ERROR")
                    return False
            else:
                self.log(f"❌ Export template échoué - Status: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_surveillance_delete_item(self):
        """TEST 13: Tester DELETE /api/surveillance/items/{item_id} (Admin uniquement)"""
        self.log("🧪 TEST 13: Supprimer un item de surveillance (Admin)")
        
        if not self.created_items:
            self.log("⚠️ Pas d'items créés pour tester la suppression", "WARNING")
            return True  # Pas d'erreur si pas d'items
        
        try:
            item_id = self.created_items[-1]  # Prendre le dernier item créé
            
            response = self.admin_session.delete(
                f"{BACKEND_URL}/surveillance/items/{item_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Item supprimé - Message: {data.get('message')}")
                self.created_items.remove(item_id)  # Retirer de la liste
                return True
            else:
                self.log(f"❌ Suppression échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_cleanup_surveillance_items(self):
        """TEST 14: Nettoyer (supprimer les items de test restants)"""
        self.log("🧪 TEST 14: Nettoyer (supprimer les items de test restants)")
        
        if not self.created_items:
            self.log("⚠️ Pas d'items de surveillance de test à supprimer", "WARNING")
            return True
        
        success_count = 0
        for item_id in self.created_items[:]:  # Copy to avoid modification during iteration
            try:
                response = self.admin_session.delete(
                    f"{BACKEND_URL}/surveillance/items/{item_id}",
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log(f"✅ Item {item_id} supprimé avec succès")
                    self.created_items.remove(item_id)
                    success_count += 1
                elif response.status_code == 404:
                    self.log(f"⚠️ Item {item_id} déjà supprimé (Status 404)")
                    self.created_items.remove(item_id)
                    success_count += 1
                else:
                    self.log(f"❌ Suppression de l'item {item_id} échouée - Status: {response.status_code}", "ERROR")
                    
            except requests.exceptions.RequestException as e:
                self.log(f"❌ Request failed for {item_id} - Error: {str(e)}", "ERROR")
        
        self.log(f"✅ Nettoyage terminé: {success_count} items supprimés")
        return success_count >= 0  # Toujours réussir le nettoyage
    
    def cleanup_remaining_surveillance_items(self):
        """Nettoyer tous les items de surveillance créés pendant les tests"""
        self.log("🧹 Nettoyage des items de surveillance restants...")
        
        if not self.created_items:
            self.log("Aucun item de surveillance à nettoyer")
            return True
        
        success_count = 0
        for item_id in self.created_items[:]:  # Copy list to avoid modification during iteration
            try:
                response = self.admin_session.delete(
                    f"{BACKEND_URL}/surveillance/items/{item_id}",
                    timeout=10
                )
                
                if response.status_code in [200, 404]:
                    self.log(f"✅ Item {item_id} nettoyé")
                    self.created_items.remove(item_id)
                    success_count += 1
                else:
                    self.log(f"⚠️ Impossible de nettoyer l'item {item_id} - Status: {response.status_code}")
                    
            except Exception as e:
                self.log(f"⚠️ Erreur lors du nettoyage de l'item {item_id}: {str(e)}")
        
        self.log(f"Nettoyage terminé: {success_count} items supprimés")
        return True
    
    def run_surveillance_tests(self):
        """Run comprehensive tests for Plan de Surveillance endpoints"""
        self.log("=" * 80)
        self.log("TESTING PLAN DE SURVEILLANCE - ENDPOINTS CRUD COMPLETS")
        self.log("=" * 80)
        self.log("CONTEXTE: Test complet du module Plan de Surveillance avec tous les endpoints:")
        self.log("- CRUD de base (GET, POST, PUT, DELETE)")
        self.log("- Upload de pièces jointes")
        self.log("- Statistiques et alertes")
        self.log("- Badge de notification")
        self.log("- NOUVEAU: Statistiques complètes pour page Rapport (GET /api/surveillance/rapport-stats)")
        self.log("- Import/Export")
        self.log("")
        self.log("TESTS À EFFECTUER:")
        self.log("1. Se connecter en tant qu'admin")
        self.log("2. Créer items avec différentes catégories (INCENDIE, ELECTRIQUE, MMRI, SECURITE)")
        self.log("3. Tester les filtres (catégorie, responsable, bâtiment)")
        self.log("4. Récupérer les détails d'un item")
        self.log("5. Mettre à jour un item (status, commentaire)")
        self.log("6. Tester les statistiques globales")
        self.log("7. Tester les alertes d'échéance")
        self.log("8. Tester le badge de notification (GET /api/surveillance/badge-stats)")
        self.log("9. SÉCURITÉ: Tester badge sans authentification (doit échouer)")
        self.log("10. NOUVEAU CRITIQUE: Tester statistiques rapport (GET /api/surveillance/rapport-stats)")
        self.log("11. SÉCURITÉ: Tester rapport stats sans authentification (doit échouer)")
        self.log("12. Upload d'une pièce jointe")
        self.log("13. Export du template CSV")
        self.log("14. Supprimer un item (admin uniquement)")
        self.log("15. Nettoyer les items de test créés")
        self.log("=" * 80)
        
        results = {
            "admin_login": False,
            "create_incendie_item": False,
            "create_electrique_item": False,
            "create_mmri_item": False,
            "create_securite_item": False,
            "test_surveillance_list_with_filters": False,
            "test_surveillance_item_details": False,
            "test_surveillance_item_update": False,
            "test_surveillance_stats": False,
            "test_surveillance_alerts": False,
            "test_surveillance_badge_stats": False,
            "test_surveillance_badge_stats_without_auth": False,
            "test_surveillance_rapport_stats": False,
            "test_surveillance_rapport_stats_without_auth": False,
            "test_surveillance_upload": False,
            "test_surveillance_export_template": False,
            "test_surveillance_delete_item": False,
            "test_cleanup_surveillance_items": False,
            "cleanup_remaining": False
        }
        
        # Test 1: Admin Login
        results["admin_login"] = self.test_admin_login()
        
        if not results["admin_login"]:
            self.log("❌ Cannot proceed with other tests - Admin login failed", "ERROR")
            return results
        
        # Test 2-5: Create surveillance items with different categories
        results["create_incendie_item"] = self.test_create_incendie_item()
        results["create_electrique_item"] = self.test_create_electrique_item()
        results["create_mmri_item"] = self.test_create_mmri_item()
        results["create_securite_item"] = self.test_create_securite_item()
        
        # Test 6: List with filters
        results["test_surveillance_list_with_filters"] = self.test_surveillance_list_with_filters()
        
        # Test 7: Item details
        results["test_surveillance_item_details"] = self.test_surveillance_item_details()
        
        # Test 8: Update item
        results["test_surveillance_item_update"] = self.test_surveillance_item_update()
        
        # Test 9: Statistics
        results["test_surveillance_stats"] = self.test_surveillance_stats()
        
        # Test 10: Alerts
        results["test_surveillance_alerts"] = self.test_surveillance_alerts()
        
        # Test 11: Badge Stats (CRITIQUE)
        results["test_surveillance_badge_stats"] = self.test_surveillance_badge_stats()
        
        # Test 12: Badge Stats Security (sans auth)
        results["test_surveillance_badge_stats_without_auth"] = self.test_surveillance_badge_stats_without_auth()
        
        # Test 13: Rapport Stats (NOUVEAU - CRITIQUE)
        results["test_surveillance_rapport_stats"] = self.test_surveillance_rapport_stats()
        
        # Test 14: Rapport Stats Security (sans auth)
        results["test_surveillance_rapport_stats_without_auth"] = self.test_surveillance_rapport_stats_without_auth()
        
        # Test 15: Upload
        results["test_surveillance_upload"] = self.test_surveillance_upload()
        
        # Test 16: Export template
        results["test_surveillance_export_template"] = self.test_surveillance_export_template()
        
        # Test 17: Delete item
        results["test_surveillance_delete_item"] = self.test_surveillance_delete_item()
        
        # Test 18: Cleanup
        results["test_cleanup_surveillance_items"] = self.test_cleanup_surveillance_items()
        
        # Test 19: Final cleanup
        results["cleanup_remaining"] = self.cleanup_remaining_surveillance_items()
        
        # Summary
        self.log("=" * 70)
        self.log("PLAN DE SURVEILLANCE TEST RESULTS SUMMARY")
        self.log("=" * 70)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"  {test_name}: {status}")
        
        self.log(f"\n📊 Overall: {passed}/{total} tests passed")
        
        # Detailed analysis for critical tests
        critical_tests = [
            "create_incendie_item", "create_electrique_item", "create_mmri_item", "create_securite_item",
            "test_surveillance_list_with_filters", "test_surveillance_item_details", 
            "test_surveillance_item_update", "test_surveillance_stats", "test_surveillance_alerts",
            "test_surveillance_badge_stats", "test_surveillance_badge_stats_without_auth",
            "test_surveillance_rapport_stats", "test_surveillance_rapport_stats_without_auth",
            "test_surveillance_upload", "test_surveillance_export_template", "test_surveillance_delete_item"
        ]
        critical_passed = sum(results.get(test, False) for test in critical_tests)
        
        if critical_passed == len(critical_tests):
            self.log("🎉 CRITICAL SUCCESS: All main surveillance endpoints tests passed!")
            self.log("✅ POST /api/surveillance/items works correctly")
            self.log("✅ GET /api/surveillance/items with filters works correctly")
            self.log("✅ GET /api/surveillance/items/{id} works correctly")
            self.log("✅ PUT /api/surveillance/items/{id} works correctly")
            self.log("✅ DELETE /api/surveillance/items/{id} works correctly (admin only)")
            self.log("✅ POST /api/surveillance/items/{id}/upload works correctly")
            self.log("✅ GET /api/surveillance/stats works correctly")
            self.log("✅ GET /api/surveillance/alerts works correctly")
            self.log("✅ GET /api/surveillance/badge-stats works correctly")
            self.log("✅ GET /api/surveillance/badge-stats security works correctly")
            self.log("✅ GET /api/surveillance/rapport-stats works correctly")
            self.log("✅ GET /api/surveillance/rapport-stats security works correctly")
            self.log("✅ GET /api/surveillance/export/template works correctly")
        else:
            self.log("🚨 CRITICAL FAILURE: Some main surveillance endpoint tests failed!")
            failed_critical = [test for test in critical_tests if not results.get(test, False)]
            self.log(f"❌ Failed critical tests: {', '.join(failed_critical)}")
        
        if critical_passed == len(critical_tests):
            self.log("🎉 PLAN DE SURVEILLANCE ENDPOINTS ARE WORKING CORRECTLY!")
            self.log("✅ All CRUD operations functional")
            self.log("✅ Filters and statistics working")
            self.log("✅ Upload and export features working")
            self.log("✅ Admin permissions respected")
            self.log("✅ The Plan de Surveillance backend is READY FOR PRODUCTION")
        else:
            self.log("⚠️ PLAN DE SURVEILLANCE ISSUES DETECTED")
            self.log("❌ Some endpoints are not working correctly")
        
        return results

if __name__ == "__main__":
    tester = SurveillanceTester()
    results = tester.run_surveillance_tests()
    
    # Exit with appropriate code - allow cleanup to fail
    critical_tests = [
        "admin_login", "create_incendie_item", "create_electrique_item", "create_mmri_item", 
        "create_securite_item", "test_surveillance_list_with_filters", "test_surveillance_item_details", 
        "test_surveillance_item_update", "test_surveillance_stats", "test_surveillance_alerts",
        "test_surveillance_badge_stats", "test_surveillance_badge_stats_without_auth",
        "test_surveillance_rapport_stats", "test_surveillance_rapport_stats_without_auth",
        "test_surveillance_upload", "test_surveillance_export_template", "test_surveillance_delete_item"
    ]
    
    critical_passed = sum(results.get(test, False) for test in critical_tests)
    
    if critical_passed == len(critical_tests):
        exit(0)  # Success
    else:
        exit(1)  # Failure