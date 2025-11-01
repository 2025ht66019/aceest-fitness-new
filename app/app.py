from flask import Flask, request, jsonify
from aceest_core.models import WorkoutEntry

app = Flask(__name__)

workouts = []  # simple list for baseline version (no categories)

@app.route('/health')
def health():
    return jsonify(status='ok', version='v1.0')

@app.route('/api/workout', methods=['POST'])
def add_workout():
    data = request.get_json(force=True)
    exercise = data.get('exercise')
    duration = data.get('duration')
    if not exercise or duration is None:
        return jsonify(error='exercise and duration required'), 400
    try:
        duration = int(duration)
        if duration <= 0:
            raise ValueError
    except ValueError:
        return jsonify(error='duration must be positive int'), 400
    entry = WorkoutEntry(category='', exercise=exercise, duration=duration)
    workouts.append(entry)
    return jsonify(message='added', exercise=exercise, duration=duration)

@app.route('/api/workouts', methods=['GET'])
def list_workouts():
    return jsonify([
        {
            'exercise': w.exercise,
            'duration': w.duration,
            'timestamp': w.timestamp.isoformat()
        } for w in workouts
    ])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
