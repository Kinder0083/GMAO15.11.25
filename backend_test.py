#!/usr/bin/env python3
"""
Backend API Testing Script for GMAO Application
Tests GET /api/inventory/stats endpoint
"""

import requests
import json
import os
from datetime import datetime, timedelta

# Use the correct backend URL from frontend .env
BACKEND_URL = "https://gmao-iris-1.preview.emergentagent.com/api"

# Test credentials - admin account as specified in the request
ADMIN_EMAIL = "admin@gmao-iris.local"
ADMIN_PASSWORD = "Admin123!"

class InventoryStatsTester:
    def __init__(self):
        self.admin_session = requests.Session()
        self.admin_token = None
        self.admin_data = None
        self.inventory_data = None
        self.stats_data = None
        
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
    
    def test_get_inventory_data(self):
        """TEST 1: Récupérer les données d'inventaire pour validation"""
        self.log("🧪 TEST 1: Récupération des données d'inventaire")
        
        try:
            # GET /api/inventory - Récupérer tous les items d'inventaire
            self.log("📦 Récupération de l'inventaire complet...")
            response = self.admin_session.get(f"{BACKEND_URL}/inventory", timeout=15)
            
            if response.status_code == 200:
                self.inventory_data = response.json()
                self.log(f"✅ Inventaire récupéré - {len(self.inventory_data)} articles trouvés")
                
                # Analyser les données pour comprendre la répartition
                rupture_count = 0
                niveau_bas_count = 0
                normal_count = 0
                
                for item in self.inventory_data:
                    quantite = item.get('quantite', 0)
                    quantite_min = item.get('quantiteMin', 0)
                    nom = item.get('nom', 'N/A')
                    
                    if quantite <= 0:
                        rupture_count += 1
                        self.log(f"   📉 RUPTURE: {nom} (Quantité: {quantite})")
                    elif quantite <= quantite_min:
                        niveau_bas_count += 1
                        self.log(f"   ⚠️ NIVEAU BAS: {nom} (Quantité: {quantite}, Min: {quantite_min})")
                    else:
                        normal_count += 1
                
                self.log(f"📊 Analyse inventaire:")
                self.log(f"   - Articles en rupture (quantité <= 0): {rupture_count}")
                self.log(f"   - Articles niveau bas (0 < quantité <= quantiteMin): {niveau_bas_count}")
                self.log(f"   - Articles normaux: {normal_count}")
                self.log(f"   - Total alertes attendues: {rupture_count + niveau_bas_count}")
                
                return True
            else:
                self.log(f"❌ Récupération inventaire échouée - Status: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_inventory_stats_endpoint(self):
        """TEST 2: Tester l'endpoint GET /api/inventory/stats"""
        self.log("🧪 TEST 2: Test de l'endpoint GET /api/inventory/stats")
        
        try:
            # GET /api/inventory/stats
            self.log("📊 Appel de l'endpoint /api/inventory/stats...")
            response = self.admin_session.get(f"{BACKEND_URL}/inventory/stats", timeout=15)
            
            if response.status_code == 200:
                self.stats_data = response.json()
                self.log("✅ Endpoint /api/inventory/stats répond correctement (200 OK)")
                
                # Vérifier la structure de la réponse
                if 'rupture' in self.stats_data and 'niveau_bas' in self.stats_data:
                    rupture = self.stats_data.get('rupture')
                    niveau_bas = self.stats_data.get('niveau_bas')
                    
                    self.log(f"✅ Réponse contient les champs requis:")
                    self.log(f"   - rupture: {rupture}")
                    self.log(f"   - niveau_bas: {niveau_bas}")
                    
                    # Vérifier que les valeurs sont des entiers >= 0
                    if isinstance(rupture, int) and rupture >= 0:
                        self.log(f"✅ Champ 'rupture' est un entier >= 0: {rupture}")
                    else:
                        self.log(f"❌ Champ 'rupture' invalide: {rupture} (type: {type(rupture)})", "ERROR")
                        return False
                    
                    if isinstance(niveau_bas, int) and niveau_bas >= 0:
                        self.log(f"✅ Champ 'niveau_bas' est un entier >= 0: {niveau_bas}")
                    else:
                        self.log(f"❌ Champ 'niveau_bas' invalide: {niveau_bas} (type: {type(niveau_bas)})", "ERROR")
                        return False
                    
                    return True
                else:
                    self.log("❌ Réponse ne contient pas les champs requis 'rupture' et 'niveau_bas'", "ERROR")
                    self.log(f"Réponse reçue: {self.stats_data}", "ERROR")
                    return False
            else:
                self.log(f"❌ Endpoint /api/inventory/stats échoué - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_validate_calculations(self):
        """TEST 3: Valider les calculs en comparant avec les données d'inventaire"""
        self.log("🧪 TEST 3: Validation des calculs de statistiques")
        
        if not self.inventory_data or not self.stats_data:
            self.log("❌ Données d'inventaire ou de stats manquantes", "ERROR")
            return False
        
        try:
            # Calculer manuellement les statistiques à partir des données d'inventaire
            expected_rupture = 0
            expected_niveau_bas = 0
            
            for item in self.inventory_data:
                quantite = item.get('quantite', 0)
                quantite_min = item.get('quantiteMin', 0)
                
                if quantite <= 0:
                    expected_rupture += 1
                elif quantite <= quantite_min:
                    expected_niveau_bas += 1
            
            # Comparer avec les résultats de l'endpoint
            actual_rupture = self.stats_data.get('rupture')
            actual_niveau_bas = self.stats_data.get('niveau_bas')
            
            self.log("📊 Comparaison des calculs:")
            self.log(f"   Rupture - Attendu: {expected_rupture}, Reçu: {actual_rupture}")
            self.log(f"   Niveau bas - Attendu: {expected_niveau_bas}, Reçu: {actual_niveau_bas}")
            
            # Vérifier la correspondance
            if actual_rupture == expected_rupture:
                self.log("✅ Calcul 'rupture' correct")
            else:
                self.log(f"❌ Calcul 'rupture' incorrect - Attendu: {expected_rupture}, Reçu: {actual_rupture}", "ERROR")
                return False
            
            if actual_niveau_bas == expected_niveau_bas:
                self.log("✅ Calcul 'niveau_bas' correct")
            else:
                self.log(f"❌ Calcul 'niveau_bas' incorrect - Attendu: {expected_niveau_bas}, Reçu: {actual_niveau_bas}", "ERROR")
                return False
            
            # Vérifier le total des alertes
            total_expected = expected_rupture + expected_niveau_bas
            total_actual = actual_rupture + actual_niveau_bas
            
            self.log(f"📊 Total alertes - Attendu: {total_expected}, Reçu: {total_actual}")
            
            if total_actual == total_expected:
                self.log("✅ Total des alertes correct")
                return True
            else:
                self.log(f"❌ Total des alertes incorrect", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erreur lors de la validation - Error: {str(e)}", "ERROR")
            return False

    def test_detailed_analysis(self):
        """TEST 4: Analyse détaillée des articles par catégorie"""
        self.log("🧪 TEST 4: Analyse détaillée des articles par catégorie")
        
        if not self.inventory_data:
            self.log("❌ Données d'inventaire manquantes", "ERROR")
            return False
        
        try:
            self.log("📋 Analyse détaillée des articles d'inventaire:")
            
            rupture_items = []
            niveau_bas_items = []
            normal_items = []
            
            for item in self.inventory_data:
                quantite = item.get('quantite', 0)
                quantite_min = item.get('quantiteMin', 0)
                nom = item.get('nom', 'N/A')
                code = item.get('code', 'N/A')
                
                if quantite <= 0:
                    rupture_items.append({
                        'nom': nom,
                        'code': code,
                        'quantite': quantite,
                        'quantiteMin': quantite_min
                    })
                elif quantite <= quantite_min:
                    niveau_bas_items.append({
                        'nom': nom,
                        'code': code,
                        'quantite': quantite,
                        'quantiteMin': quantite_min
                    })
                else:
                    normal_items.append({
                        'nom': nom,
                        'code': code,
                        'quantite': quantite,
                        'quantiteMin': quantite_min
                    })
            
            self.log(f"📊 ARTICLES EN RUPTURE ({len(rupture_items)}):")
            for item in rupture_items[:5]:  # Afficher les 5 premiers
                self.log(f"   - {item['nom']} (Code: {item['code']}, Qté: {item['quantite']})")
            if len(rupture_items) > 5:
                self.log(f"   ... et {len(rupture_items) - 5} autres")
            
            self.log(f"📊 ARTICLES NIVEAU BAS ({len(niveau_bas_items)}):")
            for item in niveau_bas_items[:5]:  # Afficher les 5 premiers
                self.log(f"   - {item['nom']} (Code: {item['code']}, Qté: {item['quantite']}, Min: {item['quantiteMin']})")
            if len(niveau_bas_items) > 5:
                self.log(f"   ... et {len(niveau_bas_items) - 5} autres")
            
            self.log(f"📊 ARTICLES NORMAUX: {len(normal_items)}")
            
            # Vérifier que les calculs correspondent aux stats
            if (len(rupture_items) == self.stats_data.get('rupture') and 
                len(niveau_bas_items) == self.stats_data.get('niveau_bas')):
                self.log("✅ Analyse détaillée cohérente avec les statistiques")
                return True
            else:
                self.log("❌ Incohérence entre l'analyse détaillée et les statistiques", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erreur lors de l'analyse - Error: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_data(self):
        """Nettoyer les données de test créées"""
        self.log("🧹 Nettoyage des données de test...")
        
        # Note: Pas de nettoyage spécifique nécessaire pour ce test
        # Les tests sont en lecture seule
        self.log("✅ Nettoyage terminé (tests en lecture seule)")
    
    def run_inventory_stats_tests(self):
        """Run comprehensive tests for GET /api/inventory/stats endpoint"""
        self.log("=" * 80)
        self.log("TESTING ENDPOINT GET /api/inventory/stats")
        self.log("=" * 80)
        self.log("CONTEXTE:")
        self.log("Test du nouvel endpoint GET /api/inventory/stats pour afficher un badge d'alerte inventaire.")
        self.log("L'endpoint doit retourner les statistiques de rupture et niveau bas de l'inventaire.")
        self.log("")
        self.log("SCÉNARIOS DE TEST:")
        self.log("1. 🔐 Connexion admin (admin@gmao-iris.local / Admin123!)")
        self.log("2. 📦 Récupération des données d'inventaire pour validation")
        self.log("3. 📊 Test de l'endpoint GET /api/inventory/stats")
        self.log("4. ✅ Validation des calculs par comparaison avec GET /api/inventory")
        self.log("5. 📋 Analyse détaillée des articles par catégorie")
        self.log("=" * 80)
        
        results = {
            "admin_login": False,
            "get_inventory_data": False,
            "inventory_stats_endpoint": False,
            "validate_calculations": False,
            "detailed_analysis": False
        }
        
        # Test 1: Admin Login
        results["admin_login"] = self.test_admin_login()
        
        if not results["admin_login"]:
            self.log("❌ Cannot proceed with other tests - Admin login failed", "ERROR")
            return results
        
        # TESTS CRITIQUES DE L'ENDPOINT INVENTORY STATS
        self.log("\n" + "=" * 60)
        self.log("📊 TESTS CRITIQUES - ENDPOINT INVENTORY STATS")
        self.log("=" * 60)
        
        # Test 1: Récupérer les données d'inventaire
        results["get_inventory_data"] = self.test_get_inventory_data()
        
        # Test 2: Tester l'endpoint stats
        results["inventory_stats_endpoint"] = self.test_inventory_stats_endpoint()
        
        # Test 3: Valider les calculs
        results["validate_calculations"] = self.test_validate_calculations()
        
        # Test 4: Analyse détaillée
        results["detailed_analysis"] = self.test_detailed_analysis()
        
        # Summary
        self.log("=" * 80)
        self.log("ENDPOINT INVENTORY STATS - RÉSULTATS DES TESTS")
        self.log("=" * 80)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"  {test_name}: {status}")
        
        self.log(f"\n📊 Overall: {passed}/{total} tests passed")
        
        # Analyse détaillée des tests critiques
        critical_tests = ["admin_login", "get_inventory_data", "inventory_stats_endpoint", "validate_calculations", "detailed_analysis"]
        critical_passed = sum(results.get(test, False) for test in critical_tests)
        
        self.log("\n" + "=" * 60)
        self.log("ANALYSE CRITIQUE DE L'ENDPOINT INVENTORY STATS")
        self.log("=" * 60)
        
        # TEST CRITIQUE 1: Connexion admin
        if results.get("admin_login", False):
            self.log("🎉 TEST CRITIQUE 1 - CONNEXION ADMIN: ✅ SUCCÈS")
            self.log("✅ Connexion admin@gmao-iris.local / Admin123! réussie")
            self.log("✅ Token JWT obtenu et utilisé pour les requêtes")
        else:
            self.log("🚨 TEST CRITIQUE 1 - CONNEXION ADMIN: ❌ ÉCHEC")
            self.log("❌ Impossible de se connecter avec les identifiants admin")
        
        # TEST CRITIQUE 2: Données d'inventaire
        if results.get("get_inventory_data", False):
            self.log("🎉 TEST CRITIQUE 2 - DONNÉES INVENTAIRE: ✅ SUCCÈS")
            self.log("✅ GET /api/inventory fonctionne correctement")
            self.log("✅ Données d'inventaire récupérées pour validation")
        else:
            self.log("🚨 TEST CRITIQUE 2 - DONNÉES INVENTAIRE: ❌ ÉCHEC")
            self.log("❌ Impossible de récupérer les données d'inventaire")
        
        # TEST CRITIQUE 3: Endpoint stats
        if results.get("inventory_stats_endpoint", False):
            self.log("🎉 TEST CRITIQUE 3 - ENDPOINT STATS: ✅ SUCCÈS")
            self.log("✅ GET /api/inventory/stats répond correctement (200 OK)")
            self.log("✅ Réponse contient les champs requis: 'rupture' et 'niveau_bas'")
            self.log("✅ Valeurs sont des entiers >= 0")
        else:
            self.log("🚨 TEST CRITIQUE 3 - ENDPOINT STATS: ❌ ÉCHEC")
            self.log("❌ Endpoint /api/inventory/stats ne fonctionne pas")
        
        # TEST CRITIQUE 4: Validation calculs
        if results.get("validate_calculations", False):
            self.log("🎉 TEST CRITIQUE 4 - VALIDATION CALCULS: ✅ SUCCÈS")
            self.log("✅ Calculs de rupture corrects (quantité <= 0)")
            self.log("✅ Calculs de niveau bas corrects (0 < quantité <= quantiteMin)")
            self.log("✅ Total des alertes = rupture + niveau_bas")
        else:
            self.log("🚨 TEST CRITIQUE 4 - VALIDATION CALCULS: ❌ ÉCHEC")
            self.log("❌ Calculs incorrects dans l'endpoint stats")
        
        # TEST CRITIQUE 5: Analyse détaillée
        if results.get("detailed_analysis", False):
            self.log("🎉 TEST CRITIQUE 5 - ANALYSE DÉTAILLÉE: ✅ SUCCÈS")
            self.log("✅ Analyse détaillée des articles par catégorie")
            self.log("✅ Cohérence entre analyse manuelle et endpoint stats")
        else:
            self.log("🚨 TEST CRITIQUE 5 - ANALYSE DÉTAILLÉE: ❌ ÉCHEC")
            self.log("❌ Incohérence dans l'analyse détaillée")
        
        # Conclusion finale
        self.log("\n" + "=" * 80)
        self.log("CONCLUSION FINALE - ENDPOINT INVENTORY STATS")
        self.log("=" * 80)
        
        if critical_passed == len(critical_tests):
            self.log("🎉 ENDPOINT GET /api/inventory/stats ENTIÈREMENT FONCTIONNEL!")
            self.log("✅ Connexion admin réussie")
            self.log("✅ Endpoint répond correctement (200 OK)")
            self.log("✅ Champs requis présents: 'rupture' et 'niveau_bas'")
            self.log("✅ Valeurs sont des entiers >= 0")
            self.log("✅ Calculs corrects:")
            self.log("   - Articles en rupture: quantité <= 0")
            self.log("   - Articles niveau bas: 0 < quantité <= quantiteMin")
            self.log("✅ Total alertes = rupture + niveau_bas")
            self.log("✅ L'endpoint est PRÊT POUR PRODUCTION")
            
            if self.stats_data:
                self.log(f"📊 RÉSULTATS FINAUX:")
                self.log(f"   - Rupture: {self.stats_data.get('rupture')}")
                self.log(f"   - Niveau bas: {self.stats_data.get('niveau_bas')}")
                self.log(f"   - Total alertes: {self.stats_data.get('rupture', 0) + self.stats_data.get('niveau_bas', 0)}")
        else:
            self.log("⚠️ ENDPOINT INVENTORY STATS INCOMPLET - PROBLÈMES DÉTECTÉS")
            failed_critical = [test for test in critical_tests if not results.get(test, False)]
            self.log(f"❌ Tests critiques échoués: {', '.join(failed_critical)}")
            self.log("❌ L'endpoint /api/inventory/stats ne fonctionne pas correctement")
            self.log("❌ Intervention requise avant mise en production")
        
        return results

if __name__ == "__main__":
    tester = InventoryStatsTester()
    results = tester.run_inventory_stats_tests()
    
    # Exit with appropriate code
    critical_tests = [
        "admin_login", "get_inventory_data", "inventory_stats_endpoint", 
        "validate_calculations", "detailed_analysis"
    ]
    
    critical_passed = sum(results.get(test, False) for test in critical_tests)
    
    if critical_passed == len(critical_tests):
        exit(0)  # Success
    else:
        exit(1)  # Failure
