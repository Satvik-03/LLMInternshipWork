import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EXCEL_FILE_PATH = os.getenv('EXCEL_FILE_PATH')

# Helper function to send emails
def send_email(to_address, subject, message, from_address, smtp_server, smtp_port, smtp_user, smtp_password):
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))
    
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(from_address, to_address, msg.as_string())

# Function to automatically find email and score columns
def find_columns(df):
    email_col = None
    score_col = None
    email_keywords = ['email', 'mail', 'e-mail']
    score_keywords = ['score', 'points', 'marks']

    for col in df.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in email_keywords):
            email_col = col
        if any(keyword in col_lower for keyword in score_keywords):
            score_col = col
    
    return email_col, score_col

# Streamlit UI
st.title('Quiz Results Notifier')

# Use environment variable for Excel file path
if EXCEL_FILE_PATH:
    try:
        df = pd.read_excel(EXCEL_FILE_PATH)
        st.write("Data Preview:", df.head())

        # Automatically find email and score columns
        email_col, score_col = find_columns(df)

        if not email_col or not score_col:
            st.error("Could not automatically detect email or score columns. Please ensure your columns are properly named.")
        else:
            st.write(f"Automatically selected email column: {email_col}")
            st.write(f"Automatically selected score column: {score_col}")

            threshold = 7  # Set score threshold automatically to 7
            st.write(f"Score threshold is set to: {threshold}")

            from_address = EMAIL_ADDRESS
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            smtp_user = from_address
            smtp_password = EMAIL_PASSWORD

            # Predefined subject and message
            subject = "Interview Selection Notification"
            message = (
                        "Dear Candidate,\n\n"
                        "We are pleased to inform you that you have successfully qualified the prescreening test and have been selected for an interview. "
                        "Detailed information regarding the interview schedule and further steps will be shared in a subsequent email.\n\n"
                        "We look forward to meeting you.\n\n"
                        "Best regards,\n"
                        "The Recruitment Team"
                    )                    
            if st.button("Send Emails"):
                if not all([from_address, smtp_user, smtp_password]):
                    st.error("Please provide email credentials and details.")
                else:
                    selected_rows = df[df[score_col] > threshold]
                    st.write("Selected Participants:", selected_rows)

                    for _, row in selected_rows.iterrows():
                        to_address = row[email_col]
                        personalized_message = message.format(score=row[score_col])
                        send_email(to_address, subject, personalized_message, from_address, smtp_server, smtp_port, smtp_user, smtp_password)
                    
                    st.success("Emails sent successfully!")
    except Exception as e:
        st.error(f"Error reading the Excel file: {e}")
else:
    st.error("Excel file path not provided. Please set the EXCEL_FILE_PATH environment variable.")
