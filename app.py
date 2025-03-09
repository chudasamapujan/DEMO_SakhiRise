from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import psycopg2
from psycopg2 import OperationalError
import logging
import numpy as np  # For simple AI prediction

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration (update with your credentials)
DB_USER = 'postgres'
DB_PASSWORD = 'your_password'  # Replace with your actual password
DB_HOST = 'localhost'
DB_NAME = 'sakhiRise_db'
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Period Tracking Model
class PeriodLog(db.Model):
    __tablename__ = 'period_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    cycle_length = db.Column(db.Integer)  # Nullable for AI to predict
    symptoms = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create database if it doesn’t exist
def create_database():
    try:
        conn = psycopg2.connect(f"dbname=postgres user={DB_USER} password={DB_PASSWORD} host={DB_HOST}")
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            logger.info(f"Database '{DB_NAME}' created successfully!")
        cursor.close()
        conn.close()
    except OperationalError as e:
        logger.error(f"Failed to create database: {e}")
        raise

# Initialize tables
def init_db():
    try:
        with app.app_context():
            db.create_all()
        logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

# Simple AI prediction for cycle length
def predict_cycle_length(user_id):
    logs = PeriodLog.query.filter_by(user_id=user_id).order_by(PeriodLog.created_at).all()
    if len(logs) < 2:
        return 28  # Default if insufficient data
    # Calculate differences between consecutive start dates
    cycle_lengths = []
    for i in range(1, len(logs)):
        delta = (logs[i].start_date - logs[i-1].start_date).days
        cycle_lengths.append(delta)
    return int(np.mean(cycle_lengths))  # Average cycle length

# Route for Periods Tracker Page
@app.route('/track_periods', methods=['GET', 'POST'])
def track_periods():
    if request.method == 'POST':
        try:
            start_date_str = request.form['start_date']
            cycle_length = request.form.get('cycle_length')
            symptoms = ','.join(request.form.getlist('symptoms')) if 'symptoms' in request.form else None
            notify = 'notify' in request.form and request.form['notify'] == 'yes'

            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            user_id = 1  # Placeholder; integrate with auth later

            # Use provided cycle length or predict with AI
            if cycle_length:
                cycle_length = int(cycle_length)
            else:
                cycle_length = predict_cycle_length(user_id)

            next_period = start_date + timedelta(days=cycle_length)

            # Store in database
            new_log = PeriodLog(user_id=user_id, start_date=start_date, cycle_length=cycle_length, symptoms=symptoms)
            db.session.add(new_log)
            db.session.commit()

            # Simulated notification message
            notification = "You’ll be notified 2 days before!" if notify else "No notification set."

            response = {
                'next_period': next_period.strftime('%Y-%m-%d'),
                'symptoms': symptoms if symptoms else 'None',
                'notification': notification
            }
            return jsonify(response), 200
        except Exception as e:
            logger.error(f"Error processing period data: {e}")
            return jsonify({'error': str(e)}), 500

    return render_template('periods_tracker.html')

# Route to fetch past logs
@app.route('/get_period_logs', methods=['GET'])
def get_period_logs():
    try:
        user_id = 1  # Placeholder
        logs = PeriodLog.query.filter_by(user_id=user_id).order_by(PeriodLog.created_at.desc()).all()
        log_data = [{'start_date': log.start_date.strftime('%Y-%m-%d'), 'cycle_length': log.cycle_length} for log in logs]
        return jsonify({'logs': log_data}), 200
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    try:
        create_database()
        init_db()
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")