from flask import Flask, render_template_string, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

workouts = []

TEMPLATE = '''
<!doctype html>
<title>ACEestFitness and Gym</title>
<h1>ACEestFitness and Gym</h1>
<form method="post" action="{{ url_for('add_workout') }}">
    <label>Workout:</label>
    <input type="text" name="workout" required>
    <label>Duration (minutes):</label>
    <input type="number" name="duration" required>
    <input type="submit" value="Add Workout">
</form>
{% with messages = get_flashed_messages() %}
  {% if messages %}
    <ul style="color: red;">
    {% for message in messages %}
      <li>{{ message }}</li>
    {% endfor %}
    </ul>
  {% endif %}
{% endwith %}
<h2>Logged Workouts:</h2>
{% if workouts %}
    <ul>
    {% for entry in workouts %}
        <li>{{ entry['workout'] }} - {{ entry['duration'] }} minutes</li>
    {% endfor %}
    </ul>
{% else %}
    <p>No workouts logged yet.</p>
{% endif %}
'''

@app.route('/', methods=['GET'])
def index():
    return render_template_string(TEMPLATE, workouts=workouts)

@app.route('/add', methods=['POST'])
def add_workout():
    workout = request.form.get('workout')
    duration = request.form.get('duration')
    if not workout or not duration:
        flash('Please enter both workout and duration.')
        return redirect(url_for('index'))
    try:
        duration_int = int(duration)
        workouts.append({'workout': workout, 'duration': duration_int})
        flash(f"'{workout}' added successfully!")
    except ValueError:
        flash('Duration must be a number.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')