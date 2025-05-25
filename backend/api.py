"""
FastAPI Application for Team Compatibility Analyzer and Interview Manager

Provides REST API endpoints for:
- Creating and managing AI interviews
- Analyzing team compatibility
- Extracting personality traits
"""
import uvicorn
import os

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
import logging
from datetime import datetime

# Import our existing classes
from interview_manager import InterviewManager
from compatibility_analyzer import CompatibilityAnalyzer
from ai_assistant import AIAssistant, sync_candidates_auto

# Import models from separate file
from models import (
    CreateInterviewRequest, InterviewResponse, TranscriptResponse,
    CompatibilityAnalysisRequest, PersonalityExtractionRequest, HealthResponse, StatusResponse,
    CandidateQueryRequest, CandidateQueryResponse, CandidateResult, SyncRequest, SyncResponse, CandidateStatsResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
interview_manager = None
compatibility_analyzer = None
ai_assistant = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    global interview_manager, compatibility_analyzer, ai_assistant
    try:
        interview_manager = InterviewManager()
        compatibility_analyzer = CompatibilityAnalyzer()
        # AI assistant initialization is optional (requires Weaviate credentials)
        try:
            ai_assistant = AIAssistant()
            logger.info("✅ AI Assistant initialized successfully")
        except Exception as ai_e:
            logger.warning(f"⚠️ AI Assistant initialization failed: {ai_e}")
            ai_assistant = None
        logger.info("✅ API services initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        # Continue anyway, endpoints will handle errors
    
    yield
    
    # Shutdown
    if ai_assistant:
        ai_assistant.close_connection()
    logger.info("🔄 API shutting down")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Team Compatibility Analyzer API",
    description="API for AI interviews and team compatibility analysis",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health and Status Endpoints

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="API is running"
    )

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get API status and configuration."""
    # Get rate limit info safely
    rate_limit_info = {"requests_per_second": "unknown"}
    if compatibility_analyzer and hasattr(compatibility_analyzer, 'rate_limiter'):
        rate_limit_info["requests_per_second"] = compatibility_analyzer.rate_limiter.requests_per_second
    
    return StatusResponse(
        status="operational",
        api_version="1.0.0",
        interview_manager_available=interview_manager is not None,
        compatibility_analyzer_available=compatibility_analyzer is not None,
        ai_assistant_available=ai_assistant is not None,
        rate_limit_info=rate_limit_info
    )

# Interview Management Endpoints

@app.post("/interviews", response_model=InterviewResponse)
async def create_interview(request: CreateInterviewRequest):
    """Create a new AI interview."""
    if not interview_manager:
        raise HTTPException(status_code=503, detail="Interview manager not available")
    
    try:
        result = interview_manager.create_interview(
            candidate_name=request.candidate_name,
            role=request.role,
            candidate_email=request.candidate_email or ""
        )
        
        return InterviewResponse(**result)
        
    except Exception as e:
        logger.error(f"Error creating interview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create interview: {str(e)}")

@app.get("/interviews/{agent_id}/transcript", response_model=TranscriptResponse)
async def get_transcript(agent_id: str, candidate_name: str = None, role: str = None):
    """Get interview transcript for an agent."""
    if not interview_manager:
        raise HTTPException(status_code=503, detail="Interview manager not available")
    
    try:
        result = interview_manager.get_transcript(
            agent_id=agent_id,
            candidate_name=candidate_name,
            role=role
        )
        
        return TranscriptResponse(**result)
        
    except Exception as e:
        logger.error(f"Error retrieving transcript: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve transcript: {str(e)}")

@app.get("/interviews")
async def list_interviews():
    """List all interviews."""
    if not interview_manager:
        raise HTTPException(status_code=503, detail="Interview manager not available")
    
    try:
        interviews = interview_manager.list_all_interviews()
        return {"interviews": interviews}
        
    except Exception as e:
        logger.error(f"Error listing interviews: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list interviews: {str(e)}")

@app.get("/interviews/saved")
async def get_saved_interviews():
    """Get all saved interviews from the tracking file."""
    if not interview_manager:
        raise HTTPException(status_code=503, detail="Interview manager not available")
    
    try:
        saved_interviews = interview_manager.get_saved_interviews()
        return {
            "saved_interviews": saved_interviews,
            "count": len(saved_interviews)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving saved interviews: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve saved interviews: {str(e)}")

@app.get("/interviews/{agent_id}/transcript/download")
async def download_transcript(agent_id: str, filename: str = None):
    """Download transcript as a file."""
    if not interview_manager:
        raise HTTPException(status_code=503, detail="Interview manager not available")
    
    try:
        # Get the transcript first
        transcript_data = interview_manager.get_transcript(agent_id)
        
        if not transcript_data.get("success"):
            raise HTTPException(status_code=404, detail="No transcript found for this agent")
        
        # Generate the transcript content
        import json
        from fastapi.responses import Response
        
        # Create filename with timestamp if not provided
        if not filename:
            filename = f"transcript_{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Ensure filename ends with .json
        if not filename.endswith('.json'):
            filename += '.json'
        
        # Convert transcript data to JSON string
        transcript_json = json.dumps(transcript_data, indent=2, ensure_ascii=False)
        
        # Return as downloadable file
        return Response(
            content=transcript_json,
            media_type="application/octet-stream",  # Force download instead of display
            headers={
                "Content-Disposition": f"attachment; filename=\"{filename}\"",
                "Content-Length": str(len(transcript_json.encode('utf-8')))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error preparing transcript download: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to prepare transcript download: {str(e)}")

# Compatibility Analysis Endpoints

@app.post("/analysis/compatibility")
async def analyze_compatibility(request: CompatibilityAnalysisRequest):
    """Analyze team compatibility with candidates."""
    if not compatibility_analyzer:
        raise HTTPException(status_code=503, detail="Compatibility analyzer not available")
    
    try:
        # Convert Pydantic models to dictionaries using model_dump()
        team_data = request.team_data.model_dump()
        candidates_data_list = [{"candidate": candidate.model_dump()} for candidate in request.candidates_data.candidates]
        
        # Run the analysis directly with JSON data
        results = compatibility_analyzer.analyze_team_compatibility(
            team_data=team_data,
            candidates_data_list=candidates_data_list
        )
        
        # Save results to file before auto-sync
        try:
            # Use the same path resolution as AI assistant to ensure consistency
            data_file_path = os.getenv("COMPATIBILITY_SCORES_FILE")
            if data_file_path:
                output_file = data_file_path
            elif os.path.exists("/app/data/"):  # Docker path
                output_file = "/app/data/compatibility_scores.json"
            else:  # Local development path
                output_file = "data/compatibility_scores.json"
                # Ensure data directory exists for local development
                os.makedirs("data", exist_ok=True)
            
            compatibility_analyzer.save_results(results, output_file)
            logger.info(f"✅ Results saved to {output_file}")
        except Exception as save_e:
            logger.error(f"❌ Error saving results: {save_e}")
            # Continue with auto-sync even if save fails
        
        # Auto-sync candidates to Weaviate if AI assistant is available and auto-sync is enabled
        if ai_assistant and ai_assistant.auto_sync:
            try:
                logger.info("⏳ Waiting 2 seconds before auto-sync...")
                import asyncio
                await asyncio.sleep(2)  # Wait 2 seconds for file to be properly written
                logger.info("🔄 Auto-syncing candidates to Weaviate...")
                sync_success = ai_assistant.sync_candidates_from_file()
                if sync_success:
                    logger.info("✅ Auto-sync completed successfully")
                else:
                    logger.warning("⚠️ Auto-sync failed - check logs")
            except Exception as sync_e:
                logger.error(f"❌ Auto-sync error: {sync_e}")
                # Don't fail the analysis if sync fails
        
        return results
                    
    except Exception as e:
        logger.error(f"Error in compatibility analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze compatibility: {str(e)}")

@app.post("/analysis/personality-extract")
async def extract_personality(request: PersonalityExtractionRequest):
    """Extract personality traits from interview responses."""
    if not compatibility_analyzer:
        raise HTTPException(status_code=503, detail="Compatibility analyzer not available")
    
    try:
        # Use the personality extractor from the compatibility analyzer
        traits = compatibility_analyzer.traits_extractor.extract_from_responses(
            request.candidate_data.model_dump()
        )
        
        return {
            "success": True,
            "candidate_id": request.candidate_data.id,
            "candidate_name": request.candidate_data.name,
            "extracted_traits": traits
        }
        
    except Exception as e:
        logger.error(f"Error extracting personality traits: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract personality traits: {str(e)}")

# AI Assistant Endpoints

@app.post("/candidates/sync", response_model=SyncResponse)
async def sync_candidates(request: SyncRequest = None):
    """Sync candidates from compatibility_scores.json to Weaviate."""
    if not ai_assistant:
        raise HTTPException(status_code=503, detail="AI Assistant not available - check Weaviate configuration")
    
    try:
        # Determine file path
        file_path = request.file_path if request and request.file_path else None
        
        # Sync candidates
        success = ai_assistant.sync_candidates_from_file(file_path)
        
        if success:
            # Get stats to return count
            stats = ai_assistant.get_candidate_stats()
            candidates_synced = stats.get("total_candidates", 0)
            
            return SyncResponse(
                success=True,
                message=f"Successfully synced {candidates_synced} candidates to Weaviate",
                candidates_synced=candidates_synced,
                timestamp=datetime.now().isoformat()
            )
        else:
            return SyncResponse(
                success=False,
                message="Failed to sync candidates - check logs for details",
                timestamp=datetime.now().isoformat()
            )
            
    except Exception as e:
        logger.error(f"Error syncing candidates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync candidates: {str(e)}")

@app.post("/candidates/query", response_model=CandidateQueryResponse)
async def query_candidates(request: CandidateQueryRequest):
    """Query candidates using natural language."""
    if not ai_assistant:
        raise HTTPException(status_code=503, detail="AI Assistant not available - check Weaviate configuration")
    
    try:
        result = ai_assistant.query_candidates(request.query, request.limit)
        
        # Convert to response model format
        candidates = []
        for candidate in result.get("candidates", []):
            candidates.append(CandidateResult(**candidate))
        
        return CandidateQueryResponse(
            query=result["query"],
            results_count=result["results_count"],
            candidates=candidates,
            timestamp=result["timestamp"],
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error querying candidates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to query candidates: {str(e)}")

@app.get("/candidates/stats", response_model=CandidateStatsResponse)
async def get_candidate_stats():
    """Get statistics about candidates in the database."""
    if not ai_assistant:
        raise HTTPException(status_code=503, detail="AI Assistant not available - check Weaviate configuration")
    
    try:
        stats = ai_assistant.get_candidate_stats()
        
        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])
        
        return CandidateStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting candidate stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get candidate stats: {str(e)}")

@app.post("/ai/chat")
async def ai_chat(request: Dict[str, Any]):
    """Enhanced AI chat endpoint with candidate data access."""
    try:
        messages = request.get("messages", [])
        max_tokens = request.get("max_tokens", 800)
        temperature = request.get("temperature", 0.7)
        
        if not messages:
            raise HTTPException(status_code=400, detail="Messages are required")
        
        # Get the latest user message
        latest_message = messages[-1].get("content", "") if messages else ""
        
        # Check if the query is about candidates and if AI Assistant is available
        is_candidate_query = _is_candidate_related_query(latest_message)
        
        if is_candidate_query and ai_assistant:
            # Use AI Assistant for candidate-related queries
            try:
                candidate_results = ai_assistant.query_candidates(latest_message, limit=5)
                
                if candidate_results.get("results_count", 0) > 0:
                    # Format candidate data for conversational response
                    response_text = _format_candidate_response(latest_message, candidate_results)
                else:
                    # No candidates found, but provide helpful context
                    stats = ai_assistant.get_candidate_stats()
                    if stats.get("total_candidates", 0) > 0:
                        response_text = f"I couldn't find candidates matching '{latest_message}' specifically, but I have access to {stats['total_candidates']} candidates in the database. Try asking about specific traits like 'most outgoing', 'best team player', 'highest compatibility', or 'most creative' candidates."
                    else:
                        response_text = "I don't currently have any candidate data loaded. Please ensure candidate data has been synchronized to the AI Assistant database."
                
                return {
                    "response": response_text,
                    "success": True,
                    "source": "candidate_database"
                }
                
            except Exception as e:
                logger.warning(f"AI Assistant query failed, falling back to general chat: {e}")
                # Fall through to general chat
        
        # Use general AI chat (original functionality)
        if not compatibility_analyzer:
            raise HTTPException(status_code=503, detail="AI service not available")
        
        # Enhance the system message for better context
        enhanced_messages = _enhance_messages_for_context(messages, ai_assistant)
        
        # Get the model from environment
        model = os.getenv('MISTRAL_MODEL', 'mistral-small-latest')
        
        # Make the chat request using the existing AI client
        response = compatibility_analyzer.client.chat.complete(
            model=model,
            messages=enhanced_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        response_text = response.choices[0].message.content
        
        return {
            "response": response_text,
            "success": True,
            "source": "general_ai"
        }
        
    except Exception as e:
        logger.error(f"Error in AI chat: {e}")
        return {
            "response": "I'm sorry, I'm having trouble processing your request right now. Please try again later.",
            "success": False,
            "error": str(e)
        }

def _is_candidate_related_query(query: str) -> bool:
    """Detect if a query is about candidates."""
    candidate_keywords = [
        "candidate", "candidates", "applicant", "applicants", 
        "outgoing", "extraverted", "introvert", "creative", "organized",
        "team player", "collaborative", "leadership", "compatible",
        "personality", "traits", "scores", "recommendation",
        "who is", "which candidate", "best fit", "most suitable",
        "highest", "lowest", "compare", "rank", "top"
    ]
    
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in candidate_keywords)

def _format_candidate_response(query: str, candidate_results: Dict[str, Any]) -> str:
    """Format candidate query results into a conversational response."""
    candidates = candidate_results.get("candidates", [])
    results_count = candidate_results.get("results_count", 0)
    
    if results_count == 0:
        return "I couldn't find any candidates matching your query. Try asking about specific traits or characteristics."
    
    # Build conversational response
    response_parts = []
    
    if results_count == 1:
        candidate = candidates[0]
        response_parts.append(f"Based on your query, I found **{candidate['name']}** who seems to be the best match.")
    else:
        response_parts.append(f"Based on your query, here are the top {min(results_count, 3)} candidates:")
    
    # Add candidate details
    for i, candidate in enumerate(candidates[:3], 1):
        name = candidate.get("name", "Unknown")
        position = candidate.get("position", "Unknown Position")
        compatibility = candidate.get("compatibility_score", 0)
        recommendation = candidate.get("recommendation", "")
        
        # Get personality highlights
        traits = candidate.get("personality_traits", {})
        trait_highlights = []
        
        if traits.get("extraversion", 0) > 0.7:
            trait_highlights.append("very outgoing and social")
        if traits.get("openness", 0) > 0.7:
            trait_highlights.append("highly creative and open to new ideas")
        if traits.get("conscientiousness", 0) > 0.7:
            trait_highlights.append("extremely organized and reliable")
        if traits.get("agreeableness", 0) > 0.7:
            trait_highlights.append("excellent team player")
        
        if results_count == 1:
            response_parts.append(f"\n**{name}** ({position})")
        else:
            response_parts.append(f"\n{i}. **{name}** ({position})")
        
        response_parts.append(f"   - Compatibility Score: {compatibility:.1%}")
        response_parts.append(f"   - Recommendation: {recommendation}")
        
        if trait_highlights:
            response_parts.append(f"   - Key Traits: {', '.join(trait_highlights)}")
        
        # Add LLM reasoning if available
        if candidate.get("relevance_reasoning"):
            response_parts.append(f"   - Why they match: {candidate['relevance_reasoning']}")
    
    # Add summary
    if results_count > 3:
        response_parts.append(f"\n*({results_count - 3} more candidates available - ask for more specific criteria to narrow down results)*")
    
    return "\n".join(response_parts)

def _enhance_messages_for_context(messages: List[Dict], ai_assistant) -> List[Dict]:
    """Enhance messages with context about available data."""
    enhanced_messages = []
    
    # Add system context
    context_info = []
    
    if ai_assistant:
        try:
            stats = ai_assistant.get_candidate_stats()
            if stats.get("total_candidates", 0) > 0:
                context_info.append(f"You have access to {stats['total_candidates']} candidates with detailed personality and compatibility data.")
                
                if stats.get("recommendations_distribution"):
                    rec_dist = stats["recommendations_distribution"]
                    context_info.append(f"Recommendation distribution: {rec_dist}")
            else:
                context_info.append("No candidate data is currently available.")
        except:
            context_info.append("Candidate database access is limited.")
    else:
        context_info.append("You are a general HR and team compatibility assistant.")
    
    # Create enhanced system message
    system_message = {
        "role": "system",
        "content": f"""You are an expert HR assistant specializing in team compatibility and candidate analysis. 

{' '.join(context_info)}

You help with:
- Candidate evaluation and comparison
- Team compatibility analysis  
- Personality trait interpretation
- Hiring recommendations
- Interview insights

Be helpful, professional, and data-driven in your responses."""
    }
    
    enhanced_messages.append(system_message)
    enhanced_messages.extend(messages)
    
    return enhanced_messages

# Error handlers

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return HTTPException(status_code=400, detail=str(exc))

@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request, exc):
    return HTTPException(status_code=404, detail=str(exc))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 