#!/usr/bin/env python3
"""
Backend API Testing Script for GMAO Application
Tests the permissions system functionality
"""

import requests
import json
import os
from datetime import datetime, timedelta

# Use the correct backend URL from frontend .env
BACKEND_URL = "https://gmao-improve.preview.emergentagent.com/api"

# Test credentials - try both admin accounts
ADMIN_EMAIL_1 = "admin@example.com"
ADMIN_PASSWORD_1 = "password123"
ADMIN_EMAIL_2 = "admin@gmao-iris.local"
ADMIN_PASSWORD_2 = "Admin123!"

# Test viewer credentials (to be created)
VIEWER_EMAIL = "test_viewer@test.com"
VIEWER_PASSWORD = "Test123!"

class PermissionsTester:
    def __init__(self):
        self.admin_session = requests.Session()
        self.viewer_session = requests.Session()
        self.admin_token = None
        self.viewer_token = None
        self.admin_data = None
        self.viewer_data = None
        self.created_work_order_id = None
        
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
    
    def test_viewer_login(self):
        """Test viewer login"""
        self.log("Testing viewer login...")
        
        try:
            response = self.viewer_session.post(
                f"{BACKEND_URL}/auth/login",
                json={
                    "email": VIEWER_EMAIL,
                    "password": VIEWER_PASSWORD
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.viewer_token = data.get("access_token")
                self.viewer_data = data.get("user")
                
                # Set authorization header for future requests
                self.viewer_session.headers.update({
                    "Authorization": f"Bearer {self.viewer_token}"
                })
                
                self.log(f"✅ Viewer login successful - User: {self.viewer_data.get('prenom')} {self.viewer_data.get('nom')} (Role: {self.viewer_data.get('role')})")
                return True
            else:
                self.log(f"❌ Viewer login failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Viewer login request failed - Error: {str(e)}", "ERROR")
            return False
    
    def create_viewer_user(self):
        """Create a viewer user with limited permissions"""
        self.log("Creating viewer user with VISUALISEUR role...")
        
        user_data = {
            "nom": "Viewer",
            "prenom": "Test",
            "email": VIEWER_EMAIL,
            "password": VIEWER_PASSWORD,
            "role": "VISUALISEUR",
            "service": "Test"
        }
        
        try:
            response = self.admin_session.post(
                f"{BACKEND_URL}/users/create-member",
                json=user_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                user = response.json()
                self.log(f"✅ Viewer user created successfully - ID: {user.get('id')}, Role: {user.get('role')}")
                return user
            else:
                self.log(f"❌ Failed to create viewer user - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Create viewer user request failed - Error: {str(e)}", "ERROR")
            return None
    
    # ==================== WORK ORDERS PERMISSIONS TESTS ====================
    
    def test_admin_get_work_orders(self):
        """Test admin can GET /api/work-orders"""
        self.log("Testing admin GET /api/work-orders...")
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/work-orders",
                timeout=10
            )
            
            if response.status_code == 200:
                work_orders = response.json()
                self.log(f"✅ Admin GET work-orders successful - Found {len(work_orders)} work orders")
                return True
            else:
                self.log(f"❌ Admin GET work-orders failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Admin GET work-orders request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_admin_post_work_orders(self):
        """Test admin can POST /api/work-orders"""
        self.log("Testing admin POST /api/work-orders...")
        
        work_order_data = {
            "titre": "Test Work Order - Admin Permission Test",
            "description": "Test work order created by admin to test permissions",
            "priorite": "MOYENNE",
            "statut": "OUVERT",
            "type": "CORRECTIVE",
            "dateLimite": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        try:
            response = self.admin_session.post(
                f"{BACKEND_URL}/work-orders",
                json=work_order_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                work_order = response.json()
                self.created_work_order_id = work_order.get('id')
                self.log(f"✅ Admin POST work-orders successful - Created work order ID: {self.created_work_order_id}")
                return True
            else:
                self.log(f"❌ Admin POST work-orders failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Admin POST work-orders request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_admin_delete_work_orders(self):
        """Test admin can DELETE /api/work-orders/{id}"""
        if not self.created_work_order_id:
            self.log("❌ No work order ID available for delete test", "ERROR")
            return False
            
        self.log(f"Testing admin DELETE /api/work-orders/{self.created_work_order_id}...")
        
        try:
            response = self.admin_session.delete(
                f"{BACKEND_URL}/work-orders/{self.created_work_order_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Admin DELETE work-orders successful - {result.get('message')}")
                return True
            else:
                self.log(f"❌ Admin DELETE work-orders failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Admin DELETE work-orders request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_viewer_get_work_orders(self):
        """Test viewer can GET /api/work-orders (should work - has view permission)"""
        self.log("Testing viewer GET /api/work-orders...")
        
        try:
            response = self.viewer_session.get(
                f"{BACKEND_URL}/work-orders",
                timeout=10
            )
            
            if response.status_code == 200:
                work_orders = response.json()
                self.log(f"✅ Viewer GET work-orders successful - Found {len(work_orders)} work orders")
                return True
            else:
                self.log(f"❌ Viewer GET work-orders failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Viewer GET work-orders request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_viewer_post_work_orders_forbidden(self):
        """Test viewer CANNOT POST /api/work-orders (should return 403)"""
        self.log("Testing viewer POST /api/work-orders (should be forbidden)...")
        
        work_order_data = {
            "titre": "Test Work Order - Viewer Permission Test",
            "description": "This should fail - viewer has no edit permission",
            "priorite": "MOYENNE",
            "statut": "OUVERT",
            "type": "CORRECTIVE",
            "dateLimite": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        try:
            response = self.viewer_session.post(
                f"{BACKEND_URL}/work-orders",
                json=work_order_data,
                timeout=10
            )
            
            if response.status_code == 403:
                self.log("✅ Viewer POST work-orders correctly forbidden (403)")
                return True
            else:
                self.log(f"❌ Viewer POST work-orders should be forbidden but got - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Viewer POST work-orders request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_viewer_delete_work_orders_forbidden(self):
        """Test viewer CANNOT DELETE /api/work-orders/{id} (should return 403)"""
        # First create a work order as admin to try to delete as viewer
        work_order_data = {
            "titre": "Test Work Order for Delete Test",
            "description": "Work order to test viewer delete permissions",
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
            
            self.log(f"Testing viewer DELETE /api/work-orders/{work_order_id} (should be forbidden)...")
            
            # Try to delete as viewer
            response = self.viewer_session.delete(
                f"{BACKEND_URL}/work-orders/{work_order_id}",
                timeout=10
            )
            
            if response.status_code == 403:
                self.log("✅ Viewer DELETE work-orders correctly forbidden (403)")
                # Clean up - delete as admin
                self.admin_session.delete(f"{BACKEND_URL}/work-orders/{work_order_id}")
                return True
            else:
                self.log(f"❌ Viewer DELETE work-orders should be forbidden but got - Status: {response.status_code}, Response: {response.text}", "ERROR")
                # Clean up - delete as admin
                self.admin_session.delete(f"{BACKEND_URL}/work-orders/{work_order_id}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Viewer DELETE work-orders request failed - Error: {str(e)}", "ERROR")
            return False
    
    # ==================== INTERVENTION REQUESTS PERMISSIONS TESTS ====================
    
    def test_viewer_get_intervention_requests(self):
        """Test viewer can GET /api/intervention-requests (should work according to permissions)"""
        self.log("Testing viewer GET /api/intervention-requests...")
        
        try:
            response = self.viewer_session.get(
                f"{BACKEND_URL}/intervention-requests",
                timeout=10
            )
            
            if response.status_code == 200:
                requests_list = response.json()
                self.log(f"✅ Viewer GET intervention-requests successful - Found {len(requests_list)} requests")
                return True
            else:
                self.log(f"❌ Viewer GET intervention-requests failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Viewer GET intervention-requests request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_viewer_post_intervention_requests_forbidden(self):
        """Test viewer CANNOT POST /api/intervention-requests (should return 403)"""
        self.log("Testing viewer POST /api/intervention-requests (should be forbidden)...")
        
        request_data = {
            "titre": "Test Intervention Request - Viewer Permission Test",
            "description": "This should fail - viewer has no edit permission on intervention requests",
            "priorite": "MOYENNE",
            "type_intervention": "MAINTENANCE_CORRECTIVE"
        }
        
        try:
            response = self.viewer_session.post(
                f"{BACKEND_URL}/intervention-requests",
                json=request_data,
                timeout=10
            )
            
            if response.status_code == 403:
                self.log("✅ Viewer POST intervention-requests correctly forbidden (403)")
                return True
            else:
                self.log(f"❌ Viewer POST intervention-requests should be forbidden but got - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Viewer POST intervention-requests request failed - Error: {str(e)}", "ERROR")
            return False

    # ==================== IMPROVEMENT REQUESTS TESTS ====================
    
    def test_create_improvement_request(self):
        """Test POST /api/improvement-requests - Create a new improvement request"""
        self.log("Testing create improvement request endpoint...")
        
        request_data = {
            "titre": "Amélioration système éclairage",
            "description": "Demande d'amélioration pour moderniser le système d'éclairage du bâtiment principal",
            "priorite": "MOYENNE",
            "type_demande": "AMELIORATION_INFRASTRUCTURE",
            "demandeur": "Jean Dupont",
            "service_demandeur": "Maintenance",
            "justification": "Réduction de la consommation énergétique et amélioration de l'éclairage"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/improvement-requests",
                json=request_data,
                timeout=10
            )
            
            if response.status_code == 201:
                request = response.json()
                self.log(f"✅ Create improvement request successful - ID: {request.get('id')}, Title: {request.get('titre')}")
                return request
            else:
                self.log(f"❌ Create improvement request failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Create improvement request failed - Error: {str(e)}", "ERROR")
            return None
    
    def test_get_improvement_requests(self):
        """Test GET /api/improvement-requests - Get all improvement requests"""
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
        
        # Test 2: Create viewer user
        viewer_user = self.create_viewer_user()
        results["create_viewer_user"] = viewer_user is not None
        
        if not viewer_user:
            self.log("❌ Cannot proceed with viewer tests - User creation failed", "ERROR")
        else:
            # Test 3: Viewer Login
            results["viewer_login"] = self.test_viewer_login()
            
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