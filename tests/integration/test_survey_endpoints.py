#!/usr/bin/env python3
"""
Test script for survey analytics and auto-sync endpoints.
"""

import requests
import sys

def test_survey_endpoints():
    """Test all survey analytics and auto-sync endpoints."""
    base_url = "http://localhost:5001"
    
    endpoints = [
        ("/surveys", "Survey Dashboard"),
        ("/surveys/analytics", "Survey Analytics"),
        ("/surveys/responses", "Survey Responses"),
        ("/sync", "Auto-Sync Dashboard"),
        ("/api/sync/status", "Sync Status API"),
        ("/api/survey/search?q=test", "Survey Search API")
    ]
    
    print("🧪 Testing Survey Analytics & Auto-Sync Endpoints")
    print("=" * 60)
    
    all_passed = True
    
    for endpoint, name in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"Testing {name:25} ({endpoint:30})", end=" ... ")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print("✅ PASS")
            else:
                print(f"❌ FAIL (Status: {response.status_code})")
                all_passed = False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ ERROR: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All survey analytics tests passed! System is fully operational.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the Flask application logs.")
        return 1

if __name__ == "__main__":
    exit(test_survey_endpoints())
