from flask import Flask, request, jsonify
from aceest_core.models import WorkoutEntry

app = Flask(__name__)

workouts_by_cat = {"Warm-up": [], "Workout": [], "Cool-down": []}

RECOMMENDED_PLAN = {
    "Warm-up": ["5 min Jog", "Jumping Jacks"],
    "Workout": ["Push-ups", "Squats"],
    "Cool-down": ["Stretch", "Breathing"]
}
DIET_GUIDE = {
    "Weight Loss": ["Oatmeal", "Grilled Chicken"],
    "Muscle Gain": ["Egg Omelet", "Protein Shake"],
    "Endurance": ["Banana", "Whole Grain Pasta"]
}

@app.route('/health')
def health():
    return jsonify(status='ok', version='v1.2')

@app.route('/api/workout', methods=['POST'])
def add_workout():
    data = request.get_json(force=True)
    category = data.get('category', 'Workout')
    exercise = data.get('exercise')
    duration = data.get('duration')
    if category not in workouts_by_cat:
        return jsonify(error='invalid category'), 400
    if not exercise or duration is None:
        return jsonify(error='category, exercise, duration required'), 400
    try:
        duration = int(duration)
        if duration <= 0:
            raise ValueError
    except ValueError:
        return jsonify(error='duration must be positive int'), 400
    entry = WorkoutEntry(category=category, exercise=exercise, duration=duration)
    workouts_by_cat[category].append(entry)
    return jsonify(message='added', category=category, exercise=exercise, duration=duration)

@app.route('/api/workouts', methods=['GET'])
def list_workouts():
    return jsonify({
        cat: [
            {
                'exercise': w.exercise,
                'duration': w.duration,
                'timestamp': w.timestamp.isoformat()
            } for w in entries
        ] for cat, entries in workouts_by_cat.items()
    })

@app.route('/api/summary', methods=['GET'])
def summary():
    totals = {cat: sum(w.duration for w in entries) for cat, entries in workouts_by_cat.items()}
    return jsonify(totals)

@app.route('/api/plan', methods=['GET'])
def plan():
    return jsonify(RECOMMENDED_PLAN)

@app.route('/api/diet', methods=['GET'])
def diet():
    return jsonify(DIET_GUIDE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
