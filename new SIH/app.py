from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import pandas as pd
import sys
import numpy as np
import os
import matplotlib.pyplot as plt
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here' # Set a secret key for sessions

# --- Hardcoded Credentials ---
ADMIN_CREDENTIALS = {"username": "admin", "password": "password123"}
# Mentor credentials will be generated dynamically
MENTOR_CREDENTIALS = {}

# --- AI Script Functions (Integrated from ai.py) ---
def load_student_data(filepath):
    """Loads student data and maps columns to a standard format."""
    try:
        df = pd.read_csv(filepath)
        print("✅ Student data loaded successfully.")
    except FileNotFoundError:
        print(f"❌ Error: The file at {filepath} was not found.")
        return None
    df.columns = [col.strip().replace(' ', '_').replace('_(%)', '').replace('%', '') for col in df.columns]
    rename_map = {
        'Student_Name': 'student_name', 'Student_ID': 'student_id',
        'Attendance': 'attendance', 'CGPA': 'cgpa',
        'Fees_Amount_Due': 'Fees_Amount_Due', 'Backlogs': 'internals'
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    bins = [-1, 0, 40000, 60000, 80000, 100000, np.inf]
    labels = ['none', 'very small', 'small', 'medium', 'large', 'very large']
    df['financial_default'] = pd.cut(df['Fees_Amount_Due'], bins=bins, labels=labels, right=True)
    df['internals_attempted'] = df['internals'].clip(upper=3)
    print("✅ Student dataset columns mapped to required format.")
    return df

def load_mentor_data(filepath):
    """Loads the mentor dataset from a CSV file."""
    try:
        df = pd.read_csv(filepath)
        print("✅ Mentor data loaded successfully from file.")
        return df
    except FileNotFoundError:
        print(f"❌ Error: The mentor file at {filepath} was not found.")
        return None
    return df

def calculate_risk_scores(df):
    """Calculates various risk scores and the final risk category for each student."""
    financial_map = {
        'none': 0, 'very small': 1, 'small': 3, 'medium': 6, 'large': 8, 'very large': 10
    }
    df['financial_risk'] = df['financial_default'].map(financial_map).astype(float)
    att_bins = [-1, 49, 65, 75, 101]
    att_labels = [9, 7, 4, 0]
    df['attendance_risk'] = pd.cut(df['attendance'], bins=att_bins, labels=att_labels, right=True).astype(float)
    internals_map = {0: 8, 1: 6, 2: 3, 3: 0}
    df['internals_risk'] = df['internals_attempted'].map(internals_map).astype(float)
    cgpa_bins = [-1, 4.99, 6, 7, 8, 11]
    cgpa_labels = [8, 6, 4, 2, 0]
    df['cgpa_risk'] = pd.cut(df['cgpa'], bins=cgpa_bins, labels=cgpa_labels, right=True).astype(float)
    weights = {'financial': 0.45, 'attendance': 0.30, 'internals': 0.15, 'cgpa': 0.10}
    df['final_risk_score'] = (
        df['financial_risk'] * weights['financial'] +
        df['attendance_risk'] * weights['attendance'] +
        df['internals_risk'] * weights['internals'] +
        df['cgpa_risk'] * weights['cgpa']
    )
    risk_bins = [-1, 3, 6, 11]
    risk_labels = ['Low Risk', 'Medium Risk', 'High Risk']
    df['risk_category'] = pd.cut(df['final_risk_score'], bins=risk_bins, labels=risk_labels, right=True)
    print("✅ Risk scores and categories calculated (with granular financial risk).")
    return df

def provide_counselling_suggestions(df):
    """Generates academic and attendance advice."""
    suggestions = []
    for _, row in df.iterrows():
        student_suggestions = []
        if row['cgpa'] < 6.5:
            student_suggestions.append("Needs academic support (bi-weekly mentoring, study workshops).")
        if row['attendance'] < 60:
            student_suggestions.append("Counselling for attendance issues is recommended.")
        if not student_suggestions:
            suggestions.append("Good. Monitor progress and encourage continued performance.")
        else:
            suggestions.append(" ".join(student_suggestions))
    df['counselling_suggestions'] = suggestions
    print("✅ Academic counselling suggestions generated.")
    return df

def provide_financial_aid_suggestions(df):
    """Generates financial aid advice based on the financial risk score."""
    suggestions = []
    for _, row in df.iterrows():
        if row['financial_risk'] >= 8.0:
            suggestions.append("Urgent: Suggest emergency financial aid or government scholarships.")
        elif row['financial_risk'] >= 3.0:
            suggestions.append("Suggest scholarships or explore fee installment plans.")
        else:
            suggestions.append("No immediate action needed for fees.")
    df['financial_aid_suggestions'] = suggestions
    print("✅ Financial aid suggestions generated.")
    return df

def balanced_mentor_allocation(students_df, mentors_df):
    """Assigns students to mentors from the loaded dataset, balancing the load."""
    allocation = {}
    mentor_names = mentors_df['mentor_name'].tolist()
    num_mentors = len(mentor_names)
    for risk_level in ['High Risk', 'Medium Risk', 'Low Risk']:
        if risk_level in students_df['risk_category'].unique():
            students_in_group = students_df[students_df['risk_category'] == risk_level]['student_id'].tolist()
            np.random.shuffle(students_in_group)
            for i, student_id in enumerate(students_in_group):
                mentor_assigned = mentor_names[i % num_mentors]
                allocation[student_id] = mentor_assigned
    print("✅ Balanced allocation using real mentor data complete.")
    return allocation

# --- Data Generation and Preparation ---
def generate_student_data():
    """Loads pre-calculated student data from the provided CSV report."""
    student_report_filepath = "student_counselling_report_with_suggestions.csv"
    mentor_filepath = "mentors_dataset.csv"

    try:
        # Load the pre-processed student data
        df = pd.read_csv(student_report_filepath)
        print("✅ Student report loaded successfully.")
    except FileNotFoundError:
        print(f"❌ Error: The file at {student_report_filepath} was not found.")
        return None

    mentors = load_mentor_data(mentor_filepath)
    if mentors is not None:
        global MENTOR_CREDENTIALS
        mentor_name_map = {}
        for _, row in mentors.iterrows():
            MENTOR_CREDENTIALS[row['username']] = row['password']
            mentor_name_map[row['username']] = row['mentor_name']
        
        global MENTOR_NAME_MAP
        MENTOR_NAME_MAP = mentor_name_map
    
    # Ensure all required columns are present and data types are correct
    required_cols = ['student_name', 'student_id', 'cgpa', 'internals', 'attendance', 'Fees_Amount_Due', 'financial_default', 'final_risk_score', 'risk_category', 'counselling_suggestions', 'financial_aid_suggestion', 'mentor_name']
    if not all(col in df.columns for col in required_cols):
        print("❌ Error: Student report CSV is missing required columns.")
        return None
    
    # Correcting column names for consistency
    df = df.rename(columns={'financial_aid_suggestion': 'financial_aid_suggestions'})

    print("✅ Student dataset columns mapped to required format.")
    return df

# Generate the data once when the application starts
df_final = generate_student_data()
if df_final is not None:
    students_data = df_final.to_dict(orient='records')
    print("✅ Successfully generated student data for the dashboard.")
else:
    students_data = []
    print("\n❌ FATAL ERROR: Data generation failed. Check CSV files.")

# --- Page Routes ---
@app.route('/')
def login_page():
    """Renders the main login page."""
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    """Renders the admin dashboard page."""
    if session.get('user_type') == 'admin':
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login_page'))

@app.route('/mentor_dashboard')
def mentor_dashboard():
    """Renders the mentor dashboard page."""
    if session.get('user_type') == 'mentor':
        return render_template('mentor_dashboard.html', mentor_name=session.get('mentor_name'))
    else:
        return redirect(url_for('login_page'))

# --- API Endpoints ---
@app.route('/login', methods=['POST'])
def handle_login():
    """Handles the login form submission."""
    login_type = request.form.get('type')
    username = request.form.get('username')
    password = request.form.get('password')

    valid_login = False
    redirect_page = url_for('login_page')

    if login_type == 'admin':
        if username == ADMIN_CREDENTIALS['username'] and password == ADMIN_CREDENTIALS['password']:
            valid_login = True
            session['user_type'] = 'admin'
            redirect_page = url_for('dashboard')
    elif login_type == 'mentor':
        if username in MENTOR_CREDENTIALS and password == MENTOR_CREDENTIALS[username]:
            valid_login = True
            session['user_type'] = 'mentor'
            session['mentor_name'] = MENTOR_NAME_MAP[username]
            redirect_page = url_for('mentor_dashboard')

    if valid_login:
        return redirect(redirect_page)
    else:
        error_message = "Invalid username or password. Please try again."
        return render_template('login.html', error=error_message)

@app.route('/api/students')
def get_students():
    """API endpoint to get all student data (for admin)."""
    if session.get('user_type') != 'admin':
        return jsonify({"error": "Unauthorized access"}), 403
    return jsonify(students_data)

@app.route('/api/mentor_students')
def get_mentor_students():
    """API endpoint to get students for the logged-in mentor."""
    if session.get('user_type') != 'mentor':
        return jsonify({"error": "Unauthorized access"}), 403

    logged_in_mentor_name = session.get('mentor_name')
    mentor_students = [s for s in students_data if s['mentor_name'] == logged_in_mentor_name]
    return jsonify(mentor_students)

@app.route('/api/statistics')
def get_statistics():
    """API endpoint for dashboard summary statistics (for admin)."""
    if session.get('user_type') != 'admin':
        return jsonify({"error": "Unauthorized access"}), 403
    if not students_data:
        return jsonify({"total": 0, "high_risk": 0, "medium_risk": 0, "low_risk": 0})
    df_stats = pd.DataFrame(students_data)
    total_students = len(df_stats)
    risk_counts = df_stats['risk_category'].value_counts()
    stats = {
        "total": total_students,
        "high_risk": int(risk_counts.get('High Risk', 0)),
        "medium_risk": int(risk_counts.get('Medium Risk', 0)),
        "low_risk": int(risk_counts.get('Low Risk', 0))
    }
    return jsonify(stats)

@app.route('/api/mentor_stats')
def get_mentor_stats():
    """API endpoint to get stats for all mentors (for admin)."""
    if session.get('user_type') != 'admin':
        return jsonify({"error": "Unauthorized access"}), 403
    
    if not students_data:
        return jsonify([])

    df = pd.DataFrame(students_data)
    
    # Group by mentor and count students in each risk category
    mentor_risk_counts = df.groupby('mentor_name')['risk_category'].value_counts().unstack(fill_value=0)
    
    # Re-order columns for consistent display
    mentor_risk_counts = mentor_risk_counts.reindex(columns=['High Risk', 'Medium Risk', 'Low Risk'], fill_value=0)
    
    mentor_risk_counts['Total Students'] = mentor_risk_counts.sum(axis=1)
    
    return jsonify(mentor_risk_counts.reset_index().to_dict(orient='records'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    if not students_data:
        print("Starting server, but no data will be shown on the dashboard.")
    app.run(debug=True, port=5001)