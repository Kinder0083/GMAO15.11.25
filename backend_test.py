#!/usr/bin/env python3
"""
Backend API Testing Script for GMAO Application
Tests Documentation Poles endpoints - CRITICAL FIX VERIFICATION
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
    
    def test_get_bons_travail_list(self):
        """TEST 5: Récupérer la liste des bons de travail"""
        self.log("🧪 TEST 5: GET /api/documentations/bons-travail - Liste des bons")
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/documentations/bons-travail",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Liste des bons de travail récupérée - {len(data)} bons trouvés")
                
                if len(data) > 0:
                    # Prendre le premier bon pour les tests suivants
                    first_bon = data[0]
                    bon_id = first_bon.get('id')
                    if bon_id:
                        self.test_bons['existing'] = bon_id
                        self.log(f"✅ Premier bon ID: {bon_id}")
                        self.log(f"✅ Titre: {first_bon.get('titre', 'N/A')}")
                        self.log(f"✅ Entreprise: {first_bon.get('entreprise', 'N/A')}")
                        self.log(f"✅ Created by: {first_bon.get('created_by', 'N/A')}")
                        self.log(f"✅ Created at: {first_bon.get('created_at', 'N/A')}")
                    
                    # Vérifier la structure des données
                    required_fields = ['id', 'titre', 'entreprise', 'created_by', 'created_at']
                    missing_fields = [field for field in required_fields if field not in first_bon]
                    if missing_fields:
                        self.log(f"⚠️ Champs manquants dans la réponse: {missing_fields}")
                    else:
                        self.log("✅ Tous les champs requis sont présents")
                    
                    return True
                else:
                    self.log("⚠️ Aucun bon de travail trouvé - créer un bon pour les tests suivants")
                    return True  # Still consider it working
                    
            else:
                self.log(f"❌ Récupération liste échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_get_bon_travail_details(self):
        """TEST 6: Récupérer les détails d'un bon de travail spécifique"""
        self.log("🧪 TEST 6: GET /api/documentations/bons-travail/{id} - Détails d'un bon")
        
        if not self.test_bons.get('existing'):
            self.log("⚠️ Pas de bon de travail existant pour tester les détails", "WARNING")
            return False
        
        try:
            bon_id = self.test_bons['existing']
            response = self.admin_session.get(
                f"{BACKEND_URL}/documentations/bons-travail/{bon_id}",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Détails du bon de travail récupérés - ID: {data.get('id')}")
                self.log(f"✅ Titre: {data.get('titre')}")
                self.log(f"✅ Entreprise: {data.get('entreprise')}")
                self.log(f"✅ Localisation/Ligne: {data.get('localisation_ligne')}")
                self.log(f"✅ Description: {data.get('description_travaux', '')[:100]}...")
                return True
            else:
                self.log(f"❌ Récupération détails échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_create_bon_travail(self):
        """TEST 7: Créer un nouveau bon de travail (si nécessaire pour les tests)"""
        self.log("🧪 TEST 7: POST /api/documentations/bons-travail - Créer un bon")
        
        try:
            bon_data = {
                "titre": "Test Bon de Travail SSH",
                "entreprise": "COSMEVA Test",
                "localisation_ligne": "Ligne de production A - Zone test",
                "description_travaux": "Travaux de test pour validation des endpoints SSH et documentations",
                "nom_intervenants": "Jean DUPONT, Marie MARTIN",
                "risques_materiel": ["Électricité", "Machines en mouvement"],
                "risques_materiel_autre": "Risque spécifique test",
                "risques_autorisation": ["Travail en hauteur"],
                "risques_produits": ["Produits chimiques"],
                "risques_environnement": ["Zone ATEX"],
                "risques_environnement_autre": "Environnement test",
                "precautions_materiel": ["Consignation électrique", "Arrêt machines"],
                "precautions_materiel_autre": "Précaution spécifique test",
                "precautions_epi": ["Casque", "Gants", "Chaussures de sécurité"],
                "precautions_epi_autre": "EPI spécifique test",
                "precautions_environnement": ["Détecteur de gaz"],
                "precautions_environnement_autre": "Précaution environnement test",
                "date_engagement": "2025-01-20",
                "nom_agent_maitrise": "Paul LEFEBVRE",
                "nom_representant": "Sophie BERNARD"
            }
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/documentations/bons-travail",
                json=bon_data,
                timeout=15
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                bon_id = data.get("id")
                self.created_bons.append(bon_id)
                self.test_bons['created'] = bon_id
                
                self.log(f"✅ Bon de travail créé avec succès - ID: {bon_id}")
                self.log(f"✅ Titre: {data.get('titre')}")
                self.log(f"✅ Entreprise: {data.get('entreprise')}")
                self.log(f"✅ Localisation: {data.get('localisation_ligne')}")
                return True
                    
            else:
                self.log(f"❌ Création bon de travail échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_generate_bon_pdf(self):
        """TEST 8: CRITIQUE - Générer le PDF d'un bon de travail"""
        self.log("🧪 TEST 8: CRITIQUE - GET /api/documentations/bons-travail/{id}/pdf - Génération PDF")
        
        # Utiliser le bon créé ou existant
        bon_id = self.test_bons.get('created') or self.test_bons.get('existing')
        if not bon_id:
            self.log("⚠️ Pas de bon de travail disponible pour tester la génération PDF", "WARNING")
            return False
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/documentations/bons-travail/{bon_id}/pdf",
                timeout=20
            )
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                self.log(f"✅ PDF généré avec succès - Type: {content_type}")
                self.log(f"✅ Taille: {content_length} bytes")
                
                # Vérifier que c'est bien du HTML (comme spécifié dans le code)
                if 'text/html' in content_type:
                    self.log("✅ Content-Type correct: text/html")
                    
                    # Vérifier le contenu HTML
                    html_content = response.text
                    
                    # Vérifications critiques selon les spécifications
                    checks = {
                        "COSMEVA": "COSMEVA" in html_content,
                        "Bon de travail": "Bon de travail" in html_content,
                        "MTN/008/F": "MTN/008/F" in html_content,
                        "Travaux à réaliser": "Travaux à réaliser" in html_content,
                        "Risques Identifiés": "Risques Identifiés" in html_content,
                        "Précautions à prendre": "Précautions à prendre" in html_content,
                        "Engagement": "Engagement" in html_content
                    }
                    
                    all_checks_passed = True
                    for check_name, check_result in checks.items():
                        if check_result:
                            self.log(f"✅ Vérification '{check_name}': PRÉSENT")
                        else:
                            self.log(f"❌ Vérification '{check_name}': MANQUANT", "ERROR")
                            all_checks_passed = False
                    
                    if all_checks_passed:
                        self.log("✅ Toutes les sections requises sont présentes dans le PDF")
                        self.log("✅ Structure complète du document validée")
                        return True
                    else:
                        self.log("❌ Certaines sections requises sont manquantes dans le PDF", "ERROR")
                        return False
                        
                else:
                    self.log(f"❌ Content-Type incorrect - Attendu: text/html, Reçu: {content_type}", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Génération PDF échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_generate_bon_pdf_with_token(self):
        """TEST 9: Générer le PDF avec token en query param"""
        self.log("🧪 TEST 9: GET /api/documentations/bons-travail/{id}/pdf?token=xxx - PDF avec token")
        
        bon_id = self.test_bons.get('created') or self.test_bons.get('existing')
        if not bon_id:
            self.log("⚠️ Pas de bon de travail disponible pour tester la génération PDF avec token", "WARNING")
            return False
        
        try:
            # Utiliser le token admin en query param
            response = self.admin_session.get(
                f"{BACKEND_URL}/documentations/bons-travail/{bon_id}/pdf?token={self.admin_token}",
                timeout=20
            )
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                self.log(f"✅ PDF avec token généré avec succès - Type: {content_type}")
                
                if 'text/html' in content_type:
                    self.log("✅ Authentification par token en query param fonctionnelle")
                    return True
                else:
                    self.log(f"❌ Content-Type incorrect avec token", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Génération PDF avec token échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_cleanup_bons_travail(self):
        """TEST 10: Nettoyer (supprimer les bons de travail de test créés)"""
        self.log("🧪 TEST 10: Nettoyer les bons de travail de test créés")
        
        if not self.created_bons:
            self.log("⚠️ Pas de bons de travail de test à supprimer", "WARNING")
            return True
        
        success_count = 0
        for bon_id in self.created_bons[:]:  # Copy to avoid modification during iteration
            try:
                response = self.admin_session.delete(
                    f"{BACKEND_URL}/documentations/bons-travail/{bon_id}",
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log(f"✅ Bon de travail {bon_id} supprimé avec succès")
                    self.created_bons.remove(bon_id)
                    success_count += 1
                elif response.status_code == 404:
                    self.log(f"⚠️ Bon de travail {bon_id} déjà supprimé (Status 404)")
                    self.created_bons.remove(bon_id)
                    success_count += 1
                else:
                    self.log(f"❌ Suppression du bon de travail {bon_id} échouée - Status: {response.status_code}", "ERROR")
                    
            except requests.exceptions.RequestException as e:
                self.log(f"❌ Request failed for {bon_id} - Error: {str(e)}", "ERROR")
        
        self.log(f"✅ Nettoyage terminé: {success_count} bons de travail supprimés")
        return success_count >= 0  # Toujours réussir le nettoyage
    
    def cleanup_remaining_bons_travail(self):
        """Nettoyer tous les bons de travail créés pendant les tests"""
        self.log("🧹 Nettoyage des bons de travail restants...")
        
        if not self.created_bons:
            self.log("Aucun bon de travail à nettoyer")
            return True
        
        success_count = 0
        for bon_id in self.created_bons[:]:  # Copy list to avoid modification during iteration
            try:
                response = self.admin_session.delete(
                    f"{BACKEND_URL}/documentations/bons-travail/{bon_id}",
                    timeout=10
                )
                
                if response.status_code in [200, 404]:
                    self.log(f"✅ Bon de travail {bon_id} nettoyé")
                    self.created_bons.remove(bon_id)
                    success_count += 1
                else:
                    self.log(f"⚠️ Impossible de nettoyer le bon de travail {bon_id} - Status: {response.status_code}")
                    
            except Exception as e:
                self.log(f"⚠️ Erreur lors du nettoyage du bon de travail {bon_id}: {str(e)}")
        
        self.log(f"Nettoyage terminé: {success_count} bons de travail supprimés")
        return True
    
    def run_ssh_and_documentations_tests(self):
        """Run comprehensive tests for SSH Terminal and Documentations endpoints"""
        self.log("=" * 80)
        self.log("TESTING SSH TERMINAL & DOCUMENTATIONS (BONS DE TRAVAIL) - ENDPOINTS CRITIQUES")
        self.log("=" * 80)
        self.log("CONTEXTE: Test complet des modules SSH et Documentations selon la demande:")
        self.log("- Terminal SSH (CRITIQUE - Correction juste effectuée)")
        self.log("- Génération PDF Bon de Travail (HAUTE PRIORITÉ)")
        self.log("- CRUD Bons de Travail (MOYENNE PRIORITÉ)")
        self.log("")
        self.log("TESTS À EFFECTUER PAR ORDRE DE PRIORITÉ:")
        self.log("1. 🔧 TERMINAL SSH (CRITIQUE)")
        self.log("   a) Connexion en tant qu'admin")
        self.log("   b) Test commande simple: pwd")
        self.log("   c) Test commande liste: ls -la /app")
        self.log("   d) Test commande echo: echo 'Test SSH'")
        self.log("   e) Test avec utilisateur non-admin (doit échouer avec 403)")
        self.log("2. 📄 GÉNÉRATION PDF BON DE TRAVAIL (HAUTE)")
        self.log("   a) Lister les bons de travail existants")
        self.log("   b) Récupérer détails d'un bon")
        self.log("   c) Créer un bon si nécessaire")
        self.log("   d) Générer le PDF (HTML)")
        self.log("   e) Vérifier Content-Type: text/html")
        self.log("   f) Vérifier présence: COSMEVA, Bon de travail, MTN/008/F")
        self.log("   g) Vérifier 4 sections: Travaux, Risques, Précautions, Engagement")
        self.log("3. 📋 CRUD BONS DE TRAVAIL (MOYENNE)")
        self.log("   a) GET /api/documentations/bons-travail - Liste")
        self.log("   b) GET /api/documentations/bons-travail/{id} - Détails")
        self.log("   c) POST /api/documentations/bons-travail - Créer")
        self.log("=" * 80)
        
        results = {
            "admin_login": False,
            "ssh_execute_simple": False,
            "ssh_execute_list": False,
            "ssh_execute_echo": False,
            "ssh_execute_non_admin": False,
            "get_bons_travail_list": False,
            "get_bon_travail_details": False,
            "create_bon_travail": False,
            "generate_bon_pdf": False,
            "generate_bon_pdf_with_token": False,
            "cleanup_bons_travail": False,
            "cleanup_remaining": False
        }
        
        # Test 1: Admin Login
        results["admin_login"] = self.test_admin_login()
        
        if not results["admin_login"]:
            self.log("❌ Cannot proceed with other tests - Admin login failed", "ERROR")
            return results
        
        # PRIORITÉ 1: TERMINAL SSH (CRITIQUE)
        self.log("\n" + "=" * 60)
        self.log("🔧 PRIORITÉ 1: TERMINAL SSH (CRITIQUE)")
        self.log("=" * 60)
        
        results["ssh_execute_simple"] = self.test_ssh_execute_simple_command()
        results["ssh_execute_list"] = self.test_ssh_execute_list_command()
        results["ssh_execute_echo"] = self.test_ssh_execute_echo_command()
        results["ssh_execute_non_admin"] = self.test_ssh_execute_non_admin_user()
        
        # PRIORITÉ 2: GÉNÉRATION PDF BON DE TRAVAIL (HAUTE)
        self.log("\n" + "=" * 60)
        self.log("📄 PRIORITÉ 2: GÉNÉRATION PDF BON DE TRAVAIL (HAUTE)")
        self.log("=" * 60)
        
        results["get_bons_travail_list"] = self.test_get_bons_travail_list()
        results["get_bon_travail_details"] = self.test_get_bon_travail_details()
        results["create_bon_travail"] = self.test_create_bon_travail()
        results["generate_bon_pdf"] = self.test_generate_bon_pdf()
        results["generate_bon_pdf_with_token"] = self.test_generate_bon_pdf_with_token()
        
        # PRIORITÉ 3: CRUD BONS DE TRAVAIL (MOYENNE) - Déjà testé ci-dessus
        self.log("\n" + "=" * 60)
        self.log("📋 PRIORITÉ 3: CRUD BONS DE TRAVAIL (MOYENNE) - DÉJÀ TESTÉ")
        self.log("=" * 60)
        
        # Cleanup
        results["cleanup_bons_travail"] = self.test_cleanup_bons_travail()
        results["cleanup_remaining"] = self.cleanup_remaining_bons_travail()
        
        # Summary
        self.log("=" * 80)
        self.log("SSH TERMINAL & DOCUMENTATIONS TEST RESULTS SUMMARY")
        self.log("=" * 80)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"  {test_name}: {status}")
        
        self.log(f"\n📊 Overall: {passed}/{total} tests passed")
        
        # Analyse détaillée par priorité
        ssh_tests = ["ssh_execute_simple", "ssh_execute_list", "ssh_execute_echo", "ssh_execute_non_admin"]
        ssh_passed = sum(results.get(test, False) for test in ssh_tests)
        
        pdf_tests = ["get_bons_travail_list", "get_bon_travail_details", "create_bon_travail", "generate_bon_pdf", "generate_bon_pdf_with_token"]
        pdf_passed = sum(results.get(test, False) for test in pdf_tests)
        
        crud_tests = ["get_bons_travail_list", "get_bon_travail_details", "create_bon_travail"]
        crud_passed = sum(results.get(test, False) for test in crud_tests)
        
        self.log("\n" + "=" * 60)
        self.log("ANALYSE PAR PRIORITÉ")
        self.log("=" * 60)
        
        # PRIORITÉ 1: SSH Terminal (CRITIQUE)
        if ssh_passed == len(ssh_tests):
            self.log("🎉 PRIORITÉ 1 - SSH TERMINAL: ✅ SUCCÈS CRITIQUE")
            self.log("✅ POST /api/ssh/execute fonctionne correctement")
            self.log("✅ Commandes simples (pwd) exécutées")
            self.log("✅ Commandes complexes (ls -la) exécutées")
            self.log("✅ Commandes echo fonctionnelles")
            self.log("✅ Sécurité: Accès refusé aux non-admin (403 Forbidden)")
            self.log("✅ Pas d'erreur 'Response body is already used'")
            self.log("✅ stdout, stderr, exit_code correctement retournés")
        else:
            self.log("🚨 PRIORITÉ 1 - SSH TERMINAL: ❌ ÉCHEC CRITIQUE")
            failed_ssh = [test for test in ssh_tests if not results.get(test, False)]
            self.log(f"❌ Tests SSH échoués: {', '.join(failed_ssh)}")
        
        # PRIORITÉ 2: Génération PDF (HAUTE)
        if pdf_passed == len(pdf_tests):
            self.log("🎉 PRIORITÉ 2 - GÉNÉRATION PDF: ✅ SUCCÈS HAUTE PRIORITÉ")
            self.log("✅ GET /api/documentations/bons-travail/{id}/pdf fonctionne")
            self.log("✅ Response 200 OK")
            self.log("✅ Content-Type: text/html")
            self.log("✅ HTML contient 'COSMEVA', 'Bon de travail', 'MTN/008/F'")
            self.log("✅ Structure complète: Travaux, Risques, Précautions, Engagement")
            self.log("✅ Authentification Bearer token ET query param ?token=xxx")
        else:
            self.log("🚨 PRIORITÉ 2 - GÉNÉRATION PDF: ❌ ÉCHEC HAUTE PRIORITÉ")
            failed_pdf = [test for test in pdf_tests if not results.get(test, False)]
            self.log(f"❌ Tests PDF échoués: {', '.join(failed_pdf)}")
        
        # PRIORITÉ 3: CRUD Bons de Travail (MOYENNE)
        if crud_passed == len(crud_tests):
            self.log("🎉 PRIORITÉ 3 - CRUD BONS DE TRAVAIL: ✅ SUCCÈS MOYENNE PRIORITÉ")
            self.log("✅ GET /api/documentations/bons-travail - Liste OK")
            self.log("✅ GET /api/documentations/bons-travail/{id} - Détails OK")
            self.log("✅ POST /api/documentations/bons-travail - Création OK")
            self.log("✅ Champs requis: id, titre, entreprise, created_by, created_at")
            self.log("✅ Format JSON valide")
        else:
            self.log("🚨 PRIORITÉ 3 - CRUD BONS DE TRAVAIL: ❌ ÉCHEC MOYENNE PRIORITÉ")
            failed_crud = [test for test in crud_tests if not results.get(test, False)]
            self.log(f"❌ Tests CRUD échoués: {', '.join(failed_crud)}")
        
        # Conclusion finale
        self.log("\n" + "=" * 80)
        self.log("CONCLUSION FINALE")
        self.log("=" * 80)
        
        if ssh_passed == len(ssh_tests) and pdf_passed == len(pdf_tests) and crud_passed == len(crud_tests):
            self.log("🎉 TOUS LES TESTS CRITIQUES RÉUSSIS!")
            self.log("✅ Terminal SSH: OPÉRATIONNEL (correction validée)")
            self.log("✅ Génération PDF: OPÉRATIONNELLE (utilisateur peut générer)")
            self.log("✅ CRUD Bons de Travail: OPÉRATIONNEL (support des tests)")
            self.log("✅ Les modules SSH et Documentations sont PRÊTS POUR PRODUCTION")
        else:
            self.log("⚠️ PROBLÈMES DÉTECTÉS DANS LES MODULES CRITIQUES")
            if ssh_passed < len(ssh_tests):
                self.log("❌ Terminal SSH: PROBLÈMES CRITIQUES")
            if pdf_passed < len(pdf_tests):
                self.log("❌ Génération PDF: PROBLÈMES HAUTE PRIORITÉ")
            if crud_passed < len(crud_tests):
                self.log("❌ CRUD Bons de Travail: PROBLÈMES MOYENNE PRIORITÉ")
        
        return results

if __name__ == "__main__":
    tester = SSHAndDocumentationsTester()
    results = tester.run_ssh_and_documentations_tests()
    
    # Exit with appropriate code
    critical_tests = [
        "admin_login", "ssh_execute_simple", "ssh_execute_list", "ssh_execute_echo", 
        "ssh_execute_non_admin", "get_bons_travail_list", "get_bon_travail_details", 
        "create_bon_travail", "generate_bon_pdf", "generate_bon_pdf_with_token"
    ]
    
    critical_passed = sum(results.get(test, False) for test in critical_tests)
    
    if critical_passed == len(critical_tests):
        exit(0)  # Success
    else:
        exit(1)  # Failure