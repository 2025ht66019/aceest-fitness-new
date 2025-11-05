import os
import json
import io
import base64
from datetime import datetime
from threading import Lock
from flask import Flask, render_template, request, redirect, url_for, flash, current_app
from flask_wtf import CSRFProtect
from matplotlib.figure import Figure
from typing import Optional

DATA_LOCK = Lock()
DEFAULT_DATA = {"Warm-up": [], "Workout": [], "Cool-down": []}


def load_data():
    """Load workout data from the configured DATA_FILE."""
    data_file = current_app.config['DATA_FILE']
    if not os.path.exists(data_file):
        return DEFAULT_DATA.copy()
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in DEFAULT_DATA.keys():
            data.setdefault(k, [])
        return data
    except (json.JSONDecodeError, OSError):
        return DEFAULT_DATA.copy()


def save_data(data):
    """Atomically persist workout data to configured DATA_FILE."""
    data_file = current_app.config['DATA_FILE']
    tmp_file = data_file + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_file, data_file)


def create_app(test_config: Optional[dict] = None) -> Flask:
    """Application factory so tests can create isolated instances.

    test_config can override DATA_FILE, SECRET_KEY, DEBUG, etc.
    """
    app = Flask(__name__)
    # Secure secret key handling: require env variable in non-testing contexts to avoid hard-coded credentials.
    # Derive secret key with secure fallbacks. Never hard-code; generate ephemeral if missing.
    if test_config and test_config.get('SECRET_KEY'):
        secret_key = test_config['SECRET_KEY']
    else:
        secret_key = os.getenv('FLASK_SECRET_KEY') or os.getenv('SECRET_KEY')
        if not secret_key:
            import secrets
            secret_key = secrets.token_hex(32)
            # Optional enforcement: set FLASK_ENFORCE_SECRET=1 to force failure when secret not set.
            if os.getenv('FLASK_ENFORCE_SECRET') == '1':
                raise RuntimeError('SECRET_KEY environment variable required (FLASK_ENFORCE_SECRET=1).')
    # Assignment required by Flask; value is sourced from env or ephemeral random token, never a static literal.
    # nosec B105 (not a hard-coded credential)  # sonar-ignore-security: generated/ephemeral, not hard-coded
    app.config['SECRET_KEY'] = secret_key

    # Enable CSRF protection except during tests to keep fixtures simple.
    if not (test_config and test_config.get('TESTING')):
        CSRFProtect(app)
    app.config.setdefault('DATA_FILE', os.path.join(os.path.dirname(__file__), 'data.json'))

    if test_config:
        app.config.update(test_config)

    # ---- Routes ---- #
    @app.route("/", methods=["GET"])
    def index():
        data = load_data()
        categories = list(data.keys())
        return render_template("index.html", categories=categories)

    @app.route("/log", methods=["POST"])
    def log_workout():
        data = load_data()
        category = request.form.get("category", "Workout")
        exercise = request.form.get("exercise", "").strip()
        duration_str = request.form.get("duration", "").strip()

        if not exercise or not duration_str:
            flash("Please provide both exercise and duration.", "error")
            return redirect(url_for("index"))

        try:
            duration = int(duration_str)
            if duration <= 0:
                raise ValueError
        except ValueError:
            flash("Duration must be a positive whole number.", "error")
            return redirect(url_for("index"))

        entry = {
            "exercise": exercise,
            "duration": duration,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        if category not in data:
            flash("Invalid category selected.", "error")
            return redirect(url_for("index"))

        with DATA_LOCK:
            data[category].append(entry)
            save_data(data)

        flash(f"Added {exercise} ({duration} min) to {category}!", "success")
        return redirect(url_for("index"))

    @app.route("/summary")
    def summary():
        data = load_data()
        total_time = sum(entry['duration'] for sessions in data.values() for entry in sessions)
        return render_template("summary.html", data=data, total_time=total_time)

    @app.route("/plan")
    def plan():
        chart_data = {
            "Warm-up (5-10 min)": ["5 min light cardio (Jog/Cycle)", "Jumping Jacks (30 reps)", "Arm Circles (15 Fwd/Bwd)"],
            "Strength Workout (45-60 min)": ["Push-ups (3 sets of 10-15)", "Squats (3 sets of 15-20)", "Plank (3 sets of 60 seconds)", "Lunges (3 sets of 10/leg)"],
            "Cool-down (5 min)": ["Slow Walking", "Static Stretching (Hold 30s each)", "Deep Breathing Exercises"]
        }
        return render_template("plan.html", chart_data=chart_data)

    @app.route("/diet")
    def diet():
        diet_plans = {
            "Weight Loss": ["Breakfast: Oatmeal with Berries", "Lunch: Grilled Chicken/Tofu Salad", "Dinner: Vegetable Soup with Lentils"],
            "Muscle Gain": ["Breakfast: 3 Egg Omelet, Spinach, Whole-wheat Toast", "Lunch: Chicken Breast, Quinoa, and Steamed Veggies", "Post-Workout: Protein Shake, Greek Yogurt"],
            "Endurance Focus": ["Pre-Workout: Banana & Peanut Butter", "Lunch: Whole Grain Pasta with Light Sauce", "Dinner: Salmon & Avocado Salad"]
        }
        return render_template("diet.html", diet_plans=diet_plans)

    @app.route("/progress")
    def progress():
        data = load_data()
        totals = {cat: sum(e['duration'] for e in sessions) for cat, sessions in data.items()}
        total_minutes = sum(totals.values())

        chart_img = None
        if total_minutes > 0:
            fig = Figure(figsize=(7.5, 4.5), dpi=100, facecolor='white')
            colors = ["#007bff", "#28a745", "#ffc107"]

            ax1 = fig.add_subplot(121)
            categories = list(totals.keys())
            values = list(totals.values())
            ax1.bar(categories, values, color=colors)
            ax1.set_title("Time Spent per Category (Min)", fontsize=10)
            ax1.set_ylabel("Total Minutes", fontsize=8)
            ax1.tick_params(axis='x', labelsize=8)
            ax1.tick_params(axis='y', labelsize=8)
            ax1.grid(axis='y', linestyle='--', alpha=0.7)

            ax2 = fig.add_subplot(122)
            pie_labels = [c for c, v in totals.items() if v > 0]
            pie_values = [v for v in totals.values() if v > 0]
            pie_colors = [colors[i] for i, v in enumerate(values) if v > 0]
            ax2.pie(pie_values, labels=pie_labels, autopct="%1.1f%%", startangle=90, colors=pie_colors,
                    wedgeprops={"edgecolor": "black", 'linewidth': 0.5}, textprops={'fontsize': 8})
            ax2.set_title("Workout Distribution", fontsize=10)
            ax2.axis('equal')

            fig.tight_layout(pad=2.0)
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            chart_img = base64.b64encode(buf.read()).decode('utf-8')

        return render_template("progress.html", totals=totals, total_minutes=total_minutes, chart_img=chart_img)

    return app


_is_pytest = bool(os.getenv('PYTEST_CURRENT_TEST'))
if _is_pytest:
    # Ensure TESTING flag so ephemeral secret + CSRF disabled for predictable tests.
    app = create_app({'TESTING': True})
else:
    app = create_app()

if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    create_app({'DEBUG': debug}).run(host=host, port=port, debug=debug)
