from flask import Flask, render_template_string, request, redirect, url_for, send_file
import io, datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from jinja2 import DictLoader

app = Flask(__name__)

workouts = {
    "Warm-up": [],
    "Workout": [],
    "Cool-down": []
}

TEMPLATE_BASE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>ACEest Fitness (Flask)</title>
<style>
body { font-family: Arial; margin:25px; }
nav a { margin-right:14px; font-weight:bold; text-decoration:none; color:#007bff; }
.active { text-decoration:underline; }
h1 { margin-top:0; }
form { padding:14px 18px; border:1px solid #ddd; border-radius:6px; max-width:360px; background:#fafafa; }
label { display:block; margin-top:10px; font-weight:bold; }
input, select { width:100%; padding:6px; margin-top:4px; }
button { margin-top:14px; padding:8px 14px; background:#007bff; color:#fff; border:none; cursor:pointer; }
.section { margin-top:25px; }
.empty { font-style:italic; color:#666; }
.total { font-weight:bold; margin-top:20px; color:#28a745; }
.chart { margin-top:25px; }
.flash { font-weight:bold; margin:12px 0; }
.error { color:#a00; }
.success { color:#0a0; }
</style>
</head>
<body>
<nav>
  <a href="{{ url_for('index') }}" class="{{ 'active' if active=='log' else '' }}">Log</a>
  <a href="{{ url_for('summary') }}" class="{{ 'active' if active=='summary' else '' }}">Summary</a>
  <a href="{{ url_for('chart') }}" class="{{ 'active' if active=='chart' else '' }}">Chart</a>
  <a href="{{ url_for('api_docs') }}" class="{{ 'active' if active=='api' else '' }}">API</a>
</nav>
{% block content %}{% endblock %}
</body>
</html>
"""

# Register base template
app.jinja_loader = DictLoader({"base.html": TEMPLATE_BASE})

INDEX_HTML = """
{% extends 'base.html' %}
{% block content %}
<h1>ACEest Fitness (Flask)</h1>
{% if msg %}
  <div class="flash {{ 'error' if 'Error:' in msg else 'success' }}">{{ msg }}</div>
{% endif %}
<form method="post" action="{{ url_for('add') }}">
  <label>Category</label>
  <select name="category">
    {% for c in workouts.keys() %}
      <option value="{{ c }}">{{ c }}</option>
    {% endfor %}
  </select>
  <label>Exercise</label>
  <input name="exercise" placeholder="Push Ups">
  <label>Duration (minutes)</label>
  <input name="duration" type="number" min="1" step="1">
  <button type="submit">Add</button>
</form>
{% for cat, items in workouts.items() %}
  <div class="section">
    <h2>{{ cat }}</h2>
    {% if items %}
      <ul>
        {% for s in items %}
          <li>{{ s.exercise }} - {{ s.duration }} min ({{ s.timestamp }})</li>
        {% endfor %}
      </ul>
    {% else %}
      <div class="empty">No entries yet.</div>
    {% endif %}
  </div>
{% endfor %}
{% endblock %}
"""

SUMMARY_HTML = """
{% extends 'base.html' %}
{% block content %}
<h1>Summary</h1>
{% for cat, items in workouts.items() %}
  <h3>{{ cat }}</h3>
  {% if items %}
    <ul>
    {% for s in items %}
      <li>{{ s.exercise }} - {{ s.duration }} min</li>
    {% endfor %}
    </ul>
  {% else %}
    <div class="empty">No sessions recorded.</div>
  {% endif %}
{% endfor %}
<div class="total">Total: {{ total }} minutes</div>
{% endblock %}
"""

CHART_HTML = """
{% extends 'base.html' %}
{% block content %}
<h1>Duration Chart</h1>
<p>Aggregated duration per category.</p>
<div class="chart">
  <img src="{{ url_for('chart_image') }}" alt="Workout Chart">
</div>
{% endblock %}
"""

API_HTML = """
{% extends 'base.html' %}
{% block content %}
<h1>API Endpoints</h1>
<ul>
  <li>GET /api/workouts</li>
  <li>POST /api/workouts {"category":"Workout","exercise":"Squats","duration":15}</li>
  <li>GET /api/summary</li>
</ul>
{% endblock %}
"""

def render(tpl, **ctx):
    return render_template_string(tpl, workouts=workouts, **ctx)

@app.route("/")
def index():
    return render(INDEX_HTML, msg=request.args.get("msg"), active="log")

@app.route("/add", methods=["POST"])
def add():
    cat = request.form.get("category", "Workout")
    ex = request.form.get("exercise", "").strip()
    dur_raw = request.form.get("duration", "").strip()
    if not ex or not dur_raw:
        return redirect(url_for("index", msg="Error: exercise and duration required"))
    try:
        dur = int(dur_raw)
    except ValueError:
        return redirect(url_for("index", msg="Error: duration must be number"))
    entry = {"exercise": ex, "duration": dur, "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    workouts.setdefault(cat, []).append(entry)
    return redirect(url_for("index", msg=f"Added {ex} ({dur} min) to {cat}!"))

@app.route("/summary")
def summary():
    total = sum(s["duration"] for v in workouts.values() for s in v)
    return render(SUMMARY_HTML, total=total, active="summary")

@app.route("/chart")
def chart():
    return render(CHART_HTML, active="chart")

@app.route("/chart.png")
def chart_image():
    cats = list(workouts.keys())
    totals = [sum(s["duration"] for s in workouts[c]) for c in cats]
    fig, ax = plt.subplots(figsize=(5,3))
    ax.bar(cats, totals, color="#007bff")
    ax.set_ylabel("Minutes")
    ax.set_title("Workout Duration")
    ax.grid(axis="y", alpha=0.25)
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

@app.route("/api")
def api_docs():
    return render(API_HTML, active="api")

@app.route("/api/workouts", methods=["GET"])
def api_workouts_get():
    return {"workouts": workouts}

@app.route("/api/workouts", methods=["POST"])
def api_workouts_post():
    data = request.get_json(force=True, silent=True) or {}
    cat = data.get("category", "Workout")
    ex = data.get("exercise", "").strip()
    dur = data.get("duration")
    if not ex or dur is None:
        return {"error": "exercise and duration required"}, 400
    try:
        dur = int(dur)
    except ValueError:
        return {"error": "duration must be integer"}, 400
    entry = {"exercise": ex, "duration": dur, "timestamp": datetime.datetime.now().isoformat(timespec="seconds")}
    workouts.setdefault(cat, []).append(entry)
    return {"status": "ok", "added": entry}, 201

@app.route("/api/summary")
def api_summary():
    return {
        "total_minutes": sum(s["duration"] for v in workouts.values() for s in v),
        "by_category": {c: sum(s["duration"] for s in v) for c, v in workouts.items()}
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)