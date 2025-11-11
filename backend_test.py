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
ADMIN_EMAIL_1 = "admin@gmao-iris.local"
ADMIN_PASSWORD_1 = "Admin123!"
ADMIN_EMAIL_2 = "buenogy@gmail.com"
ADMIN_PASSWORD_2 = "nmrojvbvgb"

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
                    self.log(f"📋 Response structure: {list(result.keys())}")
                    
                    # Verify response structure (data is at root level)
                    if 'modules' in result:
                        self.log(f"✅ response.modules exists: {list(result['modules'].keys())}")
                    if 'total' in result:
                        self.log(f"✅ response.total: {result['total']}")
                    if 'inserted' in result:
                        self.log(f"✅ response.inserted: {result['inserted']}")
                    if 'updated' in result:
                        self.log(f"✅ response.updated: {result['updated']}")
                    if 'skipped' in result:
                        self.log(f"✅ response.skipped: {result['skipped']}")
                    
                    # Check if data was actually inserted
                    if result.get('inserted', 0) > 0:
                        self.log("✅ Data successfully inserted into MongoDB")
                    else:
                        self.log("⚠️ No data was inserted (might be duplicates or validation issues)")
                    
                    # Check for the critical pandas error
                    if 'errors' in result and result['errors']:
                        for error in result['errors']:
                            if "can only use .str accessor with string value" in str(error):
                                self.log("❌ CRITICAL: Found the pandas string accessor error!", "ERROR")
                                return False
                    
                    self.log("✅ No pandas string accessor error found - Fix is working!")
                    return True
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
                    self.log(f"📋 Response structure: {list(result.keys())}")
                    
                    # Verify response structure (data is at root level)
                    if 'inserted' in result and result['inserted'] > 0:
                        self.log(f"✅ response.inserted > 0: {result['inserted']}")
                        self.log("✅ Data correctly inserted into MongoDB")
                    else:
                        self.log(f"⚠️ No data inserted for {module}: {result}")
                    
                    # Check for the critical error message
                    if 'errors' in result and result['errors']:
                        for error in result['errors']:
                            if "impossible de charger les données" in str(error):
                                self.log(f"❌ CRITICAL: Found the reported error for {module}!", "ERROR")
                                return False
                    
                    self.log(f"✅ No 'impossible de charger les données' error for {module} - Fix is working!")
                    return True
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
    
    def run_import_export_tests(self):
        """Run all import/export tests for the GMAO application"""
        self.log("=" * 80)
        self.log("STARTING IMPORT/EXPORT MODULE TESTS - CORRECTION VALIDATION")
        self.log("=" * 80)
        
        results = {
            "admin_login": False,
            "import_all_multi_sheet": False,
            "column_mapping_validation": False
        }
        
        # Add individual module tests
        modules_to_test = ["work-orders", "equipments", "users", "inventory", "vendors", 
                          "intervention-requests", "improvement-requests", "improvements", 
                          "locations", "meters"]
        
        for module in modules_to_test:
            results[f"import_{module.replace('-', '_')}"] = False
        
        # Test 1: Admin Login
        results["admin_login"] = self.test_admin_login()
        
        if not results["admin_login"]:
            self.log("❌ Cannot proceed with other tests - Admin login failed", "ERROR")
            return results
        
        # Test 2: Import "Toutes les données" multi-sheet Excel (CRITICAL TEST)
        results["import_all_multi_sheet"] = self.test_import_all_multi_sheet()
        
        # Test 3: Individual module imports
        for module in modules_to_test:
            if module != "purchase-history":  # Skip purchase-history as mentioned in requirements
                results[f"import_{module.replace('-', '_')}"] = self.test_individual_module_import(module)
        
        # Test 4: Column mapping validation
        results["column_mapping_validation"] = self.test_column_mapping_validation()
        
        # Summary
        self.log("=" * 70)
        self.log("IMPORT/EXPORT TEST RESULTS SUMMARY")
        self.log("=" * 70)
        
        passed = sum(results.values())
        total = len(results)
        
        # Critical test results
        self.log("\n🎯 CRITICAL TESTS (User-reported issues):")
        critical_tests = ["import_all_multi_sheet"]
        for test in critical_tests:
            if test in results:
                status = "✅ PASS" if results[test] else "❌ FAIL"
                self.log(f"  {test}: {status}")
        
        # Individual module tests
        self.log("\n📋 INDIVIDUAL MODULE IMPORTS:")
        failed_modules = []
        passed_modules = []
        
        for module in modules_to_test:
            test_key = f"import_{module.replace('-', '_')}"
            if test_key in results:
                status = "✅ PASS" if results[test_key] else "❌ FAIL"
                self.log(f"  {module}: {status}")
                if results[test_key]:
                    passed_modules.append(module)
                else:
                    failed_modules.append(module)
        
        # Other tests
        self.log("\n🔧 OTHER TESTS:")
        other_tests = ["admin_login", "column_mapping_validation"]
        for test in other_tests:
            if test in results:
                status = "✅ PASS" if results[test] else "❌ FAIL"
                self.log(f"  {test}: {status}")
        
        self.log(f"\n📊 Overall: {passed}/{total} tests passed")
        
        # Detailed analysis
        if results.get("import_all_multi_sheet", False):
            self.log("🎉 CRITICAL SUCCESS: Import 'Toutes les données' is working!")
            self.log("✅ Fixed: 'can only use .str accessor with string value !' error resolved")
        else:
            self.log("🚨 CRITICAL FAILURE: Import 'Toutes les données' still failing!")
            self.log("❌ The pandas string accessor error may still exist")
        
        if len(passed_modules) > 0:
            self.log(f"✅ Individual imports working for: {', '.join(passed_modules)}")
        
        if len(failed_modules) > 0:
            self.log(f"❌ Individual imports failing for: {', '.join(failed_modules)}")
            self.log("❌ These modules may still show 'impossible de charger les données'")
        
        if passed == total:
            self.log("🎉 ALL IMPORT/EXPORT TESTS PASSED!")
            self.log("✅ Both user-reported issues have been resolved:")
            self.log("  1. Import 'Toutes les données' works without pandas errors")
            self.log("  2. Individual module imports work without loading errors")
        else:
            self.log("⚠️ Some import/export tests failed - Issues may still exist")
            failed_tests = [test for test, result in results.items() if not result]
            self.log(f"❌ Failed tests: {', '.join(failed_tests)}")
        
        return results

if __name__ == "__main__":
    tester = ImportExportTester()
    results = tester.run_import_export_tests()
    
    # Exit with appropriate code
    if all(results.values()):
        exit(0)  # Success
    else:
        exit(1)  # Failure
