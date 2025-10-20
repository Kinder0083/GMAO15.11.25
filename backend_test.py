#!/usr/bin/env python3
"""
Backend API Testing for GMAO Atlas System
Tests the equipment hierarchy management system endpoints and Import/Export functionality
"""

import requests
import json
import sys
import io
import csv
import tempfile
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Backend URL from frontend/.env
BASE_URL = "https://asset-tracker-192.preview.emergentagent.com/api"

class EquipmentHierarchyTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
        self.admin_user_id = None
        self.test_locations = []
        self.test_equipments = []
        self.session = requests.Session()
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages"""
        print(f"[{level}] {message}")
        
    def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None, token: str = None) -> requests.Response:
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}{endpoint}"
        
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
            
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        elif self.admin_token:
            request_headers["Authorization"] = f"Bearer {self.admin_token}"
            
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=request_headers)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=request_headers)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=request_headers)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=request_headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            self.log(f"{method} {endpoint} -> {response.status_code}")
            return response
        except Exception as e:
            self.log(f"Request failed: {e}", "ERROR")
            raise
            
    def setup_admin_user(self) -> bool:
        """Create or login as admin user"""
        self.log("Setting up admin user...")
        
        # Try to login first
        login_data = {
            "email": "admin@example.com",
            "password": "password123"
        }
        
        response = self.make_request("POST", "/auth/login", login_data, token=None)
        
        if response.status_code == 200:
            data = response.json()
            self.admin_token = data["access_token"]
            self.admin_user_id = data["user"]["id"]
            self.log(f"Admin login successful. User ID: {self.admin_user_id}")
            return True
        elif response.status_code == 401:
            # Admin doesn't exist, create it
            self.log("Admin user not found, creating...")
            register_data = {
                "nom": "Admin",
                "prenom": "System",
                "email": "admin@example.com",
                "telephone": "+33123456789",
                "password": "password123",
                "role": "ADMIN"
            }
            
            response = self.make_request("POST", "/auth/register", register_data, token=None)
            if response.status_code == 200:
                self.log("Admin user created successfully")
                # Now login
                return self.setup_admin_user()
            else:
                self.log(f"Failed to create admin user: {response.status_code} - {response.text}", "ERROR")
                return False
        else:
            self.log(f"Login failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def setup_test_location(self) -> Optional[str]:
        """Create a test location for equipment testing"""
        self.log("Creating test location...")
        
        location_data = {
            "nom": "Atelier Principal",
            "adresse": "123 Rue de l'Industrie",
            "ville": "Paris",
            "codePostal": "75001",
            "type": "Atelier"
        }
        
        response = self.make_request("POST", "/locations", location_data)
        
        if response.status_code == 200:
            location = response.json()
            location_id = location["id"]
            self.test_locations.append(location_id)
            self.log(f"✓ Test location created: {location_id}")
            return location_id
        else:
            self.log(f"✗ Failed to create test location: {response.status_code} - {response.text}", "ERROR")
            return None
            
    def test_create_parent_equipment(self, location_id: str) -> Optional[str]:
        """Test creating parent equipment without parent_id"""
        self.log("\n=== Testing POST /api/equipments - Parent Equipment ===")
        
        equipment_data = {
            "nom": "Machine Principale A",
            "categorie": "Machine de production",
            "emplacement_id": location_id,
            "statut": "OPERATIONNEL",
            "dateAchat": "2023-01-15T10:00:00Z",
            "coutAchat": 50000.0,
            "numeroSerie": "MP-A-001",
            "garantie": "2 ans"
        }
        
        response = self.make_request("POST", "/equipments", equipment_data)
        
        if response.status_code == 200:
            equipment = response.json()
            equipment_id = equipment["id"]
            self.test_equipments.append(equipment_id)
            
            # Verify parent equipment properties
            if equipment.get("parent_id") is None and equipment.get("hasChildren") == False:
                self.log(f"✓ Parent equipment created successfully: {equipment_id}")
                self.log(f"  - Name: {equipment['nom']}")
                self.log(f"  - Location: {equipment.get('emplacement', {}).get('nom', 'N/A')}")
                self.log(f"  - Parent ID: {equipment.get('parent_id', 'None')}")
                self.log(f"  - Has Children: {equipment.get('hasChildren', False)}")
                return equipment_id
            else:
                self.log(f"✗ Parent equipment properties incorrect", "ERROR")
                return None
        else:
            self.log(f"✗ Failed to create parent equipment: {response.status_code} - {response.text}", "ERROR")
            return None
        
    def test_create_sub_equipment_with_inheritance(self, parent_id: str) -> Optional[str]:
        """Test creating sub-equipment with location inheritance"""
        self.log("\n=== Testing POST /api/equipments - Sub-equipment with Location Inheritance ===")
        
        # Create sub-equipment WITHOUT specifying location_id (should inherit from parent)
        equipment_data = {
            "nom": "Sous-module A1",
            "categorie": "Composant",
            "parent_id": parent_id,
            "statut": "OPERATIONNEL",
            "dateAchat": "2023-02-15T10:00:00Z",
            "coutAchat": 5000.0,
            "numeroSerie": "SM-A1-001",
            "garantie": "1 an"
            # Note: NO emplacement_id specified - should inherit from parent
        }
        
        response = self.make_request("POST", "/equipments", equipment_data)
        
        if response.status_code == 200:
            equipment = response.json()
            equipment_id = equipment["id"]
            self.test_equipments.append(equipment_id)
            
            # Verify inheritance properties
            if (equipment.get("parent_id") == parent_id and 
                equipment.get("hasChildren") == False and
                equipment.get("emplacement") is not None):
                self.log(f"✓ Sub-equipment created with location inheritance: {equipment_id}")
                self.log(f"  - Name: {equipment['nom']}")
                self.log(f"  - Parent ID: {equipment.get('parent_id')}")
                self.log(f"  - Inherited Location: {equipment.get('emplacement', {}).get('nom', 'N/A')}")
                self.log(f"  - Has Children: {equipment.get('hasChildren', False)}")
                return equipment_id
            else:
                self.log(f"✗ Sub-equipment inheritance properties incorrect", "ERROR")
                self.log(f"  - Parent ID: {equipment.get('parent_id')} (expected: {parent_id})")
                self.log(f"  - Location: {equipment.get('emplacement')}")
                return None
        else:
            self.log(f"✗ Failed to create sub-equipment with inheritance: {response.status_code} - {response.text}", "ERROR")
            return None
            
    def test_create_sub_equipment_with_explicit_location(self, parent_id: str, location_id: str) -> Optional[str]:
        """Test creating sub-equipment with explicit location (no inheritance)"""
        self.log("\n=== Testing POST /api/equipments - Sub-equipment with Explicit Location ===")
        
        # Create another test location first
        location_data = {
            "nom": "Atelier Secondaire",
            "adresse": "456 Avenue de la Technologie",
            "ville": "Lyon",
            "codePostal": "69001",
            "type": "Atelier"
        }
        
        response = self.make_request("POST", "/locations", location_data)
        if response.status_code != 200:
            self.log(f"✗ Failed to create second location: {response.status_code}", "ERROR")
            return None
            
        second_location = response.json()
        second_location_id = second_location["id"]
        self.test_locations.append(second_location_id)
        
        # Create sub-equipment WITH explicit location_id (should NOT inherit)
        equipment_data = {
            "nom": "Sous-module A2",
            "categorie": "Composant",
            "parent_id": parent_id,
            "emplacement_id": second_location_id,  # Explicit location - different from parent
            "statut": "OPERATIONNEL",
            "dateAchat": "2023-03-15T10:00:00Z",
            "coutAchat": 3000.0,
            "numeroSerie": "SM-A2-001",
            "garantie": "1 an"
        }
        
        response = self.make_request("POST", "/equipments", equipment_data)
        
        if response.status_code == 200:
            equipment = response.json()
            equipment_id = equipment["id"]
            self.test_equipments.append(equipment_id)
            
            # Verify explicit location is used (not inherited)
            if (equipment.get("parent_id") == parent_id and 
                equipment.get("hasChildren") == False and
                equipment.get("emplacement", {}).get("id") == second_location_id):
                self.log(f"✓ Sub-equipment created with explicit location: {equipment_id}")
                self.log(f"  - Name: {equipment['nom']}")
                self.log(f"  - Parent ID: {equipment.get('parent_id')}")
                self.log(f"  - Explicit Location: {equipment.get('emplacement', {}).get('nom', 'N/A')}")
                self.log(f"  - Has Children: {equipment.get('hasChildren', False)}")
                return equipment_id
            else:
                self.log(f"✗ Sub-equipment explicit location properties incorrect", "ERROR")
                return None
        else:
            self.log(f"✗ Failed to create sub-equipment with explicit location: {response.status_code} - {response.text}", "ERROR")
            return None
        
    def test_get_equipments_with_hierarchy_info(self) -> bool:
        """Test GET /api/equipments with hasChildren and parent info"""
        self.log("\n=== Testing GET /api/equipments with Hierarchy Info ===")
        
        response = self.make_request("GET", "/equipments")
        
        if response.status_code == 200:
            equipments = response.json()
            self.log(f"✓ Successfully retrieved {len(equipments)} equipments")
            
            success = True
            parent_found = False
            child_found = False
            
            for equipment in equipments:
                equipment_id = equipment.get("id")
                
                # Check if this is one of our test equipments
                if equipment_id in self.test_equipments:
                    # Verify required hierarchy fields are present
                    if "hasChildren" not in equipment:
                        self.log(f"✗ Missing hasChildren field for equipment {equipment_id}", "ERROR")
                        success = False
                        continue
                        
                    # Check parent equipment (should have hasChildren = True if it has children)
                    if equipment.get("parent_id") is None:
                        parent_found = True
                        # This should be a parent - check if it has children
                        has_children = equipment.get("hasChildren", False)
                        self.log(f"  - Parent Equipment: {equipment.get('nom')} (hasChildren: {has_children})")
                        
                        if has_children:
                            self.log(f"    ✓ Parent correctly shows hasChildren = True")
                        else:
                            # This might be OK if no children were created yet
                            self.log(f"    ⚠ Parent shows hasChildren = False (may be correct if no children)")
                    else:
                        child_found = True
                        # This should be a child - verify parent info
                        parent_info = equipment.get("parent")
                        if parent_info and "id" in parent_info and "nom" in parent_info:
                            self.log(f"  - Child Equipment: {equipment.get('nom')} (parent: {parent_info.get('nom')})")
                            self.log(f"    ✓ Child has correct parent info")
                        else:
                            self.log(f"✗ Child equipment missing or incomplete parent info", "ERROR")
                            success = False
                            
            if not parent_found:
                self.log("⚠ No parent equipment found in results")
            if not child_found:
                self.log("⚠ No child equipment found in results")
                
            return success
        else:
            self.log(f"✗ Failed to get equipments: {response.status_code} - {response.text}", "ERROR")
            return False
        
    def test_get_equipment_detail(self) -> bool:
        """Test GET /api/equipments/{id} with parent and hasChildren info"""
        self.log("\n=== Testing GET /api/equipments/{id} ===")
        
        if not self.test_equipments:
            self.log("✗ No test equipments available", "ERROR")
            return False
            
        success = True
        
        for equipment_id in self.test_equipments:
            response = self.make_request("GET", f"/equipments/{equipment_id}")
            
            if response.status_code == 200:
                equipment = response.json()
                self.log(f"✓ Successfully retrieved equipment details: {equipment_id}")
                self.log(f"  - Name: {equipment.get('nom')}")
                self.log(f"  - Parent ID: {equipment.get('parent_id', 'None')}")
                self.log(f"  - Has Children: {equipment.get('hasChildren', False)}")
                
                # Verify required fields are present
                required_fields = ["id", "nom", "hasChildren"]
                for field in required_fields:
                    if field not in equipment:
                        self.log(f"✗ Missing required field {field}", "ERROR")
                        success = False
                        
                # If equipment has parent, verify parent info is included
                if equipment.get("parent_id"):
                    if "parent" not in equipment or not equipment["parent"]:
                        self.log(f"✗ Equipment has parent_id but missing parent info", "ERROR")
                        success = False
                    else:
                        parent_info = equipment["parent"]
                        if "id" not in parent_info or "nom" not in parent_info:
                            self.log(f"✗ Incomplete parent info", "ERROR")
                            success = False
                        else:
                            self.log(f"  - Parent Info: {parent_info.get('nom')} ({parent_info.get('id')})")
                            
            else:
                self.log(f"✗ Failed to get equipment details: {response.status_code} - {response.text}", "ERROR")
                success = False
                
        # Test with invalid equipment ID
        response = self.make_request("GET", "/equipments/invalid_id")
        if response.status_code == 404 or response.status_code == 400:
            self.log("✓ Correctly handled invalid equipment ID")
        else:
            self.log(f"✗ Should have returned 404/400 for invalid equipment ID: {response.status_code}", "ERROR")
            success = False
            
        return success
        
    def test_get_equipment_children(self) -> bool:
        """Test GET /api/equipments/{id}/children"""
        self.log("\n=== Testing GET /api/equipments/{id}/children ===")
        
        if not self.test_equipments:
            self.log("✗ No test equipments available", "ERROR")
            return False
            
        success = True
        parent_id = self.test_equipments[0]  # Use first equipment as parent
        
        response = self.make_request("GET", f"/equipments/{parent_id}/children")
        
        if response.status_code == 200:
            children = response.json()
            self.log(f"✓ Successfully retrieved children for equipment {parent_id}")
            self.log(f"  - Number of children: {len(children)}")
            
            # Verify each child has correct parent_id
            for child in children:
                if child.get("parent_id") != parent_id:
                    self.log(f"✗ Child {child.get('id')} has incorrect parent_id: {child.get('parent_id')}", "ERROR")
                    success = False
                else:
                    self.log(f"  - Child: {child.get('nom')} (ID: {child.get('id')})")
                    
                # Verify child has required hierarchy fields
                if "hasChildren" not in child:
                    self.log(f"✗ Child missing hasChildren field", "ERROR")
                    success = False
                    
                if "parent" not in child or not child["parent"]:
                    self.log(f"✗ Child missing parent info", "ERROR")
                    success = False
                    
        else:
            self.log(f"✗ Failed to get equipment children: {response.status_code} - {response.text}", "ERROR")
            success = False
            
        # Test with invalid equipment ID
        response = self.make_request("GET", "/equipments/invalid_id/children")
        if response.status_code == 404 or response.status_code == 400:
            self.log("✓ Correctly handled invalid equipment ID for children")
        else:
            self.log(f"✗ Should have returned 404/400 for invalid equipment ID: {response.status_code}", "ERROR")
            success = False
            
        return success
        
    def test_get_equipment_hierarchy(self) -> bool:
        """Test GET /api/equipments/{id}/hierarchy - Complete recursive hierarchy"""
        self.log("\n=== Testing GET /api/equipments/{id}/hierarchy ===")
        
        if not self.test_equipments:
            self.log("✗ No test equipments available", "ERROR")
            return False
            
        # First, create a 3-level hierarchy: parent -> child -> grandchild
        parent_id = self.test_equipments[0]
        
        # Create grandchild equipment (child of the first sub-equipment)
        if len(self.test_equipments) > 1:
            child_id = self.test_equipments[1]
            
            grandchild_data = {
                "nom": "Capteur A1-1",
                "categorie": "Capteur",
                "parent_id": child_id,
                "statut": "OPERATIONNEL",
                "dateAchat": "2023-04-15T10:00:00Z",
                "coutAchat": 500.0,
                "numeroSerie": "CAP-A1-1-001",
                "garantie": "6 mois"
            }
            
            response = self.make_request("POST", "/equipments", grandchild_data)
            if response.status_code == 200:
                grandchild = response.json()
                grandchild_id = grandchild["id"]
                self.test_equipments.append(grandchild_id)
                self.log(f"✓ Created grandchild equipment: {grandchild_id}")
            else:
                self.log(f"⚠ Failed to create grandchild equipment: {response.status_code}", "WARN")
        
        # Now test the hierarchy endpoint
        success = True
        response = self.make_request("GET", f"/equipments/{parent_id}/hierarchy")
        
        if response.status_code == 200:
            hierarchy = response.json()
            self.log(f"✓ Successfully retrieved hierarchy for equipment {parent_id}")
            
            # Verify root level
            if hierarchy.get("id") != parent_id:
                self.log(f"✗ Hierarchy root ID mismatch", "ERROR")
                success = False
            else:
                self.log(f"  - Root: {hierarchy.get('nom')} (ID: {hierarchy.get('id')})")
                
            # Verify children structure
            if "children" not in hierarchy:
                self.log(f"✗ Hierarchy missing children field", "ERROR")
                success = False
            else:
                children = hierarchy["children"]
                self.log(f"  - Direct children count: {len(children)}")
                
                # Check each child
                for child in children:
                    self.log(f"    - Child: {child.get('nom')} (ID: {child.get('id')})")
                    
                    # Check if child has its own children (grandchildren)
                    if "children" in child and len(child["children"]) > 0:
                        for grandchild in child["children"]:
                            self.log(f"      - Grandchild: {grandchild.get('nom')} (ID: {grandchild.get('id')})")
                            
                    # Verify hasChildren is correctly set
                    expected_has_children = "children" in child and len(child["children"]) > 0
                    actual_has_children = child.get("hasChildren", False)
                    if expected_has_children != actual_has_children:
                        self.log(f"✗ Child hasChildren mismatch: expected {expected_has_children}, got {actual_has_children}", "ERROR")
                        success = False
                        
        else:
            self.log(f"✗ Failed to get equipment hierarchy: {response.status_code} - {response.text}", "ERROR")
            success = False
            
        # Test with invalid equipment ID
        response = self.make_request("GET", "/equipments/invalid_id/hierarchy")
        if response.status_code == 404 or response.status_code == 400:
            self.log("✓ Correctly handled invalid equipment ID for hierarchy")
        else:
            self.log(f"✗ Should have returned 404/400 for invalid equipment ID: {response.status_code}", "ERROR")
            success = False
            
        return success
        
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all equipment hierarchy system tests"""
        self.log("Starting GMAO Atlas Equipment Hierarchy System Tests...")
        self.log(f"Backend URL: {self.base_url}")
        
        results = {}
        
        # Setup
        if not self.setup_admin_user():
            self.log("Failed to setup admin user. Aborting tests.", "ERROR")
            return {"setup": False}
            
        # Create test location
        location_id = self.setup_test_location()
        if not location_id:
            self.log("Failed to setup test location. Aborting tests.", "ERROR")
            return {"setup_location": False}
            
        # Run hierarchy tests in sequence
        self.log("\n" + "="*60)
        self.log("EQUIPMENT HIERARCHY TESTS")
        self.log("="*60)
        
        # Test 1: Create parent equipment
        parent_id = self.test_create_parent_equipment(location_id)
        results["create_parent_equipment"] = parent_id is not None
        
        if parent_id:
            # Test 2: Create sub-equipment with location inheritance
            child_id = self.test_create_sub_equipment_with_inheritance(parent_id)
            results["create_sub_equipment_inheritance"] = child_id is not None
            
            # Test 3: Create sub-equipment with explicit location
            child2_id = self.test_create_sub_equipment_with_explicit_location(parent_id, location_id)
            results["create_sub_equipment_explicit"] = child2_id is not None
            
            # Test 4: GET /api/equipments with hierarchy info
            results["get_equipments_hierarchy_info"] = self.test_get_equipments_with_hierarchy_info()
            
            # Test 5: GET /api/equipments/{id} with details
            results["get_equipment_detail"] = self.test_get_equipment_detail()
            
            # Test 6: GET /api/equipments/{id}/children
            results["get_equipment_children"] = self.test_get_equipment_children()
            
            # Test 7: GET /api/equipments/{id}/hierarchy (recursive)
            results["get_equipment_hierarchy"] = self.test_get_equipment_hierarchy()
        else:
            # Skip dependent tests if parent creation failed
            results["create_sub_equipment_inheritance"] = False
            results["create_sub_equipment_explicit"] = False
            results["get_equipments_hierarchy_info"] = False
            results["get_equipment_detail"] = False
            results["get_equipment_children"] = False
            results["get_equipment_hierarchy"] = False
        
        # Summary
        self.log("\n" + "="*60)
        self.log("TEST RESULTS SUMMARY")
        self.log("="*60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            self.log(f"{test_name}: {status}")
            if result:
                passed += 1
                
        self.log(f"\nOverall: {passed}/{total} tests passed")
        
        return results

class ImportExportTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
        self.viewer_token = None
        self.admin_user_id = None
        self.viewer_user_id = None
        self.session = requests.Session()
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages"""
        print(f"[{level}] {message}")
        
    def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None, token: str = None, files: Dict = None) -> requests.Response:
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}{endpoint}"
        
        request_headers = {}
        if not files:  # Only set Content-Type for non-file uploads
            request_headers["Content-Type"] = "application/json"
        if headers:
            request_headers.update(headers)
            
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        elif self.admin_token:
            request_headers["Authorization"] = f"Bearer {self.admin_token}"
            
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=request_headers)
            elif method.upper() == "POST":
                if files:
                    response = self.session.post(url, files=files, headers=request_headers)
                else:
                    response = self.session.post(url, json=data, headers=request_headers)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=request_headers)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=request_headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            self.log(f"{method} {endpoint} -> {response.status_code}")
            return response
        except Exception as e:
            self.log(f"Request failed: {e}", "ERROR")
            raise
            
    def setup_admin_user(self) -> bool:
        """Create or login as admin user"""
        self.log("Setting up admin user...")
        
        # Try to login first
        login_data = {
            "email": "admin@example.com",
            "password": "password123"
        }
        
        response = self.make_request("POST", "/auth/login", login_data, token=None)
        
        if response.status_code == 200:
            data = response.json()
            self.admin_token = data["access_token"]
            self.admin_user_id = data["user"]["id"]
            self.log(f"Admin login successful. User ID: {self.admin_user_id}")
            return True
        elif response.status_code == 401:
            # Admin doesn't exist, create it
            self.log("Admin user not found, creating...")
            register_data = {
                "nom": "Admin",
                "prenom": "System",
                "email": "admin@example.com",
                "telephone": "+33123456789",
                "password": "password123",
                "role": "ADMIN"
            }
            
            response = self.make_request("POST", "/auth/register", register_data, token=None)
            if response.status_code == 200:
                self.log("Admin user created successfully")
                # Now login
                return self.setup_admin_user()
            else:
                self.log(f"Failed to create admin user: {response.status_code} - {response.text}", "ERROR")
                return False
        else:
            self.log(f"Login failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def setup_viewer_user(self) -> bool:
        """Create or login as viewer user for access control tests"""
        self.log("Setting up viewer user...")
        
        # Try to login first
        login_data = {
            "email": "viewer@example.com",
            "password": "password123"
        }
        
        response = self.make_request("POST", "/auth/login", login_data, token=None)
        
        if response.status_code == 200:
            data = response.json()
            self.viewer_token = data["access_token"]
            self.viewer_user_id = data["user"]["id"]
            self.log(f"Viewer login successful. User ID: {self.viewer_user_id}")
            return True
        elif response.status_code == 401:
            # Viewer doesn't exist, create it
            self.log("Viewer user not found, creating...")
            register_data = {
                "nom": "Viewer",
                "prenom": "Test",
                "email": "viewer@example.com",
                "telephone": "+33987654321",
                "password": "password123",
                "role": "VISUALISEUR"
            }
            
            response = self.make_request("POST", "/auth/register", register_data, token=None)
            if response.status_code == 200:
                self.log("Viewer user created successfully")
                # Now login
                return self.setup_viewer_user()
            else:
                self.log(f"Failed to create viewer user: {response.status_code} - {response.text}", "ERROR")
                return False
        else:
            self.log(f"Viewer login failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def test_admin_authentication(self) -> bool:
        """Test 1: Authentication Admin"""
        self.log("\n=== Test 1: Authentication Admin ===")
        
        login_data = {
            "email": "admin@example.com",
            "password": "password123"
        }
        
        response = self.make_request("POST", "/auth/login", login_data, token=None)
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and "user" in data:
                self.admin_token = data["access_token"]
                user = data["user"]
                if user.get("role") == "ADMIN":
                    self.log("✓ Admin authentication successful")
                    self.log(f"  - Token received: {self.admin_token[:20]}...")
                    self.log(f"  - User role: {user.get('role')}")
                    return True
                else:
                    self.log(f"✗ User role is not ADMIN: {user.get('role')}", "ERROR")
                    return False
            else:
                self.log("✗ Missing access_token or user in response", "ERROR")
                return False
        else:
            self.log(f"✗ Admin login failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def test_export_csv_module_specific(self) -> bool:
        """Test 2: Export CSV - Module spécifique"""
        self.log("\n=== Test 2: Export CSV - Module spécifique (work-orders) ===")
        
        response = self.make_request("GET", "/export/work-orders?format=csv")
        
        if response.status_code == 200:
            # Check Content-Type
            content_type = response.headers.get("content-type", "")
            if "text/csv" in content_type:
                self.log("✓ Correct Content-Type: text/csv")
            else:
                self.log(f"✗ Incorrect Content-Type: {content_type}", "ERROR")
                return False
                
            # Check Content-Disposition header
            content_disposition = response.headers.get("content-disposition", "")
            if "attachment" in content_disposition and "filename" in content_disposition:
                self.log(f"✓ Content-Disposition header present: {content_disposition}")
            else:
                self.log(f"✗ Missing or incorrect Content-Disposition header: {content_disposition}", "ERROR")
                return False
                
            # Check if response has content
            if len(response.content) > 0:
                self.log(f"✓ CSV export successful, size: {len(response.content)} bytes")
                return True
            else:
                self.log("✗ Empty CSV response", "ERROR")
                return False
        else:
            self.log(f"✗ CSV export failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def test_export_xlsx_module_specific(self) -> bool:
        """Test 3: Export XLSX - Module spécifique"""
        self.log("\n=== Test 3: Export XLSX - Module spécifique (equipments) ===")
        
        response = self.make_request("GET", "/export/equipments?format=xlsx")
        
        if response.status_code == 200:
            # Check Content-Type
            content_type = response.headers.get("content-type", "")
            expected_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            if expected_type in content_type:
                self.log("✓ Correct Content-Type for XLSX")
            else:
                self.log(f"✗ Incorrect Content-Type: {content_type}", "ERROR")
                return False
                
            # Check Content-Disposition header
            content_disposition = response.headers.get("content-disposition", "")
            if "attachment" in content_disposition and "filename" in content_disposition:
                self.log(f"✓ Content-Disposition header present: {content_disposition}")
            else:
                self.log(f"✗ Missing or incorrect Content-Disposition header: {content_disposition}", "ERROR")
                return False
                
            # Check if response has content
            if len(response.content) > 0:
                self.log(f"✓ XLSX export successful, size: {len(response.content)} bytes")
                return True
            else:
                self.log("✗ Empty XLSX response", "ERROR")
                return False
        else:
            self.log(f"✗ XLSX export failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def test_export_xlsx_all_data(self) -> bool:
        """Test 4: Export XLSX - Toutes les données"""
        self.log("\n=== Test 4: Export XLSX - Toutes les données ===")
        
        response = self.make_request("GET", "/export/all?format=xlsx")
        
        if response.status_code == 200:
            # Check Content-Type
            content_type = response.headers.get("content-type", "")
            expected_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            if expected_type in content_type:
                self.log("✓ Correct Content-Type for XLSX")
            else:
                self.log(f"✗ Incorrect Content-Type: {content_type}", "ERROR")
                return False
                
            # Check if response has content (should contain multiple sheets)
            if len(response.content) > 0:
                self.log(f"✓ XLSX export all data successful, size: {len(response.content)} bytes")
                # Note: We could use openpyxl to verify multiple sheets, but for now just check size
                return True
            else:
                self.log("✗ Empty XLSX response", "ERROR")
                return False
        else:
            self.log(f"✗ XLSX export all data failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def test_export_csv_all_data_should_fail(self) -> bool:
        """Test 5: Export CSV - Toutes les données (devrait échouer)"""
        self.log("\n=== Test 5: Export CSV - Toutes les données (devrait échouer) ===")
        
        response = self.make_request("GET", "/export/all?format=csv")
        
        if response.status_code == 400:
            try:
                error_data = response.json()
                if "detail" in error_data:
                    self.log(f"✓ Correctly failed with 400: {error_data['detail']}")
                    return True
                else:
                    self.log("✓ Correctly failed with 400 (no detail message)")
                    return True
            except:
                self.log("✓ Correctly failed with 400 (non-JSON response)")
                return True
        else:
            self.log(f"✗ Should have failed with 400, got: {response.status_code}", "ERROR")
            return False
            
    def create_test_csv_file(self) -> str:
        """Create a test CSV file for import testing"""
        csv_content = """nom,adresse,ville,codePostal,type
Test Location Import 1,123 Import Street,Paris,75001,Atelier
Test Location Import 2,456 Import Avenue,Lyon,69001,Bureau
Test Location Import 3,789 Import Boulevard,Marseille,13001,Entrepot"""
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.write(csv_content)
        temp_file.close()
        
        return temp_file.name
        
    def test_import_mode_add(self) -> bool:
        """Test 6: Import - Mode Add"""
        self.log("\n=== Test 6: Import - Mode Add ===")
        
        # Create test CSV file
        csv_file_path = self.create_test_csv_file()
        
        try:
            with open(csv_file_path, 'rb') as f:
                files = {'file': ('test_locations.csv', f, 'text/csv')}
                response = self.make_request("POST", "/import/locations?mode=add", files=files)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_fields = ["total", "inserted", "updated", "skipped", "errors"]
                for field in required_fields:
                    if field not in data:
                        self.log(f"✗ Missing field in response: {field}", "ERROR")
                        return False
                        
                self.log(f"✓ Import successful with correct response structure")
                self.log(f"  - Total: {data['total']}")
                self.log(f"  - Inserted: {data['inserted']}")
                self.log(f"  - Updated: {data['updated']}")
                self.log(f"  - Skipped: {data['skipped']}")
                self.log(f"  - Errors: {len(data['errors'])}")
                
                # Check that some items were inserted
                if data['inserted'] > 0:
                    self.log(f"✓ Successfully inserted {data['inserted']} items")
                    return True
                else:
                    self.log("✗ No items were inserted", "ERROR")
                    return False
            else:
                self.log(f"✗ Import failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        finally:
            # Clean up temporary file
            if os.path.exists(csv_file_path):
                os.unlink(csv_file_path)
                
    def test_import_mode_replace(self) -> bool:
        """Test 7: Import - Mode Replace"""
        self.log("\n=== Test 7: Import - Mode Replace ===")
        
        # First, create a location that we can later replace
        location_data = {
            "nom": "Location to Replace",
            "adresse": "Original Address",
            "ville": "Original City",
            "codePostal": "00000",
            "type": "Original Type"
        }
        
        response = self.make_request("POST", "/locations", location_data)
        if response.status_code != 200:
            self.log("✗ Could not create location for replace test", "ERROR")
            return False
            
        created_location = response.json()
        location_id = created_location["id"]
        self.log(f"Created location for replace test: {location_id}")
        
        # Create CSV with existing ID for replacement
        csv_content = f"""id,nom,adresse,ville,codePostal,type
{location_id},Updated Location Name,Updated Address,Updated City,99999,Updated Type"""
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.write(csv_content)
        temp_file.close()
        
        try:
            with open(temp_file.name, 'rb') as f:
                files = {'file': ('test_locations_replace.csv', f, 'text/csv')}
                response = self.make_request("POST", "/import/locations?mode=replace", files=files)
            
            if response.status_code == 200:
                data = response.json()
                
                self.log(f"✓ Replace import successful")
                self.log(f"  - Total: {data['total']}")
                self.log(f"  - Updated: {data['updated']}")
                self.log(f"  - Inserted: {data['inserted']}")
                
                # Check that items were updated
                if data['updated'] > 0:
                    self.log(f"✓ Successfully updated {data['updated']} items")
                    return True
                else:
                    # Could be inserted if ID didn't exist
                    if data['inserted'] > 0:
                        self.log(f"✓ Successfully inserted {data['inserted']} items (ID not found)")
                        return True
                    else:
                        self.log("✗ No items were updated or inserted", "ERROR")
                        return False
            else:
                self.log(f"✗ Replace import failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
                
    def test_import_invalid_module(self) -> bool:
        """Test 8: Import - Module invalide"""
        self.log("\n=== Test 8: Import - Module invalide ===")
        
        csv_file_path = self.create_test_csv_file()
        
        try:
            with open(csv_file_path, 'rb') as f:
                files = {'file': ('test.csv', f, 'text/csv')}
                response = self.make_request("POST", "/import/invalid-module", files=files)
            
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        self.log(f"✓ Correctly rejected invalid module: {error_data['detail']}")
                        return True
                except:
                    pass
                self.log("✓ Correctly rejected invalid module with 400")
                return True
            else:
                self.log(f"✗ Should have failed with 400, got: {response.status_code}", "ERROR")
                return False
                
        finally:
            if os.path.exists(csv_file_path):
                os.unlink(csv_file_path)
                
    def test_import_invalid_format(self) -> bool:
        """Test 9: Import - Format invalide"""
        self.log("\n=== Test 9: Import - Format invalide ===")
        
        # Create a .txt file instead of CSV
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_file.write("This is not a CSV file")
        temp_file.close()
        
        try:
            with open(temp_file.name, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                response = self.make_request("POST", "/import/locations", files=files)
            
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        self.log(f"✓ Correctly rejected invalid format: {error_data['detail']}")
                        return True
                except:
                    pass
                self.log("✓ Correctly rejected invalid format with 400")
                return True
            else:
                self.log(f"✗ Should have failed with 400, got: {response.status_code}", "ERROR")
                return False
                
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
                
    def test_access_control_non_admin_export(self) -> bool:
        """Test 10a: Access Control - Non-Admin Export"""
        self.log("\n=== Test 10a: Access Control - Non-Admin Export ===")
        
        if not self.setup_viewer_user():
            self.log("✗ Could not setup viewer user", "ERROR")
            return False
            
        # Try to export with viewer token
        response = self.make_request("GET", "/export/work-orders", token=self.viewer_token)
        
        if response.status_code in [401, 403]:
            self.log(f"✓ Correctly denied non-admin export access: {response.status_code}")
            return True
        else:
            self.log(f"✗ Should have denied access, got: {response.status_code}", "ERROR")
            return False
            
    def test_access_control_non_admin_import(self) -> bool:
        """Test 10b: Access Control - Non-Admin Import"""
        self.log("\n=== Test 10b: Access Control - Non-Admin Import ===")
        
        csv_file_path = self.create_test_csv_file()
        
        try:
            with open(csv_file_path, 'rb') as f:
                files = {'file': ('test.csv', f, 'text/csv')}
                response = self.make_request("POST", "/import/locations", files=files, token=self.viewer_token)
            
            if response.status_code in [401, 403]:
                self.log(f"✓ Correctly denied non-admin import access: {response.status_code}")
                return True
            else:
                self.log(f"✗ Should have denied access, got: {response.status_code}", "ERROR")
                return False
                
        finally:
            if os.path.exists(csv_file_path):
                os.unlink(csv_file_path)
                
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all Import/Export tests"""
        self.log("Starting GMAO Atlas Import/Export Tests...")
        self.log(f"Backend URL: {self.base_url}")
        
        results = {}
        
        # Setup admin user
        if not self.setup_admin_user():
            self.log("Failed to setup admin user. Aborting tests.", "ERROR")
            return {"setup": False}
            
        # Run Import/Export tests
        self.log("\n" + "="*60)
        self.log("IMPORT/EXPORT FUNCTIONALITY TESTS")
        self.log("="*60)
        
        # Test 1: Admin Authentication
        results["admin_authentication"] = self.test_admin_authentication()
        
        # Test 2: Export CSV - Module specific
        results["export_csv_module"] = self.test_export_csv_module_specific()
        
        # Test 3: Export XLSX - Module specific
        results["export_xlsx_module"] = self.test_export_xlsx_module_specific()
        
        # Test 4: Export XLSX - All data
        results["export_xlsx_all"] = self.test_export_xlsx_all_data()
        
        # Test 5: Export CSV - All data (should fail)
        results["export_csv_all_fail"] = self.test_export_csv_all_data_should_fail()
        
        # Test 6: Import - Mode Add
        results["import_mode_add"] = self.test_import_mode_add()
        
        # Test 7: Import - Mode Replace
        results["import_mode_replace"] = self.test_import_mode_replace()
        
        # Test 8: Import - Invalid module
        results["import_invalid_module"] = self.test_import_invalid_module()
        
        # Test 9: Import - Invalid format
        results["import_invalid_format"] = self.test_import_invalid_format()
        
        # Test 10: Access Control
        results["access_control_export"] = self.test_access_control_non_admin_export()
        results["access_control_import"] = self.test_access_control_non_admin_import()
        
        # Summary
        self.log("\n" + "="*60)
        self.log("IMPORT/EXPORT TEST RESULTS SUMMARY")
        self.log("="*60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            self.log(f"{test_name}: {status}")
            if result:
                passed += 1
                
        self.log(f"\nImport/Export Tests: {passed}/{total} tests passed")
        
        return results

class Phase1Tester:
    """Tests for Phase 1 - SMTP, User Profile, Password Change"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
        self.admin_user_id = None
        self.session = requests.Session()
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages"""
        print(f"[{level}] {message}")
        
    def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None, token: str = None) -> requests.Response:
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}{endpoint}"
        
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
            
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        elif self.admin_token:
            request_headers["Authorization"] = f"Bearer {self.admin_token}"
            
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=request_headers)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=request_headers)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=request_headers)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=request_headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            self.log(f"{method} {endpoint} -> {response.status_code}")
            return response
        except Exception as e:
            self.log(f"Request failed: {e}", "ERROR")
            raise
            
    def setup_admin_user(self) -> bool:
        """Login as admin user"""
        self.log("Setting up admin user...")
        
        login_data = {
            "email": "admin@example.com",
            "password": "password123"
        }
        
        response = self.make_request("POST", "/auth/login", login_data, token=None)
        
        if response.status_code == 200:
            data = response.json()
            self.admin_token = data["access_token"]
            self.admin_user_id = data["user"]["id"]
            self.log(f"Admin login successful. User ID: {self.admin_user_id}")
            return True
        elif response.status_code == 401:
            # Admin doesn't exist, create it
            self.log("Admin user not found, creating...")
            register_data = {
                "nom": "Admin",
                "prenom": "System",
                "email": "admin@example.com",
                "telephone": "+33123456789",
                "password": "password123",
                "role": "ADMIN"
            }
            
            response = self.make_request("POST", "/auth/register", register_data, token=None)
            if response.status_code == 200:
                self.log("Admin user created successfully")
                # Now login
                return self.setup_admin_user()
            else:
                self.log(f"Failed to create admin user: {response.status_code} - {response.text}", "ERROR")
                return False
        else:
            self.log(f"Login failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def test_smtp_configuration_user_invite(self) -> bool:
        """Test 1: SMTP Configuration - User Invitation Email"""
        self.log("\n=== Test 1: SMTP Configuration - User Invitation Email ===")
        
        # Test data for invitation
        invite_data = {
            "email": "test.invite@example.com",
            "role": "TECHNICIEN"
        }
        
        response = self.make_request("POST", "/users/invite-member", invite_data)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check response structure
            required_fields = ["message", "email", "role"]
            for field in required_fields:
                if field not in data:
                    self.log(f"✗ Missing field in response: {field}", "ERROR")
                    return False
                    
            # Verify email and role match
            if data["email"] != invite_data["email"]:
                self.log(f"✗ Email mismatch: expected {invite_data['email']}, got {data['email']}", "ERROR")
                return False
                
            if data["role"] != invite_data["role"]:
                self.log(f"✗ Role mismatch: expected {invite_data['role']}, got {data['role']}", "ERROR")
                return False
                
            self.log("✓ User invitation email sent successfully via SMTP")
            self.log(f"  - Email: {data['email']}")
            self.log(f"  - Role: {data['role']}")
            self.log(f"  - Message: {data['message']}")
            return True
        else:
            self.log(f"✗ User invitation failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def test_get_user_profile(self) -> bool:
        """Test 2: GET /api/auth/me - Get User Profile"""
        self.log("\n=== Test 2: GET /api/auth/me - Get User Profile ===")
        
        response = self.make_request("GET", "/auth/me")
        
        if response.status_code == 200:
            user_data = response.json()
            
            # Check required fields
            required_fields = ["id", "nom", "prenom", "email", "role", "dateCreation"]
            for field in required_fields:
                if field not in user_data:
                    self.log(f"✗ Missing field in user profile: {field}", "ERROR")
                    return False
                    
            # Verify it's the admin user
            if user_data["email"] != "admin@example.com":
                self.log(f"✗ Wrong user profile returned: {user_data['email']}", "ERROR")
                return False
                
            if user_data["role"] != "ADMIN":
                self.log(f"✗ Wrong user role: {user_data['role']}", "ERROR")
                return False
                
            self.log("✓ User profile retrieved successfully")
            self.log(f"  - ID: {user_data['id']}")
            self.log(f"  - Name: {user_data['prenom']} {user_data['nom']}")
            self.log(f"  - Email: {user_data['email']}")
            self.log(f"  - Role: {user_data['role']}")
            self.log(f"  - Service: {user_data.get('service', 'N/A')}")
            self.log(f"  - Phone: {user_data.get('telephone', 'N/A')}")
            return True
        else:
            self.log(f"✗ Failed to get user profile: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def test_update_user_profile(self) -> bool:
        """Test 3: PUT /api/auth/me - Update User Profile"""
        self.log("\n=== Test 3: PUT /api/auth/me - Update User Profile ===")
        
        # Test data for profile update
        update_data = {
            "nom": "Admin Updated",
            "prenom": "System Updated",
            "telephone": "+33987654321",
            "service": "IT Department"
        }
        
        response = self.make_request("PUT", "/auth/me", update_data)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check response structure
            if "message" not in data or "user" not in data:
                self.log("✗ Invalid response structure", "ERROR")
                return False
                
            user_data = data["user"]
            
            # Verify updates were applied
            if user_data["nom"] != update_data["nom"]:
                self.log(f"✗ Name not updated: expected {update_data['nom']}, got {user_data['nom']}", "ERROR")
                return False
                
            if user_data["prenom"] != update_data["prenom"]:
                self.log(f"✗ First name not updated: expected {update_data['prenom']}, got {user_data['prenom']}", "ERROR")
                return False
                
            if user_data["telephone"] != update_data["telephone"]:
                self.log(f"✗ Phone not updated: expected {update_data['telephone']}, got {user_data['telephone']}", "ERROR")
                return False
                
            if user_data["service"] != update_data["service"]:
                self.log(f"✗ Service not updated: expected {update_data['service']}, got {user_data['service']}", "ERROR")
                return False
                
            self.log("✓ User profile updated successfully")
            self.log(f"  - Name: {user_data['prenom']} {user_data['nom']}")
            self.log(f"  - Phone: {user_data['telephone']}")
            self.log(f"  - Service: {user_data['service']}")
            return True
        else:
            self.log(f"✗ Failed to update user profile: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def test_change_password_correct_old_password(self) -> bool:
        """Test 4a: POST /api/auth/change-password - Correct Old Password"""
        self.log("\n=== Test 4a: POST /api/auth/change-password - Correct Old Password ===")
        
        # Change password with correct old password
        change_data = {
            "old_password": "password123",
            "new_password": "newpassword456"
        }
        
        response = self.make_request("POST", "/auth/change-password", change_data)
        
        if response.status_code == 200:
            data = response.json()
            
            if "message" not in data:
                self.log("✗ Missing message in response", "ERROR")
                return False
                
            self.log("✓ Password changed successfully with correct old password")
            self.log(f"  - Message: {data['message']}")
            
            # Update our stored password for future tests
            # Try to login with new password to verify
            login_data = {
                "email": "admin@example.com",
                "password": "newpassword456"
            }
            
            login_response = self.make_request("POST", "/auth/login", login_data, token=None)
            if login_response.status_code == 200:
                self.log("✓ Login successful with new password - password change verified")
                # Update token for future requests
                login_result = login_response.json()
                self.admin_token = login_result["access_token"]
                return True
            else:
                self.log("✗ Could not login with new password - password change may have failed", "ERROR")
                return False
        else:
            self.log(f"✗ Failed to change password: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def test_change_password_incorrect_old_password(self) -> bool:
        """Test 4b: POST /api/auth/change-password - Incorrect Old Password"""
        self.log("\n=== Test 4b: POST /api/auth/change-password - Incorrect Old Password ===")
        
        # Try to change password with incorrect old password
        change_data = {
            "old_password": "wrongpassword",
            "new_password": "anothernewpassword"
        }
        
        response = self.make_request("POST", "/auth/change-password", change_data)
        
        if response.status_code == 400:
            try:
                data = response.json()
                if "detail" in data and "incorrect" in data["detail"].lower():
                    self.log("✓ Correctly rejected incorrect old password")
                    self.log(f"  - Error message: {data['detail']}")
                    return True
                else:
                    self.log(f"✗ Unexpected error message: {data.get('detail', 'No detail')}", "ERROR")
                    return False
            except:
                self.log("✓ Correctly rejected incorrect old password (non-JSON response)")
                return True
        else:
            self.log(f"✗ Should have failed with 400, got: {response.status_code}", "ERROR")
            return False
            
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all Phase 1 tests"""
        self.log("Starting GMAO Atlas Phase 1 Tests...")
        self.log(f"Backend URL: {self.base_url}")
        
        results = {}
        
        # Setup
        if not self.setup_admin_user():
            self.log("Failed to setup admin user. Aborting tests.", "ERROR")
            return {"setup": False}
            
        # Run Phase 1 tests
        self.log("\n" + "="*60)
        self.log("PHASE 1 TESTS - SMTP, USER PROFILE, PASSWORD CHANGE")
        self.log("="*60)
        
        # Test 1: SMTP Configuration - User Invitation
        results["smtp_user_invitation"] = self.test_smtp_configuration_user_invite()
        
        # Test 2: GET User Profile
        results["get_user_profile"] = self.test_get_user_profile()
        
        # Test 3: PUT User Profile
        results["update_user_profile"] = self.test_update_user_profile()
        
        # Test 4a: Change Password - Correct Old Password
        results["change_password_correct"] = self.test_change_password_correct_old_password()
        
        # Test 4b: Change Password - Incorrect Old Password
        results["change_password_incorrect"] = self.test_change_password_incorrect_old_password()
        
        # Summary
        self.log("\n" + "="*60)
        self.log("PHASE 1 TEST RESULTS SUMMARY")
        self.log("="*60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            self.log(f"{test_name}: {status}")
            if result:
                passed += 1
                
        self.log(f"\nPhase 1 Tests: {passed}/{total} tests passed")
        
        return results

def main():
    """Main test execution"""
    # Run Phase 1 Tests (Priority)
    print("="*80)
    print("RUNNING PHASE 1 TESTS - SMTP, USER PROFILE, PASSWORD CHANGE")
    print("="*80)
    
    phase1_tester = Phase1Tester()
    phase1_results = phase1_tester.run_all_tests()
    
    # Run Equipment Hierarchy Tests
    print("\n" + "="*80)
    print("RUNNING EQUIPMENT HIERARCHY TESTS")
    print("="*80)
    
    hierarchy_tester = EquipmentHierarchyTester()
    hierarchy_results = hierarchy_tester.run_all_tests()
    
    # Run Import/Export Tests
    print("\n" + "="*80)
    print("RUNNING IMPORT/EXPORT TESTS")
    print("="*80)
    
    import_export_tester = ImportExportTester()
    import_export_results = import_export_tester.run_all_tests()
    
    # Combined results
    all_results = {**phase1_results, **hierarchy_results, **import_export_results}
    
    print("\n" + "="*80)
    print("OVERALL TEST SUMMARY")
    print("="*80)
    
    total_passed = sum(1 for result in all_results.values() if result)
    total_tests = len(all_results)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_tests - total_passed}")
    
    # Show Phase 1 results specifically
    phase1_passed = sum(1 for result in phase1_results.values() if result)
    phase1_total = len(phase1_results)
    print(f"\nPhase 1 Critical Tests: {phase1_passed}/{phase1_total} passed")
    
    # Exit with error code if any tests failed
    if not all(all_results.values()):
        print("\n❌ Some tests failed!")
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()