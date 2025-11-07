from flask import Flask, render_template_string, request, redirect, url_for, jsonify
import os, secrets
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from datetime import datetime
from jinja2 import DictLoader

app = Flask(__name__)
# Secure secret key (read from env in production). A random fallback is generated for dev/local usage.
_secret = os.environ.get('SECRET_KEY') or os.environ.get('FLASK_SECRET_KEY')
_enforce = os.environ.get('FLASK_ENFORCE_SECRET') == '1'
if not _secret:
  if _enforce:
    raise RuntimeError('SECRET_KEY/FLASK_SECRET_KEY must be set when FLASK_ENFORCE_SECRET=1')
  # Allow deterministic key for local dev & tests only (explicitly marked as non-production).
  if app.config.get('TESTING') or os.environ.get('FLASK_ENV') == 'development':
    _secret = 'local-dev-test-secret'  # NOSONAR
  else:
    # Generate ephemeral runtime secret (will invalidate sessions on restart, acceptable for ad-hoc runs)
    _secret = secrets.token_hex(32)  # NOSONAR
app.config['SECRET_KEY'] = _secret  #  NOSONAR

# Initialize global CSRF protection (do NOT disable)
csrf = CSRFProtect(app)

@app.context_processor
def inject_csrf_token():  # makes {{ csrf_token() }} available in templates
  # Return dict literal to satisfy quality check (avoid dict() constructor)
  return {'csrf_token': generate_csrf}

# Register in-memory templates for inheritance
BASE_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ACEest Fitness & Gym Tracker</title>
<style>
body { font-family: Arial, sans-serif; margin:25px; }
nav a { margin-right:14px; text-decoration:none; color:#007bff; font-weight:bold; }
.active { text-decoration:underline; }
.status { margin:10px 0 18px; font-weight:bold; }
.error { color:#a00; }
form { padding:14px 18px; border:1px solid #ddd; border-radius:6px; max-width:360px; background:#fafafa; }
label { display:block; margin-top:10px; font-weight:bold; }
input, select { width:100%; padding:6px; margin-top:4px; box-sizing:border-box; }
button { margin-top:14px; padding:8px 14px; cursor:pointer; background:#007bff; color:#fff; border:none; border-radius:4px; }
.grid { display:flex; gap:40px; flex-wrap:wrap; margin-top:20px; }
.section { min-width:220px; }
.section h2 { font-size:1.05em; margin:0 0 6px; color:#007bff; }
ul { padding-left:18px; margin:4px 0 0; }
li { margin-bottom:4px; }
.empty { font-style:italic; color:#666; }
.category { color:#007bff; font-weight:bold; margin-top:18px; }
.total { margin-top:25px; font-weight:bold; color:#28a745; }
.motivation { font-style:italic; margin-top:10px; color:#444; }
</style>
</head>
<body>
<nav>
  <a href="{{ url_for('index') }}" class="{{ 'active' if active=='log' else '' }}">Log Workouts</a>
  <a href="{{ url_for('summary') }}" class="{{ 'active' if active=='summary' else '' }}">Summary</a>
  <a href="{{ url_for('workout_chart') }}" class="{{ 'active' if active=='chart' else '' }}">Workout Chart</a>
  <a href="{{ url_for('diet_chart') }}" class="{{ 'active' if active=='diet' else '' }}">Diet Chart</a>
</nav>
{% block content %}{% endblock %}
</body>
</html>
"""

app.jinja_loader = DictLoader({"base.html": BASE_HTML})

workouts = {"Warm-up": [], "Workout": [], "Cool-down": []}

WORKOUT_CHART = {
    "Warm-up": ["5 min Jog", "Jumping Jacks", "Arm Circles", "Leg Swings", "Dynamic Stretching"],
    "Workout": ["Push-ups", "Squats", "Plank", "Lunges", "Burpees", "Crunches"],
    "Cool-down": ["Slow Walking", "Static Stretching", "Deep Breathing", "Yoga Poses"]
}

DIET_PLANS = {
    "Weight Loss": ["Oatmeal with Fruits", "Grilled Chicken Salad", "Vegetable Soup", "Brown Rice & Stir-fry Veggies"],
    "Muscle Gain": ["Egg Omelet", "Chicken Breast", "Quinoa & Beans", "Protein Shake", "Greek Yogurt with Nuts"],
    "Endurance": ["Banana & Peanut Butter", "Whole Grain Pasta", "Sweet Potatoes", "Salmon & Avocado", "Trail Mix"]
}

INDEX_HTML = """
{% extends 'base.html' %}
{% block content %}
<h1>ACEest Fitness & Gym Tracker</h1>
{% if status %}
  <div class="status {% if 'Error:' in status %}error{% endif %}">{{ status }}</div>
{% endif %}
<form method="post" action="{{ url_for('add_session') }}">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />
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
{% endblock %}
"""

SUMMARY_HTML = """
{% extends 'base.html' %}
{% block content %}
<h1>Session Summary</h1>
{% for category, sessions in workouts.items() %}
  <div class="category">{{ category }}:</div>
  {% if sessions %}
    {% for s in sessions %}
      <div>{{ loop.index }}. {{ s.exercise }} - {{ s.duration }} min ({{ s.timestamp }})</div>
    {% endfor %}
  {% else %}
    <div class="empty">No sessions recorded.</div>
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
{% endblock %}
"""

WORKOUT_CHART_HTML = """
{% extends 'base.html' %}
{% block content %}
<h1>Personalized Workout Chart</h1>
{% for cat, items in chart.items() %}
  <div class="category">{{ cat }} Exercises:</div>
  <ul>
    {% for it in items %}
      <li>{{ it }}</li>
    {% endfor %}
  </ul>
{% endfor %}
{% endblock %}
"""

DIET_CHART_HTML = """
{% extends 'base.html' %}
{% block content %}
<h1>Best Diet Chart for Fitness Goals</h1>
{% for goal, foods in diets.items() %}
  <div class="category">{{ goal }} Plan:</div>
  <ul>
    {% for f in foods %}
      <li>{{ f }}</li>
    {% endfor %}
  </ul>
{% endfor %}
{% endblock %}
"""

def _render(tpl, **ctx):
    return render_template_string(tpl, workouts=workouts, **ctx)

@app.route("/", methods=["GET"])
def index():
    return _render(INDEX_HTML, status=request.args.get("status"), active="log")

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
    entry = {"exercise": exercise, "duration": duration, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    workouts.setdefault(category, []).append(entry)
    return redirect(url_for('index', status=f"Added {exercise} ({duration} min) to {category}!"))

@app.route("/summary")
def summary():
    total_time = sum(s["duration"] for v in workouts.values() for s in v)
    return _render(SUMMARY_HTML, total_time=total_time, active="summary")

@app.route("/chart")
def workout_chart():
    return _render(WORKOUT_CHART_HTML, chart=WORKOUT_CHART, active="chart")

@app.route("/diet")
def diet_chart():
    return _render(DIET_CHART_HTML, diets=DIET_PLANS, active="diet")

@app.route('/healthz')
def healthz():
  # Lightweight probe response; avoid heavy computations
  return jsonify({
    'status': 'ok',
    'csrf_enabled': True,
    'workout_categories': list(workouts.keys())
  }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)