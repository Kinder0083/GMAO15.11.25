#!/usr/bin/env python3
"""
Backend API Testing Script for GMAO Application
Tests Plan de Surveillance endpoints - CRUD complets
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
BACKEND_URL = "https://cmms-maintenance.preview.emergentagent.com/api"

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
    
    def test_cleanup_work_orders(self):
        """TEST 7: Nettoyer (supprimer les ordres de test créés)"""
        self.log("🧪 TEST 7: Nettoyer (supprimer les ordres de test créés)")
        
        if not self.created_work_orders:
            self.log("⚠️ Pas d'ordres de travail de test à supprimer", "WARNING")
            return True
        
        success_count = 0
        for wo_id in self.created_work_orders[:]:  # Copy to avoid modification during iteration
            try:
                response = self.admin_session.delete(
                    f"{BACKEND_URL}/work-orders/{wo_id}",
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log(f"✅ Ordre {wo_id} supprimé avec succès")
                    self.created_work_orders.remove(wo_id)
                    success_count += 1
                elif response.status_code == 404:
                    self.log(f"⚠️ Ordre {wo_id} déjà supprimé (Status 404)")
                    self.created_work_orders.remove(wo_id)
                    success_count += 1
                else:
                    self.log(f"❌ Suppression de l'ordre {wo_id} échouée - Status: {response.status_code}", "ERROR")
                    
            except requests.exceptions.RequestException as e:
                self.log(f"❌ Request failed for {wo_id} - Error: {str(e)}", "ERROR")
        
        self.log(f"✅ Nettoyage terminé: {success_count} ordres supprimés")
        return success_count > 0
    
    def cleanup_remaining_work_orders(self):
        """Nettoyer tous les ordres de travail créés pendant les tests"""
        self.log("🧹 Nettoyage des ordres de travail restants...")
        
        if not self.created_work_orders:
            self.log("Aucun ordre de travail à nettoyer")
            return True
        
        success_count = 0
        for wo_id in self.created_work_orders[:]:  # Copy list to avoid modification during iteration
            try:
                response = self.admin_session.delete(
                    f"{BACKEND_URL}/work-orders/{wo_id}",
                    timeout=10
                )
                
                if response.status_code in [200, 404]:
                    self.log(f"✅ Ordre {wo_id} nettoyé")
                    self.created_work_orders.remove(wo_id)
                    success_count += 1
                else:
                    self.log(f"⚠️ Impossible de nettoyer l'ordre {wo_id} - Status: {response.status_code}")
                    
            except Exception as e:
                self.log(f"⚠️ Erreur lors du nettoyage de l'ordre {wo_id}: {str(e)}")
        
        self.log(f"Nettoyage terminé: {success_count} ordres supprimés")
        return True
    
    # Removed old methods - replaced with work order time tracking tests
    
    def run_category_time_tracking_tests(self):
        """Run comprehensive tests for category time tracking in reports"""
        self.log("=" * 80)
        self.log("TESTING EVOLUTION HORAIRE DES MAINTENANCES - CATEGORY COUNTING")
        self.log("=" * 80)
        self.log("CONTEXTE: Test de l'endpoint 'Evolution horaire des maintenances' pour vérifier")
        self.log("le comptage de toutes les catégories, notamment:")
        self.log("- TRAVAUX_CURATIF")
        self.log("- TRAVAUX_DIVERS") 
        self.log("- FORMATION")
        self.log("")
        self.log("TESTS À EFFECTUER:")
        self.log("1. Se connecter en tant qu'admin")
        self.log("2. Créer ordre avec catégorie TRAVAUX_CURATIF + temps passé")
        self.log("3. Créer ordre avec catégorie TRAVAUX_DIVERS + temps passé")
        self.log("4. Créer ordre avec catégorie FORMATION + temps passé")
        self.log("5. Créer ordre avec catégorie CHANGEMENT_FORMAT + temps passé (comparaison)")
        self.log("6. Tester GET /api/reports/time-by-category?start_month=2025-11")
        self.log("7. Nettoyer les ordres de test créés")
        self.log("=" * 80)
        
        results = {
            "admin_login": False,
            "create_curatif_order": False,
            "create_divers_order": False,
            "create_formation_order": False,
            "create_changement_format_order": False,
            "test_time_by_category_stats": False,
            "cleanup_work_orders": False,
            "cleanup_remaining": False
        }
        
        # Test 1: Admin Login
        results["admin_login"] = self.test_admin_login()
        
        if not results["admin_login"]:
            self.log("❌ Cannot proceed with other tests - Admin login failed", "ERROR")
            return results
        
        # Test 2: Create TRAVAUX_CURATIF order
        results["create_curatif_order"] = self.test_create_curatif_order()
        
        # Test 3: Create TRAVAUX_DIVERS order
        results["create_divers_order"] = self.test_create_divers_order()
        
        # Test 4: Create FORMATION order
        results["create_formation_order"] = self.test_create_formation_order()
        
        # Test 5: Create CHANGEMENT_FORMAT order (for comparison)
        results["create_changement_format_order"] = self.test_create_changement_format_order()
        
        # Test 6: Test time-by-category stats
        results["test_time_by_category_stats"] = self.test_time_by_category_stats()
        
        # Test 7: Cleanup work orders
        results["cleanup_work_orders"] = self.test_cleanup_work_orders()
        
        # Test 8: Cleanup remaining
        results["cleanup_remaining"] = self.cleanup_remaining_work_orders()
        
        # Summary
        self.log("=" * 70)
        self.log("CATEGORY TIME TRACKING TEST RESULTS SUMMARY")
        self.log("=" * 70)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"  {test_name}: {status}")
        
        self.log(f"\n📊 Overall: {passed}/{total} tests passed")
        
        # Detailed analysis for critical tests
        critical_tests = ["create_curatif_order", "create_divers_order", "create_formation_order", 
                         "create_changement_format_order", "test_time_by_category_stats"]
        critical_passed = sum(results.get(test, False) for test in critical_tests)
        
        if critical_passed == len(critical_tests):
            self.log("🎉 CRITICAL SUCCESS: All main category tracking tests passed!")
            self.log("✅ POST /api/work-orders with categories works correctly")
            self.log("✅ POST /api/work-orders/{id}/add-time works for all categories")
            self.log("✅ GET /api/reports/time-by-category includes all categories")
            self.log("✅ TRAVAUX_CURATIF, TRAVAUX_DIVERS, FORMATION are counted correctly")
        else:
            self.log("🚨 CRITICAL FAILURE: Some main category tracking tests failed!")
            failed_critical = [test for test in critical_tests if not results.get(test, False)]
            self.log(f"❌ Failed critical tests: {', '.join(failed_critical)}")
        
        if results.get("test_time_by_category_stats", False):
            self.log("🎉 ENDPOINT EVOLUTION HORAIRE DES MAINTENANCES IS WORKING CORRECTLY!")
            self.log("✅ All categories are being counted in the histogram")
            self.log("✅ TRAVAUX_CURATIF, TRAVAUX_DIVERS, FORMATION have values > 0")
            self.log("✅ The reported issue is RESOLVED")
        else:
            self.log("⚠️ ENDPOINT ISSUE DETECTED - Categories may not be counted correctly")
            self.log("❌ The reported issue is NOT RESOLVED")
        
        return results

if __name__ == "__main__":
    tester = CategoryTimeTrackingTester()
    results = tester.run_category_time_tracking_tests()
    
    # Exit with appropriate code - allow cleanup to fail
    critical_tests = ["admin_login", "create_curatif_order", "create_divers_order", 
                     "create_formation_order", "create_changement_format_order", 
                     "test_time_by_category_stats"]
    
    critical_passed = sum(results.get(test, False) for test in critical_tests)
    
    if critical_passed == len(critical_tests):
        exit(0)  # Success
    else:
        exit(1)  # Failure