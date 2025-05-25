#!/usr/bin/env python3
"""
Team Compatibility Analyzer - Main Module

This script analyzes the compatibility between job candidates and an existing software engineering team
using the Big Five personality traits and Mistral AI's API for advanced analysis.

Key Features:
- Supports multiple data formats (direct personality traits or interview responses)
- Extracts personality traits from interview responses using AI when needed
- Calculates mathematical compatibility scores
- Uses advanced AI analysis for comprehensive compatibility assessment
- Includes robust error handling and data validation
- Provides detailed fallback mechanisms
- Rate limiting support for API constraints
"""

import json
import os
from typing import Dict, List, Any, Optional, Union
import logging
from pathlib import Path
import sys
from datetime import datetime
import statistics
import time
import random

from dotenv import load_dotenv
from mistralai import Mistral
# from openai import OpenAI

# Import our custom modules
from rate_limiter import RateLimiter
from personality_extractor import PersonalityTraitsExtractor
from utils import print_results_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CompatibilityAnalyzer:
    """Handles the analysis of team compatibility using personality traits and AI."""
    
    def __init__(self, requests_per_second: float = 1.0):
        """Initialize the analyzer with API configuration and rate limiting."""
        load_dotenv()
        self.mistral_api_key = os.getenv('MISTRAL_API_KEY')
        # self.openai_api_key = os.getenv('OPENAI_API_KEY')

        if not self.mistral_api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is not set. Please add it to your .env file or set it as an environment variable.")
        # if not self.openai_api_key:
        #     raise ValueError("OPENAI_API_KEY environment variable is not set. Please add it to your .env file or set it as an environment variable.")
        try:
            self.client = Mistral(api_key=self.mistral_api_key)
            # self.client = OpenAI(api_key=self.openai_api_key, base_url=os.getenv('OPENAI_BASE_URL'))
            logger.info("Successfully initialized Mistral AI client")
        except Exception as e:
            raise ValueError(f"Failed to initialize Mistral AI client: {str(e)}")
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(requests_per_second)
        logger.info(f"🚦 Rate limiter initialized: {requests_per_second} requests per second")
        
        self.traits_extractor = PersonalityTraitsExtractor(self.client, self.rate_limiter)

    def load_json_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load and parse a JSON file with validation.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dict containing the parsed JSON data
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                logger.info(f"Successfully loaded {file_path}")
                return data
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {file_path}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            raise

    def process_team_data(self, team_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract personality traits from team data, handling different formats."""
        team_members = team_data.get('team', team_data.get('team_members', []))
        if not team_members:
            raise ValueError("No team members found in team data")
        
        processed_members = []
        for member in team_members:
            # Check for direct personality traits
            traits = member.get('big_five', member.get('personality_traits'))
            if traits:
                # Normalize trait keys to lowercase
                normalized_traits = {k.lower(): v for k, v in traits.items()}
                processed_member = {
                    'id': member.get('id', 'unknown'),
                    'name': member.get('name', 'Unknown'),
                    'position': member.get('position', member.get('role', 'Unknown')),
                    'traits': normalized_traits
                }
                processed_members.append(processed_member)
            else:
                logger.warning(f"No personality traits found for team member {member.get('name', 'Unknown')}")
        
        if not processed_members:
            raise ValueError("No team members with valid personality traits found")
        
        return processed_members

    def extract_candidate_traits(self, candidates_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract personality traits from candidates, handling different formats."""
        candidates = candidates_data.get('candidates', [])
        if not candidates:
            raise ValueError("No candidates found in candidates data")
        
        processed_candidates = []
        candidates_needing_extraction = []
        
        # First pass: identify candidates that need trait extraction
        for candidate in candidates:
            candidate_info = {
                'id': candidate.get('id', 'unknown'),
                'name': candidate.get('name', 'Unknown'),
                'position': candidate.get('position', candidate.get('role_applied', 'Unknown'))
            }
            
            # Check for direct personality traits
            traits = candidate.get('big_five', candidate.get('personality_traits'))
            if traits:
                # Normalize trait keys to lowercase
                normalized_traits = {k.lower(): v for k, v in traits.items()}
                candidate_info['traits'] = normalized_traits
                candidate_info['source'] = 'direct'
            else:
                # Mark for extraction
                candidates_needing_extraction.append((candidate_info, candidate))
                continue
            
            # Include interview responses if available
            if 'responses' in candidate:
                candidate_info['interview_responses'] = candidate['responses']
            elif 'interview_responses' in candidate:
                candidate_info['interview_responses'] = candidate['interview_responses']
            
            processed_candidates.append(candidate_info)
        
        # Second pass: extract traits for candidates that need it (with rate limiting)
        if candidates_needing_extraction:
            logger.info(f"🧠 Extracting personality traits for {len(candidates_needing_extraction)} candidates (this may take a while due to rate limits)")
            
            for i, (candidate_info, original_candidate) in enumerate(candidates_needing_extraction):
                logger.info(f"🔍 Processing candidate {i+1}/{len(candidates_needing_extraction)}: {candidate_info['name']}")
                
                extracted_traits = self.traits_extractor.extract_from_responses(original_candidate)
                candidate_info['traits'] = extracted_traits
                candidate_info['source'] = 'extracted'
                
                # Include interview responses if available
                if 'responses' in original_candidate:
                    candidate_info['interview_responses'] = original_candidate['responses']
                elif 'interview_responses' in original_candidate:
                    candidate_info['interview_responses'] = original_candidate['interview_responses']
                
                processed_candidates.append(candidate_info)
        
        return processed_candidates

    def process_candidates_data(self, candidates_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract personality traits, handling different formats."""
        processed_candidates = []
        candidates_needing_extraction = []
        
        # First pass: identify candidates that need trait extraction
        for candidate_data in candidates_data_list:
            # Handle the new individual file format
            candidate = candidate_data.get('candidate', candidate_data)
            
            candidate_info = {
                'id': candidate.get('id', 'unknown'),
                'name': candidate.get('name', 'Unknown'),
                'position': candidate.get('position', candidate.get('role_applied', 'Unknown'))
            }
            
            # Check for direct personality traits
            traits = candidate.get('big_five', candidate.get('personality_traits'))
            if traits:
                # Normalize trait keys to lowercase
                normalized_traits = {k.lower(): v for k, v in traits.items()}
                candidate_info['traits'] = normalized_traits
                candidate_info['source'] = 'direct'
            else:
                # Mark for extraction
                candidates_needing_extraction.append((candidate_info, candidate))
                continue
            
            # Include interview responses if available
            if 'responses' in candidate:
                candidate_info['interview_responses'] = candidate['responses']
            elif 'interview_responses' in candidate:
                candidate_info['interview_responses'] = candidate['interview_responses']
            
            processed_candidates.append(candidate_info)
        
        # Second pass: extract traits for candidates that need it (with rate limiting)
        if candidates_needing_extraction:
            logger.info(f"🧠 Extracting personality traits for {len(candidates_needing_extraction)} candidates (this may take a while due to rate limits)")
            
            for i, (candidate_info, original_candidate) in enumerate(candidates_needing_extraction):
                logger.info(f"🔍 Processing candidate {i+1}/{len(candidates_needing_extraction)}: {candidate_info['name']}")
                
                extracted_traits = self.traits_extractor.extract_from_responses(original_candidate)
                candidate_info['traits'] = extracted_traits
                candidate_info['source'] = 'extracted'
                
                # Include interview responses if available
                if 'responses' in original_candidate:
                    candidate_info['interview_responses'] = original_candidate['responses']
                elif 'interview_responses' in original_candidate:
                    candidate_info['interview_responses'] = original_candidate['interview_responses']
                
                processed_candidates.append(candidate_info)
        
        return processed_candidates

    def get_ai_compatibility_analysis(self, team_members: List[Dict[str, Any]], 
                                   candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get comprehensive AI-powered compatibility analysis using Mistral AI.
        
        Args:
            team_members: Team members data
            candidate: Candidate data
            
        Returns:
            Dict containing AI-generated compatibility analysis
        """
        # Prepare team summary
        team_summary = []
        for member in team_members:
            member_info = f"- {member['name']} ({member['position']}): "
            traits_str = ", ".join([f"{k.title()}: {v:.2f}" for k, v in member['traits'].items()])
            member_info += traits_str
            team_summary.append(member_info)
        
        team_summary_text = "\n".join(team_summary)
        
        # Prepare candidate summary
        candidate_traits_str = ", ".join([f"{k.title()}: {v:.2f}" for k, v in candidate['traits'].items()])
        candidate_summary = f"{candidate['name']} ({candidate['position']}): {candidate_traits_str}"
        
        # Include interview responses if available
        interview_context = ""
        if 'interview_responses' in candidate:
            responses = candidate['interview_responses'][:3]  # Limit to first 3 responses
            interview_text = []
            for resp in responses:
                q = resp.get('question', '')
                a = resp.get('answer', resp.get('response', ''))
                if q and a:
                    interview_text.append(f"Q: {q}\nA: {a}")
            if interview_text:
                interview_context = f"\n\nKey Interview Responses:\n" + "\n\n".join(interview_text)

        system_prompt = """
        You are a world-class team compatibility analyst and organizational psychologist.
        Provide thorough, nuanced, and actionable analysis based on personality psychology and team dynamics research.
        """
        
        prompt = f"""
        As an expert team dynamics consultant and organizational psychologist, analyze the compatibility between this candidate and the existing team.
        Consider personality fit, collaboration potential, and team dynamics.
        Provide a concise narrative-style summary of the candidate's overall soft skills and general personality.
        Highlight key strengths and potential areas for development relevant to a team environment.
        Also, identify any behavioral flags based on the conversation (e.g., "May avoid conflict", "Good under pressure").

        CURRENT TEAM:
        {team_summary_text}

        CANDIDATE:
        {candidate_summary}{interview_context}

        ANALYSIS FRAMEWORK:
        1. Personality Fit: How well do the candidate's traits complement the team?
        2. Team Dynamics: Will this addition improve or challenge team cohesion?
        3. Collaboration Style: How will the candidate work with existing members?
        4. Growth Potential: What opportunities and risks does this hire present?
        5. Cultural Integration: How well will the candidate adapt to team culture?

        Provide a comprehensive analysis in JSON format with this exact structure:
        {{
            "compatibility_score": float,  // 0.0-1.0, your expert assessment considering all factors
            "confidence_level": float,     // 0.0-1.0, how confident you are in this assessment
            "summary": "string",           // 2-3 sentence overall assessment
            "strengths": ["string"],       // 3-5 specific compatibility strengths
            "concerns": ["string"],        // 2-4 potential concerns or challenges
            "recommendations": ["string"], // 3-4 actionable recommendations
            "team_dynamics_impact": {{
                "likely_role": "string",           // Expected role in team dynamics
                "collaboration_style": "string",   // How they'll collaborate
                "influence_on_team": "string"      // Expected impact on team culture
            }},
            "development_opportunities": ["string"], // 2-3 growth/mentoring opportunities
            "risk_factors": ["string"]              // 2-3 potential risks to monitor
        }}
        
        Be specific, actionable, and balanced in your assessment. Consider the personality traits and qualitative aspects of team fit.
        """

        try:
            # Apply rate limiting before making request
            self.rate_limiter.wait_if_needed()
            
            response = self._make_api_request_with_retry(
                model=os.getenv('MISTRAL_MODEL', 'mistral-small-latest'),
                # model=os.getenv('OPENAI_MODEL', 'deepseek-chat'),
                messages=[
                    {
                        "role": "system", 
                        "content": system_prompt
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            analysis = json.loads(content)
            
            # Validate the response structure
            return self._validate_ai_analysis(analysis)
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            return self._get_fallback_analysis()

    def _make_api_request_with_retry(self, max_retries: int = 3, **kwargs):
        """Make API request with retry logic for rate limiting."""
        for attempt in range(max_retries):
            try:
                response = self.client.chat.complete(**kwargs)
                # response = self.client.chat.completions.create(**kwargs)
                return response
            except Exception as e:
                error_str = str(e).lower()
                if 'rate limit' in error_str or 'too many requests' in error_str:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + random.uniform(1, 3)  # Exponential backoff with jitter
                        logger.warning(f"Rate limit hit, retrying in {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                raise e

    def _validate_ai_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize AI analysis response."""
        validated = {
            'compatibility_score': float(analysis.get('compatibility_score', 0.5)),
            'confidence_level': float(analysis.get('confidence_level', 0.5)),
            'summary': str(analysis.get('summary', 'Analysis unavailable')),
            'strengths': analysis.get('strengths', ['Analysis pending']),
            'concerns': analysis.get('concerns', ['Further evaluation needed']),
            'recommendations': analysis.get('recommendations', ['Conduct additional assessment']),
            'team_dynamics_impact': analysis.get('team_dynamics_impact', {}),
            'development_opportunities': analysis.get('development_opportunities', []),
            'risk_factors': analysis.get('risk_factors', [])
        }
        
        # Clamp scores between 0 and 1
        validated['compatibility_score'] = max(0.0, min(1.0, validated['compatibility_score']))
        validated['confidence_level'] = max(0.0, min(1.0, validated['confidence_level']))
        
        return validated

    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Provide fallback analysis when AI analysis fails."""
        return {
            'compatibility_score': 0.5,
            'confidence_level': 0.3,  # Low confidence for fallback
            'summary': "AI analysis unavailable",
            'strengths': ["Fallback analysis"],
            'concerns': ["AI analysis unavailable"],
            'recommendations': ["Conduct follow-up interviews", "Consider team integration plan"],
            'team_dynamics_impact': {},
            'development_opportunities': [],
            'risk_factors': []
        }

    def analyze_team_compatibility(self, team_data: Dict[str, Any], candidates_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze compatibility between team and candidates using AI analysis only.
        
        Args:
            team_data: Team data as dictionary
            candidates_data_list: List of candidate data dictionaries
            
        Returns:
            Dict containing comprehensive compatibility analysis results
        """
        analysis_start_time = time.time()
        
        try:
            # Process team and candidates data
            team_members = self.process_team_data(team_data)
            candidates = self.process_candidates_data(candidates_data_list)
            logger.info(f"Processing {len(team_members)} team members and {len(candidates)} candidates")
            
            # Estimate total time based on number of API calls needed
            api_calls_needed = len([c for c in candidates if c.get('source') == 'extracted']) + len(candidates)
            estimated_time = api_calls_needed * self.rate_limiter.min_interval
            if estimated_time > 10:  # Only show estimate if it's significant
                logger.info(f"⏱️  Estimated completion time: {estimated_time:.0f}s ({estimated_time/60:.1f} minutes) due to rate limiting")
            
            results = {
                "analysis_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "team_size": len(team_members),
                    "candidates_count": len(candidates),
                    "analyzer_version": "3.0",
                    "analysis_type": "ai_only",
                    "rate_limit_info": {
                        "requests_per_second": self.rate_limiter.requests_per_second,
                        "estimated_api_calls": api_calls_needed
                    }
                },
                "team_summary": {
                    "members": [
                        {
                            "name": member['name'],
                            "position": member['position'],
                            "traits_summary": {k: round(v, 2) for k, v in member['traits'].items()}
                        } for member in team_members
                    ]
                },
                "candidates_analysis": []
            }
            
            # Analyze each candidate
            for i, candidate in enumerate(candidates):
                logger.info(f"🤖 AI analysis for candidate {i+1}/{len(candidates)}: {candidate['name']}")
                
                # Get AI-powered analysis
                ai_analysis = self.get_ai_compatibility_analysis(team_members, candidate)
                
                # Combine analyses
                candidate_result = {
                    "candidate_info": {
                        "id": candidate['id'],
                        "name": candidate['name'],
                        "position": candidate['position'],
                        "traits_source": candidate.get('source', 'unknown'),
                        "personality_traits": {k: round(v, 3) for k, v in candidate['traits'].items()}
                    },
                    "ai_analysis": ai_analysis,
                    "overall_recommendation": self._generate_recommendation(
                        ai_analysis['compatibility_score'],
                        ai_analysis['confidence_level']
                    )
                }
                
                results["candidates_analysis"].append(candidate_result)
            
            # Add team-level insights and rate limiter stats
            results["team_insights"] = self._generate_team_insights(results["candidates_analysis"])
            results["analysis_metadata"]["rate_limiter_stats"] = self.rate_limiter.get_stats()
            results["analysis_metadata"]["total_analysis_time"] = round(time.time() - analysis_start_time, 2)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in compatibility analysis: {str(e)}")
            raise

    def _generate_recommendation(self, ai_score: float, confidence: float) -> Dict[str, Any]:
        """Generate overall recommendation based on scores."""
        combined_score = ai_score
        
        if combined_score >= 0.8 and confidence >= 0.7:
            recommendation = "HIGHLY RECOMMENDED"
            reasoning = "Strong compatibility across multiple assessment dimensions."
        elif combined_score >= 0.7 and confidence >= 0.6:
            recommendation = "RECOMMENDED"
            reasoning = "Good compatibility with positive indicators for team fit."
        elif combined_score >= 0.6:
            recommendation = "CONDITIONAL"
            reasoning = "Moderate compatibility - recommend additional evaluation or targeted team integration."
        elif combined_score >= 0.4:
            recommendation = "CAUTIOUS"
            reasoning = "Lower compatibility scores suggest careful consideration needed."
        else:
            recommendation = "NOT RECOMMENDED"
            reasoning = "Significant compatibility concerns across multiple dimensions."
        
        return {
            "status": recommendation,
            "combined_score": round(combined_score, 3),
            "reasoning": reasoning,
            "confidence_level": round(confidence, 3)
        }

    def _generate_team_insights(self, candidates_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate insights about the candidate pool relative to the team."""
        if not candidates_analysis:
            return {}
        
        scores = [c["ai_analysis"]["compatibility_score"] for c in candidates_analysis]
        
        return {
            "candidate_pool_summary": {
                "average_compatibility": round(statistics.mean(scores), 3),
                "best_compatibility": round(max(scores), 3),
                "compatibility_range": round(max(scores) - min(scores), 3),
                "candidates_above_threshold": len([s for s in scores if s >= 0.7])
            },
            "top_candidates": sorted(
                [
                    {
                        "name": c["candidate_info"]["name"],
                        "compatibility": c["ai_analysis"]["compatibility_score"],
                        "recommendation": c["overall_recommendation"]["status"]
                    } for c in candidates_analysis
                ],
                key=lambda x: x["compatibility"],
                reverse=True
            )[:3]
        }

    def save_results(self, results: Dict[str, Any], output_file: str) -> None:
        """
        Save analysis results to a JSON file with proper formatting.
        
        Args:
            results: Analysis results to save
            output_file: Path to output file
        """
        try:
            output_path = Path(output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            raise 