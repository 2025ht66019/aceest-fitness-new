import os
import json
import io
import base64
import logging
from datetime import datetime
from threading import Lock
from flask import Flask, render_template, request, redirect, url_for, flash, current_app
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from matplotlib.figure import Figure
from typing import Optional

DATA_LOCK = Lock()
DEFAULT_DATA = {"Warm-up": [], "Workout": [], "Cool-down": []}

# Cache a single SECRET_KEY value so all Gunicorn workers share it.
_GLOBAL_SECRET: Optional[str] = None
# Removed persistent secret file approach to prevent race conditions across gunicorn workers.

# Module-level logger (safe outside app context)
logger = logging.getLogger(__name__)


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
    """Atomically persist workout data to configured DATA_FILE.

    Returns True on success, False if an OS error occurs (logged).
    """
    data_file = current_app.config['DATA_FILE']
    tmp_file = data_file + ".tmp"
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_file, data_file)
        return True
    except OSError as e:  # pragma: no cover (hard to simulate in tests reliably)
        current_app.logger.error(f"Failed to write data file '{data_file}': {e}")
        try:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
        except OSError:
            pass
        return False


def _get_global_secret(test_config: Optional[dict], testing: bool) -> str:
    """Return a stable SECRET_KEY (env or test override; ephemeral only for tests).

    Production MUST supply FLASK_SECRET_KEY or SECRET_KEY to avoid per-worker divergence.
    """
    global _GLOBAL_SECRET
    if _GLOBAL_SECRET:
        return _GLOBAL_SECRET

    if test_config and test_config.get('SECRET_KEY'):
        _GLOBAL_SECRET = test_config['SECRET_KEY']
        return _GLOBAL_SECRET

    env_secret = os.getenv('FLASK_SECRET_KEY') or os.getenv('SECRET_KEY')
    if env_secret:
        _GLOBAL_SECRET = env_secret
        return _GLOBAL_SECRET

    import secrets
    if not testing:
        # Enforce presence in production context
        if os.getenv('FLASK_ENFORCE_SECRET') == '1':
            raise RuntimeError('SECRET_KEY environment variable required (FLASK_ENFORCE_SECRET=1).')
        logger.warning('No FLASK_SECRET_KEY provided; generating ephemeral secret (NOT recommended for multi-worker).')
    _GLOBAL_SECRET = secrets.token_hex(32)
    return _GLOBAL_SECRET


def _register_routes(app: Flask) -> None:
    """Attach route view functions to app (isolated for lower complexity)."""

    @app.route('/', methods=['GET'])
    def index():
        data = load_data()
        categories = list(data.keys())
        return render_template('index.html', categories=categories)

    @app.route('/log', methods=['POST'])
    def log_workout():
        data = load_data()
        category = request.form.get('category', 'Workout')
        exercise = request.form.get('exercise', '').strip()
        duration_str = request.form.get('duration', '').strip()

        if not exercise or not duration_str:
            flash('Please provide both exercise and duration.', 'error')
            return redirect(url_for('index'))

        try:
            duration = int(duration_str)
            if duration <= 0:
                raise ValueError
        except ValueError:
            flash('Duration must be a positive whole number.', 'error')
            return redirect(url_for('index'))

        entry = {
            'exercise': exercise,
            'duration': duration,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        if category not in data:
            flash('Invalid category selected.', 'error')
            return redirect(url_for('index'))

        with DATA_LOCK:
            data[category].append(entry)
            if not save_data(data):
                flash('Failed to persist workout data (server filesystem issue).', 'error')
                return redirect(url_for('index'))

        flash(f'Added {exercise} ({duration} min) to {category}!', 'success')
        return redirect(url_for('index'))

    @app.route('/summary')
    def summary():
        data = load_data()
        total_time = sum(entry['duration'] for sessions in data.values() for entry in sessions)
        return render_template('summary.html', data=data, total_time=total_time)

    @app.route('/plan')
    def plan():
        # Updated to match enhanced GUI workout plan detail (ACEest FitnessTrackerApp)
        chart_data = {
            'Warm-up (5-10 min)': [
                '5 min light cardio (Jog/Cycle) to raise heart rate.',
                'Jumping Jacks (30 reps) for dynamic mobility.',
                'Arm Circles (15 Fwd/Bwd) to prepare shoulders.'
            ],
            'Strength & Cardio (45-60 min)': [
                'Push-ups (3 sets of 10-15) - Upper body strength.',
                'Squats (3 sets of 15-20) - Lower body foundation.',
                'Plank (3 sets of 60 seconds) - Core stabilization.',
                'Lunges (3 sets of 10/leg) - Balance and leg development.'
            ],
            'Cool-down (5 min)': [
                'Slow Walking - Bring heart rate down gradually.',
                'Static Stretching (Hold 30s each) - Focus on major muscle groups.',
                'Deep Breathing Exercises - Aid recovery and relaxation.'
            ]
        }
        return render_template('plan.html', chart_data=chart_data)

    @app.route('/diet')
    def diet():
        # Updated diet guide to reflect GUI nutritional goal setting details.
        diet_plans = {
            '🎯 Weight Loss Focus (Calorie Deficit)': [
                'Breakfast: Oatmeal with Berries (High Fiber).',
                'Lunch: Grilled Chicken/Tofu Salad (Lean Protein).',
                'Dinner: Vegetable Soup with Lentils (Low Calorie, High Volume).'
            ],
            '💪 Muscle Gain Focus (High Protein)': [
                'Breakfast: 3 Egg Omelet, Spinach, Whole-wheat Toast (Protein/Carb combo).',
                'Lunch: Chicken Breast, Quinoa, and Steamed Veggies (Balanced Meal).',
                'Post-Workout: Protein Shake & Greek Yogurt (Immediate Recovery).'
            ],
            '🏃 Endurance Focus (Complex Carbs)': [
                'Pre-Workout: Banana & Peanut Butter (Quick Energy).',
                'Lunch: Whole Grain Pasta with Light Sauce (Sustainable Carbs).',
                'Dinner: Salmon & Avocado Salad (Omega-3s and Healthy Fats).'
            ]
        }
        return render_template('diet.html', diet_plans=diet_plans)

    @app.route('/progress')
    def progress():
        data = load_data()
        totals = {cat: sum(e['duration'] for e in sessions) for cat, sessions in data.items()}
        total_minutes = sum(totals.values())

        chart_img = None
        if total_minutes > 0:
            fig = Figure(figsize=(7.5, 4.5), dpi=100, facecolor='white')
            colors = ['#007bff', '#28a745', '#ffc107']

            ax1 = fig.add_subplot(121)
            categories = list(totals.keys())
            values = list(totals.values())
            ax1.bar(categories, values, color=colors)
            ax1.set_title('Time Spent per Category (Min)', fontsize=10)
            ax1.set_ylabel('Total Minutes', fontsize=8)
            ax1.tick_params(axis='x', labelsize=8)
            ax1.tick_params(axis='y', labelsize=8)
            ax1.grid(axis='y', linestyle='--', alpha=0.7)

            ax2 = fig.add_subplot(122)
            pie_labels = [c for c, v in totals.items() if v > 0]
            pie_values = [v for v in totals.values() if v > 0]
            pie_colors = [colors[i] for i, v in enumerate(values) if v > 0]
            ax2.pie(
                pie_values,
                labels=pie_labels,
                autopct='%1.1f%%',
                startangle=90,
                colors=pie_colors,
                wedgeprops={'edgecolor': 'black', 'linewidth': 0.5},
                textprops={'fontsize': 8},
            )
            ax2.set_title('Workout Distribution', fontsize=10)
            ax2.axis('equal')

            fig.tight_layout(pad=2.0)
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            chart_img = base64.b64encode(buf.read()).decode('utf-8')

        return render_template('progress.html', totals=totals, total_minutes=total_minutes, chart_img=chart_img)


def create_app(test_config: Optional[dict] = None) -> Flask:
    """Application factory with reduced cognitive complexity (<15)."""
    app = Flask(__name__)
    testing = bool(test_config and test_config.get('TESTING')) or bool(os.getenv('PYTEST_CURRENT_TEST'))
    # Secret key resolved via helper; never hard-coded.
    app.config['SECRET_KEY'] = _get_global_secret(test_config, testing)  # NOSONAR env/ephemeral sourced + cached
    app.config.setdefault('SESSION_COOKIE_SAMESITE', 'Lax')
    app.config.setdefault('SESSION_COOKIE_HTTPONLY', True)
    app.config.setdefault('WTF_CSRF_ENABLED', not testing)

    # Re-enable CSRF protection (disabled automatically when testing flag set)
    if not testing:
        CSRFProtect(app)

    # Data file configuration: allow env override (DATA_FILE) else default under application directory.
    default_data_path = os.path.join(os.path.dirname(__file__), 'data.json')
    env_data_path = os.getenv('DATA_FILE')
    app.config.setdefault('DATA_FILE', env_data_path if env_data_path else default_data_path)
    # If directory is not writable, attempt permissive warning so user sees flash message instead of silent failure.
    data_dir = os.path.dirname(app.config['DATA_FILE']) or '.'
    if not os.access(data_dir, os.W_OK):  # pragma: no cover (environment dependent)
        logger.warning(f"Data directory '{data_dir}' not writable for user; workout logs may fail to persist.")
    if test_config:
        app.config.update(test_config)

    # Ensure Matplotlib config directory writable (defensive runtime fix)
    mpl_dir = os.getenv('MPLCONFIGDIR')
    if mpl_dir and not os.path.exists(mpl_dir):
        try:
            os.makedirs(mpl_dir, exist_ok=True)
        except OSError as e:  # pragma: no cover
            logger.warning(f"Unable to create MPLCONFIGDIR '{mpl_dir}': {e}")

    _register_routes(app)
    # Provide csrf_token helper for templates using manual forms
    @app.context_processor
    def inject_csrf():  # pragma: no cover simple helper
        return {"csrf_token": generate_csrf}
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
