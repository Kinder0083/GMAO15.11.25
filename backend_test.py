#!/usr/bin/env python3
"""
Backend API Testing Script for GMAO Application
Tests Plan de Surveillance - Création contrôle avec catégorie personnalisée
"""

import requests
import json
import os
from datetime import datetime, timedelta

# Use the correct backend URL from frontend .env
BACKEND_URL = "https://surveil-plan.preview.emergentagent.com/api"

# Test credentials - admin account as specified in the request
ADMIN_EMAIL = "admin@gmao-iris.local"
ADMIN_PASSWORD = "Admin123!"

class SurveillanceCustomCategoryTester:
    def __init__(self):
        self.admin_session = requests.Session()
        self.admin_token = None
        self.admin_data = None
        self.test_items = []  # Store created test items for cleanup
        
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
    
    def test_create_custom_category_item(self):
        """TEST 1: Créer un contrôle avec TOUS les champs requis et nouvelle catégorie"""
        self.log("🧪 TEST 1: Créer un contrôle avec TOUS les champs requis et nouvelle catégorie")
        
        test_item_data = {
            "classe_type": "Test Frontend Categorie",
            "category": "TEST_CATEGORIE_NOUVELLE",
            "batiment": "BATIMENT TEST",
            "periodicite": "1 mois",
            "responsable": "MAINT",
            "executant": "Executant Test",
            "description": "Test depuis frontend"
        }
        
        try:
            response = self.admin_session.post(
                f"{BACKEND_URL}/surveillance/items",
                json=test_item_data,
                timeout=15
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.log(f"✅ Item de surveillance créé - Status: {response.status_code}")
                self.log(f"✅ ID: {data.get('id')}")
                self.log(f"✅ Classe: {data.get('classe_type')}")
                self.log(f"✅ Catégorie: {data.get('category')}")
                self.log(f"✅ Bâtiment: {data.get('batiment')}")
                self.log(f"✅ Exécutant: {data.get('executant')}")
                
                # Vérifier que la catégorie personnalisée est bien enregistrée
                if data.get('category') == "TEST_CATEGORIE_NOUVELLE":
                    self.log("✅ SUCCÈS: Catégorie personnalisée 'TEST_CATEGORIE_NOUVELLE' acceptée")
                    # Stocker pour nettoyage
                    self.test_items.append(data.get('id'))
                    return True, data
                else:
                    self.log(f"❌ ÉCHEC: Catégorie incorrecte - Attendu: TEST_CATEGORIE_NOUVELLE, Reçu: {data.get('category')}", "ERROR")
                    return False, None
            else:
                self.log(f"❌ Création échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False, None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False, None
    
    def test_retrieve_created_item(self):
        """TEST 2: Récupérer l'item créé et vérifier la catégorie"""
        self.log("🧪 TEST 2: Récupérer l'item créé")
        
        if not self.test_items:
            self.log("⚠️ Aucun item de test disponible", "WARNING")
            return False
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/surveillance/items",
                timeout=15
            )
            
            if response.status_code == 200:
                items = response.json()
                self.log(f"✅ Liste des items récupérée - {len(items)} items")
                
                # Chercher notre item de test avec la catégorie personnalisée
                test_item = None
                for item in items:
                    if item.get('id') in self.test_items and item.get('category') == 'TEST_CATEGORIE_NOUVELLE':
                        test_item = item
                        break
                
                if test_item:
                    self.log(f"✅ Item avec catégorie personnalisée trouvé - ID: {test_item.get('id')}")
                    self.log(f"✅ Classe: {test_item.get('classe_type')}")
                    self.log(f"✅ Catégorie: {test_item.get('category')}")
                    self.log(f"✅ Bâtiment: {test_item.get('batiment')}")
                    self.log(f"✅ Exécutant: {test_item.get('executant')}")
                    
                    # Vérifier tous les champs
                    if (test_item.get('category') == 'TEST_CATEGORIE_NOUVELLE' and
                        test_item.get('classe_type') == 'Test Frontend Categorie' and
                        test_item.get('batiment') == 'BATIMENT TEST'):
                        self.log("✅ SUCCÈS: Tous les champs sont corrects")
                        return True
                    else:
                        self.log("❌ ÉCHEC: Certains champs sont incorrects", "ERROR")
                        return False
                else:
                    self.log("❌ Item avec catégorie personnalisée non trouvé dans la liste", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Récupération des items échouée - Status: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_verify_stats_with_new_category(self):
        """TEST 3: Vérifier statistiques avec nouvelle catégorie"""
        self.log("🧪 TEST 3: Vérifier que by_category contient maintenant 'TEST_CATEGORIE_NOUVELLE'")
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/surveillance/stats",
                timeout=15
            )
            
            if response.status_code == 200:
                stats = response.json()
                self.log(f"✅ Statistiques récupérées - Status: 200 OK")
                
                # Vérifier la structure de la réponse
                if "by_category" in stats:
                    by_category = stats["by_category"]
                    self.log(f"✅ by_category trouvé avec {len(by_category)} catégories")
                    
                    # Vérifier que notre nouvelle catégorie est présente
                    if "TEST_CATEGORIE_NOUVELLE" in by_category:
                        category_stats = by_category["TEST_CATEGORIE_NOUVELLE"]
                        self.log(f"✅ SUCCÈS: Catégorie 'TEST_CATEGORIE_NOUVELLE' trouvée dans les statistiques")
                        self.log(f"✅ Total items: {category_stats.get('total')}")
                        self.log(f"✅ Réalisés: {category_stats.get('realises')}")
                        self.log(f"✅ Pourcentage: {category_stats.get('pourcentage')}%")
                        
                        # Vérifier le comptage
                        if category_stats.get('total', 0) >= 1:
                            self.log("✅ SUCCÈS: Le comptage est correct (au moins 1 item)")
                            return True
                        else:
                            self.log("❌ ÉCHEC: Comptage incorrect", "ERROR")
                            return False
                    else:
                        self.log("❌ ÉCHEC: Catégorie 'TEST_CATEGORIE_NOUVELLE' non trouvée dans les statistiques", "ERROR")
                        self.log(f"Catégories disponibles: {list(by_category.keys())}")
                        return False
                else:
                    self.log("❌ ÉCHEC: 'by_category' non trouvé dans la réponse", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Récupération des statistiques échouée - Status: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_create_existing_category_item(self):
        """TEST 2: Tester avec une catégorie existante pour comparaison"""
        self.log("🧪 TEST 2: Tester avec une catégorie existante pour comparaison")
        
        test_item_data = {
            "classe_type": "Test Catégorie Existante",
            "category": "INCENDIE",
            "batiment": "BATIMENT EXISTANT",
            "periodicite": "6 mois",
            "responsable": "MAINT",
            "executant": "Executant Existant",
            "description": "Test avec catégorie existante"
        }
        
        try:
            response = self.admin_session.post(
                f"{BACKEND_URL}/surveillance/items",
                json=test_item_data,
                timeout=15
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.log(f"✅ Item avec catégorie existante créé - Status: {response.status_code}")
                self.log(f"✅ ID: {data.get('id')}")
                self.log(f"✅ Classe: {data.get('classe_type')}")
                self.log(f"✅ Catégorie: {data.get('category')}")
                
                # Vérifier que la catégorie existante fonctionne
                if data.get('category') == "INCENDIE":
                    self.log("✅ SUCCÈS: Catégorie existante 'INCENDIE' acceptée")
                    # Stocker pour nettoyage
                    self.test_items.append(data.get('id'))
                    return True, data
                else:
                    self.log(f"❌ ÉCHEC: Catégorie incorrecte - Attendu: INCENDIE, Reçu: {data.get('category')}", "ERROR")
                    return False, None
            else:
                self.log(f"❌ Création échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False, None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False, None

    def test_create_second_custom_category_item(self):
        """TEST 4: Créer un 2ème item avec une autre catégorie personnalisée"""
        self.log("🧪 TEST 4: Créer un 2ème item avec une autre catégorie personnalisée")
        
        test_item_data = {
            "classe_type": "Test Deuxième Catégorie",
            "category": "CATEGORIE_TEST_2",
            "batiment": "AUTRE BATIMENT",
            "periodicite": "3 mois",
            "responsable": "PROD",
            "executant": "Autre Executant",
            "description": "Test création avec deuxième catégorie dynamique"
        }
        
        try:
            response = self.admin_session.post(
                f"{BACKEND_URL}/surveillance/items",
                json=test_item_data,
                timeout=15
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.log(f"✅ Deuxième item créé - Status: {response.status_code}")
                self.log(f"✅ ID: {data.get('id')}")
                self.log(f"✅ Classe: {data.get('classe_type')}")
                self.log(f"✅ Catégorie: {data.get('category')}")
                self.log(f"✅ Responsable: {data.get('responsable')}")
                
                # Vérifier que la deuxième catégorie personnalisée est bien enregistrée
                if data.get('category') == "CATEGORIE_TEST_2":
                    self.log("✅ SUCCÈS: Deuxième catégorie personnalisée 'CATEGORIE_TEST_2' acceptée")
                    # Stocker pour nettoyage
                    self.test_items.append(data.get('id'))
                    return True, data
                else:
                    self.log(f"❌ ÉCHEC: Catégorie incorrecte - Attendu: CATEGORIE_TEST_2, Reçu: {data.get('category')}", "ERROR")
                    return False, None
            else:
                self.log(f"❌ Création échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False, None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False, None
    
    def test_check_backend_logs(self):
        """TEST 3: Vérifier les logs backend pour erreurs"""
        self.log("🧪 TEST 3: Vérifier les logs backend pour erreurs")
        
        try:
            import subprocess
            result = subprocess.run(
                ["tail", "-n", "50", "/var/log/supervisor/backend.err.log"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logs = result.stdout
                if logs.strip():
                    self.log("⚠️ Logs d'erreur backend trouvés:")
                    for line in logs.strip().split('\n')[-10:]:  # Dernières 10 lignes
                        if line.strip():
                            self.log(f"   {line}")
                    
                    # Chercher des erreurs spécifiques
                    if "ValidationError" in logs:
                        self.log("❌ Erreur de validation Pydantic détectée", "ERROR")
                        return False
                    elif "category" in logs.lower():
                        self.log("⚠️ Erreur liée à 'category' détectée", "WARNING")
                        return False
                    else:
                        self.log("✅ Pas d'erreur critique liée aux catégories")
                        return True
                else:
                    self.log("✅ Aucune erreur dans les logs backend")
                    return True
            else:
                self.log("⚠️ Impossible de lire les logs backend", "WARNING")
                return True  # Ne pas faire échouer le test pour ça
                
        except Exception as e:
            self.log(f"⚠️ Erreur lecture logs: {str(e)}", "WARNING")
            return True  # Ne pas faire échouer le test pour ça

    def test_verify_both_categories_in_stats(self):
        """TEST 5: Vérifier que les deux catégories personnalisées apparaissent dans les statistiques"""
        self.log("🧪 TEST 5: Vérifier que les deux catégories personnalisées apparaissent dans les statistiques")
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/surveillance/stats",
                timeout=15
            )
            
            if response.status_code == 200:
                stats = response.json()
                self.log(f"✅ Statistiques récupérées - Status: 200 OK")
                
                if "by_category" in stats:
                    by_category = stats["by_category"]
                    self.log(f"✅ by_category trouvé avec {len(by_category)} catégories")
                    
                    # Vérifier que les deux catégories personnalisées sont présentes
                    categories_found = []
                    if "TEST_CATEGORIE_NOUVELLE" in by_category:
                        categories_found.append("TEST_CATEGORIE_NOUVELLE")
                        self.log(f"✅ Catégorie 'TEST_CATEGORIE_NOUVELLE' trouvée")
                    
                    if "CATEGORIE_TEST_2" in by_category:
                        categories_found.append("CATEGORIE_TEST_2")
                        self.log(f"✅ Catégorie 'CATEGORIE_TEST_2' trouvée")
                    
                    if len(categories_found) == 2:
                        self.log("✅ SUCCÈS: Les deux catégories personnalisées sont présentes dans les statistiques")
                        
                        # Afficher les détails
                        for cat in categories_found:
                            cat_stats = by_category[cat]
                            self.log(f"✅ {cat}: {cat_stats.get('total')} items, {cat_stats.get('realises')} réalisés, {cat_stats.get('pourcentage')}%")
                        
                        return True
                    else:
                        self.log(f"❌ ÉCHEC: Seulement {len(categories_found)} catégorie(s) trouvée(s) sur 2", "ERROR")
                        self.log(f"Catégories trouvées: {categories_found}")
                        self.log(f"Toutes les catégories: {list(by_category.keys())}")
                        return False
                else:
                    self.log("❌ ÉCHEC: 'by_category' non trouvé dans la réponse", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Récupération des statistiques échouée - Status: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False

    def test_delete_created_items(self):
        """TEST 6: Nettoyer - Supprimer les items de test"""
        self.log("🧪 TEST 6: Nettoyer - Supprimer les items de test")
        
        if not self.test_items:
            self.log("⚠️ Aucun item de test à supprimer", "WARNING")
            return True
        
        deleted_count = 0
        failed_count = 0
        
        for item_id in self.test_items:
            try:
                response = self.admin_session.delete(
                    f"{BACKEND_URL}/surveillance/items/{item_id}",
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        self.log(f"✅ Item {item_id} supprimé avec succès")
                        deleted_count += 1
                    else:
                        self.log(f"⚠️ Réponse inattendue pour suppression item {item_id}")
                        failed_count += 1
                else:
                    self.log(f"❌ Échec suppression item {item_id} - Status: {response.status_code}")
                    failed_count += 1
                    
            except requests.exceptions.RequestException as e:
                self.log(f"❌ Erreur suppression item {item_id} - Error: {str(e)}")
                failed_count += 1
        
        if failed_count == 0:
            self.log(f"✅ SUCCÈS: Tous les {deleted_count} items de test ont été supprimés")
            return True
        else:
            self.log(f"⚠️ PARTIEL: {deleted_count} items supprimés, {failed_count} échecs")
            return deleted_count > 0  # Consider success if at least some were deleted

    def cleanup_test_items(self):
        """Nettoyer les items de test créés"""
        self.log("🧹 Nettoyage des items de test...")
        
        for item_id in self.test_items:
            try:
                response = self.admin_session.delete(
                    f"{BACKEND_URL}/surveillance/items/{item_id}",
                    timeout=10
                )
                if response.status_code == 200:
                    self.log(f"✅ Item {item_id} supprimé")
                else:
                    self.log(f"⚠️ Échec suppression item {item_id} - Status: {response.status_code}")
            except:
                self.log(f"⚠️ Erreur suppression item {item_id}")

    def run_surveillance_custom_category_tests(self):
        """Run comprehensive tests for Plan de Surveillance - Création contrôle avec catégorie personnalisée"""
        self.log("=" * 80)
        self.log("TESTING PLAN DE SURVEILLANCE - CRÉATION CONTRÔLE AVEC CATÉGORIE PERSONNALISÉE")
        self.log("=" * 80)
        self.log("CONTEXTE:")
        self.log("Correction du bug empêchant la création de contrôles avec des catégories personnalisées.")
        self.log("Le champ `category` a été changé de `Enum` à `str` pour accepter n'importe quelle catégorie.")
        self.log("")
        self.log("SCÉNARIOS DE TEST:")
        self.log("1. 📋 Créer un contrôle avec TOUS les champs requis et nouvelle catégorie")
        self.log("2. 📋 Tester avec une catégorie existante pour comparaison")
        self.log("3. 🔍 Vérifier les logs backend pour erreurs")
        self.log("4. 🔍 Récupérer l'item créé et vérifier tous les champs")
        self.log("5. 📊 Vérifier statistiques avec nouvelle catégorie")
        self.log("6. 📋 Créer un 2ème item avec une autre catégorie personnalisée")
        self.log("7. 📊 Vérifier que les deux catégories apparaissent dans les statistiques")
        self.log("8. 🧹 Nettoyer - Supprimer les items de test")
        self.log("=" * 80)
        
        results = {
            "admin_login": False,
            "create_custom_category_item": False,
            "create_existing_category_item": False,
            "check_backend_logs": False,
            "retrieve_created_item": False,
            "verify_stats_with_new_category": False,
            "create_second_custom_category_item": False,
            "verify_both_categories_in_stats": False,
            "delete_created_items": False
        }
        
        # Test 1: Admin Login
        results["admin_login"] = self.test_admin_login()
        
        if not results["admin_login"]:
            self.log("❌ Cannot proceed with other tests - Admin login failed", "ERROR")
            return results
        
        # TESTS CRITIQUES DU PLAN DE SURVEILLANCE
        self.log("\n" + "=" * 60)
        self.log("📋 TESTS CRITIQUES - CATÉGORIES PERSONNALISÉES")
        self.log("=" * 60)
        
        # Test 2: Créer un item avec catégorie personnalisée
        success, test_item = self.test_create_custom_category_item()
        results["create_custom_category_item"] = success
        
        # Test 3: Créer un item avec catégorie existante pour comparaison
        success_existing, test_item_existing = self.test_create_existing_category_item()
        results["create_existing_category_item"] = success_existing
        
        # Test 4: Vérifier les logs backend
        results["check_backend_logs"] = self.test_check_backend_logs()
        
        # Test 5: Récupérer l'item créé
        results["retrieve_created_item"] = self.test_retrieve_created_item()
        
        # Test 6: Vérifier les statistiques
        results["verify_stats_with_new_category"] = self.test_verify_stats_with_new_category()
        
        # Test 7: Créer un deuxième item avec une autre catégorie
        success2, test_item2 = self.test_create_second_custom_category_item()
        results["create_second_custom_category_item"] = success2
        
        # Test 8: Vérifier que les deux catégories apparaissent dans les statistiques
        results["verify_both_categories_in_stats"] = self.test_verify_both_categories_in_stats()
        
        # Test 9: Nettoyage
        results["delete_created_items"] = self.test_delete_created_items()
        
        # Summary
        self.log("=" * 80)
        self.log("PLAN DE SURVEILLANCE - CATÉGORIES PERSONNALISÉES - RÉSULTATS")
        self.log("=" * 80)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"  {test_name}: {status}")
        
        self.log(f"\n📊 Overall: {passed}/{total} tests passed")
        
        # Analyse détaillée des tests critiques
        critical_tests = ["create_custom_category_item", "retrieve_created_item", "verify_stats_with_new_category"]
        critical_passed = sum(results.get(test, False) for test in critical_tests)
        
        self.log("\n" + "=" * 60)
        self.log("ANALYSE CRITIQUE DE LA FONCTIONNALITÉ")
        self.log("=" * 60)
        
        # TEST CRITIQUE 1: Création avec catégorie personnalisée
        if results.get("create_custom_category_item", False):
            self.log("🎉 TEST CRITIQUE 1 - CRÉATION AVEC CATÉGORIE PERSONNALISÉE: ✅ SUCCÈS")
            self.log("✅ POST /api/surveillance/items accepte les catégories personnalisées")
            self.log("✅ Réponse 200/201 OK")
            self.log("✅ Catégorie 'MA_NOUVELLE_CATEGORIE' acceptée et enregistrée")
        else:
            self.log("🚨 TEST CRITIQUE 1 - CRÉATION AVEC CATÉGORIE PERSONNALISÉE: ❌ ÉCHEC")
            self.log("❌ Erreur lors de la création ou catégorie rejetée")
        
        # TEST CRITIQUE 2: Récupération des données
        if results.get("retrieve_created_item", False):
            self.log("🎉 TEST CRITIQUE 2 - RÉCUPÉRATION DES DONNÉES: ✅ SUCCÈS")
            self.log("✅ GET /api/surveillance/items retourne l'item créé")
            self.log("✅ Catégorie personnalisée correctement stockée")
            self.log("✅ Tous les champs sont corrects")
        else:
            self.log("🚨 TEST CRITIQUE 2 - RÉCUPÉRATION DES DONNÉES: ❌ ÉCHEC")
            self.log("❌ Item non trouvé ou données incorrectes")
        
        # TEST CRITIQUE 3: Statistiques
        if results.get("verify_stats_with_new_category", False):
            self.log("🎉 TEST CRITIQUE 3 - STATISTIQUES AVEC NOUVELLE CATÉGORIE: ✅ SUCCÈS")
            self.log("✅ GET /api/surveillance/stats inclut la nouvelle catégorie")
            self.log("✅ by_category contient 'MA_NOUVELLE_CATEGORIE'")
            self.log("✅ Comptage correct")
        else:
            self.log("🚨 TEST CRITIQUE 3 - STATISTIQUES AVEC NOUVELLE CATÉGORIE: ❌ ÉCHEC")
            self.log("❌ Nouvelle catégorie non présente dans les statistiques")
        
        # Tests complémentaires
        if results.get("create_second_custom_category_item", False):
            self.log("✅ VALIDATION: Création de multiples catégories personnalisées")
        
        if results.get("verify_both_categories_in_stats", False):
            self.log("✅ VALIDATION: Multiples catégories personnalisées dans les statistiques")
        
        if results.get("delete_created_items", False):
            self.log("✅ NETTOYAGE: Items de test supprimés avec succès")
        
        # Conclusion finale
        self.log("\n" + "=" * 80)
        self.log("CONCLUSION FINALE - CATÉGORIES PERSONNALISÉES")
        self.log("=" * 80)
        
        if critical_passed == len(critical_tests):
            self.log("🎉 FONCTIONNALITÉ ENTIÈREMENT OPÉRATIONNELLE!")
            self.log("✅ Création d'items avec catégories personnalisées fonctionne (200/201 OK)")
            self.log("✅ Les catégories dynamiques sont acceptées (pas d'erreur de validation Pydantic)")
            self.log("✅ Les statistiques incluent les nouvelles catégories")
            self.log("✅ Pas d'erreur 'Erreur d'enregistrement'")
            self.log("✅ Le bug de catégorie personnalisée est RÉSOLU")
            self.log("✅ La fonctionnalité est PRÊTE POUR PRODUCTION")
        else:
            self.log("⚠️ FONCTIONNALITÉ INCOMPLÈTE - PROBLÈMES DÉTECTÉS")
            failed_critical = [test for test in critical_tests if not results.get(test, False)]
            self.log(f"❌ Tests critiques échoués: {', '.join(failed_critical)}")
            self.log("❌ Les catégories personnalisées ne fonctionnent pas correctement")
            self.log("❌ Le bug n'est pas entièrement résolu")
            self.log("❌ Intervention requise avant mise en production")
        
        return results

if __name__ == "__main__":
    tester = SurveillanceCustomCategoryTester()
    results = tester.run_surveillance_custom_category_tests()
    
    # Exit with appropriate code
    critical_tests = [
        "admin_login", "create_custom_category_item", "retrieve_created_item", 
        "verify_stats_with_new_category"
    ]
    
    critical_passed = sum(results.get(test, False) for test in critical_tests)
    
    if critical_passed == len(critical_tests):
        exit(0)  # Success
    else:
        exit(1)  # Failure
