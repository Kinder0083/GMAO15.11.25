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
    
    def test_create_work_order_with_category(self, category, title, hours, minutes):
        """Créer un ordre de travail avec une catégorie spécifique et ajouter du temps"""
        self.log(f"🧪 Créer ordre avec catégorie {category} + temps passé ({hours}h{minutes:02d}min)")
        
        try:
            # Créer l'ordre de travail
            work_order_data = {
                "titre": title,
                "description": "Test",
                "priorite": "MOYENNE",
                "categorie": category,
                "statut": "EN_COURS"
            }
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/work-orders",
                json=work_order_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                work_order_id = data.get("id")
                self.created_work_orders.append(work_order_id)
                self.test_work_orders[category] = work_order_id
                
                self.log(f"✅ Ordre créé avec succès - ID: {work_order_id}")
                self.log(f"✅ Catégorie: {data.get('categorie')}")
                
                # Ajouter du temps passé
                time_data = {
                    "hours": hours,
                    "minutes": minutes
                }
                
                time_response = self.admin_session.post(
                    f"{BACKEND_URL}/work-orders/{work_order_id}/add-time",
                    json=time_data,
                    timeout=10
                )
                
                if time_response.status_code == 200:
                    time_data_response = time_response.json()
                    expected_time = hours + (minutes / 60.0)
                    actual_time = time_data_response.get("tempsReel")
                    
                    if actual_time == expected_time:
                        self.log(f"✅ Temps ajouté avec succès: {actual_time}h")
                        return True
                    else:
                        self.log(f"❌ Temps incorrect - Attendu: {expected_time}h, Reçu: {actual_time}h", "ERROR")
                        return False
                else:
                    self.log(f"❌ Ajout de temps échoué - Status: {time_response.status_code}", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Création d'ordre échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_create_curatif_order(self):
        """TEST 2: Créer ordre avec catégorie TRAVAUX_CURATIF + temps passé"""
        return self.test_create_work_order_with_category("TRAVAUX_CURATIF", "Test Curatif", 3, 30)
    
    def test_create_divers_order(self):
        """TEST 3: Créer ordre avec catégorie TRAVAUX_DIVERS + temps passé"""
        return self.test_create_work_order_with_category("TRAVAUX_DIVERS", "Test Divers", 2, 15)
    
    def test_create_formation_order(self):
        """TEST 4: Créer ordre avec catégorie FORMATION + temps passé"""
        return self.test_create_work_order_with_category("FORMATION", "Test Formation", 1, 45)
    
    def test_create_changement_format_order(self):
        """TEST 5: Créer ordre avec catégorie CHANGEMENT_FORMAT + temps passé (pour comparaison)"""
        return self.test_create_work_order_with_category("CHANGEMENT_FORMAT", "Test Format", 4, 0)
    
    def test_time_by_category_stats(self):
        """TEST 6: Vérifier l'endpoint de statistiques par catégorie"""
        self.log("🧪 TEST 6: Récupérer les stats du mois actuel (novembre 2025)")
        
        try:
            # Test avec le mois actuel (novembre 2025)
            response = self.admin_session.get(
                f"{BACKEND_URL}/reports/time-by-category?start_month=2025-11",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Récupération des statistiques réussie (Status 200)")
                
                # Vérifier la structure de la réponse
                if "months" not in data:
                    self.log("❌ Réponse manque le champ 'months'", "ERROR")
                    return False
                
                months = data["months"]
                if len(months) != 12:
                    self.log(f"❌ Attendu 12 mois, reçu {len(months)}", "ERROR")
                    return False
                
                self.log(f"✅ La réponse contient {len(months)} mois")
                
                # Chercher le mois actuel (novembre 2025)
                current_month_data = None
                for month in months:
                    if month.get("month") == "2025-11":
                        current_month_data = month
                        break
                
                if not current_month_data:
                    self.log("❌ Mois actuel (2025-11) non trouvé dans la réponse", "ERROR")
                    return False
                
                categories = current_month_data.get("categories", {})
                self.log(f"✅ Mois actuel trouvé avec catégories: {categories}")
                
                # Vérifier que les catégories problématiques ont des valeurs > 0
                expected_categories = {
                    "TRAVAUX_CURATIF": 3.5,  # 3h30min
                    "TRAVAUX_DIVERS": 2.25,  # 2h15min
                    "FORMATION": 1.75,       # 1h45min
                    "CHANGEMENT_FORMAT": 4.0  # 4h00min
                }
                
                all_categories_found = True
                for category, expected_time in expected_categories.items():
                    actual_time = categories.get(category, 0)
                    if actual_time >= expected_time:
                        self.log(f"✅ {category}: {actual_time}h (>= {expected_time}h attendu)")
                    else:
                        self.log(f"❌ {category}: {actual_time}h (< {expected_time}h attendu)", "ERROR")
                        all_categories_found = False
                
                if all_categories_found:
                    self.log("✅ IMPORTANT: Toutes les 3 catégories problématiques ont des valeurs > 0")
                    return True
                else:
                    self.log("❌ PROBLÈME: Certaines catégories ne sont pas comptées correctement", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Récupération des statistiques échouée - Status: {response.status_code}", "ERROR")
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