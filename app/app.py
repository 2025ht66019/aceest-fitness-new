from flask import Flask, request, jsonify
from aceest_core.models import WorkoutEntry, User
from aceest_core.calculations import calculate_bmi, calculate_bmr, calculate_calories
from aceest_core.report import export_pdf
from datetime import datetime, date

app = Flask(__name__)

workouts_by_cat = {"Warm-up": [], "Workout": [], "Cool-down": []}
daily_workouts: dict[str, dict[str, list[WorkoutEntry]]] = {}
user_info: dict | None = None

@app.route('/health')
def health():
    return jsonify(status='ok', version='v1.4')

@app.route('/api/user', methods=['POST'])
def save_user():
    global user_info
    data = request.get_json(force=True)
    try:
        name = data['name']; regn_id = data['regn_id']; age = int(data['age']); gender = data['gender'].upper()
        height_cm = float(data['height_cm']); weight_kg = float(data['weight_kg'])
        bmi = calculate_bmi(weight_kg, height_cm); bmr = calculate_bmr(weight_kg, height_cm, age, gender)
        user = User(name, regn_id, age, gender, height_cm, weight_kg, bmi, bmr)
        user_info = user.__dict__
        return jsonify(message='saved', bmi=round(bmi,1), bmr=round(bmr,0))
    except Exception as e:
        return jsonify(error=str(e)), 400

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
    weight = user_info.get('weight_kg', 70) if user_info else 70
    calories = calculate_calories(category, duration, weight)
    entry = WorkoutEntry(category=category, exercise=exercise, duration=duration, calories=calories)
    workouts_by_cat[category].append(entry)
    today = date.today().isoformat()
    if today not in daily_workouts:
        daily_workouts[today] = {"Warm-up": [], "Workout": [], "Cool-down": []}
    daily_workouts[today][category].append(entry)
    return jsonify(message='added', category=category, exercise=exercise, duration=duration, calories=round(calories,1))

@app.route('/api/workouts', methods=['GET'])
def list_workouts():
    return jsonify({
        cat: [
            {
                'exercise': w.exercise,
                'duration': w.duration,
                'calories': w.calories,
                'timestamp': w.timestamp.isoformat()
            } for w in entries
        ] for cat, entries in workouts_by_cat.items()
    })

@app.route('/api/progress', methods=['GET'])
def progress():
    totals = {cat: sum(w.duration for w in entries) for cat, entries in workouts_by_cat.items()}
    return jsonify({"categories": list(totals.keys()), "values": list(totals.values())})

@app.route('/api/report', methods=['GET'])
def report():
    if not user_info:
        return jsonify(error='user info not saved'), 400
    filename = export_pdf(user_info, workouts_by_cat)
    return jsonify(filename=filename)

@app.route('/api/daily', methods=['GET'])
def daily():
    result = {}
    for day, cats in daily_workouts.items():
        result[day] = {cat: sum(w.duration for w in entries) for cat, entries in cats.items()}
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5007)
