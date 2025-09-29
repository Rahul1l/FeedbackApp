import streamlit as st
from pymongo import MongoClient
import pandas as pd
import altair as alt
from datetime import datetime

# ---------------------------
# MongoDB connection
# ---------------------------
MONGO_URI = st.secrets["MONGO_URI"]
client = MongoClient(MONGO_URI)
db = client["feedbackdb"]        # your database
collection = db["feedbacks"]     # feedback collection

# ---------------------------
# Helper functions
# ---------------------------
def save_feedback(data):
    """Insert feedback with timestamp"""
    data["timestamp"] = datetime.now()
    collection.insert_one(data)

def get_all_trainers():
    """Return a list of unique trainers"""
    return collection.distinct("trainer")

def get_feedback_by_trainer(trainer_name):
    """Return all feedbacks for a trainer"""
    return list(collection.find({"trainer": trainer_name}))

def export_feedback_to_excel(trainer_name):
    """Export feedback to Excel"""
    feedbacks = get_feedback_by_trainer(trainer_name)
    if not feedbacks:
        return None
    df = pd.DataFrame(feedbacks)
    # Drop MongoDB _id column
    if "_id" in df.columns:
        df = df.drop(columns=["_id"])
    file_name = f"{trainer_name}_feedback.xlsx"
    df.to_excel(file_name, index=False)
    return file_name

def run_analytics(trainer_name):
    """Aggregate and visualize analytics for a trainer"""
    feedbacks = get_feedback_by_trainer(trainer_name)
    if not feedbacks:
        st.warning("No feedback available for this trainer.")
        return
    
    df = pd.DataFrame(feedbacks)
    questions = ["q1", "q2", "q3", "q4"]
    q_labels = ["Training Delivery Quality",
                "Understandability",
                "Relevance of Topics",
                "Wish to continue with same trainer?"]
    
    # Compute average scores
    avg_scores = {label: df[q].mean() for label, q in zip(q_labels, questions)}
    
    # Display as bar chart
    chart_data = pd.DataFrame({
        "Question": list(avg_scores.keys()),
        "Average Score": list(avg_scores.values())
    })
    
    chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X("Question", sort=None),
        y="Average Score",
        tooltip=["Question", "Average Score"]
    ).properties(title=f"Average Feedback Scores for {trainer_name}")
    
    st.altair_chart(chart, use_container_width=True)

# ---------------------------
# Pages
# ---------------------------
page = st.sidebar.selectbox("Select Page", ["User Feedback", "Admin Login"])

# ---------------------------
# User Feedback Page
# ---------------------------
if page == "User Feedback":
    st.title("Trainer Feedback Form")
    
    with st.form("feedback_form"):
        trainer_name = st.text_input("Trainer Name")
        subject = st.text_input("Subject")
        hours = st.number_input("Training Hours", min_value=0, step=1)
        
        q1 = st.radio("Training Delivery Quality", list(range(11)))
        q2 = st.radio("How Understandable was the training?", list(range(11)))
        q3 = st.radio("How Relevant were the topics covered?", list(range(11)))
        q4 = st.radio("Wish to continue with same trainer?", list(range(11)))
        
        comments = st.text_area("Additional Comments")
        
        submitted = st.form_submit_button("Submit Feedback")
        if submitted:
            feedback_data = {
                "trainer": trainer_name,
                "subject": subject,
                "hours": hours,
                "q1": q1,
                "q2": q2,
                "q3": q3,
                "q4": q4,
                "comments": comments
            }
            save_feedback(feedback_data)
            st.success("Feedback submitted successfully!")

# ---------------------------
# Admin Login Page
# ---------------------------
elif page == "Admin Login":
    st.title("Admin Login")
    password = st.text_input("Enter Admin Password", type="password")
    if st.button("Login"):
        if password == st.secrets["ADMIN_PASSWORD"]:
            st.success("Login Successful!")
            
            # Admin actions
            st.subheader("Feedback Overview")
            trainers = get_all_trainers()
            trainer_selected = st.selectbox("Select Trainer", ["--Select--"] + trainers)
            
            if trainer_selected != "--Select--":
                feedbacks = get_feedback_by_trainer(trainer_selected)
                st.write(f"Total Feedbacks: {len(feedbacks)}")
                
                # Show each feedback with timestamp
                for fb in feedbacks:
                    st.markdown("---")
                    st.write(f"**Submitted on:** {fb['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                    st.write(f"**Subject:** {fb['subject']}")
                    st.write(f"**Training Hours:** {fb['hours']}")
                    st.write(f"**Q1:** {fb['q1']}")
                    st.write(f"**Q2:** {fb['q2']}")
                    st.write(f"**Q3:** {fb['q3']}")
                    st.write(f"**Q4:** {fb['q4']}")
                    st.write(f"**Comments:** {fb['comments']}")
                
                # Admin buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Export to Excel", key=f"export_{trainer_selected}"):
                        file_path = export_feedback_to_excel(trainer_selected)
                        if file_path:
                            st.success(f"Feedback exported to {file_path}")
                with col2:
                    if st.button("Delete All Feedbacks", key=f"delete_{trainer_selected}"):
                        collection.delete_many({"trainer": trainer_selected})
                        st.warning(f"All feedbacks for {trainer_selected} deleted!")
                        st.experimental_rerun()
                with col3:
                    if st.button("Run Analytics", key=f"analytics_{trainer_selected}"):
                        run_analytics(trainer_selected)
                        
        else:
            st.error("Incorrect Password!")
