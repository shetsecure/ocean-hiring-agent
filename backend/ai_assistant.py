"""
AI Assistant for Candidate Querying

This module handles:
- Weaviate vector database operations
- Candidate data synchronization
- Natural language querying of candidates
- Auto-sync with compatibility analysis results
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import weaviate
import weaviate.classes as wvc
from weaviate.classes.config import Configure, Property, DataType
from dotenv import load_dotenv
import logging
from mistralai import Mistral

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIAssistant:
    """
    AI Assistant for querying candidate information using Weaviate vector database.
    """
    
    def __init__(self):
        """Initialize the AI Assistant with Weaviate configuration."""
        load_dotenv()
        
        # Weaviate configuration
        self.weaviate_url = os.getenv("WEAVIATE_URL")
        self.weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
        self.collection_name = os.getenv("WEAVIATE_COLLECTION_NAME", "Candidates")
        self.auto_sync = os.getenv("WEAVIATE_AUTO_SYNC", "true").lower() == "true"
        
        # AI configuration
        self.max_results = int(os.getenv("AI_ASSISTANT_MAX_RESULTS", "5"))
        self.ai_model = os.getenv("AI_ASSISTANT_MODEL", "mistral-small-latest")
        
        # Mistral client for RAG analysis
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        if not mistral_api_key:
            raise ValueError("Mistral API key is required for RAG functionality. Check your .env file.")
        self.mistral_client = Mistral(api_key=mistral_api_key)
        
        # Data file path - check if running in Docker or use env var
        data_file_path = os.getenv("COMPATIBILITY_SCORES_FILE")
        if data_file_path:
            self.compatibility_file = data_file_path
        elif os.path.exists("/app/data/compatibility_scores.json"):  # Docker path
            self.compatibility_file = "/app/data/compatibility_scores.json"
        else:  # Local development path
            self.compatibility_file = "../data/compatibility_scores.json"
        
        if not self.weaviate_url or not self.weaviate_api_key:
            raise ValueError("Weaviate URL and API key are required. Check your .env file.")
        
        # Initialize Weaviate client
        self.client = None
        self._connect_to_weaviate()
    
    def _connect_to_weaviate(self):
        """Connect to Weaviate cloud instance."""
        try:
            # Connect to Weaviate Cloud with Mistral API key for embeddings
            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=self.weaviate_url,
                auth_credentials=weaviate.auth.AuthApiKey(self.weaviate_api_key),
                headers={
                    "X-Mistral-Api-Key": os.getenv("MISTRAL_API_KEY", "")
                }
            )
            
            # Test connection
            if self.client.is_ready():
                logger.info("✅ Successfully connected to Weaviate Cloud")
            else:
                raise Exception("Weaviate client is not ready")
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to Weaviate: {e}")
            raise
    
    def setup_collection(self):
        """Create or recreate the Candidates collection."""
        try:
            # Delete existing collection if it exists
            if self.client.collections.exists(self.collection_name):
                self.client.collections.delete(self.collection_name)
                logger.info(f"🗑️ Deleted existing collection: {self.collection_name}")
            
            # Create new collection with schema (using Mistral embeddings)
            collection = self.client.collections.create(
                name=self.collection_name,
                description="Candidate profiles for AI-powered querying",
                vectorizer_config=Configure.Vectorizer.text2vec_mistral(),
                properties=[
                    Property(name="name", data_type=DataType.TEXT),
                    Property(name="position", data_type=DataType.TEXT),
                    Property(name="candidate_id", data_type=DataType.TEXT),
                    Property(name="compatibility_score", data_type=DataType.NUMBER),
                    Property(name="recommendation", data_type=DataType.TEXT),
                    Property(name="summary", data_type=DataType.TEXT),
                    Property(name="strengths", data_type=DataType.TEXT_ARRAY),
                    Property(name="concerns", data_type=DataType.TEXT_ARRAY),
                    Property(name="openness", data_type=DataType.NUMBER),
                    Property(name="conscientiousness", data_type=DataType.NUMBER),
                    Property(name="extraversion", data_type=DataType.NUMBER),
                    Property(name="agreeableness", data_type=DataType.NUMBER),
                    Property(name="neuroticism", data_type=DataType.NUMBER),
                    Property(name="searchable_text", data_type=DataType.TEXT),  # Combined text for vector search
                    Property(name="created_at", data_type=DataType.DATE),
                ]
            )
            
            logger.info(f"✅ Created collection: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup collection: {e}")
            return False
    
    def sync_candidates_from_file(self, file_path: Optional[str] = None) -> bool:
        """
        Synchronize candidates from compatibility_scores.json to Weaviate.
        
        Args:
            file_path: Path to compatibility scores file (optional)
            
        Returns:
            bool: Success status
        """
        try:
            file_path = file_path or self.compatibility_file
            
            # Load compatibility scores
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Setup collection (this will delete and recreate)
            if not self.setup_collection():
                return False
            
            # Get the collection
            collection = self.client.collections.get(self.collection_name)
            
            # Prepare candidate data
            candidates_to_insert = []
            
            for candidate_analysis in data.get("candidates_analysis", []):
                candidate_info = candidate_analysis.get("candidate_info", {})
                ai_analysis = candidate_analysis.get("ai_analysis", {})
                overall_rec = candidate_analysis.get("overall_recommendation", {})
                
                # Extract personality traits
                traits = candidate_info.get("personality_traits", {})
                
                # Create searchable text combining key information
                searchable_text = self._create_searchable_text(
                    ai_analysis.get("summary", ""),
                    ai_analysis.get("strengths", []),
                    ai_analysis.get("concerns", []),
                    candidate_info.get("name", ""),
                    candidate_info.get("position", ""),
                    traits
                )
                
                # Prepare candidate object
                candidate_obj = {
                    "name": candidate_info.get("name", ""),
                    "position": candidate_info.get("position", ""),
                    "candidate_id": candidate_info.get("id", ""),
                    "compatibility_score": overall_rec.get("combined_score", 0),
                    "recommendation": overall_rec.get("status", ""),
                    "summary": ai_analysis.get("summary", ""),
                    "strengths": ai_analysis.get("strengths", []),
                    "concerns": ai_analysis.get("concerns", []),
                    "openness": traits.get("openness", 0),
                    "conscientiousness": traits.get("conscientiousness", 0),
                    "extraversion": traits.get("extraversion", 0),
                    "agreeableness": traits.get("agreeableness", 0),
                    "neuroticism": traits.get("neuroticism", 0),
                    "searchable_text": searchable_text,
                    "created_at": datetime.now()
                }
                
                candidates_to_insert.append(candidate_obj)
            
            # Batch insert candidates
            if candidates_to_insert:
                with collection.batch.dynamic() as batch:
                    for candidate in candidates_to_insert:
                        batch.add_object(properties=candidate)
                
                logger.info(f"✅ Successfully synced {len(candidates_to_insert)} candidates to Weaviate")
                return True
            else:
                logger.warning("⚠️ No candidates found in compatibility scores file")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to sync candidates: {e}")
            return False
    
    def _create_searchable_text(self, summary: str, strengths: List[str], concerns: List[str], 
                              name: str, position: str, traits: Dict[str, float]) -> str:
        """Create combined searchable text for vector embeddings."""
        
        # Convert traits to descriptive text
        trait_descriptions = []
        if traits.get("openness", 0) > 0.7:
            trait_descriptions.append("highly open to new experiences, creative, innovative")
        if traits.get("conscientiousness", 0) > 0.7:
            trait_descriptions.append("very organized, reliable, detail-oriented")
        if traits.get("extraversion", 0) > 0.7:
            trait_descriptions.append("outgoing, social, energetic, great communicator")
        if traits.get("agreeableness", 0) > 0.7:
            trait_descriptions.append("collaborative, team-oriented, cooperative")
        if traits.get("neuroticism", 0) < 0.3:
            trait_descriptions.append("handles pressure well, emotionally stable, stress-resistant")
        
        # Combine all text
        searchable_parts = [
            f"Name: {name}",
            f"Position: {position}",
            f"Summary: {summary}",
            f"Strengths: {' '.join(strengths)}",
            f"Concerns: {' '.join(concerns)}",
            f"Personality traits: {' '.join(trait_descriptions)}"
        ]
        
        return " ".join(searchable_parts)
    
    def query_candidates(self, query: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Query candidates using RAG (Retrieval-Augmented Generation).
        
        Args:
            query: Natural language query
            limit: Maximum number of results to return
            
        Returns:
            Dictionary with RAG-processed query results and metadata
        """
        try:
            limit = limit or self.max_results
            
            # Step 1: Retrieval - Get broader candidate pool via vector search
            retrieval_limit = min(limit * 3, 10)  # Get more candidates for LLM to analyze
            vector_candidates = self._vector_retrieval(query, retrieval_limit)
            
            if not vector_candidates:
                return {
                    "query": query,
                    "results_count": 0,
                    "candidates": [],
                    "error": "No candidates found in vector search",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Step 2: LLM Analysis - Intelligent ranking based on actual personality scores
            rag_results = self._llm_analyze_and_rank(query, vector_candidates, limit)
            
            response = {
                "query": query,
                "results_count": len(rag_results),
                "candidates": rag_results,
                "retrieval_count": len(vector_candidates),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"🧠 RAG Query '{query}' processed {len(vector_candidates)} candidates, returned {len(rag_results)} results")
            return response
            
        except Exception as e:
            logger.error(f"❌ Failed to process RAG query: {e}")
            return {
                "query": query,
                "results_count": 0,
                "candidates": [],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _vector_retrieval(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Perform vector search to retrieve candidate pool.
        
        Args:
            query: Search query
            limit: Number of candidates to retrieve
            
        Returns:
            List of candidate dictionaries
        """
        try:
            collection = self.client.collections.get(self.collection_name)
            
            # Perform vector search using Mistral embeddings
            results = collection.query.near_text(
                query=query,
                limit=limit,
                return_metadata=wvc.query.MetadataQuery(score=True)
            )
            
            # Format candidates for LLM analysis
            candidates = []
            for result in results.objects:
                candidate = {
                    "name": result.properties.get("name"),
                    "position": result.properties.get("position"),
                    "candidate_id": result.properties.get("candidate_id"),
                    "compatibility_score": result.properties.get("compatibility_score"),
                    "recommendation": result.properties.get("recommendation"),
                    "summary": result.properties.get("summary"),
                    "strengths": result.properties.get("strengths", []),
                    "concerns": result.properties.get("concerns", []),
                    "personality_traits": {
                        "openness": result.properties.get("openness"),
                        "conscientiousness": result.properties.get("conscientiousness"),
                        "extraversion": result.properties.get("extraversion"),
                        "agreeableness": result.properties.get("agreeableness"),
                        "neuroticism": result.properties.get("neuroticism")
                    },
                    "vector_relevance_score": result.metadata.score if result.metadata else None
                }
                candidates.append(candidate)
            
            return candidates
            
        except Exception as e:
            logger.error(f"❌ Vector retrieval failed: {e}")
            return []
    
    def _llm_analyze_and_rank(self, query: str, candidates: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """
        Use Mistral LLM to analyze candidates and provide intelligent ranking.
        
        Args:
            query: Original user query
            candidates: List of candidates from vector search
            limit: Number of top candidates to return
            
        Returns:
            List of ranked candidates with LLM analysis
        """
        try:
            # Prepare candidate data for LLM analysis
            candidates_data = ""
            for i, candidate in enumerate(candidates, 1):
                traits = candidate["personality_traits"]
                candidates_data += f"""
{i}. {candidate['name']} ({candidate['position']})
   - Personality Scores:
     * Extraversion: {traits['extraversion']:.2f} (outgoing, social, energetic)
     * Openness: {traits['openness']:.2f} (creative, innovative, adaptable)
     * Conscientiousness: {traits['conscientiousness']:.2f} (organized, reliable, detail-oriented)
     * Agreeableness: {traits['agreeableness']:.2f} (collaborative, team-oriented, cooperative)
     * Neuroticism: {traits['neuroticism']:.2f} (stress levels - lower is better)
   - Compatibility Score: {candidate['compatibility_score']:.2f}
   - Recommendation: {candidate['recommendation']}
   - Summary: {candidate['summary'][:200]}...
"""
            
            # Create LLM prompt for intelligent analysis
            prompt = f"""You are an expert HR analyst tasked with ranking candidates based on a specific query.

Query: "{query}"

Available Candidates:
{candidates_data}

INSTRUCTIONS:
1. Analyze the query to understand what personality traits or characteristics are most relevant
2. Focus on the NUMERICAL personality scores, not just text descriptions
3. Rank candidates based on how well their actual personality scores match the query intent
4. Return EXACTLY the top {limit} candidates in order of relevance
5. For each candidate, provide a brief explanation of why they fit the query

RESPONSE FORMAT (JSON):
{{
  "analysis": "Brief explanation of how you interpreted the query and ranking criteria",
  "ranked_candidates": [
    {{
      "name": "Candidate Name",
      "rank": 1,
      "relevance_reasoning": "Why this candidate fits the query based on personality scores",
      "key_traits": ["trait1", "trait2"]
    }}
  ]
}}

Focus on NUMERICAL personality trait scores over text descriptions. Be precise and data-driven in your analysis."""

            # Call Mistral LLM
            messages = [{"role": "user", "content": prompt}]
            
            response = self.mistral_client.chat.complete(
                model=self.ai_model,
                messages=messages,
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=1000
            )
            
            # Parse LLM response
            llm_content = response.choices[0].message.content
            
            try:
                import re
                # Extract JSON from LLM response
                json_match = re.search(r'\{.*\}', llm_content, re.DOTALL)
                if json_match:
                    llm_analysis = json.loads(json_match.group())
                else:
                    raise ValueError("No JSON found in LLM response")
            except:
                # Fallback: Parse text response manually
                llm_analysis = self._parse_text_response(llm_content, candidates, limit)
            
            # Map LLM rankings back to full candidate data
            ranked_results = []
            for llm_candidate in llm_analysis.get("ranked_candidates", []):
                # Find matching candidate
                for candidate in candidates:
                    if candidate["name"] == llm_candidate["name"]:
                        result = candidate.copy()
                        result["llm_rank"] = llm_candidate["rank"]
                        result["relevance_reasoning"] = llm_candidate["relevance_reasoning"]
                        result["key_traits"] = llm_candidate.get("key_traits", [])
                        ranked_results.append(result)
                        break
            
            logger.info(f"🤖 LLM analyzed {len(candidates)} candidates, ranked top {len(ranked_results)}")
            return ranked_results[:limit]
            
        except Exception as e:
            logger.error(f"❌ LLM analysis failed: {e}")
            # Fallback to original vector search results
            return candidates[:limit]
    
    def _parse_text_response(self, llm_content: str, candidates: List[Dict], limit: int) -> Dict[str, Any]:
        """
        Fallback parser for non-JSON LLM responses.
        
        Args:
            llm_content: Raw LLM response text
            candidates: Original candidate list
            limit: Number of candidates to return
            
        Returns:
            Parsed analysis dict
        """
        # Simple fallback: extract candidate names mentioned in order
        ranked_candidates = []
        
        for i, candidate in enumerate(candidates[:limit], 1):
            ranked_candidates.append({
                "name": candidate["name"],
                "rank": i,
                "relevance_reasoning": f"Selected based on vector similarity and compatibility score",
                "key_traits": []
            })
        
        return {
            "analysis": "Fallback ranking due to parsing issues",
            "ranked_candidates": ranked_candidates
        }
    
    def get_candidate_stats(self) -> Dict[str, Any]:
        """Get statistics about the candidates in the database."""
        try:
            collection = self.client.collections.get(self.collection_name)
            
            # Get total count
            total_count = collection.aggregate.over_all(total_count=True)
            
            # Get recommendation distribution
            recommendations = collection.aggregate.over_all(
                group_by="recommendation"
            )
            
            return {
                "total_candidates": total_count.total_count,
                "recommendations_distribution": recommendations.groups if hasattr(recommendations, 'groups') else {},
                "collection_name": self.collection_name,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get candidate stats: {e}")
            return {"error": str(e)}
    
    def close_connection(self):
        """Close the Weaviate connection."""
        if self.client:
            self.client.close()
            logger.info("🔌 Weaviate connection closed")


# Convenience functions for API endpoints
def create_ai_assistant() -> AIAssistant:
    """Create and return an AIAssistant instance."""
    return AIAssistant()


def sync_candidates_auto() -> bool:
    """Auto-sync candidates from compatibility scores file."""
    try:
        assistant = create_ai_assistant()
        success = assistant.sync_candidates_from_file()
        assistant.close_connection()
        return success
    except Exception as e:
        logger.error(f"❌ Auto-sync failed: {e}")
        return False 