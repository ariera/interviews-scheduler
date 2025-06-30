#!/usr/bin/env python3
"""
Web Interface for Interview Scheduler

A simple Flask application that allows users to upload YAML configuration files
and get multiple scheduling solutions.
"""

import os
import sys
import tempfile
import yaml
import json
import time
from flask import Flask, render_template, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename
import uuid
from copy import deepcopy

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scheduler import InterviewScheduler, create_scheduler_from_config, load_config

app = Flask(__name__)

# Configuration from environment variables
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB max file size
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Upload folder configuration
upload_folder = os.environ.get('UPLOAD_FOLDER')
if upload_folder:
    # Use environment-specified upload folder
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder
else:
    # Fallback to temporary directory
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

# Store temporary files
temp_files = {}

def cleanup_old_sessions():
    """Remove sessions older than 1 hour."""
    current_time = time.time()
    expired_sessions = []

    for session_id, data in temp_files.items():
        if current_time - data['timestamp'] > 3600:  # 1 hour
            expired_sessions.append(session_id)

    for session_id in expired_sessions:
        del temp_files[session_id]

@app.route('/')
def index():
    """Main page with file upload form."""
    cleanup_old_sessions()  # Clean up old sessions
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and run scheduler."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.lower().endswith('.yaml') and not file.filename.lower().endswith('.yml'):
            return jsonify({'error': 'Please upload a YAML file (.yaml or .yml)'}), 400

        # Read and validate the YAML file
        try:
            yaml_content = file.read().decode('utf-8')
            config = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            return jsonify({'error': f'Invalid YAML file: {str(e)}'}), 400

        # Validate required fields
        required_fields = ['num_candidates', 'panels', 'order', 'availabilities']
        for field in required_fields:
            if field not in config:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Create scheduler and run multiple times
        try:
            scheduler = create_scheduler_from_config(config)
        except Exception as e:
            return jsonify({'error': f'Configuration error: {str(e)}'}), 400

        # Generate multiple solutions
        solutions = []
        max_attempts = 10  # Try up to 10 times to get 3 different solutions

        for attempt in range(max_attempts):
            if len(solutions) >= 3:
                break

            # Run the scheduler
            success = scheduler.solve(max_time_seconds=30, verbose=False)

            if success:
                # Get solution data
                summary = scheduler.get_solution_summary()
                candidate_schedules = {}

                for i in range(scheduler.num_candidates):
                    candidate_schedules[f'candidate_{i+1}'] = scheduler.get_candidate_schedule(i)

                solution_data = {
                    'summary': summary,
                    'schedules': candidate_schedules,
                    'attempt': attempt + 1
                }

                # Check if this solution is different from previous ones
                is_different = True
                for existing_solution in solutions:
                    if _solutions_are_similar(solution_data, existing_solution):
                        is_different = False
                        break

                if is_different:
                    solutions.append(solution_data)

        if not solutions:
            return jsonify({'error': 'No feasible solutions found. Try relaxing constraints.'}), 400

        # Store results temporarily
        session_id = str(uuid.uuid4())
        temp_files[session_id] = {
            'solutions': solutions,
            'config': config,
            'timestamp': time.time()
        }

        return jsonify({
            'success': True,
            'session_id': session_id,
            'num_solutions': len(solutions),
            'summary': {
                'num_candidates': config['num_candidates'],
                'num_panels': len(config['panels']),
                'max_gap': config.get('max_gap_minutes', 15)
            }
        })

    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/solutions/<session_id>')
def get_solutions(session_id):
    """Get the solutions for a session."""
    cleanup_old_sessions()  # Clean up old sessions

    if session_id not in temp_files:
        return jsonify({'error': 'Session not found or expired'}), 404

    return jsonify(temp_files[session_id]['solutions'])

@app.route('/download/<session_id>')
def download_results(session_id):
    """Download results as JSON file."""
    cleanup_old_sessions()  # Clean up old sessions

    if session_id not in temp_files:
        return jsonify({'error': 'Session not found or expired'}), 404

    data = temp_files[session_id]

    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(data, temp_file, indent=2)
    temp_file.close()

    return send_file(
        temp_file.name,
        as_attachment=True,
        download_name=f'interview_schedule_{session_id}.json',
        mimetype='application/json'
    )

@app.route('/health')
def health_check():
    """Health check endpoint."""
    cleanup_old_sessions()  # Clean up old sessions
    return jsonify({'status': 'healthy'})

@app.route('/download_csv/<session_id>/<int:solution_index>')
def download_csv(session_id, solution_index):
    """Download the CSV export for a specific solution."""
    cleanup_old_sessions()
    if session_id not in temp_files:
        return jsonify({'error': 'Session not found or expired'}), 404
    solutions = temp_files[session_id]['solutions']
    config = temp_files[session_id]['config']
    if not (0 <= solution_index < len(solutions)):
        return jsonify({'error': 'Invalid solution index'}), 400
    # Recreate the scheduler for this solution
    scheduler = create_scheduler_from_config(config)
    # Solve until we get the desired solution (same logic as upload)
    found = False
    for attempt in range(20):
        scheduler.solve(max_time_seconds=30, verbose=False)
        # Compare with the stored solution
        summary = scheduler.get_solution_summary()
        candidate_schedules = {
            f'candidate_{i+1}': scheduler.get_candidate_schedule(i)
            for i in range(scheduler.num_candidates)
        }
        solution_data = {
            'summary': summary,
            'schedules': candidate_schedules
        }
        # Use the same similarity check as before
        def _strip_attempt(sol):
            sol = deepcopy(sol)
            sol.pop('attempt', None)
            return sol
        if _strip_attempt(solution_data) == _strip_attempt(solutions[solution_index]):
            found = True
            break
    if not found:
        return jsonify({'error': 'Could not regenerate the selected solution.'}), 500
    # Export to CSV string
    csv_str = scheduler.export_to_csv_string()
    # Serve as file
    return Response(
        csv_str,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=interview_schedule_{session_id}_sol{solution_index+1}.csv'
        }
    )

def _solutions_are_similar(sol1, sol2, tolerance=0.1):
    """Check if two solutions are similar (to avoid duplicates)."""
    # Compare makespan (day end time)
    makespan1 = _parse_time_to_minutes(sol1['summary']['day_ends_at'])
    makespan2 = _parse_time_to_minutes(sol2['summary']['day_ends_at'])

    if abs(makespan1 - makespan2) > 30:  # More than 30 minutes difference
        return False

    # Compare order breaks
    breaks1 = sol1['summary']['order_breaks']
    breaks2 = sol2['summary']['order_breaks']

    if abs(breaks1 - breaks2) > 0:  # Different number of breaks
        return False

    # Compare total idle time across candidates
    idle1 = _calculate_total_idle_time(sol1['schedules'])
    idle2 = _calculate_total_idle_time(sol2['schedules'])

    if abs(idle1 - idle2) > 60:  # More than 60 minutes difference in total idle time
        return False

    return True

def _parse_time_to_minutes(time_str):
    """Parse time string like '14:45' to total minutes since midnight."""
    hour, minute = map(int, time_str.split(':'))
    return hour * 60 + minute

def _calculate_total_idle_time(schedules):
    """Calculate total idle time across all candidates."""
    total_idle = 0
    for candidate_schedule in schedules.values():
        for session in candidate_schedule:
            if 'gap_before' in session:
                total_idle += session['gap_before']
    return total_idle

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)