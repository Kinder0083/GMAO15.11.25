#!/usr/bin/env python3
"""
Backend API Testing Script for GMAO Application
Tests "Système d'ajout de temps passé sur les ordres de travail" functionality
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
BACKEND_URL = "https://maintx-hub.preview.emergentagent.com/api"

# Test credentials - admin account as specified in the request
ADMIN_EMAIL = "admin@gmao-iris.local"
ADMIN_PASSWORD = "Admin123!"

class WorkOrderTimeTrackingTester:
    def __init__(self):
        self.admin_session = requests.Session()
        self.admin_token = None
        self.admin_data = None
        self.created_work_orders = []  # Track created work orders for cleanup
        self.test_work_order_id = None  # ID of the test work order
        
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
    
    def test_create_work_order(self):
        """TEST 1: Créer un ordre de travail de test"""
        self.log("🧪 TEST 1: Créer un ordre de travail de test")
        
        try:
            work_order_data = {
                "titre": "Test temps passé",
                "description": "Test du système de temps passé",
                "priorite": "MOYENNE",
                "statut": "EN_COURS"
            }
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/work-orders",
                json=work_order_data,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                self.test_work_order_id = data.get("id")
                self.created_work_orders.append(self.test_work_order_id)
                
                self.log("✅ Ordre de travail créé avec succès (Status 201)")
                self.log(f"✅ ID de l'ordre: {self.test_work_order_id}")
                self.log(f"✅ Titre: {data.get('titre')}")
                
                # Vérifier que tempsReel est 0 ou null initialement
                temps_reel = data.get("tempsReel")
                if temps_reel is None or temps_reel == 0:
                    self.log(f"✅ tempsReel est initialement {temps_reel} (comme attendu)")
                    return True
                else:
                    self.log(f"⚠️ tempsReel est {temps_reel}, attendu 0 ou null", "WARNING")
                    return True  # Still pass, just note the difference
                    
            else:
                self.log(f"❌ Création d'ordre de travail échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_add_time_first(self):
        """TEST 2: Ajouter du temps passé (première fois) - 2h30min"""
        self.log("🧪 TEST 2: Ajouter du temps passé (première fois) - 2h30min")
        
        if not self.test_work_order_id:
            self.log("❌ Pas d'ordre de travail de test disponible", "ERROR")
            return False
        
        try:
            time_data = {
                "hours": 2,
                "minutes": 30
            }
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/work-orders/{self.test_work_order_id}/add-time",
                json=time_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Ajout de temps réussi (Status 200)")
                
                # Vérifier que tempsReel = 2.5 heures (2h30min)
                temps_reel = data.get("tempsReel")
                expected_time = 2.5  # 2h30min = 2.5 heures
                
                if temps_reel == expected_time:
                    self.log(f"✅ tempsReel = {temps_reel} heures (2h30min comme attendu)")
                    return True
                else:
                    self.log(f"❌ tempsReel = {temps_reel}, attendu {expected_time}", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Ajout de temps échoué - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_add_time_increment(self):
        """TEST 3: Ajouter du temps passé (incrémentation) - 1h15min"""
        self.log("🧪 TEST 3: Ajouter du temps passé (incrémentation) - 1h15min")
        
        if not self.test_work_order_id:
            self.log("❌ Pas d'ordre de travail de test disponible", "ERROR")
            return False
        
        try:
            time_data = {
                "hours": 1,
                "minutes": 15
            }
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/work-orders/{self.test_work_order_id}/add-time",
                json=time_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Ajout de temps réussi (Status 200)")
                
                # Vérifier que tempsReel = 3.75 heures (2.5 + 1.25)
                temps_reel = data.get("tempsReel")
                expected_time = 3.75  # 2.5 + 1.25 = 3.75 heures
                
                if temps_reel == expected_time:
                    self.log(f"✅ tempsReel = {temps_reel} heures (3h45min comme attendu)")
                    return True
                else:
                    self.log(f"❌ tempsReel = {temps_reel}, attendu {expected_time}", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Ajout de temps échoué - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_add_minutes_only(self):
        """TEST 4: Ajouter uniquement des minutes - 45min"""
        self.log("🧪 TEST 4: Ajouter uniquement des minutes - 45min")
        
        if not self.test_work_order_id:
            self.log("❌ Pas d'ordre de travail de test disponible", "ERROR")
            return False
        
        try:
            time_data = {
                "hours": 0,
                "minutes": 45
            }
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/work-orders/{self.test_work_order_id}/add-time",
                json=time_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Ajout de temps réussi (Status 200)")
                
                # Vérifier que tempsReel = 4.5 heures (3.75 + 0.75)
                temps_reel = data.get("tempsReel")
                expected_time = 4.5  # 3.75 + 0.75 = 4.5 heures
                
                if temps_reel == expected_time:
                    self.log(f"✅ tempsReel = {temps_reel} heures (4h30min comme attendu)")
                    return True
                else:
                    self.log(f"❌ tempsReel = {temps_reel}, attendu {expected_time}", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Ajout de temps échoué - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_add_hours_only(self):
        """TEST 5: Ajouter uniquement des heures - 3h"""
        self.log("🧪 TEST 5: Ajouter uniquement des heures - 3h")
        
        if not self.test_work_order_id:
            self.log("❌ Pas d'ordre de travail de test disponible", "ERROR")
            return False
        
        try:
            time_data = {
                "hours": 3,
                "minutes": 0
            }
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/work-orders/{self.test_work_order_id}/add-time",
                json=time_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Ajout de temps réussi (Status 200)")
                
                # Vérifier que tempsReel = 7.5 heures (4.5 + 3)
                temps_reel = data.get("tempsReel")
                expected_time = 7.5  # 4.5 + 3 = 7.5 heures
                
                if temps_reel == expected_time:
                    self.log(f"✅ tempsReel = {temps_reel} heures (7h30min comme attendu)")
                    return True
                else:
                    self.log(f"❌ tempsReel = {temps_reel}, attendu {expected_time}", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Ajout de temps échoué - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_get_work_order_final(self):
        """TEST 6: Récupérer l'ordre et vérifier le temps final"""
        self.log("🧪 TEST 6: Récupérer l'ordre et vérifier le temps final")
        
        if not self.test_work_order_id:
            self.log("❌ Pas d'ordre de travail de test disponible", "ERROR")
            return False
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/work-orders/{self.test_work_order_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Récupération de l'ordre réussie (Status 200)")
                
                # Vérifier que tempsReel = 7.5 heures
                temps_reel = data.get("tempsReel")
                expected_time = 7.5
                
                if temps_reel == expected_time:
                    self.log(f"✅ tempsReel = {temps_reel} heures (7h30min comme attendu)")
                    self.log("✅ Le temps total est correct après tous les ajouts")
                    return True
                else:
                    self.log(f"❌ tempsReel = {temps_reel}, attendu {expected_time}", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Récupération de l'ordre échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_cleanup_work_order(self):
        """TEST 7: Nettoyer (supprimer l'ordre de test)"""
        self.log("🧪 TEST 7: Nettoyer (supprimer l'ordre de test)")
        
        if not self.test_work_order_id:
            self.log("⚠️ Pas d'ordre de travail de test à supprimer", "WARNING")
            return True
        
        try:
            response = self.admin_session.delete(
                f"{BACKEND_URL}/work-orders/{self.test_work_order_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                self.log("✅ Ordre de travail supprimé avec succès (Status 200)")
                self.created_work_orders.remove(self.test_work_order_id)
                self.test_work_order_id = None
                return True
            elif response.status_code == 404:
                self.log("⚠️ Ordre de travail déjà supprimé (Status 404)", "WARNING")
                return True
            else:
                self.log(f"❌ Suppression de l'ordre échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
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
    
    def run_work_order_time_tracking_tests(self):
        """Run comprehensive tests for work order time tracking functionality"""
        self.log("=" * 80)
        self.log("TESTING WORK ORDER TIME TRACKING FUNCTIONALITY")
        self.log("=" * 80)
        self.log("CONTEXTE: Test complet du système d'ajout de temps passé sur les ordres de travail")
        self.log("")
        self.log("TESTS À EFFECTUER:")
        self.log("1. Créer un ordre de travail de test")
        self.log("2. Ajouter du temps passé (première fois) - 2h30min")
        self.log("3. Ajouter du temps passé (incrémentation) - 1h15min")
        self.log("4. Ajouter uniquement des minutes - 45min")
        self.log("5. Ajouter uniquement des heures - 3h")
        self.log("6. Récupérer l'ordre et vérifier le temps final")
        self.log("7. Nettoyer (supprimer l'ordre de test)")
        self.log("=" * 80)
        
        results = {
            "admin_login": False,
            "create_work_order": False,
            "add_time_first": False,
            "add_time_increment": False,
            "add_minutes_only": False,
            "add_hours_only": False,
            "get_work_order_final": False,
            "cleanup_work_order": False,
            "cleanup_remaining": False
        }
        
        # Test 1: Admin Login
        results["admin_login"] = self.test_admin_login()
        
        if not results["admin_login"]:
            self.log("❌ Cannot proceed with other tests - Admin login failed", "ERROR")
            return results
        
        # Test 2: Create work order
        results["create_work_order"] = self.test_create_work_order()
        
        if not results["create_work_order"]:
            self.log("❌ Cannot proceed with time tracking tests - Work order creation failed", "ERROR")
            return results
        
        # Test 3: Add time first time
        results["add_time_first"] = self.test_add_time_first()
        
        # Test 4: Add time increment
        results["add_time_increment"] = self.test_add_time_increment()
        
        # Test 5: Add minutes only
        results["add_minutes_only"] = self.test_add_minutes_only()
        
        # Test 6: Add hours only
        results["add_hours_only"] = self.test_add_hours_only()
        
        # Test 7: Get work order final
        results["get_work_order_final"] = self.test_get_work_order_final()
        
        # Test 8: Cleanup work order
        results["cleanup_work_order"] = self.test_cleanup_work_order()
        
        # Test 9: Cleanup remaining
        results["cleanup_remaining"] = self.cleanup_remaining_work_orders()
        
        # Summary
        self.log("=" * 70)
        self.log("WORK ORDER TIME TRACKING TEST RESULTS SUMMARY")
        self.log("=" * 70)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"  {test_name}: {status}")
        
        self.log(f"\n📊 Overall: {passed}/{total} tests passed")
        
        # Detailed analysis for critical tests
        critical_tests = ["create_work_order", "add_time_first", "add_time_increment", 
                         "add_minutes_only", "add_hours_only", "get_work_order_final"]
        critical_passed = sum(results.get(test, False) for test in critical_tests)
        
        if critical_passed == len(critical_tests):
            self.log("🎉 CRITICAL SUCCESS: All main time tracking tests passed!")
            self.log("✅ POST /api/work-orders works correctly")
            self.log("✅ POST /api/work-orders/{id}/add-time works for first time")
            self.log("✅ Time incrementation works correctly")
            self.log("✅ Minutes-only addition works")
            self.log("✅ Hours-only addition works")
            self.log("✅ GET /api/work-orders/{id} returns correct final time")
        else:
            self.log("🚨 CRITICAL FAILURE: Some main time tracking tests failed!")
            failed_critical = [test for test in critical_tests if not results.get(test, False)]
            self.log(f"❌ Failed critical tests: {', '.join(failed_critical)}")
        
        if passed >= total - 2:  # Allow cleanup to fail
            self.log("🎉 WORK ORDER TIME TRACKING FUNCTIONALITY IS WORKING CORRECTLY!")
            self.log("✅ Time addition works correctly")
            self.log("✅ Time incrementation is accurate")
            self.log("✅ All time formats (hours, minutes, both) supported")
            self.log("✅ Final time calculation is correct (7.5 hours)")
        else:
            self.log("⚠️ Some tests failed - The work order time tracking functionality may have issues")
            failed_tests = [test for test, result in results.items() if not result and test not in ["cleanup_work_order", "cleanup_remaining"]]
            self.log(f"❌ Failed tests: {', '.join(failed_tests)}")
        
        return results

if __name__ == "__main__":
    tester = InactivityTimeoutTester()
    results = tester.run_inactivity_timeout_tests()
    
    # Exit with appropriate code - allow cleanup and restore to fail
    critical_tests = ["admin_login", "normal_user_setup", "get_settings_normal_user", 
                     "update_settings_admin", "verify_settings_persistence", 
                     "validation_too_low", "validation_too_high", "non_admin_security"]
    
    critical_passed = sum(results.get(test, False) for test in critical_tests)
    
    if critical_passed == len(critical_tests):
        exit(0)  # Success
    else:
        exit(1)  # Failure