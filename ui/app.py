from flask import Flask, render_template, jsonify, request
import json
import os
import requests
import glob
from datetime import datetime

app = Flask(__name__)

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

def load_dashboard_data_api():
    """Load dashboard data by calling the API endpoint"""
    try:
        # Load team data - try different paths for Docker and local development
        team_data_path = None
        possible_team_paths = [
            'data/team.json',  # Docker mounted volume
            '../data/team.json',  # Local development from ui folder
            'team.json'  # Current directory
        ]
        
        for path in possible_team_paths:
            if os.path.exists(path):
                team_data_path = path
                break
        
        if team_data_path is None:
            raise FileNotFoundError("team.json not found in expected locations")
            
        with open(team_data_path, 'r', encoding='utf-8') as f:
            team_data = json.load(f)
        
        
        if os.path.exists('data/c_data_for_analyzer/candidates_analysis_latest.json'):
            with open('data/c_data_for_analyzer/candidates_analysis_latest.json', 'r', encoding='utf-8') as f:
                chosen_candidates = json.load(f)
                print(f"Chosen candidates: {chosen_candidates}")
                
                # Extract candidate names for easier comparison
                chosen_candidate_names = [candidate.get('candidate_name') for candidate in chosen_candidates.get('candidates', [])]
                print(f"Chosen candidate names: {chosen_candidate_names}")
        else:
            print("No candidates analysis data found")
        
        
        # Load all candidate data files - use the same directory as team.json for demo
        # for production, we will use INTERVIEW API CALLS to get the candidates data
        data_dir = os.path.dirname(team_data_path)
        candidates_data = []
        candidate_files_pattern = os.path.join(data_dir, 'candidate_*.json')
        candidate_files = glob.glob(candidate_files_pattern)
        
        for candidate_file in candidate_files:
            with open(candidate_file, 'r', encoding='utf-8') as f:
                candidate_data = json.load(f)
                candidate_name = candidate_data['candidate']['name']
                print(f"Checking candidate: {candidate_name}")
                
                if candidate_name in chosen_candidate_names:
                    print(f"✅ Found chosen candidate: {candidate_name}")
                    candidates_data.append(candidate_data['candidate'])
                else:
                    print(f"❌ Candidate not chosen: {candidate_name}")
            
        # Format the request payload according to API requirements
        payload = {
            "team_data": team_data,
            "candidates_data": {
                "candidates": candidates_data
            }
        }
        
        # Make POST request to the API
        api_url = f"{API_BASE_URL}/analysis/compatibility"
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=300)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Save API response to compatibility_scores.json
        output_path = os.path.join(data_dir, 'compatibility_scores.json')
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(response.json(), f, indent=2)
        return response.json()
        
    except requests.exceptions.ConnectionError:
        print("API server is not running or not accessible")
        return None
    except requests.exceptions.Timeout:
        print("API request timed out")
        return None
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None
    except FileNotFoundError as e:
        print(f"Data file not found: {e}")
        return None
    except Exception as e:
        print(f"Error loading data from API: {e}")
        return None


def load_dashboard_data():
    """Load the dashboard data from JSON file or API"""
    try:
        # Try different paths for compatibility_scores.json
        possible_paths = [
            'data/compatibility_scores.json',  # Docker mounted volume
            '../data/compatibility_scores.json',  # Local development
            'compatibility_scores.json'  # Current directory
        ]

 
        for data_path in possible_paths:
            if os.path.exists(data_path):
                with open(data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        # If no local file found, fallback to API call
        print("Local compatibility_scores.json not found, trying API...")
        return load_dashboard_data_api()
        
    except Exception as e:
        print(f"Error loading data: {e}")
        # Fallback to API call if local file read fails
        return load_dashboard_data_api()

@app.route('/health')
def health_check():
    """Health check endpoint for Docker"""
    return jsonify({
        'status': 'healthy',
        'service': 'Team Compatibility Dashboard UI',
        'version': '1.0.0'
    }), 200

@app.route('/')
def home():
    """Home page - main landing page"""
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    """Team compatibility dashboard page"""
    # Check for analyze_interviews parameter
    analyze_interviews_json = request.args.get('analyze_interviews')
    
    if analyze_interviews_json:
        try:
            # Parse the JSON data
            candidates_data = json.loads(analyze_interviews_json)
            
            # Create the data directory if it doesn't exist
            data_dir = 'data/c_data_for_analyzer'
            os.makedirs(data_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'candidates_analysis_{timestamp}.json'
            filename_latest = f'candidates_analysis_latest.json'
            filepath = os.path.join(data_dir, filename)
            filepath_latest = os.path.join(data_dir, filename_latest)
            # Save the candidate information to file
            output_data = {
                'timestamp': datetime.now().isoformat(),
                'source': 'interview_analysis',
                'candidates': candidates_data,
                'total_candidates': len(candidates_data) if isinstance(candidates_data, list) else 1
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            with open(filepath_latest, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Saved candidate data for analysis: {filepath} and {filepath_latest}")
            
            if len(candidates_data) != 0:
                print("Candidates chosen, continuing compatibility analysis")
                # Rename existing compatibility_scores.json to compatibility_scores.json.old if it exists
                compatibility_scores_path = os.path.join("data", 'compatibility_scores.json')
                if os.path.exists(compatibility_scores_path):
                    old_path = compatibility_scores_path + '.old'
                    os.replace(compatibility_scores_path, old_path)
                    
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing analyze_interviews JSON: {e}")
        except Exception as e:
            print(f"❌ Error saving candidate data: {e}")
    
    return render_template('dashboard.html')


@app.route('/api/dashboard-data')
def get_dashboard_data():
    """API endpoint to get dashboard data"""
    data = load_dashboard_data()
    if data is None:
        return jsonify({'error': 'Data file not found'}), 404
    return jsonify(data)

@app.route('/api/team-summary')
def get_team_summary():
    """API endpoint to get team summary"""
    data = load_dashboard_data()
    if data is None:
        return jsonify({'error': 'Data file not found'}), 404
    return jsonify(data.get('team_summary', {}))

@app.route('/api/candidates')
def get_candidates():
    """API endpoint to get candidates analysis"""
    data = load_dashboard_data()
    if data is None:
        return jsonify({'error': 'Data file not found'}), 404
    return jsonify(data.get('candidates_analysis', []))

@app.route('/api/insights')
def get_insights():
    """API endpoint to get team insights"""
    data = load_dashboard_data()
    if data is None:
        return jsonify({'error': 'Data file not found'}), 404
    return jsonify(data.get('team_insights', {}))

@app.route('/api/debug/compatibility')
def debug_compatibility():
    """Debug endpoint to check compatibility calculation"""
    data = load_dashboard_data()
    if data is None:
        return jsonify({'error': 'Data file not found'}), 404
    
    insights = data.get('team_insights', {})
    pool_summary = insights.get('candidate_pool_summary', {})
    
    debug_info = {
        'raw_average_compatibility': pool_summary.get('average_compatibility'),
        'formatted_percentage': f"{pool_summary.get('average_compatibility', 0) * 100:.1f}%",
        'candidates_above_threshold': pool_summary.get('candidates_above_threshold'),
        'total_candidates': len(data.get('candidates_analysis', [])),
        'team_size': data.get('analysis_metadata', {}).get('team_size')
    }
    
    return jsonify(debug_info)

@app.route('/interview')
def interview_page():
    """Interview page for creating and conducting AI interviews"""
    return render_template('interview.html')

@app.route('/api/create-interview', methods=['POST'])
def create_interview_proxy():
    """Proxy endpoint to create interview via API"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('candidate_name') or not data.get('role'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Make request to actual API
        api_url = f"{API_BASE_URL}/interviews"
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(api_url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else {'detail': response.text}
            return jsonify(error_data), response.status_code
            
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'API server is not accessible'}), 503
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timeout'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/interview-history')
def get_interview_history():
    """Get interview history from interviews.json file"""
    try:
        # Try different paths for interviews.json
        possible_paths = [
            'data/interviews.json',  # Docker mounted volume
            '../data/interviews.json',  # Local development from ui folder
            'interviews.json'  # Current directory
        ]
        
        interviews_data = None
        for interviews_path in possible_paths:
            if os.path.exists(interviews_path):
                with open(interviews_path, 'r', encoding='utf-8') as f:
                    interviews_data = json.load(f)
                break
        
        if interviews_data is None:
            # Fallback to sample data if file not found
            return get_sample_interview_history()
        
        # Transform the interviews data to match frontend expectations
        interviews_list = []
        for agent_id, interview_data in interviews_data.items():
            # Extract email from system prompt if available
            candidate_email = None
            agent_details = interview_data.get('agent_details', {})
            system_prompt = agent_details.get('system_prompt', '')
            
            # Try to extract email from system prompt
            import re
            email_match = re.search(r'Email:\s*([^\s\n]+)', system_prompt)
            if email_match:
                candidate_email = email_match.group(1)
            
            # Determine status based on creation time and other factors
            created_at = interview_data.get('created_at')
            status = 'completed'  # Default to completed for existing interviews
            duration = '25 minutes'  # Default duration
            has_transcript = True  # Assume transcripts are available for completed interviews
            
            # If the interview was created very recently (within last hour), mark as in-progress
            if created_at:
                try:
                    from datetime import datetime, timezone
                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    now = datetime.now(timezone.utc)
                    time_diff = now - created_time
                    
                    if time_diff.total_seconds() < 3600:  # Less than 1 hour ago
                        status = 'in-progress'
                        duration = 'In progress'
                        has_transcript = False
                except:
                    pass  # Keep default values if parsing fails
            
            formatted_interview = {
                'agent_id': interview_data.get('agent_id', agent_id),
                'candidate_name': interview_data.get('candidate_name', 'Unknown'),
                'role': interview_data.get('role', 'Unknown Role'),
                'candidate_email': candidate_email,
                'status': status,
                'created_at': created_at or datetime.now().isoformat() + 'Z',
                'duration': duration,
                'has_transcript': has_transcript,
                'interview_link': interview_data.get('interview_link', f'https://bey.chat/{agent_id}')
            }
            
            interviews_list.append(formatted_interview)
        
        # Sort by creation time (newest first)
        interviews_list.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'success': True,
            'interviews': interviews_list,
            'total_count': len(interviews_list)
        })
        
    except Exception as e:
        print(f"Error loading interviews from file: {e}")
        # Fallback to sample data on any error
        return get_sample_interview_history()

def get_sample_interview_history():
    """Fallback function to return sample interview data"""
    sample_interviews = [
        {
            'agent_id': 'agent_001',
            'candidate_name': 'John Smith',
            'role': 'Software Engineer',
            'candidate_email': 'john.smith@email.com',
            'status': 'completed',
            'created_at': '2024-01-15T10:30:00Z',
            'duration': '25 minutes',
            'has_transcript': True,
            'interview_link': 'https://agent.ai-interviewer.com/agent_001'
        },
        {
            'agent_id': 'agent_002',
            'candidate_name': 'Sarah Johnson',
            'role': 'Frontend Developer',
            'candidate_email': 'sarah.johnson@email.com',
            'status': 'completed',
            'created_at': '2024-01-14T14:15:00Z',
            'duration': '30 minutes',
            'has_transcript': True,
            'interview_link': 'https://agent.ai-interviewer.com/agent_002'
        },
        {
            'agent_id': 'agent_003',
            'candidate_name': 'Mike Davis',
            'role': 'Backend Developer',
            'candidate_email': 'mike.davis@email.com',
            'status': 'in-progress',
            'created_at': '2024-01-16T09:00:00Z',
            'duration': 'In progress',
            'has_transcript': False,
            'interview_link': 'https://agent.ai-interviewer.com/agent_003'
        }
    ]
    
    return jsonify({
        'success': True,
        'interviews': sample_interviews,
        'total_count': len(sample_interviews)
    })

@app.route('/api/interview-transcript/<agent_id>')
def get_interview_transcript_proxy(agent_id):
    """Proxy endpoint to get interview transcript via API"""
    try:
        candidate_name = request.args.get('candidate_name')
        role = request.args.get('role')
        
        # Build query parameters
        params = {}
        if candidate_name:
            params['candidate_name'] = candidate_name
        if role:
            params['role'] = role
        
        # Make request to actual API
        api_url = f"{API_BASE_URL}/interviews/{agent_id}/transcript"
        
        response = requests.get(api_url, params=params, timeout=30)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else {'detail': response.text}
            return jsonify(error_data), response.status_code
            
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'API server is not accessible'}), 503
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timeout'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005) 