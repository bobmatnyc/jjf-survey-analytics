#!/usr/bin/env python3
"""
Quick test script to verify templates are working correctly.
"""

import requests
import sys

def test_endpoints():
    """Test all main endpoints to ensure they're working."""
    base_url = "http://localhost:5001"
    
    endpoints = [
        ("/", "Dashboard"),
        ("/spreadsheets", "Spreadsheets"),
        ("/jobs", "Jobs"),
        ("/api/stats", "API Stats")
    ]
    
    print("🧪 Testing Flask Application Endpoints")
    print("=" * 50)
    
    all_passed = True
    
    for endpoint, name in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"Testing {name:15} ({endpoint:20})", end=" ... ")
            
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print("✅ PASS")
            else:
                print(f"❌ FAIL (Status: {response.status_code})")
                all_passed = False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ ERROR: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Web application is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the Flask application logs.")
        return 1

if __name__ == "__main__":
    exit(test_endpoints())
