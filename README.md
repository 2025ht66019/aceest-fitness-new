# ACEest Fitness Tracker (Web Version)

Converted from a Tkinter desktop GUI to a Flask web application.

## Features
- Log workout sessions by category (Warm-up, Workout, Cool-down)
- View weekly/session summary with total minutes
- Predefined workout plan suggestions
- Diet guide for different fitness goals
- Progress page with dynamic bar + pie charts rendered server-side via Matplotlib

## Tech Stack
- Python (Flask, Matplotlib)
- Jinja2 templates
- Simple JSON file persistence (`data.json` in project root)

### Quick Start
```bash
# From project root
# (Ensure virtual environment already created; if not, create one)
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# Install dependencies
pip install -r requirements.txt
# Run server
python app.py
# Open browser: http://127.0.0.1:5000
```

## Data Persistence
Workout logs are stored in `data.json`. This is NOT suitable for multi-user or production deployment. For scaling, migrate to SQLite or PostgreSQL and replace `load_data()` / `save_data()` with DB operations.

## Project Structure
```
app.py                # Flask application entrypoint
ACEest_Fitness-V1.2.2.py # Original Tkinter script (reference)
requirements.txt      # Python dependencies
templates/            # Jinja HTML templates
static/style.css      # Stylesheet
data.json             # Created automatically after first log
README.md             # This file
```

## Environment Variables (Optional)
You can override host/port/debug:
```
FLASK_HOST=0.0.0.0
FLASK_PORT=8000
FLASK_DEBUG=false
```

## Next Improvements
- Add user authentication (Flask-Login)
- Persist data to SQLite (SQLAlchemy)
- Replace server-side Matplotlib with client-side Chart.js for lighter response
- Add export (CSV/JSON) for workout history
- Add weekly aggregation and trend lines

## License
Internal / Unspecified. Add a proper license file if distributing.
