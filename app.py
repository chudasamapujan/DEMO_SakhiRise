from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Database configuration (update with your credentials)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:your_password@localhost/sakhiRise_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Period Tracking Model
class PeriodLog(db.Model):
    __tablename__ = 'period_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # Placeholder; integrate with auth later
    start_date = db.Column(db.Date, nullable=False)
    cycle_length = db.Column(db.Integer, nullable=False)
    symptoms = db.Column(db.String(200))  # Comma-separated symptoms
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Function to initialize database
def init_db():
    try:
        with app.app_context():
            db.create_all()
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating database tables: {e}")

# Route for Periods Tracker Page
@app.route('/track_periods', methods=['GET', 'POST'])
def track_periods():
    if request.method == 'POST':
        try:
            # Get form data
            start_date_str = request.form['start_date']
            cycle_length = int(request.form['cycle_length'])
            symptoms = ','.join(request.form.getlist('symptoms')) if 'symptoms' in request.form else None

            # Convert start date to datetime
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

            # Calculate next period
            next_period = start_date + timedelta(days=cycle_length)

            # Store in database (user_id=1 for demo)
            new_log = PeriodLog(user_id=1, start_date=start_date, cycle_length=cycle_length, symptoms=symptoms)
            db.session.add(new_log)
            db.session.commit()

            # Prepare response
            response = {
                'next_period': next_period.strftime('%Y-%m-%d'),
                'symptoms': symptoms if symptoms else 'None'
            }
            return jsonify(response), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # GET request renders the page
    return render_template('periods_tracker.html')

# Home page route (for reference)
@app.route('/')
def home():
    return render_template('index.html')  # Assumes index.html exists

if __name__ == '__main__':
    # Initialize database before running the app
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)