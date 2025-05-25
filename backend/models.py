"""
Pydantic Models for Team Compatibility Analyzer API

Contains all request/response models for API validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

# Interview Management Models

class CreateInterviewRequest(BaseModel):
    candidate_name: str = Field(..., description="Name of the candidate")
    role: str = Field(..., description="Job role they're applying for")
    candidate_email: Optional[str] = Field(None, description="Email address (optional)")

class InterviewResponse(BaseModel):
    agent_id: str
    interview_link: str
    candidate_name: str
    role: str
    agent_details: Dict[str, Any]

class TranscriptRequest(BaseModel):
    candidate_name: Optional[str] = None
    role: Optional[str] = None

class TranscriptResponse(BaseModel):
    success: bool
    agent_id: str
    call_id: Optional[str] = None
    call_info: Optional[Dict[str, Any]] = None
    messages: Optional[List[Dict[str, Any]]] = None
    formatted_transcript: Optional[Dict[str, Any]] = None
    message_count: Optional[int] = None
    error: Optional[str] = None

# Team and Candidate Models

class TeamMember(BaseModel):
    id: str
    name: str
    position: str
    big_five: Optional[Dict[str, float]] = None
    personality_traits: Optional[Dict[str, float]] = None

class TeamData(BaseModel):
    team: List[TeamMember]

class CandidateResponse(BaseModel):
    question: str
    answer: str
    trait: Optional[str] = None

class Candidate(BaseModel):
    id: str
    name: str
    position: str
    big_five: Optional[Dict[str, float]] = None
    personality_traits: Optional[Dict[str, float]] = None
    responses: Optional[List[CandidateResponse]] = None
    interview_responses: Optional[List[CandidateResponse]] = None

class CandidatesData(BaseModel):
    candidates: List[Candidate]

# Analysis Models

class CompatibilityAnalysisRequest(BaseModel):
    team_data: TeamData
    candidates_data: CandidatesData

class PersonalityExtractionRequest(BaseModel):
    candidate_data: Candidate

# Utility Models

class HealthResponse(BaseModel):
    status: str
    message: str

class StatusResponse(BaseModel):
    status: str
    api_version: str
    interview_manager_available: bool
    compatibility_analyzer_available: bool
    ai_assistant_available: bool
    rate_limit_info: Dict[str, Any]

# AI Assistant Models

class CandidateQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query about candidates")
    limit: Optional[int] = Field(5, description="Maximum number of results to return")

class PersonalityTraits(BaseModel):
    openness: Optional[float] = None
    conscientiousness: Optional[float] = None
    extraversion: Optional[float] = None
    agreeableness: Optional[float] = None
    neuroticism: Optional[float] = None

class CandidateResult(BaseModel):
    name: str
    position: str
    candidate_id: str
    compatibility_score: float
    recommendation: str
    summary: str
    strengths: List[str]
    concerns: List[str]
    personality_traits: PersonalityTraits
    relevance_score: Optional[float] = None

class CandidateQueryResponse(BaseModel):
    query: str
    results_count: int
    candidates: List[CandidateResult]
    timestamp: str
    error: Optional[str] = None

class SyncRequest(BaseModel):
    file_path: Optional[str] = Field(None, description="Path to compatibility scores file (optional)")

class SyncResponse(BaseModel):
    success: bool
    message: str
    candidates_synced: Optional[int] = None
    timestamp: str

class CandidateStatsResponse(BaseModel):
    total_candidates: int
    recommendations_distribution: Dict[str, Any]
    collection_name: str
    timestamp: str
    error: Optional[str] = None 