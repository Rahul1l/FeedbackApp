import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

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

# --- Session state for User form ---
if "trainer_name" not in st.session_state:
    st.session_state.trainer_name = ""
    st.session_state.subject_name = ""
    st.session_state.subject_hours = 1
    st.session_state.q1 = 1
    st.session_state.q2 = 1
    st.session_state.q3 = 1
    st.session_state.request_repeat = "Yes"
    st.session_state.comments = ""

# -------------------- USER MODE --------------------
if mode == "User":
    st.header("Submit Feedback")

    trainer_name = st.text_input("Trainer Name", value=st.session_state.trainer_name)
    subject_name = st.text_input("Subject Name", value=st.session_state.subject_name)
    subject_hours = st.number_input("Subject Hours", min_value=1, max_value=100, step=1, value=st.session_state.subject_hours)

    st.write("Rate from 1 (Poor) to 5 (Excellent)")
    q1 = st.radio("Trainer Knowledge:", [1, 2, 3, 4, 5], horizontal=True, index=st.session_state.q1-1)
    q2 = st.radio("Communication Skills:", [1, 2, 3, 4, 5], horizontal=True, index=st.session_state.q2-1)
    q3 = st.radio("Engagement Level:", [1, 2, 3, 4, 5], horizontal=True, index=st.session_state.q3-1)

    request_repeat = st.radio("Would you like this trainer again?", ["Yes", "No"], horizontal=True,
                              index=0 if st.session_state.request_repeat=="Yes" else 1)
    comments = st.text_area("Additional Comments:", value=st.session_state.comments)

    if st.button("Submit Feedback"):
        if trainer_name.strip() == "" or subject_name.strip() == "":
            st.error("Please enter both trainer and subject names!")
        else:
            save_feedback(
                trainer_name.strip(), subject_name.strip(), subject_hours,
                q1, q2, q3, request_repeat, comments.strip()
            )
            st.success("Feedback submitted successfully!")
            # Reset form
            st.session_state.trainer_name = ""
            st.session_state.subject_name = ""
            st.session_state.subject_hours = 1
            st.session_state.q1 = 1
            st.session_state.q2 = 1
            st.session_state.q3 = 1
            st.session_state.request_repeat = "Yes"
            st.session_state.comments = ""

# -------------------- ADMIN MODE --------------------
elif mode == "Admin":
    st.header("Admin Login")

    # Password input
    password_input = st.text_input("Enter Admin Password", type="password")
    admin_password = st.secrets.get("admin_password", "")

    if st.button("Login"):
        if password_input == admin_password:
            st.success("Login successful!")
            df = load_data()
            if df.empty:
                st.info("No feedback data available.")
            else:
                # Select trainer
                trainers = df["Trainer"].unique().tolist()
                selected_trainer = st.selectbox("Select Trainer", trainers)

                if selected_trainer:
                    st.subheader(f"Actions for {selected_trainer}")
                    action = st.radio("Choose Action", ["View Feedback", "Export to Excel", "View Analytics", "Delete Feedback"], horizontal=True)

                    trainer_data = df[df["Trainer"] == selected_trainer]

                    if action == "View Feedback":
                        st.dataframe(trainer_data)

                    elif action == "Export to Excel":
                        towrite = BytesIO()
                        trainer_data.to_excel(towrite, index=False, engine='openpyxl')
                        towrite.seek(0)
                        st.download_button(
                            label="Download Feedback as Excel",
                            data=towrite,
                            file_name=f"{selected_trainer}_feedback.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                    elif action == "View Analytics":
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

                    elif action == "Delete Feedback":
                        if st.button("Confirm Delete"):
                            df = df[df["Trainer"] != selected_trainer]
                            df.to_csv(FEEDBACK_FILE, index=False)
                            st.success(f"All feedback for {selected_trainer} has been deleted.")
        else:
            st.error("Incorrect password! Access denied.")
