from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import os
import uuid
from main import generate_video
import threading
import time

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://localhost:5001"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept"],
        "expose_headers": ["Content-Type", "Accept"],
        "supports_credentials": True
    }
})

# Store job status
jobs = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'status': 'processing',
        'progress': 0,
        'video_path': None,
        'error': None
    }

    def generate_video_task():
        try:
            from main import generate_video_from_json
            output_path = generate_video_from_json(data, job_id=job_id)
            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['video_path'] = output_path
        except Exception as e:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['error'] = str(e)

    thread = threading.Thread(target=generate_video_task)
    thread.daemon = True
    thread.start()

    return jsonify({'job_id': job_id})

@app.route('/status/<job_id>')
def status(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(jobs[job_id])

@app.route('/download/<job_id>')
def download(job_id):
    if job_id not in jobs or jobs[job_id]['status'] != 'completed':
        return jsonify({'error': 'Video not ready'}), 404

    video_path = jobs[job_id]['video_path']
    return send_file(video_path, as_attachment=True)

if __name__ == '__main__':

    port = int(os.environ.get("PORT", 5001))  # fallback for local dev
    app.run(host="0.0.0.0", port=port)