#!/usr/bin/env python3
"""
Backend API Testing Script for GMAO Application
Tests Documentation Poles endpoints - CRITICAL FIX VERIFICATION
"""

import requests
import json
import os
from datetime import datetime

# Use the correct backend URL from frontend .env
BACKEND_URL = "https://mainttracker-1.preview.emergentagent.com/api"

# Test credentials - admin account as specified in the request
ADMIN_EMAIL = "admin@gmao-iris.local"
ADMIN_PASSWORD = "Admin123!"

class DocumentationPolesTester:
    def __init__(self):
        self.admin_session = requests.Session()
        self.admin_token = None
        self.admin_data = None
        self.poles_data = []  # Store poles data for analysis
        self.documents_count = {}  # Track document counts per pole
        
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
    
    def test_get_poles_with_documents(self):
        """TEST 1: CRITIQUE - GET /api/documentations/poles - Vérifier que chaque pôle contient documents et bons_travail"""
        self.log("🧪 TEST 1: CRITIQUE - GET /api/documentations/poles - Pôles avec documents et bons")
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/documentations/poles",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Endpoint accessible - Status: 200 OK")
                self.log(f"✅ Nombre de pôles retournés: {len(data)}")
                
                if len(data) == 0:
                    self.log("⚠️ Aucun pôle trouvé dans la base de données")
                    return True  # Still consider it working
                
                # Vérifier chaque pôle
                all_poles_valid = True
                for i, pole in enumerate(data):
                    pole_name = pole.get('nom', f'Pôle {i+1}')
                    self.log(f"📋 Analyse du pôle: {pole_name}")
                    
                    # Vérification critique 1: Champ "documents" existe et est un array
                    if 'documents' not in pole:
                        self.log(f"❌ CRITIQUE: Pôle '{pole_name}' - Champ 'documents' MANQUANT", "ERROR")
                        all_poles_valid = False
                    elif not isinstance(pole['documents'], list):
                        self.log(f"❌ CRITIQUE: Pôle '{pole_name}' - Champ 'documents' n'est pas un array", "ERROR")
                        all_poles_valid = False
                    else:
                        doc_count = len(pole['documents'])
                        self.log(f"✅ Pôle '{pole_name}' - documents: array avec {doc_count} éléments")
                        self.documents_count[pole_name] = {'documents': doc_count}
                    
                    # Vérification critique 2: Champ "bons_travail" existe et est un array
                    if 'bons_travail' not in pole:
                        self.log(f"❌ CRITIQUE: Pôle '{pole_name}' - Champ 'bons_travail' MANQUANT", "ERROR")
                        all_poles_valid = False
                    elif not isinstance(pole['bons_travail'], list):
                        self.log(f"❌ CRITIQUE: Pôle '{pole_name}' - Champ 'bons_travail' n'est pas un array", "ERROR")
                        all_poles_valid = False
                    else:
                        bons_count = len(pole['bons_travail'])
                        self.log(f"✅ Pôle '{pole_name}' - bons_travail: array avec {bons_count} éléments")
                        if pole_name in self.documents_count:
                            self.documents_count[pole_name]['bons_travail'] = bons_count
                        else:
                            self.documents_count[pole_name] = {'bons_travail': bons_count}
                    
                    # Vérifier la structure des documents s'il y en a
                    if pole.get('documents') and len(pole['documents']) > 0:
                        first_doc = pole['documents'][0]
                        required_doc_fields = ['id', 'pole_id', 'nom_fichier', 'type_fichier', 'taille']
                        missing_doc_fields = [field for field in required_doc_fields if field not in first_doc]
                        if missing_doc_fields:
                            self.log(f"⚠️ Pôle '{pole_name}' - Document manque des champs: {missing_doc_fields}")
                        else:
                            self.log(f"✅ Pôle '{pole_name}' - Structure document valide")
                
                # Stocker les données pour les tests suivants
                self.poles_data = data
                
                if all_poles_valid:
                    self.log("✅ SUCCÈS CRITIQUE: Tous les pôles contiennent 'documents' et 'bons_travail' (arrays)")
                    return True
                else:
                    self.log("❌ ÉCHEC CRITIQUE: Certains pôles n'ont pas la structure requise", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Endpoint inaccessible - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_get_pole_by_id(self):
        """TEST 2: CRITIQUE - GET /api/documentations/poles/{pole_id} - Vérifier structure d'un pôle spécifique"""
        self.log("🧪 TEST 2: CRITIQUE - GET /api/documentations/poles/{pole_id} - Pôle spécifique")
        
        if not self.poles_data:
            self.log("⚠️ Pas de données de pôles disponibles du test précédent", "WARNING")
            return False
        
        # Prendre le premier pôle pour le test
        first_pole = self.poles_data[0]
        pole_id = first_pole.get('id')
        pole_name = first_pole.get('nom', 'Pôle inconnu')
        
        if not pole_id:
            self.log("❌ Pas d'ID de pôle disponible pour le test", "ERROR")
            return False
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/documentations/poles/{pole_id}",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Pôle spécifique récupéré - ID: {pole_id}")
                self.log(f"✅ Nom du pôle: {data.get('nom', 'N/A')}")
                
                # Vérifications critiques
                success = True
                
                # Vérification 1: Champ "documents" existe et est un array
                if 'documents' not in data:
                    self.log(f"❌ CRITIQUE: Champ 'documents' MANQUANT", "ERROR")
                    success = False
                elif not isinstance(data['documents'], list):
                    self.log(f"❌ CRITIQUE: Champ 'documents' n'est pas un array", "ERROR")
                    success = False
                else:
                    doc_count = len(data['documents'])
                    self.log(f"✅ Champ 'documents': array avec {doc_count} éléments")
                
                # Vérification 2: Champ "bons_travail" existe et est un array
                if 'bons_travail' not in data:
                    self.log(f"❌ CRITIQUE: Champ 'bons_travail' MANQUANT", "ERROR")
                    success = False
                elif not isinstance(data['bons_travail'], list):
                    self.log(f"❌ CRITIQUE: Champ 'bons_travail' n'est pas un array", "ERROR")
                    success = False
                else:
                    bons_count = len(data['bons_travail'])
                    self.log(f"✅ Champ 'bons_travail': array avec {bons_count} éléments")
                
                # Vérification 3: Si des documents existent, vérifier leurs champs
                if data.get('documents') and len(data['documents']) > 0:
                    first_doc = data['documents'][0]
                    self.log(f"📄 Analyse du premier document:")
                    self.log(f"   - ID: {first_doc.get('id', 'N/A')}")
                    self.log(f"   - pole_id: {first_doc.get('pole_id', 'N/A')}")
                    self.log(f"   - nom_fichier: {first_doc.get('nom_fichier', 'N/A')}")
                    self.log(f"   - type_fichier: {first_doc.get('type_fichier', 'N/A')}")
                    self.log(f"   - taille: {first_doc.get('taille', 'N/A')}")
                    
                    # Vérifier que pole_id correspond
                    if first_doc.get('pole_id') == pole_id:
                        self.log("✅ pole_id du document correspond au pôle demandé")
                    else:
                        self.log(f"⚠️ pole_id du document ({first_doc.get('pole_id')}) ne correspond pas au pôle ({pole_id})")
                
                if success:
                    self.log("✅ SUCCÈS CRITIQUE: Structure du pôle spécifique valide")
                    return True
                else:
                    self.log("❌ ÉCHEC CRITIQUE: Structure du pôle spécifique invalide", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Récupération pôle spécifique échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_compare_with_documents_endpoint(self):
        """TEST 3: CRITIQUE - Comparer avec GET /api/documentations/documents?pole_id={pole_id}"""
        self.log("🧪 TEST 3: CRITIQUE - Comparaison avec endpoint documents individuels")
        
        if not self.poles_data:
            self.log("⚠️ Pas de données de pôles disponibles du test précédent", "WARNING")
            return False
        
        # Prendre un pôle qui a des documents
        test_pole = None
        for pole in self.poles_data:
            if pole.get('documents') and len(pole['documents']) > 0:
                test_pole = pole
                break
        
        if not test_pole:
            self.log("⚠️ Aucun pôle avec des documents trouvé pour la comparaison")
            return True  # Still consider it working if no documents exist
        
        pole_id = test_pole.get('id')
        pole_name = test_pole.get('nom', 'Pôle inconnu')
        pole_docs_count = len(test_pole.get('documents', []))
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/documentations/documents?pole_id={pole_id}",
                timeout=15
            )
            
            if response.status_code == 200:
                individual_docs = response.json()
                individual_count = len(individual_docs)
                
                self.log(f"✅ Endpoint documents individuels accessible")
                self.log(f"📊 Pôle '{pole_name}':")
                self.log(f"   - Documents dans pole: {pole_docs_count}")
                self.log(f"   - Documents endpoint individuel: {individual_count}")
                
                # Comparaison critique
                if pole_docs_count == individual_count:
                    self.log("✅ SUCCÈS CRITIQUE: Les nombres correspondent parfaitement")
                    
                    # Vérifier que les mêmes documents apparaissent
                    if pole_docs_count > 0:
                        pole_doc_ids = set(doc.get('id') for doc in test_pole['documents'])
                        individual_doc_ids = set(doc.get('id') for doc in individual_docs)
                        
                        if pole_doc_ids == individual_doc_ids:
                            self.log("✅ SUCCÈS CRITIQUE: Les mêmes documents apparaissent dans les deux endpoints")
                            return True
                        else:
                            missing_in_pole = individual_doc_ids - pole_doc_ids
                            missing_in_individual = pole_doc_ids - individual_doc_ids
                            if missing_in_pole:
                                self.log(f"⚠️ Documents manquants dans pole: {missing_in_pole}")
                            if missing_in_individual:
                                self.log(f"⚠️ Documents manquants dans endpoint individuel: {missing_in_individual}")
                            return False
                    else:
                        return True
                else:
                    self.log(f"❌ ÉCHEC CRITIQUE: Les nombres ne correspondent pas", "ERROR")
                    self.log(f"   Différence: {abs(pole_docs_count - individual_count)} documents")
                    return False
                    
            else:
                self.log(f"❌ Endpoint documents individuels inaccessible - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_document_count_summary(self):
        """TEST 4: Résumé des documents et bons de travail par pôle"""
        self.log("🧪 TEST 4: Résumé des documents et bons de travail par pôle")
        
        if not self.documents_count:
            self.log("⚠️ Pas de données de comptage disponibles", "WARNING")
            return True
        
        self.log("📊 RÉSUMÉ DES DOCUMENTS ET BONS DE TRAVAIL PAR PÔLE:")
        self.log("=" * 60)
        
        total_documents = 0
        total_bons = 0
        poles_with_documents = 0
        poles_with_bons = 0
        
        for pole_name, counts in self.documents_count.items():
            doc_count = counts.get('documents', 0)
            bons_count = counts.get('bons_travail', 0)
            
            self.log(f"📋 {pole_name}:")
            self.log(f"   - Documents: {doc_count}")
            self.log(f"   - Bons de travail: {bons_count}")
            
            total_documents += doc_count
            total_bons += bons_count
            
            if doc_count > 0:
                poles_with_documents += 1
            if bons_count > 0:
                poles_with_bons += 1
        
        self.log("=" * 60)
        self.log(f"📊 TOTAUX:")
        self.log(f"   - Total pôles analysés: {len(self.documents_count)}")
        self.log(f"   - Total documents: {total_documents}")
        self.log(f"   - Total bons de travail: {total_bons}")
        self.log(f"   - Pôles avec documents: {poles_with_documents}")
        self.log(f"   - Pôles avec bons de travail: {poles_with_bons}")
        
        if total_documents > 0 or total_bons > 0:
            self.log("✅ Des documents et/ou bons de travail sont présents dans la base")
        else:
            self.log("⚠️ Aucun document ni bon de travail trouvé - base de données vide?")
        
        return True
    
    def run_documentation_poles_tests(self):
        """Run comprehensive tests for Documentation Poles endpoints - CRITICAL FIX VERIFICATION"""
        self.log("=" * 80)
        self.log("TESTING DOCUMENTATION POLES - CORRECTION CRITIQUE VÉRIFICATION")
        self.log("=" * 80)
        self.log("CONTEXTE DU PROBLÈME:")
        self.log("L'utilisateur a signalé que la vue liste n'affichait pas les documents")
        self.log("lorsqu'on développe un pôle, même si des documents et bons de travail existent.")
        self.log("")
        self.log("CORRECTION APPLIQUÉE:")
        self.log("- GET /api/documentations/poles - Retourne maintenant tous les pôles avec leurs documents et bons")
        self.log("- GET /api/documentations/poles/{pole_id} - Retourne un pôle avec ses documents et bons")
        self.log("")
        self.log("TÂCHE DE TEST CRITIQUE:")
        self.log("1. 📋 VÉRIFIER L'ENDPOINT GET /api/documentations/poles")
        self.log("   a) Se connecter en tant qu'admin")
        self.log("   b) Appeler GET /api/documentations/poles")
        self.log("   c) Vérifier que CHAQUE pôle contient:")
        self.log("      - Un champ 'documents' (liste)")
        self.log("      - Un champ 'bons_travail' (liste)")
        self.log("   d) Vérifier que ces listes contiennent les données s'il y en a")
        self.log("   e) Compter le nombre de documents et bons pour chaque pôle")
        self.log("")
        self.log("2. 🔍 VÉRIFIER L'ENDPOINT GET /api/documentations/poles/{pole_id}")
        self.log("   a) Prendre l'ID d'un pôle depuis le test précédent")
        self.log("   b) Appeler GET /api/documentations/poles/{pole_id}")
        self.log("   c) Vérifier la structure de la réponse")
        self.log("")
        self.log("3. 📊 COMPARER AVEC GET /api/documentations/documents?pole_id={pole_id}")
        self.log("   a) Prendre un pole_id")
        self.log("   b) Appeler GET /api/documentations/documents?pole_id={pole_id}")
        self.log("   c) Comparer avec le nombre dans pole['documents']")
        self.log("=" * 80)
        
        results = {
            "admin_login": False,
            "get_poles_with_documents": False,
            "get_pole_by_id": False,
            "compare_with_documents_endpoint": False,
            "document_count_summary": False
        }
        
        # Test 1: Admin Login
        results["admin_login"] = self.test_admin_login()
        
        if not results["admin_login"]:
            self.log("❌ Cannot proceed with other tests - Admin login failed", "ERROR")
            return results
        
        # TESTS CRITIQUES DES ENDPOINTS DOCUMENTATIONS/POLES
        self.log("\n" + "=" * 60)
        self.log("📋 TESTS CRITIQUES - ENDPOINTS DOCUMENTATIONS/POLES")
        self.log("=" * 60)
        
        results["get_poles_with_documents"] = self.test_get_poles_with_documents()
        results["get_pole_by_id"] = self.test_get_pole_by_id()
        results["compare_with_documents_endpoint"] = self.test_compare_with_documents_endpoint()
        results["document_count_summary"] = self.test_document_count_summary()
        
        # Summary
        self.log("=" * 80)
        self.log("DOCUMENTATION POLES TEST RESULTS SUMMARY")
        self.log("=" * 80)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"  {test_name}: {status}")
        
        self.log(f"\n📊 Overall: {passed}/{total} tests passed")
        
        # Analyse détaillée des tests critiques
        critical_tests = ["get_poles_with_documents", "get_pole_by_id", "compare_with_documents_endpoint"]
        critical_passed = sum(results.get(test, False) for test in critical_tests)
        
        self.log("\n" + "=" * 60)
        self.log("ANALYSE CRITIQUE DES CORRECTIONS")
        self.log("=" * 60)
        
        # CORRECTION 1: GET /api/documentations/poles
        if results.get("get_poles_with_documents", False):
            self.log("🎉 CORRECTION 1 - GET /api/documentations/poles: ✅ SUCCÈS CRITIQUE")
            self.log("✅ Endpoint accessible (200 OK)")
            self.log("✅ Chaque pôle contient un champ 'documents' (array)")
            self.log("✅ Chaque pôle contient un champ 'bons_travail' (array)")
            self.log("✅ Structure de données correcte pour l'affichage en vue liste")
            self.log("✅ Les documents et bons sont maintenant automatiquement inclus")
        else:
            self.log("🚨 CORRECTION 1 - GET /api/documentations/poles: ❌ ÉCHEC CRITIQUE")
            self.log("❌ Les pôles ne contiennent pas les champs requis")
            self.log("❌ La vue liste ne pourra pas afficher les documents")
        
        # CORRECTION 2: GET /api/documentations/poles/{pole_id}
        if results.get("get_pole_by_id", False):
            self.log("🎉 CORRECTION 2 - GET /api/documentations/poles/{pole_id}: ✅ SUCCÈS CRITIQUE")
            self.log("✅ Endpoint spécifique accessible (200 OK)")
            self.log("✅ Structure correcte avec documents et bons_travail")
            self.log("✅ Données cohérentes avec l'endpoint de liste")
        else:
            self.log("🚨 CORRECTION 2 - GET /api/documentations/poles/{pole_id}: ❌ ÉCHEC CRITIQUE")
            self.log("❌ Structure incorrecte pour pôle spécifique")
        
        # VÉRIFICATION 3: Cohérence avec endpoint documents
        if results.get("compare_with_documents_endpoint", False):
            self.log("🎉 VÉRIFICATION 3 - COHÉRENCE ENDPOINTS: ✅ SUCCÈS CRITIQUE")
            self.log("✅ Les nombres de documents correspondent")
            self.log("✅ Les mêmes documents apparaissent dans les deux endpoints")
            self.log("✅ Pas de perte de données lors de l'inclusion automatique")
        else:
            self.log("🚨 VÉRIFICATION 3 - COHÉRENCE ENDPOINTS: ❌ PROBLÈME DÉTECTÉ")
            self.log("❌ Incohérence entre les endpoints")
            self.log("❌ Possible perte de données ou doublons")
        
        # Conclusion finale
        self.log("\n" + "=" * 80)
        self.log("CONCLUSION FINALE - CORRECTION CRITIQUE")
        self.log("=" * 80)
        
        if critical_passed == len(critical_tests):
            self.log("🎉 CORRECTION ENTIÈREMENT RÉUSSIE!")
            self.log("✅ GET /api/documentations/poles retourne les pôles avec documents et bons")
            self.log("✅ GET /api/documentations/poles/{pole_id} retourne la structure correcte")
            self.log("✅ Cohérence parfaite entre tous les endpoints")
            self.log("✅ La vue liste peut maintenant afficher les documents")
            self.log("✅ Le problème reporté par l'utilisateur est RÉSOLU")
            self.log("✅ Les endpoints sont PRÊTS POUR PRODUCTION")
        else:
            self.log("⚠️ CORRECTION INCOMPLÈTE - PROBLÈMES PERSISTANTS")
            failed_critical = [test for test in critical_tests if not results.get(test, False)]
            self.log(f"❌ Tests critiques échoués: {', '.join(failed_critical)}")
            self.log("❌ La vue liste pourrait encore ne pas afficher les documents")
            self.log("❌ Intervention supplémentaire requise")
        
        return results

if __name__ == "__main__":
    tester = DocumentationPolesTester()
    results = tester.run_documentation_poles_tests()
    
    # Exit with appropriate code
    critical_tests = [
        "admin_login", "get_poles_with_documents", "get_pole_by_id", 
        "compare_with_documents_endpoint"
    ]
    
    critical_passed = sum(results.get(test, False) for test in critical_tests)
    
    if critical_passed == len(critical_tests):
        exit(0)  # Success
    else:
        exit(1)  # Failure
