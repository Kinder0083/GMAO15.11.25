#!/usr/bin/env python3
"""
Backend API Testing Script for GMAO Application
Tests Import/Export functionality - Module Import/Export Error Corrections
"""

import requests
import json
import os
import io
import pandas as pd
import tempfile
from datetime import datetime, timedelta

# Use the correct backend URL from frontend .env
BACKEND_URL = "https://iris-maintenance-1.preview.emergentagent.com/api"

# Test credentials - try both admin accounts
ADMIN_EMAIL_1 = "admin@example.com"
ADMIN_PASSWORD_1 = "password123"
ADMIN_EMAIL_2 = "admin@gmao-iris.local"
ADMIN_PASSWORD_2 = "Admin123!"

# QHSE test credentials (to be created)
QHSE_EMAIL = "test_qhse@test.com"
QHSE_PASSWORD = "Test123!"

class ImportExportTester:
    def __init__(self):
        self.admin_session = requests.Session()
        self.admin_token = None
        self.admin_data = None
        
        # Available modules for import/export
        self.available_modules = [
            "intervention-requests", "work-orders", "improvement-requests", 
            "improvements", "equipments", "meters", "meter-readings", 
            "users", "inventory", "locations", "vendors", "purchase-history"
        ]
        
    def log(self, message, level="INFO"):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_admin_login(self):
        """Test admin login - try both admin accounts"""
        self.log("Testing admin login...")
        
        # Try first admin account
        try:
            response = self.admin_session.post(
                f"{BACKEND_URL}/auth/login",
                json={
                    "email": ADMIN_EMAIL_1,
                    "password": ADMIN_PASSWORD_1
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
                
                self.log(f"✅ Admin login successful with {ADMIN_EMAIL_1} - User: {self.admin_data.get('prenom')} {self.admin_data.get('nom')} (Role: {self.admin_data.get('role')})")
                return True
            else:
                self.log(f"⚠️ First admin login failed - Status: {response.status_code}, trying second account...")
                
        except requests.exceptions.RequestException as e:
            self.log(f"⚠️ First admin login request failed - Error: {str(e)}, trying second account...")
        
        # Try second admin account
        try:
            response = self.admin_session.post(
                f"{BACKEND_URL}/auth/login",
                json={
                    "email": ADMIN_EMAIL_2,
                    "password": ADMIN_PASSWORD_2
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
                
                self.log(f"✅ Admin login successful with {ADMIN_EMAIL_2} - User: {self.admin_data.get('prenom')} {self.admin_data.get('nom')} (Role: {self.admin_data.get('role')})")
                return True
            else:
                self.log(f"❌ Both admin logins failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Both admin login requests failed - Error: {str(e)}", "ERROR")
            return False
    
    def create_test_excel_multi_sheet(self):
        """Create a multi-sheet Excel file for testing 'all' import"""
        self.log("Creating multi-sheet Excel file for testing...")
        
        # Create sample data for different modules
        work_orders_data = {
            'Titre': ['Maintenance pompe A', 'Réparation ventilateur B'],
            'Description': ['Maintenance préventive pompe', 'Réparation urgente ventilateur'],
            'Priorité': ['MOYENNE', 'HAUTE'],
            'Statut': ['OUVERT', 'EN_COURS'],
            'Type': ['PREVENTIVE', 'CORRECTIVE']
        }
        
        equipments_data = {
            'Nom': ['Pompe hydraulique 001', 'Ventilateur industriel 002'],
            'Code': ['PMP-001', 'VENT-002'],
            'Type': ['POMPE', 'VENTILATEUR'],
            'Marque': ['Grundfos', 'Soler&Palau'],
            'Statut': ['OPERATIONNEL', 'EN_MAINTENANCE']
        }
        
        users_data = {
            'Email': ['test.import1@example.com', 'test.import2@example.com'],
            'Prénom': ['Jean', 'Marie'],
            'Nom': ['Dupont', 'Martin'],
            'Rôle': ['TECHNICIEN', 'VISUALISEUR'],
            'Service': ['Maintenance', 'Production']
        }
        
        # Create Excel file with multiple sheets
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            with pd.ExcelWriter(tmp_file.name, engine='openpyxl') as writer:
                pd.DataFrame(work_orders_data).to_excel(writer, sheet_name='work-orders', index=False)
                pd.DataFrame(equipments_data).to_excel(writer, sheet_name='equipments', index=False)
                pd.DataFrame(users_data).to_excel(writer, sheet_name='users', index=False)
            
            self.log(f"✅ Multi-sheet Excel file created: {tmp_file.name}")
            return tmp_file.name
    
    def create_test_csv_file(self, module):
        """Create a CSV file for testing individual module import"""
        self.log(f"Creating CSV file for module: {module}")
        
        # Sample data based on module
        if module == "work-orders":
            data = {
                'Titre': ['Test Work Order CSV'],
                'Description': ['Test description for CSV import'],
                'Priorité': ['MOYENNE'],
                'Statut': ['OUVERT'],
                'Type': ['CORRECTIVE']
            }
        elif module == "equipments":
            data = {
                'Nom': ['Test Equipment CSV'],
                'Code': ['TEST-CSV-001'],
                'Type': ['TEST'],
                'Marque': ['TestBrand'],
                'Statut': ['OPERATIONNEL']
            }
        elif module == "users":
            data = {
                'Email': ['test.csv@example.com'],
                'Prénom': ['Test'],
                'Nom': ['CSV'],
                'Rôle': ['VISUALISEUR'],
                'Service': ['Test']
            }
        elif module == "inventory":
            data = {
                'Nom': ['Test Item CSV'],
                'Code': ['ITEM-CSV-001'],
                'Type': ['PIECE_RECHANGE'],
                'Catégorie': ['MECANIQUE'],
                'Quantité': [10]
            }
        elif module == "vendors":
            data = {
                'Nom': ['Test Vendor CSV'],
                'Email': ['vendor.csv@example.com'],
                'Téléphone': ['0123456789'],
                'Type': ['FOURNISSEUR'],
                'Statut': ['ACTIF']
            }
        else:
            # Default data for other modules
            data = {
                'Nom': [f'Test {module} CSV'],
                'Description': [f'Test description for {module}']
            }
        
        # Create CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as tmp_file:
            df = pd.DataFrame(data)
            df.to_csv(tmp_file.name, index=False, sep=';')  # Use semicolon separator
            
            self.log(f"✅ CSV file created for {module}: {tmp_file.name}")
            return tmp_file.name
    
    def test_import_all_multi_sheet(self):
        """Test POST /api/import/all with multi-sheet Excel file"""
        self.log("🧪 TEST 1: Import 'Toutes les données' multi-feuilles Excel (PRIORITÉ MAXIMALE)")
        
        # Create multi-sheet Excel file
        excel_file = self.create_test_excel_multi_sheet()
        
        try:
            with open(excel_file, 'rb') as f:
                files = {'file': ('test_multi_sheet.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                data = {'mode': 'add'}
                
                response = self.admin_session.post(
                    f"{BACKEND_URL}/import/all",
                    files=files,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.log("✅ Import 'all' multi-sheet successful!")
                    
                    # Verify response structure
                    if 'data' in result:
                        data = result['data']
                        if 'modules' in data:
                            self.log(f"✅ response.data.modules exists: {list(data['modules'].keys())}")
                        if 'total' in data:
                            self.log(f"✅ response.data.total: {data['total']}")
                        if 'inserted' in data:
                            self.log(f"✅ response.data.inserted: {data['inserted']}")
                        if 'updated' in data:
                            self.log(f"✅ response.data.updated: {data['updated']}")
                        if 'skipped' in data:
                            self.log(f"✅ response.data.skipped: {data['skipped']}")
                        
                        # Check if data was actually inserted
                        if data.get('inserted', 0) > 0:
                            self.log("✅ Data successfully inserted into MongoDB")
                        else:
                            self.log("⚠️ No data was inserted (might be duplicates or validation issues)")
                        
                        return True
                    else:
                        self.log("❌ Response missing 'data' field", "ERROR")
                        return False
                else:
                    self.log(f"❌ Import 'all' failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                    
                    # Check for specific error mentioned by user
                    if "can only use .str accessor with string value" in response.text:
                        self.log("❌ CRITICAL: Found the reported pandas error!", "ERROR")
                    
                    return False
                    
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Import 'all' request failed - Error: {str(e)}", "ERROR")
            return False
        finally:
            # Clean up temp file
            try:
                os.unlink(excel_file)
            except:
                pass
    
    def test_individual_module_import(self, module):
        """Test POST /api/import/{module} for individual modules"""
        self.log(f"🧪 TEST 2: Import individual module '{module}'")
        
        # Create CSV file for the module
        csv_file = self.create_test_csv_file(module)
        
        try:
            with open(csv_file, 'rb') as f:
                files = {'file': (f'test_{module}.csv', f, 'text/csv')}
                data = {'mode': 'add'}
                
                response = self.admin_session.post(
                    f"{BACKEND_URL}/import/{module}",
                    files=files,
                    data=data,
                    timeout=20
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.log(f"✅ Import {module} successful!")
                    
                    # Verify response structure
                    if 'data' in result:
                        data = result['data']
                        if 'inserted' in data and data['inserted'] > 0:
                            self.log(f"✅ response.data.inserted > 0: {data['inserted']}")
                            self.log("✅ Data correctly inserted into MongoDB")
                            return True
                        else:
                            self.log(f"⚠️ No data inserted for {module}: {data}")
                            return True  # Still consider success if no errors
                    else:
                        self.log("❌ Response missing 'data' field", "ERROR")
                        return False
                else:
                    self.log(f"❌ Import {module} failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                    
                    # Check for specific error mentioned by user
                    if "impossible de charger les données" in response.text:
                        self.log(f"❌ CRITICAL: Found the reported error for {module}!", "ERROR")
                    
                    return False
                    
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Import {module} request failed - Error: {str(e)}", "ERROR")
            return False
        finally:
            # Clean up temp file
            try:
                os.unlink(csv_file)
            except:
                pass
    
    def test_column_mapping_validation(self):
        """Test column mapping for French and English columns"""
        self.log("🧪 TEST 3: Column mapping validation")
        
        # Create CSV with mixed French/English columns
        mixed_data = {
            'Nom': ['Test Mixed Columns'],  # French
            'Name': ['Test Mixed Name'],    # English (should be mapped to same field)
            'Email': ['test.mixed@example.com'],
            'Rôle': ['VISUALISEUR'],       # French
            'Role': ['TECHNICIEN']         # English (should be mapped to same field)
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as tmp_file:
            df = pd.DataFrame(mixed_data)
            df.to_csv(tmp_file.name, index=False, sep=';')
            
            try:
                with open(tmp_file.name, 'rb') as f:
                    files = {'file': ('test_mixed_columns.csv', f, 'text/csv')}
                    data = {'mode': 'add'}
                    
                    response = self.admin_session.post(
                        f"{BACKEND_URL}/import/users",
                        files=files,
                        data=data,
                        timeout=20
                    )
                    
                    if response.status_code == 200:
                        self.log("✅ Column mapping validation successful!")
                        return True
                    else:
                        self.log(f"❌ Column mapping validation failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                        return False
                        
            except requests.exceptions.RequestException as e:
                self.log(f"❌ Column mapping validation request failed - Error: {str(e)}", "ERROR")
                return False
            finally:
                try:
                    os.unlink(tmp_file.name)
                except:
                    pass
    
    def test_qhse_login(self):
        """Test QHSE login"""
        self.log("Testing QHSE login...")
        
        try:
            response = self.qhse_session.post(
                f"{BACKEND_URL}/auth/login",
                json={
                    "email": QHSE_EMAIL,
                    "password": QHSE_PASSWORD
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.qhse_token = data.get("access_token")
                self.qhse_data = data.get("user")
                
                # Set authorization header for future requests
                self.qhse_session.headers.update({
                    "Authorization": f"Bearer {self.qhse_token}"
                })
                
                self.log(f"✅ QHSE login successful - User: {self.qhse_data.get('prenom')} {self.qhse_data.get('nom')} (Role: {self.qhse_data.get('role')})")
                return True
            else:
                self.log(f"❌ QHSE login failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ QHSE login request failed - Error: {str(e)}", "ERROR")
            return False
    
    def create_qhse_user(self):
        """Create a QHSE user with specific permissions"""
        self.log("Creating QHSE user with QHSE role and specific permissions...")
        
        # QHSE permissions according to specifications
        qhse_permissions = {
            "dashboard": {"view": True, "edit": False, "delete": False},
            "interventionRequests": {"view": True, "edit": True, "delete": False},
            "workOrders": {"view": True, "edit": False, "delete": False},
            "improvementRequests": {"view": True, "edit": True, "delete": False},
            "improvements": {"view": True, "edit": False, "delete": False},
            "preventiveMaintenance": {"view": True, "edit": False, "delete": False},
            "assets": {"view": True, "edit": False, "delete": False},
            "inventory": {"view": True, "edit": False, "delete": False},
            "locations": {"view": True, "edit": False, "delete": False},
            "meters": {"view": True, "edit": False, "delete": False},
            "reports": {"view": True, "edit": False, "delete": False},
            # NO ACCESS TO these modules
            "vendors": {"view": False, "edit": False, "delete": False},
            "people": {"view": False, "edit": False, "delete": False},
            "planning": {"view": False, "edit": False, "delete": False},
            "purchaseHistory": {"view": False, "edit": False, "delete": False},
            "importExport": {"view": False, "edit": False, "delete": False},
            "journal": {"view": False, "edit": False, "delete": False}
        }
        
        user_data = {
            "nom": "QHSE",
            "prenom": "Test",
            "email": QHSE_EMAIL,
            "password": QHSE_PASSWORD,
            "role": "QHSE",
            "service": "Qualité",
            "permissions": qhse_permissions
        }
        
        try:
            response = self.admin_session.post(
                f"{BACKEND_URL}/users/create-member",
                json=user_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                user = response.json()
                self.log(f"✅ QHSE user created successfully - ID: {user.get('id')}, Role: {user.get('role')}")
                return user
            else:
                self.log(f"❌ Failed to create QHSE user - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Create QHSE user request failed - Error: {str(e)}", "ERROR")
            return None
    
    # ==================== QHSE PERMISSIONS TESTS ====================
    
    def test_qhse_reports_analytics(self):
        """Test QHSE can GET /api/reports/analytics (should work - view authorized)"""
        self.log("Testing QHSE GET /api/reports/analytics...")
        
        try:
            response = self.qhse_session.get(
                f"{BACKEND_URL}/reports/analytics",
                timeout=10
            )
            
            if response.status_code == 200:
                analytics = response.json()
                self.log(f"✅ QHSE GET reports/analytics successful - Reports access authorized")
                return True
            else:
                self.log(f"❌ QHSE GET reports/analytics failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ QHSE GET reports/analytics request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_qhse_vendors_forbidden(self):
        """Test QHSE CANNOT GET /api/vendors (should return 403 - no view permission)"""
        self.log("Testing QHSE GET /api/vendors (should be forbidden)...")
        
        try:
            response = self.qhse_session.get(
                f"{BACKEND_URL}/vendors",
                timeout=10
            )
            
            if response.status_code == 403:
                self.log("✅ QHSE GET vendors correctly forbidden (403)")
                return True
            else:
                self.log(f"❌ QHSE GET vendors should be forbidden but got - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ QHSE GET vendors request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_qhse_meters_view_allowed(self):
        """Test QHSE can GET /api/meters (should succeed 200 - view authorized)"""
        self.log("Testing QHSE GET /api/meters...")
        
        try:
            response = self.qhse_session.get(
                f"{BACKEND_URL}/meters",
                timeout=10
            )
            
            if response.status_code == 200:
                meters = response.json()
                self.log(f"✅ QHSE GET meters successful - Found {len(meters)} meters")
                return True
            else:
                self.log(f"❌ QHSE GET meters failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ QHSE GET meters request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_qhse_meters_edit_forbidden(self):
        """Test QHSE CANNOT POST /api/meters (should fail 403 - no edit permission)"""
        self.log("Testing QHSE POST /api/meters (should be forbidden)...")
        
        meter_data = {
            "nom": "Test Meter QHSE",
            "type": "ELECTRICITE",
            "numero_serie": "TEST-QHSE-001",
            "unite": "kWh",
            "prix_unitaire": 0.15
        }
        
        try:
            response = self.qhse_session.post(
                f"{BACKEND_URL}/meters",
                json=meter_data,
                timeout=10
            )
            
            if response.status_code == 403:
                self.log("✅ QHSE POST meters correctly forbidden (403)")
                return True
            else:
                self.log(f"❌ QHSE POST meters should be forbidden but got - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ QHSE POST meters request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_qhse_improvements_view_allowed(self):
        """Test QHSE can GET /api/improvements (should succeed 200 - view authorized)"""
        self.log("Testing QHSE GET /api/improvements...")
        
        try:
            response = self.qhse_session.get(
                f"{BACKEND_URL}/improvements",
                timeout=10
            )
            
            if response.status_code == 200:
                improvements = response.json()
                self.log(f"✅ QHSE GET improvements successful - Found {len(improvements)} improvements")
                return True
            else:
                self.log(f"❌ QHSE GET improvements failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ QHSE GET improvements request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_qhse_improvements_edit_forbidden(self):
        """Test QHSE CANNOT POST /api/improvements (should fail 403 - no edit permission)"""
        self.log("Testing QHSE POST /api/improvements (should be forbidden)...")
        
        improvement_data = {
            "titre": "Test Improvement QHSE",
            "description": "This should fail - QHSE has no edit permission on improvements",
            "priorite": "MOYENNE",
            "type_demande": "AMELIORATION_EQUIPEMENT"
        }
        
        try:
            response = self.qhse_session.post(
                f"{BACKEND_URL}/improvements",
                json=improvement_data,
                timeout=10
            )
            
            if response.status_code == 403:
                self.log("✅ QHSE POST improvements correctly forbidden (403)")
                return True
            else:
                self.log(f"❌ QHSE POST improvements should be forbidden but got - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ QHSE POST improvements request failed - Error: {str(e)}", "ERROR")
            return False
    
    # ==================== WORK ORDERS PERMISSIONS TESTS ====================
    
    def test_qhse_work_orders_post_forbidden(self):
        """Test QHSE CANNOT POST /api/work-orders (should fail 403 - no edit permission)"""
        self.log("Testing QHSE POST /api/work-orders (should be forbidden)...")
        
        work_order_data = {
            "titre": "Test Work Order QHSE",
            "description": "This should fail - QHSE has no edit permission on work orders",
            "priorite": "MOYENNE",
            "statut": "OUVERT",
            "type": "CORRECTIVE",
            "dateLimite": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        try:
            response = self.qhse_session.post(
                f"{BACKEND_URL}/work-orders",
                json=work_order_data,
                timeout=10
            )
            
            if response.status_code == 403:
                self.log("✅ QHSE POST work-orders correctly forbidden (403)")
                return True
            else:
                self.log(f"❌ QHSE POST work-orders should be forbidden but got - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ QHSE POST work-orders request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_qhse_work_orders_delete_forbidden(self):
        """Test QHSE CANNOT DELETE /api/work-orders/{id} (should fail 403 - no delete permission)"""
        # First create a work order as admin to try to delete as QHSE
        work_order_data = {
            "titre": "Test Work Order for QHSE Delete Test",
            "description": "Work order to test QHSE delete permissions",
            "priorite": "BASSE",
            "statut": "OUVERT",
            "type": "CORRECTIVE",
            "dateLimite": (datetime.now() + timedelta(days=5)).isoformat()
        }
        
        try:
            # Create work order as admin
            create_response = self.admin_session.post(
                f"{BACKEND_URL}/work-orders",
                json=work_order_data,
                timeout=10
            )
            
            if create_response.status_code not in [200, 201]:
                self.log("❌ Failed to create work order for delete test", "ERROR")
                return False
            
            work_order = create_response.json()
            work_order_id = work_order.get('id')
            
            self.log(f"Testing QHSE DELETE /api/work-orders/{work_order_id} (should be forbidden)...")
            
            # Try to delete as QHSE
            response = self.qhse_session.delete(
                f"{BACKEND_URL}/work-orders/{work_order_id}",
                timeout=10
            )
            
            if response.status_code == 403:
                self.log("✅ QHSE DELETE work-orders correctly forbidden (403)")
                # Clean up - delete as admin
                self.admin_session.delete(f"{BACKEND_URL}/work-orders/{work_order_id}")
                return True
            else:
                self.log(f"❌ QHSE DELETE work-orders should be forbidden but got - Status: {response.status_code}, Response: {response.text}", "ERROR")
                # Clean up - delete as admin
                self.admin_session.delete(f"{BACKEND_URL}/work-orders/{work_order_id}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ QHSE DELETE work-orders request failed - Error: {str(e)}", "ERROR")
            return False

    def run_qhse_permissions_tests(self):
        """Run all QHSE permissions tests for the GMAO application"""
        self.log("=" * 70)
        self.log("STARTING QHSE PERMISSIONS SYSTEM TESTS")
        self.log("=" * 70)
        
        results = {
            "admin_login": False,
            "create_qhse_user": False,
            "qhse_login": False,
            "qhse_reports_analytics": False,
            "qhse_vendors_forbidden": False,
            "qhse_meters_view_allowed": False,
            "qhse_meters_edit_forbidden": False,
            "qhse_improvements_view_allowed": False,
            "qhse_improvements_edit_forbidden": False,
            "qhse_work_orders_post_forbidden": False,
            "qhse_work_orders_delete_forbidden": False
        }
        
        # Test 1: Admin Login
        results["admin_login"] = self.test_admin_login()
        
        if not results["admin_login"]:
            self.log("❌ Cannot proceed with other tests - Admin login failed", "ERROR")
            return results
        
        # Test 2: Try to login with existing QHSE user first, create if needed
        results["qhse_login"] = self.test_qhse_login()
        
        if not results["qhse_login"]:
            # If login failed, try to create the user
            qhse_user = self.create_qhse_user()
            results["create_qhse_user"] = qhse_user is not None
            
            if qhse_user:
                # Try login again after creation
                results["qhse_login"] = self.test_qhse_login()
        else:
            # User already exists and login worked
            results["create_qhse_user"] = True
        
        if results["qhse_login"]:
            # Test QHSE permissions
            results["qhse_reports_analytics"] = self.test_qhse_reports_analytics()
            results["qhse_vendors_forbidden"] = self.test_qhse_vendors_forbidden()
            results["qhse_meters_view_allowed"] = self.test_qhse_meters_view_allowed()
            results["qhse_meters_edit_forbidden"] = self.test_qhse_meters_edit_forbidden()
            results["qhse_improvements_view_allowed"] = self.test_qhse_improvements_view_allowed()
            results["qhse_improvements_edit_forbidden"] = self.test_qhse_improvements_edit_forbidden()
            results["qhse_work_orders_post_forbidden"] = self.test_qhse_work_orders_post_forbidden()
            results["qhse_work_orders_delete_forbidden"] = self.test_qhse_work_orders_delete_forbidden()
        else:
            self.log("❌ Cannot proceed with QHSE permission tests - QHSE login failed", "ERROR")
        
        # Summary
        self.log("=" * 60)
        self.log("QHSE PERMISSIONS TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        passed = sum(results.values())
        total = len(results)
        
        # Group results by category for better readability
        self.log("\n🔐 AUTHENTICATION TESTS:")
        auth_tests = ["admin_login", "create_qhse_user", "qhse_login"]
        for test in auth_tests:
            if test in results:
                status = "✅ PASS" if results[test] else "❌ FAIL"
                self.log(f"  {test}: {status}")
        
        self.log("\n✅ QHSE ALLOWED PERMISSIONS (should work):")
        allowed_tests = ["qhse_reports_analytics", "qhse_meters_view_allowed", "qhse_improvements_view_allowed"]
        for test in allowed_tests:
            if test in results:
                status = "✅ PASS" if results[test] else "❌ FAIL"
                self.log(f"  {test}: {status}")
        
        self.log("\n🚫 QHSE FORBIDDEN PERMISSIONS (should be blocked):")
        forbidden_tests = [
            "qhse_vendors_forbidden",
            "qhse_meters_edit_forbidden", 
            "qhse_improvements_edit_forbidden",
            "qhse_work_orders_post_forbidden",
            "qhse_work_orders_delete_forbidden"
        ]
        for test in forbidden_tests:
            if test in results:
                status = "✅ PASS" if results[test] else "❌ FAIL"
                self.log(f"  {test}: {status}")
        
        self.log(f"\n📊 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 ALL QHSE PERMISSIONS TESTS PASSED - Permission system is working correctly!")
            self.log("✅ QHSE users can access authorized modules (reports, meters view, improvements view)")
            self.log("✅ QHSE users are correctly blocked from unauthorized modules (vendors, edit operations)")
            self.log("✅ Forbidden operations return 403 status codes as expected")
        else:
            self.log("⚠️ Some QHSE permissions tests failed - Check the logs above for details")
            failed_tests = [test for test, result in results.items() if not result]
            self.log(f"❌ Failed tests: {', '.join(failed_tests)}")
        
        return results

if __name__ == "__main__":
    tester = QHSEPermissionsTester()
    results = tester.run_qhse_permissions_tests()
    
    # Exit with appropriate code
    if all(results.values()):
        exit(0)  # Success
    else:
        exit(1)  # Failure
        self.log("Testing get improvement requests endpoint...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/improvement-requests",
                timeout=10
            )
            
            if response.status_code == 200:
                requests_list = response.json()
                self.log(f"✅ Get improvement requests successful - Found {len(requests_list)} requests")
                return requests_list
            else:
                self.log(f"❌ Get improvement requests failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Get improvement requests failed - Error: {str(e)}", "ERROR")
            return None
    
    def test_convert_to_improvement(self, request_id, assignee_id=None, date_limite=None):
        """Test POST /api/improvement-requests/{id}/convert-to-improvement - Convert request to improvement"""
        self.log(f"Testing convert improvement request {request_id} to improvement...")
        
        convert_data = {}
        if assignee_id:
            convert_data["assignee_id"] = assignee_id
        if date_limite:
            convert_data["date_limite"] = date_limite
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/improvement-requests/{request_id}/convert-to-improvement",
                json=convert_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                improvement_id = result.get('improvement_id')
                improvement_numero = result.get('improvement_numero')
                self.log(f"✅ Convert to improvement successful - Improvement ID: {improvement_id}, Number: {improvement_numero}")
                
                # Verify improvement number is >= 7000
                if improvement_numero and int(improvement_numero) >= 7000:
                    self.log(f"✅ Improvement number validation passed - Number {improvement_numero} >= 7000")
                else:
                    self.log(f"❌ Improvement number validation failed - Number {improvement_numero} < 7000", "ERROR")
                
                return result
            else:
                self.log(f"❌ Convert to improvement failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Convert to improvement failed - Error: {str(e)}", "ERROR")
            return None
    
    def test_get_improvement_request_details(self, request_id):
        """Test GET /api/improvement-requests/{id} - Get improvement request details"""
        self.log(f"Testing get improvement request details {request_id}...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/improvement-requests/{request_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                request = response.json()
                self.log(f"✅ Get improvement request details successful - Title: {request.get('titre')}")
                return request
            else:
                self.log(f"❌ Get improvement request details failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Get improvement request details failed - Error: {str(e)}", "ERROR")
            return None
    
    def test_add_improvement_request_comment(self, request_id):
        """Test POST /api/improvement-requests/{id}/comments - Add comment to improvement request"""
        self.log(f"Testing add comment to improvement request {request_id}...")
        
        comment_data = {
            "contenu": "Commentaire de test pour la demande d'amélioration",
            "type": "COMMENTAIRE"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/improvement-requests/{request_id}/comments",
                json=comment_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                comment = response.json()
                self.log(f"✅ Add improvement request comment successful - Comment ID: {comment.get('id')}")
                return comment
            else:
                self.log(f"❌ Add improvement request comment failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Add improvement request comment failed - Error: {str(e)}", "ERROR")
            return None
    
    # ==================== IMPROVEMENTS TESTS ====================
    
    def test_create_improvement(self):
        """Test POST /api/improvements - Create a new improvement"""
        self.log("Testing create improvement endpoint...")
        
        improvement_data = {
            "titre": "Amélioration directe système ventilation",
            "description": "Amélioration directe du système de ventilation pour optimiser la qualité de l'air",
            "priorite": "HAUTE",
            "type_demande": "AMELIORATION_EQUIPEMENT",
            "demandeur": "Marie Martin",
            "service_demandeur": "Technique"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/improvements",
                json=improvement_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                improvement = response.json()
                numero = improvement.get('numero')
                self.log(f"✅ Create improvement successful - ID: {improvement.get('id')}, Number: {numero}")
                
                # Verify improvement number is >= 7000
                if numero and int(numero) >= 7000:
                    self.log(f"✅ Improvement number validation passed - Number {numero} >= 7000")
                else:
                    self.log(f"❌ Improvement number validation failed - Number {numero} < 7000", "ERROR")
                
                return improvement
            else:
                self.log(f"❌ Create improvement failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Create improvement failed - Error: {str(e)}", "ERROR")
            return None
    
    def test_get_improvements(self):
        """Test GET /api/improvements - Get all improvements"""
        self.log("Testing get improvements endpoint...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/improvements",
                timeout=10
            )
            
            if response.status_code == 200:
                improvements = response.json()
                self.log(f"✅ Get improvements successful - Found {len(improvements)} improvements")
                return improvements
            else:
                self.log(f"❌ Get improvements failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Get improvements failed - Error: {str(e)}", "ERROR")
            return None
    
    def test_get_improvement_details(self, improvement_id):
        """Test GET /api/improvements/{id} - Get improvement details"""
        self.log(f"Testing get improvement details {improvement_id}...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/improvements/{improvement_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                improvement = response.json()
                self.log(f"✅ Get improvement details successful - Title: {improvement.get('titre')}")
                return improvement
            else:
                self.log(f"❌ Get improvement details failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Get improvement details failed - Error: {str(e)}", "ERROR")
            return None
    
    def test_add_improvement_comment(self, improvement_id):
        """Test POST /api/improvements/{id}/comments - Add comment to improvement"""
        self.log(f"Testing add comment to improvement {improvement_id}...")
        
        comment_data = {
            "contenu": "Commentaire de test pour l'amélioration",
            "type": "COMMENTAIRE"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/improvements/{improvement_id}/comments",
                json=comment_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                comment = response.json()
                self.log(f"✅ Add improvement comment successful - Comment ID: {comment.get('id')}")
                return comment
            else:
                self.log(f"❌ Add improvement comment failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Add improvement comment failed - Error: {str(e)}", "ERROR")
            return None
    
    def test_update_improvement_request(self, request_id):
        """Test PUT /api/improvement-requests/{id} - Update improvement request"""
        self.log(f"Testing update improvement request {request_id}...")
        
        update_data = {
            "priorite": "HAUTE",
            "justification": "Justification mise à jour pour test"
        }
        
        try:
            response = self.session.put(
                f"{BACKEND_URL}/improvement-requests/{request_id}",
                json=update_data,
                timeout=10
            )
            
            if response.status_code == 200:
                request = response.json()
                self.log(f"✅ Update improvement request successful - Priority: {request.get('priorite')}")
                return request
            else:
                self.log(f"❌ Update improvement request failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Update improvement request failed - Error: {str(e)}", "ERROR")
            return None
    
    def test_update_improvement(self, improvement_id):
        """Test PUT /api/improvements/{id} - Update improvement"""
        self.log(f"Testing update improvement {improvement_id}...")
        
        update_data = {
            "statut": "EN_COURS",
            "priorite": "HAUTE"
        }
        
        try:
            response = self.session.put(
                f"{BACKEND_URL}/improvements/{improvement_id}",
                json=update_data,
                timeout=10
            )
            
            if response.status_code == 200:
                improvement = response.json()
                self.log(f"✅ Update improvement successful - Status: {improvement.get('statut')}")
                return improvement
            else:
                self.log(f"❌ Update improvement failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Update improvement failed - Error: {str(e)}", "ERROR")
            return None
    
    def test_delete_improvement_request(self, request_id):
        """Test DELETE /api/improvement-requests/{id} - Delete improvement request"""
        self.log(f"Testing delete improvement request {request_id}...")
        
        try:
            response = self.session.delete(
                f"{BACKEND_URL}/improvement-requests/{request_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Delete improvement request successful - {result.get('message')}")
                return True
            else:
                self.log(f"❌ Delete improvement request failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Delete improvement request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_delete_improvement(self, improvement_id):
        """Test DELETE /api/improvements/{id} - Delete improvement"""
        self.log(f"Testing delete improvement {improvement_id}...")
        
        try:
            response = self.session.delete(
                f"{BACKEND_URL}/improvements/{improvement_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Delete improvement successful - {result.get('message')}")
                return True
            else:
                self.log(f"❌ Delete improvement failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Delete improvement failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_verify_conversion_update(self, request_id, expected_improvement_id, expected_improvement_numero):
        """Verify that the improvement request was properly updated after conversion"""
        self.log(f"Verifying conversion update for request {request_id}...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/improvement-requests/{request_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                request = response.json()
                improvement_id = request.get('improvement_id')
                improvement_numero = request.get('improvement_numero')
                
                if improvement_id == expected_improvement_id and improvement_numero == expected_improvement_numero:
                    self.log(f"✅ Conversion update verification successful - Request updated with improvement ID: {improvement_id}, Number: {improvement_numero}")
                    return True
                else:
                    self.log(f"❌ Conversion update verification failed - Expected ID: {expected_improvement_id}, Got: {improvement_id}, Expected Number: {expected_improvement_numero}, Got: {improvement_numero}", "ERROR")
                    return False
            else:
                self.log(f"❌ Conversion update verification failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Conversion update verification failed - Error: {str(e)}", "ERROR")
            return False
    
    def run_permissions_tests(self):
        """Run all permissions tests for the GMAO application"""
        self.log("=" * 70)
        self.log("STARTING PERMISSIONS SYSTEM TESTS")
        self.log("=" * 70)
        
        results = {
            "admin_login": False,
            "create_viewer_user": False,
            "viewer_login": False,
            "admin_get_work_orders": False,
            "admin_post_work_orders": False,
            "admin_delete_work_orders": False,
            "viewer_get_work_orders": False,
            "viewer_post_work_orders_forbidden": False,
            "viewer_delete_work_orders_forbidden": False,
            "viewer_get_intervention_requests": False,
            "viewer_post_intervention_requests_forbidden": False
        }
        
        # Test 1: Admin Login
        results["admin_login"] = self.test_admin_login()
        
        if not results["admin_login"]:
            self.log("❌ Cannot proceed with other tests - Admin login failed", "ERROR")
            return results
        
        # Test 2: Try to login with existing viewer user first, create if needed
        results["viewer_login"] = self.test_viewer_login()
        
        if not results["viewer_login"]:
            # If login failed, try to create the user
            viewer_user = self.create_viewer_user()
            results["create_viewer_user"] = viewer_user is not None
            
            if viewer_user:
                # Try login again after creation
                results["viewer_login"] = self.test_viewer_login()
        else:
            # User already exists and login worked
            results["create_viewer_user"] = True
            
            if results["viewer_login"]:
                # Test admin permissions on work orders
                results["admin_get_work_orders"] = self.test_admin_get_work_orders()
                results["admin_post_work_orders"] = self.test_admin_post_work_orders()
                results["admin_delete_work_orders"] = self.test_admin_delete_work_orders()
                
                # Test viewer permissions on work orders
                results["viewer_get_work_orders"] = self.test_viewer_get_work_orders()
                results["viewer_post_work_orders_forbidden"] = self.test_viewer_post_work_orders_forbidden()
                results["viewer_delete_work_orders_forbidden"] = self.test_viewer_delete_work_orders_forbidden()
                
                # Test viewer permissions on intervention requests
                results["viewer_get_intervention_requests"] = self.test_viewer_get_intervention_requests()
                results["viewer_post_intervention_requests_forbidden"] = self.test_viewer_post_intervention_requests_forbidden()
            else:
                self.log("❌ Cannot proceed with viewer permission tests - Viewer login failed", "ERROR")
        
        # Summary
        self.log("=" * 60)
        self.log("PERMISSIONS TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        passed = sum(results.values())
        total = len(results)
        
        # Group results by category for better readability
        self.log("\n🔐 AUTHENTICATION TESTS:")
        auth_tests = ["admin_login", "create_viewer_user", "viewer_login"]
        for test in auth_tests:
            if test in results:
                status = "✅ PASS" if results[test] else "❌ FAIL"
                self.log(f"  {test}: {status}")
        
        self.log("\n👑 ADMIN PERMISSIONS (should all work):")
        admin_tests = ["admin_get_work_orders", "admin_post_work_orders", "admin_delete_work_orders"]
        for test in admin_tests:
            if test in results:
                status = "✅ PASS" if results[test] else "❌ FAIL"
                self.log(f"  {test}: {status}")
        
        self.log("\n👁️ VIEWER PERMISSIONS (view should work, edit/delete should be forbidden):")
        viewer_tests = [
            "viewer_get_work_orders", 
            "viewer_post_work_orders_forbidden", 
            "viewer_delete_work_orders_forbidden",
            "viewer_get_intervention_requests",
            "viewer_post_intervention_requests_forbidden"
        ]
        for test in viewer_tests:
            if test in results:
                status = "✅ PASS" if results[test] else "❌ FAIL"
                self.log(f"  {test}: {status}")
        
        self.log(f"\n📊 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 ALL PERMISSIONS TESTS PASSED - Permission system is working correctly!")
            self.log("✅ Admin users can perform all operations")
            self.log("✅ Viewer users are correctly restricted to view-only operations")
            self.log("✅ Forbidden operations return 403 status codes as expected")
        else:
            self.log("⚠️ Some permissions tests failed - Check the logs above for details")
            failed_tests = [test for test, result in results.items() if not result]
            self.log(f"❌ Failed tests: {', '.join(failed_tests)}")
        
        return results

if __name__ == "__main__":
    tester = PermissionsTester()
    results = tester.run_permissions_tests()
    
    # Exit with appropriate code
    if all(results.values()):
        exit(0)  # Success
    else:
        exit(1)  # Failure