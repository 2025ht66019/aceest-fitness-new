from flask import Flask, render_template_string, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

workouts = {"Warm-up": [], "Workout": [], "Cool-down": []}

INDEX_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>ACEest Fitness & Gym Tracker</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 25px; }
    h1 { color:#222; }
    .container { max-width: 600px; margin:auto; }
    .status { margin-top:10px; color: #28a745; }
    .error { color:#dc3545; }
    form, .summary { background:#f9f9f9; padding:15px; border-radius:8px; }
    button { padding:8px 16px; }
    .sessions { margin-left:15px; }
    .category { color:#007bff; font-weight:bold; margin-top:18px; }
  </style>
</head>
<body>
<div class="container">
  <h1>🏋️ ACEest Fitness & Gym Tracker</h1>

  <form method="POST" action="{{ url_for('add_session') }}">
    <label>Category:</label>
    <select name="category">
      {% for c in workouts.keys() %}
      <option value="{{ c }}" {% if c == 'Workout' %}selected{% endif %}>{{ c }}</option>
      {% endfor %}
    </select><br><br>

    <label>Exercise:</label><br>
    <input type="text" name="exercise" required><br><br>

    <label>Duration (min):</label><br>
    <input type="number" min="1" name="duration" required><br><br>

    <button type="submit">Add Session</button>
    <a href="{{ url_for('summary') }}"><button type="button">View Summary</button></a>
  </form>

  {% if status %}
    <div class="status">{{ status }}</div>
  {% endif %}
</div>
</body>
</html>
"""

SUMMARY_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Workout Summary</title>
  <style>
    body { font-family: Arial, sans-serif; margin:25px;}
    .container { max-width:650px; margin:auto;}
    .category { color:#007bff; font-weight:bold; margin-top:18px; }
    .empty { font-style:italic; color:#666; }
    .total { margin-top:25px; font-weight:bold; color:#28a745;}
    .motivation { font-style:italic; margin-top:10px; color:#444;}
    a { text-decoration:none; }
  </style>
</head>
<body>
<div class="container">
  <h1>Session Summary</h1>
  {% set total_time = 0 %}
  {% for category, sessions in workouts.items() %}
    <div class="category">{{ category }}:</div>
    {% if sessions %}
      <div class="sessions">
      {% for s in sessions %}
        <div>{{ loop.index }}. {{ s.exercise }} - {{ s.duration }} min ({{ s.timestamp }})</div>
        {% set total_time = total_time + s.duration %}
      {% endfor %}
      </div>
    {% else %}
      <div class="sessions empty">No sessions recorded.</div>
    {% endif %}
  {% endfor %}
  <div class="total">Total Time Spent: {{ total_time }} minutes</div>
  {% if total_time < 30 %}
    <div class="motivation">Good start! Keep moving 💪</div>
  {% elif total_time < 60 %}
    <div class="motivation">Nice effort! You're building consistency 🔥</div>
  {% else %}
    <div class="motivation">Excellent dedication! Keep up the great work 🏆</div>
  {% endif %}
  <p><a href="{{ url_for('index') }}">← Back</a></p>
</div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    status = request.args.get("status")
    return render_template_string(INDEX_TEMPLATE, workouts=workouts, status=status)

@app.route("/add", methods=["POST"])
def add_session():
    category = request.form.get("category", "Workout")
    exercise = request.form.get("exercise", "").strip()
    duration_raw = request.form.get("duration", "").strip()

    if not exercise or not duration_raw:
        return redirect(url_for('index', status="Error: exercise and duration required"))
    try:
        duration = int(duration_raw)
    except ValueError:
        return redirect(url_for('index', status="Error: duration must be a number"))

    entry = {
        "exercise": exercise,
        "duration": duration,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    if category not in workouts:
        workouts[category] = []
    workouts[category].append(entry)

    msg = f"Added {exercise} ({duration} min) to {category}!"
    return redirect(url_for('index', status=msg))

@app.route("/summary", methods=["GET"])
def summary():
    return render_template_string(SUMMARY_TEMPLATE, workouts=workouts)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)