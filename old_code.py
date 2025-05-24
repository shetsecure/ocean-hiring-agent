import requests
import json
import numpy as np # For numerical operations on Big Five vectors
from scipy.spatial.distance import cosine # For compatibility score

# --- Configuration (Load from environment variables in a real app) ---
BEYOND_PRESENCE_API_KEY = "your_bp_api_key"
MISTRAL_API_KEY = "your_mistral_api_key"
ELEVENLABS_API_KEY = "your_elevenlabs_api_key"
WEAVIATE_URL = "your_weaviate_instance_url" # e.g., "http://localhost:8080"

# --- Define the BFI-10 scoring mapping (simplified example) ---
# This would map trait descriptions to item numbers for automated scoring later
# Example: 1-Strongly Disagree, 5-Strongly Agree
# BFI-10 item mapping (from reliable source like John, Naumann, Soto, 2008)
BFI_10_ITEMS = {
    "Extraversion": {
        "positive": [1], # e.g., 'Is outgoing, sociable'
        "negative": [6]  # e.g., 'Is reserved' (reversed scored)
    },
    "Agreeableness": {
        "positive": [2], # e.g., 'Is compassionate, softhearted'
        "negative": [7]  # e.g., 'Tends to be rude' (reversed scored)
    },
    "Conscientiousness": {
        "positive": [3], # e.g., 'Tends to be disorganized' (reversed scored)
        "negative": [8]  # e.g., 'Does a thorough job'
    },
    "Neuroticism": { # Often called Emotional Stability, reversed for Neuroticism
        "positive": [4], # e.g., 'Is relaxed, handles stress well' (reversed for N)
        "negative": [9]  # e.g., 'Gets nervous easily'
    },
    "Openness to Experience": {
        "positive": [5], # e.g., 'Is curious, has wide interests'
        "negative": [10] # e.g., 'Has few artistic interests' (reversed scored)
    }
}


def calculate_big5_from_bfi10(bfi10_scores):
    """
    Calculates Big Five scores from BFI-10 item scores.
    Assumes bfi10_scores is a dict {item_number: score (1-5)}
    """
    big5_result = {}
    for trait, items in BFI_10_ITEMS.items():
        trait_score = 0
        count = 0
        for item_num in items.get("positive", []):
            if item_num in bfi10_scores:
                trait_score += bfi10_scores[item_num]
                count += 1
        for item_num in items.get("negative", []):
            if item_num in bfi10_scores:
                trait_score += (6 - bfi10_scores[item_num]) # Reverse scoring (6-score for 1-5 scale)
                count += 1
        big5_result[trait] = (trait_score / count) if count > 0 else 0 # Average score for trait
    return big5_result

def calculate_compatibility_score(candidate_big5_vector, team_big5_vectors):
    """
    Calculates compatibility score based on the provided formula.
    candidate_big5_vector: numpy array of [O, C, E, A, N]
    team_big5_vectors: list of numpy arrays for each team member
    """
    if not team_big5_vectors:
        return 0, 0, 0, 0, 0 # No team to compare against

    team_avg_vector = np.mean(team_big5_vectors, axis=0)

    # 1. Similarity Index (using Cosine Similarity)
    # Cosine similarity measures angle between vectors; 1 is perfectly similar, 0 is orthogonal, -1 is opposite
    similarity_index = 1 - cosine(candidate_big5_vector, team_avg_vector) if np.linalg.norm(candidate_big5_vector) > 0 and np.linalg.norm(team_avg_vector) > 0 else 0


    # 2. Complementarity Bonus
    # This is more nuanced. A simple approach: identify traits where the team average is low
    # and the candidate is high (and vice-versa for 'N' - low N is good)
    complementarity_bonus = 0
    # Example: if team is low in Extraversion (e.g., avg < 0.4 on 0-1 scale) and candidate is high (e.g., > 0.6)
    # Scale Big5 scores to 0-1 for easier comparison if not already.
    scaled_candidate = candidate_big5_vector / 100 # Assuming 0-100 scale input
    scaled_team_avg = team_avg_vector / 100

    # Define thresholds for "low" and "high" traits for complementarity
    LOW_THRESHOLD = 0.4
    HIGH_THRESHOLD = 0.6

    # Openness: Good if candidate is high and team is low
    if scaled_team_avg[0] < LOW_THRESHOLD and scaled_candidate[0] > HIGH_THRESHOLD:
        complementarity_bonus += 0.1
    # Conscientiousness: Good if candidate is high and team is low (less common use case for comp)
    # Extraversion: Good if candidate is high and team is low
    if scaled_team_avg[2] < LOW_THRESHOLD and scaled_candidate[2] > HIGH_THRESHOLD:
        complementarity_bonus += 0.1
    # Agreeableness: Good if candidate is high and team is low
    if scaled_team_avg[3] < LOW_THRESHOLD and scaled_candidate[3] > HIGH_THRESHOLD:
        complementarity_bonus += 0.1
    # Neuroticism (Emotional Stability): Good if candidate is *low* and team is high in N (or low in ES)
    # Assuming Neuroticism is high score = more neurotic, low score = more stable
    if scaled_team_avg[4] > HIGH_THRESHOLD and scaled_candidate[4] < LOW_THRESHOLD:
        complementarity_bonus += 0.1

    # 3. Friction Risk
    # High deltas on Neuroticism (Emotional Stability) or Agreeableness = tension risk
    # Higher difference means higher risk. Max difference on a 0-100 scale is 100.
    friction_risk = 0
    # Difference in Neuroticism (Absolute difference)
    friction_risk += abs(scaled_candidate[4] - scaled_team_avg[4]) * 0.5 # Give more weight to N diff
    # Difference in Agreeableness (Absolute difference)
    friction_risk += abs(scaled_candidate[3] - scaled_team_avg[3]) * 0.25 # Less weight than N

    # Normalize friction risk to a reasonable range (e.g., 0 to 1, or 0 to 0.5 bonus deduction)
    friction_risk = min(friction_risk, 0.5) # Cap max risk deduction

    # 4. Custom Culture Fit Questions (This would be based on analysis of specific Q&A)
    # For hackathon, this might be a placeholder or a simple keyword match from a specific "culture fit" question.
    custom_culture_fit_bonus = 0.05 # Placeholder for now, refine based on actual answers analysis

    # Apply a weighted compatibility formula:
    compatibility_score = (
        0.4 * similarity_index +
        0.3 * complementarity_bonus -
        0.2 * friction_risk +
        0.1 * custom_culture_fit_bonus
    )

    # Normalize the final score to be a percentage (0-100)
    # This formula outputs values often between -0.5 and 1.0. We can scale it.
    # A simple linear scaling to 0-100: (score + 1) / 2 * 100
    compatibility_score_percent = max(0, min(100, (compatibility_score + 0.5) * 100)) # Adjust based on actual formula output range

    return compatibility_score_percent, similarity_index, complementarity_bonus, friction_risk, custom_culture_fit_bonus


def get_team_profiles_from_weaviate(team_id):
    """
    Fetches Big Five profiles of existing team members from Weaviate.
    (Placeholder - actual Weaviate query would be here)
    Returns a list of numpy arrays, e.g., [[O,C,E,A,N], [O,C,E,A,N], ...]
    """
    # Dummy data for demonstration
    if team_id == "dev_team_alpha":
        return [
            np.array([70, 85, 60, 75, 30]), # O, C, E, A, N (N is low for stability)
            np.array([65, 80, 55, 70, 25]),
            np.array([75, 90, 65, 80, 35])
        ]
    return []

def your_backend_interview_trigger(candidate_data, team_id_for_compatibility):
    """
    Main function to trigger the interview and get the consolidated output.
    """
    candidate_name = candidate_data.get("name", "Valued Candidate")
    applied_role = candidate_data.get("role", "Technical Role")
    candidate_skills = candidate_data.get("skills", [])

    # 1. Prepare Beyond Presence System Prompt
    bp_system_prompt = json.dumps({
        "system_prompt": """
            You are 'Maki AI Recruiter', an advanced, autonomous AI interview agent specializing in technical talent
            assessment, focusing on soft skills and team compatibility.
            Your goal is to conduct a professional, engaging, and in-depth video interview.

            **Candidate Information:**
            - Name: {candidate_name}
            - Applied Role: {applied_role}
            - Key Skills: {candidate_skills}

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
            """ + json.dumps([
                {
                    "trait": "Openness to Experience",
                    "type": "behavioral",
                    "questions": [
                        "Tell me about a time you embraced a new technology or approach at work. What was the outcome?",
                        "How do you stay current with new trends and ideas in your field?",
                        "Describe a situation where you had to think outside the box to solve a problem.",
                        "What's a new skill or hobby you've pursued recently, and what motivated you?"
                    ]
                },
                {
                    "trait": "Conscientiousness",
                    "type": "behavioral",
                    "questions": [
                        "Describe a project where you had to manage multiple tasks or priorities. How did you ensure everything was completed on time and to a high standard?",
                        "Walk me through your typical approach to planning and organizing your work.",
                        "Tell me about a time you made a mistake at work. How did you handle it and what did you learn?",
                        "How do you ensure accuracy and attention to detail in your work?"
                    ]
                },
                {
                    "trait": "Extraversion",
                    "type": "behavioral",
                    "questions": [
                        "How do you typically contribute in team meetings or group discussions?",
                        "Describe a situation where you had to persuade or influence others. What was your approach?",
                        "How do you prefer to collaborate with colleagues on a project?",
                        "Tell me about a time you took on a leadership role or initiated a group activity."
                    ]
                },
                {
                    "trait": "Agreeableness",
                    "type": "behavioral",
                    "questions": [
                        "Describe a time you had a disagreement with a colleague. How did you resolve it?",
                        "How do you typically approach working with others from different backgrounds or with different working styles?",
                        "Tell me about a time you went out of your way to help a team member. What was the impact?",
                        "How do you build and maintain positive relationships with your colleagues?"
                    ]
                },
                {
                    "trait": "Neuroticism (Emotional Stability)",
                    "type": "behavioral",
                    "questions": [
                        "Tell me about a time you faced significant pressure or stress at work. How did you manage it?",
                        "Describe a situation where a project didn't go as planned. How did you react and what did you do next?",
                        "How do you typically handle constructive criticism or negative feedback?",
                        "What strategies do you use to maintain a positive outlook, even when facing challenges?"
                    ]
                },
                {
                    "trait": "General Soft Skills",
                    "type": "situational",
                    "questions": [
                        "Imagine you're leading a project, and half your team is unexpectedly pulled onto another critical task. How would you adjust your plan to ensure the project still meets its deadline?",
                        "You discover a critical bug in a system right before launch, but fixing it will delay the release. What steps do you take, and who do you communicate with?",
                        "A team member consistently misses deadlines, impacting your progress. You've spoken to them before, but the issue persists. How do you address this now?",
                        "You receive conflicting instructions from two different managers on the same task. How do you proceed?"
                    ]
                },
                {
                    "trait": "Custom Culture Fit",
                    "type": "custom",
                    "questions": [
                        "What aspects of a team environment help you perform your best?",
                        "How do you prefer to receive feedback, and how do you give it?",
                        "Describe your ideal team dynamic.",
                        "What's one thing you appreciate most about your previous team experiences?"
                    ]
                }
            ]) + """

            **Interview State (for internal use by agent - do not directly reveal to candidate):**
            - Questions asked so far: []
            - Traits covered: []
            - Remaining questions to cover: [All questions initially from KNOWLEDGE_BANK_QUESTIONS]

            Remember to keep the conversation natural and human-like.
            Your primary directive is to gather rich, detailed responses related to the candidate's professional behaviors
            and decision-making, which will inform their comprehensive profile."
        """.format(
            candidate_name=candidate_name,
            applied_role=applied_role,
            candidate_skills=", ".join(candidate_skills) if candidate_skills else "not provided"
        )
    )

    # 2. Call Beyond Presence API to start interview
    try:
        # This is a placeholder for actual Beyond Presence API call
        # You'll need to consult their API documentation for the exact endpoint and payload.
        # It might involve creating an agent, setting its prompt, and getting an interview URL.
        # For a hackathon, you might just get a 'demo' agent URL and manually conduct.
        bp_response = requests.post(
            "https://api.beyondpresence.ai/v1/interviews/create", # Example URL
            headers={"Authorization": f"Bearer {BEYOND_PRESENCE_API_KEY}", "Content-Type": "application/json"},
            json={
                "agent_id": "maki_recruiter_agent_id", # Or create a new one dynamically
                "system_prompt": bp_system_prompt,
                "candidate_name": candidate_name, # Pass separately if BP supports it
                "metadata": {"candidate_id": candidate_data.get("id")}
            }
        )
        bp_response.raise_for_status()
        interview_details = bp_response.json()
        interview_url = interview_details.get("interview_url")
        # In a real scenario, you'd send this URL to the candidate.
        print(f"Interview started. Share this URL with candidate: {interview_url}")

        # For the hackathon demo, you might need a way to *wait* for the interview to finish,
        # or use webhooks if Beyond Presence supports them, to get the transcript.
        # For a quick demo, you might manually paste a pre-recorded transcript.
        # Let's assume for now, we simulate getting a transcript after the interview.

        # --- SIMULATE GETTING TRANSCRIPT ---
        # In a real scenario, you'd get this via webhook or polling Beyond Presence for completion.
        simulated_transcript = """
        AI: Hello, {candidate_name}! Thank you for joining us today for the {applied_role} position.
        Candidate: Hi! Thanks for having me.
        AI: Great. Let's start with your experience. Tell me about a time you embraced a new technology or approach at work. What was the outcome?
        Candidate: Sure. In my previous role at XYZ Corp, we were still using an outdated SQL database. I proposed migrating to a NoSQL solution, specifically MongoDB, for our new project. It was a big learning curve for the team, but I led a few internal workshops. The outcome was significant: our data processing time decreased by 40%, and development cycles became much faster. It was challenging, but very rewarding.
        AI: That sounds like a significant improvement. How did you convince your team to adopt such a new approach, especially with an outdated system already in place?
        Candidate: I started by presenting the clear benefits – faster queries, better scalability for our growing data. Then, I put together a small proof-of-concept. Seeing it in action, and understanding the future-proofing aspects, helped get everyone on board. Some resistance was there initially, but showing rather than just telling made a big difference.
        AI: Excellent. Now, let's talk about planning. Describe a project where you had to manage multiple tasks or priorities. How did you ensure everything was completed on time and to a high standard?
        Candidate: Last year, I was juggling two major client projects simultaneously. One involved a new e-commerce platform, and the other was a complex data analytics dashboard. I used Agile methodologies, breaking down tasks into smaller sprints, and relied heavily on Jira for tracking. Daily stand-ups ensured everyone was aligned. I also blocked out dedicated focus time for each project and communicated proactively with stakeholders if any potential delays arose. Prioritization was key, and I always aimed for quality over speed, even if it meant working a bit extra.
        AI: That's a very structured approach. And how do you ensure accuracy and attention to detail in your work, especially when juggling multiple high-stakes projects?
        Candidate: For critical components, I always implement robust unit and integration tests. Peer code reviews are also non-negotiable for me – a second pair of eyes often catches what you might miss. I also have a personal checklist for deployments and major releases to ensure all prerequisites are met. I believe that prevention is better than cure, so I focus on getting it right the first time.
        AI: Fascinating. Let's shift gears slightly. How do you typically contribute in team meetings or group discussions?
        Candidate: I try to be an active listener first, to fully grasp what others are saying. Then, I aim to contribute ideas that are well-thought-out, usually supported by data or my own research. I'm not afraid to voice a different opinion if I believe it benefits the project, but I always do so respectfully and constructively. I also make an effort to encourage quieter team members to share their thoughts.
        AI: That's a great approach to collaboration. Finally, what aspects of a team environment help you perform your best?
        Candidate: I thrive in environments where there's open communication and psychological safety. I appreciate a team that's willing to experiment and learn from failures, rather than pointing fingers. Clear goals and mutual respect are also incredibly important to me. I enjoy working with people who are passionate about their work and willing to challenge themselves.
        AI: Thank you, {candidate_name}. That concludes our interview. We appreciate your time today.
        """.format(candidate_name=candidate_name, applied_role=applied_role)

    except requests.exceptions.RequestException as e:
        print(f"Error starting Beyond Presence interview: {e}")
        return {"error": "Failed to start interview"}

    # 3. Process Transcript with Mistral AI for Personality Profile
    mistral_prompt = f"""
    You are a highly skilled organizational psychologist analyzing a candidate's interview transcript. Your task is to infer the candidate's Big Five personality traits (Openness to Experience, Conscientiousness, Extraversion, Agreeableness, Neuroticism/Emotional Stability) based *solely* on their spoken responses.

    First, for each of the following BFI-10 (Big Five Inventory-10) statements, rate how accurately it describes the candidate, based on their responses. Use a 5-point Likert scale (1 = Strongly Disagree, 2 = Disagree, 3 = Neutral, 4 = Agree, 5 = Strongly Agree). Provide your rating as a JSON object.

    BFI-10 Statements:
    1.  Is outgoing, sociable.
    2.  Is compassionate, softhearted.
    3.  Tends to be disorganized. (Reverse-scored)
    4.  Is relaxed, handles stress well. (Reverse-scored for Neuroticism)
    5.  Is curious, has wide interests.
    6.  Is reserved. (Reverse-scored)
    7.  Tends to be rude. (Reverse-scored)
    8.  Does a thorough job.
    9.  Gets nervous easily. (Reverse-scored for Emotional Stability)
    10. Has few artistic interests. (Reverse-scored)

    After rating the BFI-10 items, provide a concise narrative-style summary of the candidate's overall soft skills and general personality. Highlight key strengths and potential areas for development relevant to a team environment. Also, identify any behavioral flags based on the conversation (e.g., "May avoid conflict", "Good under pressure").

    **Interview Transcript:**
    {simulated_transcript}

    **Expected Output Format (JSON):**
    ```json
    {{
      "bfi_10_ratings": {{
        "1": <score>, "2": <score>, ..., "10": <score>
      }},
      "soft_skill_summary": "Narrative summary here...",
      "behavioral_flags": ["flag1", "flag2"],
      "raw_mistral_analysis": "Optional: Mistral's full reasoning or additional notes"
    }}
    ```
    """

    try:
        mistral_response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "mistral-large-latest", # Or mistral-small-latest
                "messages": [
                    {"role": "user", "content": mistral_prompt}
                ],
                "response_format": {"type": "json_object"}
            }
        )
        mistral_response.raise_for_status()
        mistral_output = mistral_response.json()
        mistral_content = mistral_output["choices"][0]["message"]["content"]
        parsed_mistral_content = json.loads(mistral_content)

        bfi10_ratings = {int(k): v for k, v in parsed_mistral_content["bfi_10_ratings"].items()}
        
        # Calculate Big Five from BFI-10
        big5_scores_raw = calculate_big5_from_bfi10(bfi10_ratings)
        
        # Scale to 0-100 for radar chart (assuming 1-5 scale for raw, so *20)
        psychological_profile_big5 = {
            trait: round(score * 20) for trait, score in big5_scores_raw.items()
        }
        
        soft_skill_summary = parsed_mistral_content["soft_skill_summary"]
        behavioral_flags = parsed_mistral_content["behavioral_flags"]

    except requests.exceptions.RequestException as e:
        print(f"Error with Mistral AI: {e}")
        return {"error": "Failed to process personality"}
    except json.JSONDecodeError as e:
        print(f"Error decoding Mistral JSON: {e}. Raw content: {mistral_content}")
        return {"error": "Failed to parse Mistral output"}


    # 4. Get existing team profiles from Weaviate
    team_big5_vectors = get_team_profiles_from_weaviate(team_id_for_compatibility)
    
    # 5. Calculate Compatibility Score
    candidate_big5_vector = np.array([
        psychological_profile_big5["Openness to Experience"],
        psychological_profile_big5["Conscientiousness"],
        psychological_profile_big5["Extraversion"],
        psychological_profile_big5["Agreeableness"],
        psychological_profile_big5["Neuroticism"]
    ])
    
    compatibility_score_percent, similarity_index, complementarity_bonus, friction_risk, custom_culture_fit_bonus = \
        calculate_compatibility_score(candidate_big5_vector, team_big5_vectors)

    # 6. Assemble Final Output
    final_output = {
        "candidate_id": candidate_data.get("id"),
        "candidate_name": candidate_name,
        "applied_role": applied_role,
        "psychological_profile": {
            "radar_chart_data": psychological_profile_big5,
            "raw_bfi10_ratings": bfi10_ratings # Include for transparency/debugging
        },
        "compatibility_score": round(compatibility_score_percent, 2),
        "compatibility_breakdown": {
            "similarity_index": round(similarity_index, 2),
            "complementarity_bonus": round(complementarity_bonus, 2),
            "friction_risk": round(friction_risk, 2),
            "custom_culture_fit_bonus": round(custom_culture_fit_bonus, 2)
        },
        "risk_areas": [], # Populate based on friction_risk and specific trait mismatches
        "behavioral_flags": behavioral_flags,
        "soft_skill_summary": soft_skill_summary
    }

    # Populate risk areas based on the compatibility calculation
    if friction_risk > 0.2: # Example threshold
        final_output["risk_areas"].append("Potential friction due to high trait delta (e.g., Neuroticism/Agreeableness).")
    # Add more specific risk areas, e.g., if candidate is very low in Agreeableness and team is very high.
    # This requires more detailed comparison logic.

    return final_output

# --- Example Usage ---
# candidate_info = {"id": "CAND001", "name": "Jane Doe", "role": "Senior Backend Engineer", "skills": ["Python", "Flask", "MongoDB"]}
# team_to_join_id = "dev_team_alpha" # This would come from your frontend/recruiter input
#
# result = your_backend_interview_trigger(candidate_info, team_to_join_id)
# print(json.dumps(result, indent=2))