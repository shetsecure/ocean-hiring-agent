#!/usr/bin/env python3
"""
Quick test for compatibility display
"""

import json
import os

def test_compatibility_display():
    """Test the compatibility calculation"""
    print("🧪 Testing Compatibility Display")
    print("=" * 40)
    
    # Load data
    try:
        with open('../data_for_dashboard.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ Data file not found")
        return
    
    # Extract compatibility data
    insights = data.get('team_insights', {})
    pool_summary = insights.get('candidate_pool_summary', {})
    
    raw_compatibility = pool_summary.get('average_compatibility')
    candidates_above_threshold = pool_summary.get('candidates_above_threshold')
    best_compatibility = pool_summary.get('best_compatibility')
    
    print(f"📊 Raw Average Compatibility: {raw_compatibility}")
    print(f"📊 Formatted Percentage: {(raw_compatibility * 100):.1f}%")
    print(f"⭐ Best Compatibility: {(best_compatibility * 100):.1f}%")
    print(f"🎯 Candidates Above Threshold: {candidates_above_threshold}")
    
    # Test individual candidates
    candidates = data.get('candidates_analysis', [])
    print(f"\n👥 Individual Candidate Compatibility:")
    for candidate in candidates:
        name = candidate['candidate_info']['name']
        compatibility = candidate['ai_analysis']['compatibility_score']
        recommendation = candidate['overall_recommendation']['status']
        print(f"   {name}: {(compatibility * 100):.1f}% ({recommendation})")
    
    print("\n✅ All compatibility data loaded successfully!")
    
    return {
        'average_compatibility': raw_compatibility,
        'formatted_percentage': f"{(raw_compatibility * 100):.1f}%",
        'candidates_above_threshold': candidates_above_threshold,
        'total_candidates': len(candidates)
    }

if __name__ == '__main__':
    result = test_compatibility_display()
    print(f"\n🎯 Dashboard should show: {result['formatted_percentage']} average compatibility") 