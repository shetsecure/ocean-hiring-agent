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
        
        # Load all candidate data files - use the same directory as team.json
        data_dir = os.path.dirname(team_data_path)
        candidates_data = []
        candidate_files_pattern = os.path.join(data_dir, 'candidate_*.json')
        candidate_files = glob.glob(candidate_files_pattern)
        
        for candidate_file in candidate_files:
            with open(candidate_file, 'r', encoding='utf-8') as f:
                candidate_data = json.load(f)
                candidates_data.append(candidate_data['candidate'])
        
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
    """Get interview history - for now returns sample data"""
    try:
        # For now, return sample data since we don't have a real interview storage system
        # In a real implementation, this would query a database or API
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
            },
            {
                'agent_id': 'agent_004',
                'candidate_name': 'Emily Chen',
                'role': 'Full Stack Developer',
                'candidate_email': 'emily.chen@email.com',
                'status': 'completed',
                'created_at': '2024-01-13T16:45:00Z',
                'duration': '28 minutes',
                'has_transcript': True,
                'interview_link': 'https://agent.ai-interviewer.com/agent_004'
            },
            {
                'agent_id': 'agent_005',
                'candidate_name': 'David Wilson',
                'role': 'DevOps Engineer',
                'candidate_email': 'david.wilson@email.com',
                'status': 'failed',
                'created_at': '2024-01-12T11:20:00Z',
                'duration': '10 minutes',
                'has_transcript': False,
                'interview_link': 'https://agent.ai-interviewer.com/agent_005'
            }
        ]
        
        return jsonify({
            'success': True,
            'interviews': sample_interviews,
            'total_count': len(sample_interviews)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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