#!/usr/bin/env python3
"""
Team Compatibility Analyzer - Main Entry Point

Main execution script for the Team Compatibility Analyzer.
Run this file to start the analysis process.
"""

import os
import sys
import logging
from pathlib import Path

from compatibility_analyzer import CompatibilityAnalyzer
from utils import print_results_summary
from interview_manager import InterviewManager

from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main execution function."""
    try:
        print("🚀 Initializing Team Compatibility Analyzer...")
        
        # Check for custom rate limit from environment
        requests_per_second = float(os.getenv('MISTRAL_REQUESTS_PER_SECOND', '1.0'))
        print(f"🚦 Rate limit: {requests_per_second} requests per second")
        
        # Initialize analyzer
        analyzer = CompatibilityAnalyzer(requests_per_second=requests_per_second)
        
        # Check if required files exist
        team_file = "data/team.json"
        candidates_dir = "data"
        
        if not Path(team_file).exists():
            print(f"❌ Error: {team_file} not found. Please ensure the team data file exists in the data/ directory.")
            sys.exit(1)
        
        # Find all candidate files in the data directory
        candidate_files = list(Path(candidates_dir).glob("candidate_*.json"))
        if not candidate_files:
            print(f"❌ Error: No candidate files found in {candidates_dir}/. Please ensure candidate files (candidate_*.json) exist.")
            sys.exit(1)
        
        print(f"📁 Loading data files... Found {len(candidate_files)} candidate files")
        
        # Perform analysis
        results = analyzer.analyze_team_compatibility(team_file, candidate_files)
        
        # Print formatted results
        print_results_summary(results)
        
        # Save detailed results
        output_file = "data/compatibility_scores.json"
        analyzer.save_results(results, output_file)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        print("✅ Analysis completed successfully!")
        
    except ValueError as e:
        print(f"❌ Configuration Error: {str(e)}")
        print("\n💡 Make sure to:")
        print("   1. Set your MISTRAL_API_KEY environment variable")
        print("   2. Copy env.example to .env and add your API key")
        print("   3. Ensure data/team.json exists and individual candidate files (data/candidate_*.json)")
        print("   4. (Optional) Set MISTRAL_REQUESTS_PER_SECOND if you need different rate limits")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
