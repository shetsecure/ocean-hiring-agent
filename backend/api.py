"""
FastAPI Application for Team Compatibility Analyzer and Interview Manager

Provides REST API endpoints for:
- Creating and managing AI interviews
- Analyzing team compatibility
- Extracting personality traits
"""
import uvicorn

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import logging
from datetime import datetime

# Import our existing classes
from interview_manager import InterviewManager
from compatibility_analyzer import CompatibilityAnalyzer

# Import models from separate file
from models import (
    CreateInterviewRequest, InterviewResponse, TranscriptResponse,
    CompatibilityAnalysisRequest, PersonalityExtractionRequest, HealthResponse, StatusResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
interview_manager = None
compatibility_analyzer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    global interview_manager, compatibility_analyzer
    try:
        interview_manager = InterviewManager()
        compatibility_analyzer = CompatibilityAnalyzer()
        logger.info("✅ API services initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        # Continue anyway, endpoints will handle errors
    
    yield
    
    # Shutdown (if needed)
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

# Error handlers

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return HTTPException(status_code=400, detail=str(exc))

@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request, exc):
    return HTTPException(status_code=404, detail=str(exc))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 