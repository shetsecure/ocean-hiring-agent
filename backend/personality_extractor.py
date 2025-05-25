#!/usr/bin/env python3
"""
Personality Traits Extractor Module

Extracts Big Five personality traits from interview responses using AI.
"""

import json
import time
import random
import logging
import os
from typing import Dict, Any

#from mistralai import Mistral
from rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class PersonalityTraitsExtractor:
    """Extracts personality traits from interview responses using AI."""
    
    def __init__(self, client, rate_limiter: RateLimiter):
        self.client = client
        self.rate_limiter = rate_limiter
    
    def extract_from_responses(self, candidate_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract Big Five personality traits from interview responses.
        
        Args:
            candidate_data: Candidate data with interview responses
            
        Returns:
            Dict with Big Five traits as floats between 0 and 1
        """
        responses = candidate_data.get('responses', [])
        if not responses:
            logger.warning(f"No interview responses found for candidate {candidate_data.get('name', 'Unknown')}")
            return self._get_default_traits()
        
        # Prepare responses text for analysis
        responses_text = []
        for response in responses:
            question = response.get('question', '')
            answer = response.get('answer', '')
            responses_text.append(f"Q: {question}\nA: {answer}")
        
        combined_responses = "\n\n".join(responses_text)
        
        try:
            # Apply rate limiting before making request
            self.rate_limiter.wait_if_needed()
            system_prompt = """
            You are a personality assessment expert. Analyze interview responses and provide accurate Big Five personality trait scores.
            """
            system_prompt = """
            You are a highly skilled organizational psychologist analyzing a candidate's interview transcript. Your task is to infer the
            candidate's Big Five personality traits (Openness to Experience, Conscientiousness, Extraversion, Agreeableness, Neuroticism/Emotional Stability) based *solely* on their spoken responses.
            """

            prompt = f"""
                    Analyze the following interview responses and extract Big Five personality traits. 
                    Provide scores between 0.0 and 1.0 for each trait based on the responses.

                    Interview Responses:
                    {combined_responses}

                    Big Five Personality Traits to assess:
                    - Openness: Willingness to experience new things, creativity, intellectual curiosity
                    - Conscientiousness: Organization, responsibility, dependability, persistence
                    - Extraversion: Sociability, assertiveness, energy level, tendency to seek stimulation
                    - Agreeableness: Cooperation, trust, empathy, concern for others
                    - Neuroticism: Emotional instability, anxiety, moodiness (higher = more neurotic)

                    Respond ONLY with a valid JSON object in this exact format:
                    {{
                        "openness": 0.75,
                        "conscientiousness": 0.85,
                        "extraversion": 0.60,
                        "agreeableness": 0.80,
                        "neuroticism": 0.30
                    }}
                    """
            
            response = self._make_api_request_with_retry(
                model=os.getenv('MISTRAL_MODEL', 'mistral-small-latest'),
                # model=os.getenv('OPENAI_MODEL', 'deepseek-chat'),
                
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            traits = json.loads(content)
            
            # Validate and normalize traits
            return self._validate_and_normalize_traits(traits)
            
        except Exception as e:
            logger.error(f"Error extracting personality traits: {str(e)}")
            return self._get_default_traits()
    
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
    
    def _validate_and_normalize_traits(self, traits: Dict[str, Any]) -> Dict[str, float]:
        """Validate and normalize personality traits."""
        required_traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        normalized_traits = {}
        
        for trait in required_traits:
            value = traits.get(trait, 0.5)
            try:
                # Convert to float and clamp between 0 and 1
                value = float(value)
                value = max(0.0, min(1.0, value))
                normalized_traits[trait] = value
            except (ValueError, TypeError):
                logger.warning(f"Invalid value for trait {trait}: {value}. Using default 0.5")
                normalized_traits[trait] = 0.5
        
        return normalized_traits
    
    def _get_default_traits(self) -> Dict[str, float]:
        """Return default personality traits (neutral values)."""
        return {
            'openness': 0.5,
            'conscientiousness': 0.5,
            'extraversion': 0.5,
            'agreeableness': 0.5,
            'neuroticism': 0.5
        } 