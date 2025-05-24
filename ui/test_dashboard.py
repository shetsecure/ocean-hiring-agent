#!/usr/bin/env python3
"""
Test script for the Team Compatibility Dashboard
Validates data loading and basic functionality.
"""

import os
import sys
import json
from app import load_dashboard_data

def test_data_loading():
    """Test if data loads correctly"""
    print("🧪 Testing data loading...")
    data = load_dashboard_data()
    
    if data is None:
        print("❌ Failed to load data - data_for_dashboard.json not found")
        return False
    
    print("✅ Data loaded successfully!")
    
    # Check required keys
    required_keys = ['analysis_metadata', 'team_summary', 'candidates_analysis', 'team_insights']
    for key in required_keys:
        if key not in data:
            print(f"❌ Missing required key: {key}")
            return False
        print(f"✅ Found key: {key}")
    
    # Print summary
    metadata = data['analysis_metadata']
    insights = data['team_insights']
    
    print(f"\n📊 Dashboard Summary:")
    print(f"   Team Size: {metadata['team_size']}")
    print(f"   Candidates: {metadata['candidates_count']}")
    print(f"   Analysis Date: {metadata['timestamp']}")
    print(f"   Average Compatibility: {insights['candidate_pool_summary']['average_compatibility']:.1%}")
    
    return True

def test_api_structure():
    """Test API data structure"""
    print("\n🔍 Testing API structure...")
    data = load_dashboard_data()
    
    if not data:
        print("❌ No data available for API testing")
        return False
    
    # Test candidates structure
    candidates = data.get('candidates_analysis', [])
    if not candidates:
        print("❌ No candidates found")
        return False
    
    candidate = candidates[0]
    required_candidate_keys = [
        'candidate_info', 'mathematical_analysis', 
        'ai_analysis', 'overall_recommendation'
    ]
    
    for key in required_candidate_keys:
        if key not in candidate:
            print(f"❌ Missing candidate key: {key}")
            return False
        print(f"✅ Found candidate key: {key}")
    
    print(f"✅ All {len(candidates)} candidates have proper structure")
    return True

def test_dashboard_features():
    """Test dashboard feature compatibility"""
    print("\n🎯 Testing dashboard features...")
    data = load_dashboard_data()
    
    if not data:
        return False
    
    # Test chart data preparation
    candidates = data['candidates_analysis']
    
    # Test compatibility chart data
    compatibility_scores = [c['ai_analysis']['compatibility_score'] for c in candidates]
    print(f"✅ Compatibility scores range: {min(compatibility_scores):.2f} - {max(compatibility_scores):.2f}")
    
    # Test recommendation distribution
    recommendations = {}
    for candidate in candidates:
        status = candidate['overall_recommendation']['status']
        recommendations[status] = recommendations.get(status, 0) + 1
    
    print("✅ Recommendation distribution:")
    for status, count in recommendations.items():
        print(f"   {status}: {count}")
    
    return True

if __name__ == '__main__':
    print("🚀 Team Compatibility Dashboard - Test Suite")
    print("=" * 50)
    
    # Change to parent directory to find data file
    original_dir = os.getcwd()
    parent_dir = os.path.dirname(os.getcwd())
    os.chdir(parent_dir)
    
    try:
        success = True
        success &= test_data_loading()
        success &= test_api_structure()
        success &= test_dashboard_features()
        
        print("\n" + "=" * 50)
        if success:
            print("✅ All tests passed! Dashboard is ready to run.")
            print("💡 Start the dashboard with: cd ui && python run.py")
        else:
            print("❌ Some tests failed. Check the errors above.")
            sys.exit(1)
            
    finally:
        os.chdir(original_dir) 