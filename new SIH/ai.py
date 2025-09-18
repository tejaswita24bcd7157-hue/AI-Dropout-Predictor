import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import OrdinalEncoder
from sklearn.impute import SimpleImputer
import matplotlib.pyplot as plt
import warnings
from twilio.rest import Client
import sys # <-- This line allows the script to read command-line arguments

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# --- Twilio Configuration ---

# Uncomment the bottom 4 lines and enter the ACCOUNT SID AND AUTH TOKEN for WhatsApp notification part to work (TWILIO API Isn't allowing me to post my details publicly on GITHUB)
# ACCOUNT_SID = "" 
# AUTH_TOKEN = ""
# TWILIO_PHONE_NUMBER = "whatsapp:+14155238886"  # Twilio's Sandbox Number
# MENTOR_PHONE_NUMBER = "whatsapp:+919636601573" # Your Verified WhatsApp Number

# --- (All your other functions like send_notification, load_student_data, etc., remain unchanged) ---
def send_notification(student_name, student_id, risk_score):
    try:
        if "ACxx" in ACCOUNT_SID or "your_auth" in AUTH_TOKEN:
            print(f"💡 NOTIFICATION SKIPPED for {student_name}: Please add your Twilio credentials to ai.py.")
            return False
        
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        message_body = (
            f"🚨 *Critical Risk Alert: Student Dropout Prediction System*\n\n"
            f"A student requires immediate attention:\n\n"
            f"👤 *Name:* {student_name}\n"
            f"🆔 *ID:* {student_id}\n"
            f"🔥 *Risk Score:* {risk_score:.2f}\n\n"
            f"Please log in to the dashboard for detailed analytics."
        )
        message = client.messages.create(body=message_body, from_=TWILIO_PHONE_NUMBER, to=MENTOR_PHONE_NUMBER)
        print(f"✅ Successfully sent CRITICAL notification for {student_name}.")
        return True
    except Exception as e:
        print(f"❌ FAILED TO SEND NOTIFICATION for {student_name}: {e}")
        return False

def load_student_data(filepath):
    try:
        df = pd.read_csv(filepath)
        print("✅ Student data loaded successfully.")
    except FileNotFoundError:
        print(f"❌ Error: The file at {filepath} was not found.")
        return None
    df.columns = [col.strip().replace(' ', '_').replace('_(%)', '').replace('%', '') for col in df.columns]
    rename_map = {'Student_Name': 'student_name', 'Student_ID': 'student_id', 'Attendance': 'attendance', 'CGPA': 'cgpa', 'Fees_Amount_Due': 'Fees_Amount_Due', 'Backlogs': 'internals'}
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    bins = [-1, 0, 40000, 60000, 80000, 100000, np.inf]
    labels = ['none', 'very_small', 'small', 'medium', 'large', 'very_large']
    df['financial_default'] = pd.cut(df['Fees_Amount_Due'], bins=bins, labels=labels, right=True)
    return df

def load_mentor_data(filepath):
    try:
        df = pd.read_csv(filepath)
        print("✅ Mentor data loaded successfully.")
        return df
    except FileNotFoundError:
        print(f"❌ Error: The mentor file at {filepath} was not found.")
        return None

def preprocess_data(df):
    num_cols = ['cgpa', 'attendance', 'internals', 'Fees_Amount_Due']
    imputer_num = SimpleImputer(strategy='median')
    df[num_cols] = imputer_num.fit_transform(df[num_cols])
    cat_cols = ['financial_default']
    imputer_cat = SimpleImputer(strategy='most_frequent')
    df[cat_cols] = imputer_cat.fit_transform(df[cat_cols])
    encoder = OrdinalEncoder(categories=[['none', 'very_small', 'small', 'medium', 'large', 'very_large']])
    df['financial_default_encoded'] = encoder.fit_transform(df[['financial_default']])
    return df

def calculate_risk_scores(df):
    financial_map = {'none': 0, 'very_small': 1, 'small': 3, 'medium': 6, 'large': 8, 'very_large': 10}
    df['financial_risk'] = df['financial_default'].map(financial_map)
    att_bins = [-1, 49, 65, 75, 101]; att_labels = [9, 7, 4, 0]
    df['attendance_risk'] = pd.cut(df['attendance'], bins=att_bins, labels=att_labels, right=True).astype(int)
    internals_map = {0: 8, 1: 6, 2: 2, 3: 0}
    df['internals_risk'] = df['internals'].clip(upper=3).map(internals_map)
    cgpa_bins = [-1, 4.99, 6, 7, 8, 11]; cgpa_labels = [8, 6, 4, 2, 0]
    df['cgpa_risk'] = pd.cut(df['cgpa'], bins=cgpa_bins, labels=cgpa_labels, right=True).astype(int)
    weights = {'financial': 0.45, 'attendance': 0.30, 'internals': 0.15, 'cgpa': 0.10}
    df['final_risk_score'] = (df['financial_risk'] * weights['financial'] + df['attendance_risk'] * weights['attendance'] + df['internals_risk'] * weights['internals'] + df['cgpa_risk'] * weights['cgpa'])
    risk_bins = [-1, 4, 7, 11]; risk_labels = ['Low Risk', 'Medium Risk', 'High Risk']
    df['risk_category'] = pd.cut(df['final_risk_score'], bins=risk_bins, labels=risk_labels, right=True)
    return df

def provide_counselling_suggestions(df):
    suggestions = []
    for _, row in df.iterrows():
        if row['risk_category'] == 'High Risk':
            suggestions.append("Weekly one-on-one mentoring, financial guidance, backlog support, and stress management help.")
        elif row['risk_category'] == 'Medium Risk':
            suggestions.append("Bi-weekly mentoring, study skills workshops, peer group support, and exam preparation strategies.")
        else:
            suggestions.append("Career development advice, leadership opportunities, recognition of achievements, and encouragement for advanced projects.")
    df['counselling_suggestions'] = suggestions
    return df

def provide_financial_aid_suggestions(df):
    suggestions = []
    for _, row in df.iterrows():
        if row['financial_risk'] == 10:
            suggestions.append("Suggest urgent financial aid, government scholarships, or emergency funds.")
        elif row['financial_risk'] >= 5:
            suggestions.append("Suggest scholarships or fee installment plans.")
        else:
            suggestions.append("No dues pending.")
    df['financial_aid_suggestion'] = suggestions
    return df

def balanced_mentor_allocation(students_df, mentors_df):
    students_df['risk_category'] = pd.Categorical(students_df['risk_category'], categories=['High Risk', 'Medium Risk', 'Low Risk'], ordered=True)
    students_df = students_df.sort_values('risk_category')
    mentor_list = mentors_df['mentor_name'].tolist()
    num_mentors = len(mentor_list)
    allocation_map = {student_id: mentor_list[i % num_mentors] for i, student_id in enumerate(students_df['student_id'])}
    students_df['mentor_name'] = students_df['student_id'].map(allocation_map)
    return allocation_map

def generate_reports(df, mentors, allocation_map):
    output_dir = 'mentor_reports'
    os.makedirs(output_dir, exist_ok=True)
    df['mentor_name'] = df['student_id'].map(allocation_map)
    for mentor_name in mentors['mentor_name']:
        mentor_students_df = df[df['mentor_name'] == mentor_name]
        if not mentor_students_df.empty:
            report_path = os.path.join(output_dir, f"{mentor_name.replace(' ', '_')}_report.csv")
            mentor_students_df.to_csv(report_path, index=False)
    df.to_csv("student_counselling_report.csv", index=False)
    print(f"\n✅ Generated individual reports for {len(mentors)} mentors in '{output_dir}' folder.")

def visualize_results(df):
    risk_counts = df['risk_category'].value_counts()
    plt.figure(figsize=(8, 8)); plt.pie(risk_counts, labels=risk_counts.index, autopct='%1.1f%%', startangle=140)
    plt.title('Student Risk Category Distribution', fontsize=16); plt.ylabel('')
    plt.savefig('risk_distribution.png')
    print("📊 Risk distribution chart saved as 'risk_distribution.png'")

# --- Main Execution ---
if __name__ == "__main__":
    student_filepath = "student_dropout_dataset(1).csv"
    mentor_filepath = "mentors_dataset.csv"
    
    students = load_student_data(student_filepath)
    mentors = load_mentor_data(mentor_filepath)

    if students is not None and mentors is not None:
        students = preprocess_data(students)
        df_risk = calculate_risk_scores(students.copy())
        df_counselling = provide_counselling_suggestions(df_risk.copy())
        df_final = provide_financial_aid_suggestions(df_counselling)
        
        internal_allocation_map = balanced_mentor_allocation(df_final, mentors)
        
        # --- THIS IS THE SAFETY SWITCH ---
        # It checks if the special command was used when you ran the script.
        if '--send-notifications' in sys.argv:
            print("\n--- Sending Notifications for Critically At-Risk Students ---")
            critical_risk_students = df_final[df_final['final_risk_score'] > 8]
            
            if critical_risk_students.empty:
                print("No students with risk score > 8 found. No notifications sent.")
            else:
                print(f"Found {len(critical_risk_students)} critically at-risk students. Sending alerts...")
                for _, student in critical_risk_students.iterrows():
                    send_notification(
                        student_name=student['student_name'],
                        student_id=student['student_id'],
                        risk_score=student['final_risk_score']
                    )
            print("----------------------------------------------------------")
        else:
            # This is the block that will run if you don't use the special command.
            print("\n--- Notifications Disabled ---")
            print("To send notifications, run the script with the --send-notifications flag.")
            print("Example: python ai.py --send-notifications")
            print("--------------------------------")

        generate_reports(df_final.copy(), mentors, internal_allocation_map)
        visualize_results(df_final)