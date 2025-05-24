from flask import Flask, render_template, jsonify
import json
import os
import requests
import glob
from datetime import datetime

app = Flask(__name__)


def load_dashboard_data_api():
    """Load dashboard data by calling the API endpoint"""
    try:
        # Load team data - try both relative paths
        team_data_path = None
        for path in ['../data/team.json', 'data/team.json']:
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
        api_url = "http://localhost:8000/analysis/compatibility"
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=300)
        response.raise_for_status()  # Raise an exception for bad status codes
        # Save API response to compatibility_scores.json
        output_path = os.path.join(data_dir, 'compatibility_scores.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
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
        data_path = os.path.join('..', 'data', 'compatibility_scores.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Try relative to ui folder
        try:
            with open('../data/compatibility_scores.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Fallback to API call if local file not found
            print("Local compatibility_scores.json not found, trying API...")
            return load_dashboard_data_api()

@app.route('/')
def dashboard():
    """Main dashboard page"""
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005) 