"""
Beyond Presence Interview Manager

A clean, modular interface for creating AI interviews and retrieving transcripts.
"""

import requests
import os
import json
import re
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv


class InterviewManager:
    """
    Simplified interface for Beyond Presence AI interviews.
    
    Main methods:
    - create_interview(): Create an interview and get the link
    - get_transcript(): Get the interview transcript
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Interview Manager.
        
        Args:
            api_key: Beyond Presence API key (optional, will use .env if not provided)
        """
        # Load environment variables
        load_dotenv()
        
        # Configuration
        self.api_key = api_key or os.getenv("BEYOND_PRESENCE_API_KEY")
        self.avatar_id = os.getenv("DEFAULT_AVATAR_ID", "b9be11b8-89fb-4227-8f86-4a881393cbdb")
        self.session_length = int(os.getenv("DEFAULT_SESSION_LENGTH_MINUTES", "5"))
        self.language = os.getenv("DEFAULT_LANGUAGE", "en")
        self.base_url = "https://api.bey.dev/v1"
        self.chat_url = "https://bey.chat"
        
        # Store candidate info for transcript formatting
        self._candidate_info = {}
        
        if not self.api_key:
            raise ValueError("API key is required. Provide it or set BEYOND_PRESENCE_API_KEY in .env file")
    
    def create_interview(
        self, 
        candidate_name: str, 
        role: str, 
        candidate_email: str = ""
    ) -> Dict[str, Any]:
        """
        Create an interview agent and return the interview link.
        
        Args:
            candidate_name: Name of the candidate
            role: Job role they're applying for
            candidate_email: Email address (optional)
            
        Returns:
            Dictionary with agent_id, interview_link, and agent details
        """
        print(f"🚀 Creating interview for {candidate_name} - {role}")
        
        # Create the agent
        agent = self._create_agent(candidate_name, role, candidate_email)
        agent_id = agent["id"]
        
        # Store candidate info for later use in transcript formatting
        self._candidate_info[agent_id] = {
            "name": candidate_name,
            "position": role,
            "email": candidate_email
        }
        
        # Generate interview link
        interview_link = f"{self.chat_url}/{agent_id}"
        
        result = {
            "agent_id": agent_id,
            "interview_link": interview_link,
            "candidate_name": candidate_name,
            "role": role,
            "agent_details": agent
        }
        
        print(f"✅ Interview created successfully!")
        print(f"📧 Send this link to {candidate_name}: {interview_link}")
        
        return result
    
    def get_transcript(self, agent_id: str, candidate_name: str = None, role: str = None) -> Dict[str, Any]:
        """
        Get the latest interview transcript for an agent.
        
        Args:
            agent_id: The ID of the agent
            candidate_name: Name of the candidate (optional, will try to retrieve from stored info)
            role: Role of the candidate (optional, will try to retrieve from stored info)
            
        Returns:
            Dictionary containing the formatted transcript and metadata
        """
        print(f"📄 Retrieving transcript for agent: {agent_id}")
        
        try:
            # Get candidate info (from parameters or stored info)
            if agent_id in self._candidate_info:
                candidate_info = self._candidate_info[agent_id]
            else:
                candidate_info = {
                    "name": candidate_name or "Unknown Candidate",
                    "position": role or "Unknown Position",
                    "email": ""
                }
            
            # Get the latest call for this agent
            agent_calls = self._get_calls_for_agent(agent_id)
            
            if not agent_calls:
                return {
                    "success": False,
                    "error": "No interviews found for this agent",
                    "agent_id": agent_id,
                    "transcript": {}
                }
            
            # Get the most recent call
            latest_call = max(agent_calls, key=lambda x: x.get("started_at", ""))
            call_id = latest_call["id"]
            
            # Get the transcript
            messages = self._get_call_messages(call_id)
            formatted_transcript = self._format_transcript(latest_call, messages, candidate_info)
            
            result = {
                "success": True,
                "agent_id": agent_id,
                "call_id": call_id,
                "call_info": latest_call,
                "messages": messages,
                "formatted_transcript": formatted_transcript,
                "message_count": len(messages)
            }
            
            print(f"✅ Retrieved transcript with {len(messages)} messages")
            return result
            
        except Exception as e:
            print(f"❌ Error retrieving transcript: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent_id,
                "transcript": {}
            }
    
    def save_transcript(self, transcript_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Save the transcript to a file.
        
        Args:
            transcript_data: Result from get_transcript()
            filename: Custom filename (optional)
            
        Returns:
            Path to the saved file
        """
        if not transcript_data.get("success"):
            raise ValueError("Cannot save transcript - no valid data provided")
        
        if not filename:
            agent_id = transcript_data["agent_id"]
            call_id = transcript_data["call_id"]
            filename = f"interview_transcript_{agent_id}_{call_id}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(transcript_data["formatted_transcript"], f, indent=2, ensure_ascii=False)
        
        print(f"💾 Transcript saved to: {filename}")
        return filename
    
    def list_all_interviews(self) -> List[Dict[str, Any]]:
        """
        List all interviews (calls) across all agents.
        
        Returns:
            List of all call information
        """
        try:
            calls = self._get_all_calls()
            print(f"📋 Found {len(calls)} total interviews")
            return calls
        except Exception as e:
            print(f"❌ Error listing interviews: {e}")
            return []
    
    # Private helper methods
    def _create_agent(self, candidate_name: str, role: str, candidate_email: str = "") -> Dict[str, Any]:
        """Create an interview agent via the API."""
        candidate_info = f"Candidate Name: {candidate_name}\nRole: {role}"
        if candidate_email:
            candidate_info += f"\nEmail: {candidate_email}"
        
        system_prompt = self._generate_system_prompt(candidate_info)
        
        payload = {
            "avatar_id": self.avatar_id,
            "system_prompt": system_prompt,
            "name": f"{candidate_name}'s Interview Agent",
            "language": self.language,
            "max_session_length_minutes": self.session_length,
            "capabilities": [
                "webcam_vision"
            ],
            "greeting": f"Hello {candidate_name}! Welcome to your interview for the {role} position. I'm Maki, your AI interviewer today."
        }
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        response = requests.post(f"{self.base_url}/agent", headers=headers, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def _get_all_calls(self) -> List[Dict[str, Any]]:
        """Get all calls from the API."""
        headers = {"x-api-key": self.api_key}
        response = requests.get(f"{self.base_url}/calls", headers=headers)
        response.raise_for_status()
        return response.json()
    
    def _get_calls_for_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all calls for a specific agent."""
        all_calls = self._get_all_calls()
        return [call for call in all_calls if call.get("agent_id") == agent_id]
    
    def _get_call_messages(self, call_id: str) -> List[Dict[str, Any]]:
        """Get messages from a specific call."""
        headers = {"x-api-key": self.api_key}
        response = requests.get(f"{self.base_url}/calls/{call_id}/messages", headers=headers)
        response.raise_for_status()
        return response.json()
    
    def _format_transcript(self, call_info: Dict[str, Any], messages: List[Dict[str, Any]], candidate_info: Dict[str, Any]) -> Dict[str, Any]:
        """Format the transcript into JSON structure."""
        
        # Parse messages into question-answer pairs
        responses = []
        current_question = None
        
        for message in messages:
            sender = message.get("sender", "unknown")
            content = message.get("message", "").strip().replace('\\', '').replace('"', '')
            
            if sender == "ai" and content:
                current_question = content
            elif sender == "user" and content:
                responses.append({
                    "question": current_question,
                    "answer": content
                })
                current_question = None  # Reset for next Q&A pair
        
        # Generate candidate ID from name and position
        candidate_id = self._generate_candidate_id(candidate_info["name"], candidate_info["position"])
        
        # Structure the transcript according to the required format
        transcript = {
            "candidate": {
                "id": candidate_id,
                "name": candidate_info["name"],
                "position": candidate_info["position"],
                "responses": responses
            }
        }
        
        return transcript

    
    def _generate_candidate_id(self, name: str, position: str) -> str:
        """Generate a candidate ID from name and position."""
        # Simple ID generation: first letters of names + position abbreviation
        name_parts = name.split()
        initials = "".join([part[0].upper() for part in name_parts if part])
        
        # Position abbreviation
        if "software" in position.lower() or "engineer" in position.lower():
            pos_abbrev = "SE"
        elif "data" in position.lower():
            pos_abbrev = "DS"
        elif "product" in position.lower():
            pos_abbrev = "PM"
        elif "design" in position.lower():
            pos_abbrev = "DES"
        else:
            pos_abbrev = "GEN"
        
        return f"{pos_abbrev}{initials}"
    
    def _generate_system_prompt(self, candidate_information: str) -> str:
        """Generate the system prompt for the AI interviewer."""

        return f"""
You are 'Maki AI Recruiter', an advanced, autonomous AI interview agent specializing in technical talent
            assessment, focusing on soft skills and team compatibility.
            Your goal is to conduct a professional, engaging, and in-depth video interview.

            **Candidate Information:**
            {candidate_information}
            **Your Core Objectives:**
            1.  **Personalized Greeting:** Start by warmly greeting the candidate by their name and acknowledging the role they've applied for.
            2.  **Build Rapport:** Maintain a professional yet friendly and empathetic tone throughout the interview.
            3.  **Adaptive Questioning:** Your primary task is to elicit responses that allow for a comprehensive 
                psychological profile (specifically the Big Five personality traits) and soft skill assessment.
                You have access to a `KNOWLEDGE_BANK_QUESTIONS` and should strategically choose questions based on the flow
                of conversation and what you still need to learn about the candidate's personality and soft skills.
            4.  **Deep Dive & Follow-ups:** Ask insightful follow-up questions to probe deeper into responses, focusing
                on behavioral examples and specific situations (e.g., 'Tell me more about that experience,'
                'How did you handle that specific challenge?').
            5.  **Cover All Traits:** Ensure you gather sufficient information to infer all five Big Five traits:
                Openness, Conscientiousness, Extraversion, Agreeableness, and Neuroticism (Emotional Stability).
                Focus on examples that demonstrate these traits in a professional context.
            6.  **Situational Judgment:** Incorporate situational judgment questions to assess problem-solving,
                ethical reasoning, and teamwork in hypothetical scenarios.
            7.  **Consistent Information Gathering:** While adaptive, ensure the interview covers enough ground across all
                soft skill and personality dimensions to provide consistent data for the final output.
                Aim for a balanced set of questions across different personality aspects.
            8.  **Interview Conclusion:** Clearly signal the end of the interview and thank the candidate for their time.

            **KNOWLEDGE_BANK_QUESTIONS:**
            [
                {{
                    "trait": "Openness to Experience",
                    "type": "behavioral",
                    "questions": [
                        "Tell me about a time you embraced a new technology or approach at work. What was the outcome?",
                        "How do you stay current with new trends and ideas in your field?",
                        "Describe a situation where you had to think outside the box to solve a problem.",
                        "What's a new skill or hobby you've pursued recently, and what motivated you?"
                    ]
                }},
                {{
                    "trait": "Conscientiousness",
                    "type": "behavioral",
                    "questions": [
                        "Describe a project where you had to manage multiple tasks or priorities. How did you ensure everything was completed on time and to a high standard?",
                        "Walk me through your typical approach to planning and organizing your work.",
                        "Tell me about a time you made a mistake at work. How did you handle it and what did you learn?",
                        "How do you ensure accuracy and attention to detail in your work?"
                    ]
                }},
                {{
                    "trait": "Extraversion",
                    "type": "behavioral",
                    "questions": [
                        "How do you typically contribute in team meetings or group discussions?",
                        "Describe a situation where you had to persuade or influence others. What was your approach?",
                        "How do you prefer to collaborate with colleagues on a project?",
                        "Tell me about a time you took on a leadership role or initiated a group activity."
                    ]
                }},
                {{
                    "trait": "Agreeableness",
                    "type": "behavioral",
                    "questions": [
                        "Describe a time you had a disagreement with a colleague. How did you resolve it?",
                        "How do you typically approach working with others from different backgrounds or with different working styles?",
                        "Tell me about a time you went out of your way to help a team member. What was the impact?",
                        "How do you build and maintain positive relationships with your colleagues?"
                    ]
                }},
                {{
                    "trait": "Neuroticism (Emotional Stability)",
                    "type": "behavioral",
                    "questions": [
                        "Tell me about a time you faced significant pressure or stress at work. How did you manage it?",
                        "Describe a situation where a project didn't go as planned. How did you react and what did you do next?",
                        "How do you typically handle constructive criticism or negative feedback?",
                        "What strategies do you use to maintain a positive outlook, even when facing challenges?"
                    ]
                }},
                {{
                    "trait": "General Soft Skills",
                    "type": "situational",
                    "questions": [
                        "Imagine you're leading a project, and half your team is unexpectedly pulled onto another critical task. How would you adjust your plan to ensure the project still meets its deadline?",
                        "You discover a critical bug in a system right before launch, but fixing it will delay the release. What steps do you take, and who do you communicate with?",
                        "A team member consistently misses deadlines, impacting your progress. You've spoken to them before, but the issue persists. How do you address this now?",
                        "You receive conflicting instructions from two different managers on the same task. How do you proceed?"
                    ]
                }},
                {{
                    "trait": "Custom Culture Fit",
                    "type": "custom",
                    "questions": [
                        "What aspects of a team environment help you perform your best?",
                        "How do you prefer to receive feedback, and how do you give it?",
                        "Describe your ideal team dynamic.",
                        "What's one thing you appreciate most about your previous team experiences?"
                    ]
                }}
            ]

            **Interview State (for internal use by agent - do not directly reveal to candidate):**
            - Questions asked so far: []
            - Traits covered: []
            - Remaining questions to cover: [All questions initially from KNOWLEDGE_BANK_QUESTIONS]

            Remember to keep the conversation natural and human-like.
            Your primary directive is to gather rich, detailed responses related to the candidate's professional behaviors
            and decision-making, which will inform their personality profile."
        """