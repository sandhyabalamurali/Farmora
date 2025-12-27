#!/usr/bin/env python3
"""
Farmora Backend API Testing Suite
Tests all endpoints with real API integrations
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class FarmoraAPITester:
    def __init__(self, base_url="https://greenfarmer-fix.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test_name": name,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        })

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Optional[Dict] = None, headers: Optional[Dict] = None) -> tuple:
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            
            try:
                response_json = response.json()
            except:
                response_json = {"raw_response": response.text}

            if success:
                self.log_test(name, True, f"Status: {response.status_code}", response_json)
                return True, response_json
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}. Response: {response.text[:200]}", response_json)
                return False, response_json

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        return self.run_test("Health Check", "GET", "health", 200)

    def test_signup(self):
        """Test user signup with GPS location"""
        timestamp = int(time.time())
        signup_data = {
            "email": f"farmer{timestamp}@gmail.com",
            "name": f"Test Farmer {timestamp}",
            "password": "TestPass123!",
            "farm_location": "Maharashtra, India",
            "crops": ["Paddy", "Wheat", "Cotton"],
            "latitude": 19.0760,  # Mumbai coordinates
            "longitude": 72.8777,
            "language": "en"
        }
        
        success, response = self.run_test("User Signup", "POST", "auth/signup", 200, signup_data)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response.get('user_id')
            print(f"   ✅ Token acquired: {self.token[:20]}...")
            print(f"   ✅ User ID: {self.user_id}")
            return True
        return False

    def test_login(self):
        """Test user login - using existing user or create new one"""
        # Try with a known test account first
        login_data = {
            "email": "test@farmora.com",
            "password": "TestPass123!"
        }
        
        success, response = self.run_test("User Login (existing)", "POST", "auth/login", 200, login_data)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response.get('user_id')
            print(f"   ✅ Login successful with existing account")
            return True
        else:
            print("   ℹ️ Existing account not found, will use signup token")
            return self.token is not None

    def test_get_profile(self):
        """Test get user profile"""
        if not self.token:
            self.log_test("Get Profile", False, "No authentication token available")
            return False
            
        return self.run_test("Get User Profile", "GET", "auth/profile", 200)

    def test_update_profile(self):
        """Test profile update with language change"""
        if not self.token:
            self.log_test("Update Profile", False, "No authentication token available")
            return False
            
        update_data = {
            "language": "hi",
            "farm_location": "Updated Farm Location, Maharashtra"
        }
        
        return self.run_test("Update Profile", "PUT", "auth/profile", 200, update_data)

    def test_chat_endpoint(self):
        """Test chat endpoint with agricultural query"""
        if not self.user_id:
            self.log_test("Chat Endpoint", False, "No user ID available")
            return False
            
        chat_data = {
            "user_id": self.user_id,
            "text_message": "What is the best time to plant wheat in Maharashtra?",
            "crop_image": None,
            "caption": None
        }
        
        print("   ⏳ Chat may take 10-15 seconds due to AI processing...")
        success, response = self.run_test("Chat Endpoint", "POST", "chat", 200, chat_data)
        
        if success:
            print(f"   📝 AI Response: {response.get('ai_response', '')[:100]}...")
            print(f"   🎯 Intent: {response.get('intent', 'unknown')}")
            print(f"   📊 Confidence: {response.get('confidence_score', 0)}")
        
        return success, response

    def test_market_data(self):
        """Test market data endpoint"""
        if not self.user_id:
            self.log_test("Market Data", False, "No user ID available")
            return False
            
        return self.run_test("Market Data", "GET", f"market/{self.user_id}", 200)

    def test_timeline(self):
        """Test timeline endpoint"""
        if not self.user_id:
            self.log_test("Timeline", False, "No user ID available")
            return False
            
        return self.run_test("Timeline", "GET", f"timeline/{self.user_id}", 200)

    def test_task_confirmation(self):
        """Test task confirmation endpoint"""
        if not self.user_id:
            self.log_test("Task Confirmation", False, "No user ID available")
            return False
            
        # First, try to get a task suggestion from chat
        chat_data = {
            "user_id": self.user_id,
            "text_message": "Create a farming schedule for next week",
            "crop_image": None,
            "caption": None
        }
        
        print("   ⏳ Getting task suggestions from chat...")
        chat_success, chat_response = self.run_test("Chat for Tasks", "POST", "chat", 200, chat_data)
        
        if chat_success and chat_response.get('planner_suggestions'):
            tasks = chat_response['planner_suggestions']
            if tasks and len(tasks) > 0:
                task = tasks[0]
                task_id = task.get('task_id') or f"task_{int(time.time())}"
                
                confirm_data = {
                    "task_id": task_id,
                    "user_id": self.user_id,
                    "confirmation": True
                }
                
                return self.run_test("Task Confirmation", "POST", "tasks/confirm", 200, confirm_data)
            else:
                self.log_test("Task Confirmation", False, "No tasks generated from chat")
                return False
        else:
            # Try with a dummy task ID
            confirm_data = {
                "task_id": f"dummy_task_{int(time.time())}",
                "user_id": self.user_id,
                "confirmation": True
            }
            
            return self.run_test("Task Confirmation (dummy)", "POST", "tasks/confirm", 200, confirm_data)

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Farmora Backend API Tests")
        print(f"📍 Base URL: {self.base_url}")
        print("=" * 60)
        
        # Test 1: Health Check
        self.test_health_check()
        
        # Test 2: User Signup
        signup_success = self.test_signup()
        
        # Test 3: User Login (fallback if signup fails)
        if not signup_success:
            self.test_login()
        
        # Test 4: Get Profile
        self.test_get_profile()
        
        # Test 5: Update Profile
        self.test_update_profile()
        
        # Test 6: Chat Endpoint
        self.test_chat_endpoint()
        
        # Test 7: Market Data
        self.test_market_data()
        
        # Test 8: Timeline
        self.test_timeline()
        
        # Test 9: Task Confirmation
        self.test_task_confirmation()
        
        # Print Results
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"✅ Tests Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}/{self.tests_run}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Print failed tests
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['test_name']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = FarmoraAPITester()
    
    try:
        success = tester.run_all_tests()
        
        # Save detailed results
        with open('/app/test_reports/backend_test_results.json', 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": tester.tests_run,
                    "passed_tests": tester.tests_passed,
                    "failed_tests": tester.tests_run - tester.tests_passed,
                    "success_rate": (tester.tests_passed/tester.tests_run)*100 if tester.tests_run > 0 else 0,
                    "timestamp": datetime.now().isoformat()
                },
                "detailed_results": tester.test_results
            }, indent=2)
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())