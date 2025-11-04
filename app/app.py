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
    body { font-family: Arial, sans-serif; margin:25px;}
    h1 { margin-top:0;}
    .status { margin-bottom:15px; font-weight:bold; }
    .error { color:#a00; }
    form { margin-bottom:30px; padding:12px 16px; border:1px solid #ddd; border-radius:6px; max-width:320px;}
    label { display:block; margin-top:10px; font-weight:bold;}
    input, select { width:100%; padding:6px; margin-top:4px; box-sizing:border-box;}
    button { margin-top:14px; padding:8px 14px; cursor:pointer; background:#007bff; color:#fff; border:none; border-radius:4px;}
    .grid { display:flex; gap:40px; flex-wrap:wrap; margin-top:10px;}
    .section { min-width:220px;}
    .section h2 { font-size:1.05em; margin:0 0 6px; color:#007bff;}
    ul { padding-left:18px; margin:4px 0 0;}
    li { margin-bottom:4px;}
    .empty { font-style:italic; color:#666; }
    a { text-decoration:none; color:#007bff; }
  </style>
</head>
<body>
  <h1>ACEest Fitness & Gym Tracker</h1>
  {% if status %}
    <div class="status {% if 'Error:' in status %}error{% endif %}">{{ status }}</div>
  {% endif %}
  <form method="post" action="{{ url_for('add_session') }}">
    <label for="category">Category</label>
    <select name="category" id="category">
      {% for c in workouts.keys() %}
        <option value="{{ c }}">{{ c }}</option>
      {% endfor %}
    </select>

    <label for="exercise">Exercise</label>
    <input type="text" id="exercise" name="exercise" placeholder="e.g. Push Ups">

    <label for="duration">Duration (minutes)</label>
    <input type="number" id="duration" name="duration" min="1" step="1" placeholder="e.g. 15">

    <button type="submit">Add Session</button>
  </form>

  <div class="grid">
    {% for category, sessions in workouts.items() %}
      <div class="section">
        <h2>{{ category }}</h2>
        {% if sessions %}
          <ul>
            {% for s in sessions %}
              <li>{{ s.exercise }} - {{ s.duration }} min ({{ s.timestamp }})</li>
            {% endfor %}
          </ul>
        {% else %}
          <div class="empty">No entries yet.</div>
        {% endif %}
      </div>
    {% endfor %}
  </div>

  <p><a href="{{ url_for('summary') }}">View Summary →</a></p>
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
  {% for category, sessions in workouts.items() %}
    <div class="category">{{ category }}:</div>
    {% if sessions %}
      <div class="sessions">
      {% for s in sessions %}
        <div>{{ loop.index }}. {{ s.exercise }} - {{ s.duration }} min ({{ s.timestamp }})</div>
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
    total_time = sum(s["duration"] for sessions in workouts.values() for s in sessions)
    return render_template_string(SUMMARY_TEMPLATE, workouts=workouts, total_time=total_time)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)