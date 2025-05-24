#!/usr/bin/env python3
"""
Utility Functions Module

Contains helper functions for formatting output and general utilities.
"""

from typing import Dict, Any

def print_results_summary(results: Dict[str, Any]) -> None:
    """Print a formatted summary of the analysis results."""
    print("\n" + "="*80)
    print("🔍 TEAM COMPATIBILITY ANALYSIS RESULTS")
    print("="*80)
    
    metadata = results.get("analysis_metadata", {})
    print(f"📊 Analysis Date: {metadata.get('timestamp', 'Unknown')[:19]}")
    print(f"👥 Team Size: {metadata.get('team_size', 'Unknown')}")
    print(f"🎯 Candidates Evaluated: {metadata.get('candidates_count', 'Unknown')}")
    
    # Rate limiting info
    if "rate_limiter_stats" in metadata:
        stats = metadata["rate_limiter_stats"]
        print(f"🚦 API Requests Made: {stats.get('total_requests', 'Unknown')}")
        print(f"⏱️  Total Analysis Time: {metadata.get('total_analysis_time', 'Unknown')}s")
    
    # Team insights
    if "team_insights" in results:
        insights = results["team_insights"]
        pool_summary = insights.get("candidate_pool_summary", {})
        print(f"\n📈 Candidate Pool Overview:")
        print(f"   Average Compatibility: {pool_summary.get('average_compatibility', 'N/A')}")
        print(f"   Best Score: {pool_summary.get('best_compatibility', 'N/A')}")
        print(f"   Candidates Above 70% Threshold: {pool_summary.get('candidates_above_threshold', 'N/A')}")
    
    print("\n" + "="*80)
    print("🧑‍💼 INDIVIDUAL CANDIDATE ANALYSIS")
    print("="*80)
    
    for candidate in results.get("candidates_analysis", []):
        info = candidate.get("candidate_info", {})
        math_analysis = candidate.get("mathematical_analysis", {})
        ai_analysis = candidate.get("ai_analysis", {})
        recommendation = candidate.get("overall_recommendation", {})
        
        print(f"\n👤 {info.get('name', 'Unknown')} - {info.get('position', 'Unknown Position')}")
        print(f"   Traits Source: {info.get('traits_source', 'Unknown').title()}")
        print(f"   📊 Mathematical Compatibility: {math_analysis.get('overall_compatibility', 'N/A')}")
        print(f"   🤖 AI Compatibility Score: {ai_analysis.get('compatibility_score', 'N/A')}")
        print(f"   🎯 Recommendation: {recommendation.get('status', 'N/A')} ({recommendation.get('combined_score', 'N/A')})")
        
        # AI Analysis Summary
        print(f"   💭 AI Summary: {ai_analysis.get('summary', 'N/A')}")
        
        # Top strengths
        strengths = ai_analysis.get('strengths', [])
        if strengths:
            print(f"   ✅ Key Strengths: {', '.join(strengths[:2])}")
        
        # Top concerns
        concerns = ai_analysis.get('concerns', [])
        if concerns:
            print(f"   ⚠️  Main Concerns: {', '.join(concerns[:2])}") 