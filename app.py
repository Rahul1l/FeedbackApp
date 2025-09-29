import streamlit as st
import pandas as pd
import os
from datetime import datetime

# File to store feedbacks
FEEDBACK_FILE = "feedback_data.csv"

# Ensure feedback file exists
if not os.path.exists(FEEDBACK_FILE):
    df = pd.DataFrame(columns=[
        "Trainer", "Subject", "Hours", "Date", 
        "Q1", "Q2", "Q3", "Request_Repeat", "Comments"
    ])
    df.to_csv(FEEDBACK_FILE, index=False)

# Load existing feedback data
def load_data():
    return pd.read_csv(FEEDBACK_FILE)

# Save new feedback
def save_feedback(trainer, subject, hours, q1, q2, q3, request_repeat, comments):
    df = load_data()
    new_entry = {
        "Trainer": trainer,
        "Subject": subject,
        "Hours": hours,
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Q1": q1,
        "Q2": q2,
        "Q3": q3,
        "Request_Repeat": request_repeat,
        "Comments": comments
    }
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df.to_csv(FEEDBACK_FILE, index=False)

# --- Streamlit App ---
st.title("Trainer Feedback Form")

mode = st.radio("Select Mode", ["User", "Admin"], horizontal=True)

if mode == "User":
    st.header("Submit Feedback")

    # Input fields
    trainer_name = st.text_input("Trainer Name (Enter New or Select Existing)")
    subject_name = st.text_input("Subject Name")
    subject_hours = st.number_input("Subject Hours", min_value=1, max_value=100, step=1)

    st.write("Rate from 1 (Poor) to 5 (Excellent)")
    q1 = st.radio("Trainer Knowledge:", [1, 2, 3, 4, 5], horizontal=True)
    q2 = st.radio("Communication Skills:", [1, 2, 3, 4, 5], horizontal=True)
    q3 = st.radio("Engagement Level:", [1, 2, 3, 4, 5], horizontal=True)

    request_repeat = st.radio("Would you like this trainer again?", ["Yes", "No"], horizontal=True)
    comments = st.text_area("Additional Comments:")

    if st.button("Submit Feedback"):
        if trainer_name.strip() == "" or subject_name.strip() == "":
            st.error("Please enter both trainer and subject names!")
        else:
            save_feedback(
                trainer_name.strip(), subject_name.strip(), subject_hours,
                q1, q2, q3, request_repeat, comments.strip()
            )
            st.success("Feedback submitted successfully!")
            st.experimental_rerun()  # Refresh page for next user

elif mode == "Admin":
    st.header("View Feedback & Analytics")
    df = load_data()

    if df.empty:
        st.info("No feedback data available.")
    else:
        trainers = df["Trainer"].unique().tolist()
        selected_trainer = st.selectbox("Select Trainer", trainers)

        if selected_trainer:
            trainer_data = df[df["Trainer"] == selected_trainer]
            st.subheader(f"All Feedback for {selected_trainer}")
            st.dataframe(trainer_data)

            # Analytics
            st.subheader("Analytics")
            avg_q1 = trainer_data["Q1"].mean()
            avg_q2 = trainer_data["Q2"].mean()
            avg_q3 = trainer_data["Q3"].mean()
            repeat_count = trainer_data["Request_Repeat"].value_counts()

            st.write(f"Average Trainer Knowledge: {avg_q1:.2f}")
            st.write(f"Average Communication Skills: {avg_q2:.2f}")
            st.write(f"Average Engagement Level: {avg_q3:.2f}")
            st.write("Request Repeating Trainer:")
            st.bar_chart(repeat_count)
