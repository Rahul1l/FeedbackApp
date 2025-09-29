# app.py
import streamlit as st
from pymongo import MongoClient
import pandas as pd
import altair as alt
from io import BytesIO
from datetime import datetime
import re
from collections import Counter

# -------------------------------
# MongoDB Atlas via connection string
# -------------------------------
MONGO_URI = st.secrets["MONGO_URI"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

client = MongoClient(MONGO_URI)
db = client.get_default_database()  # feedbackdb
collection = db["feedbacks"]

# -------------------------------
# Helper functions
# -------------------------------
def save_feedback(doc: dict):
    doc["submitted_at"] = datetime.utcnow()
    result = collection.insert_one(doc)
    return str(result.inserted_id)

def fetch_feedbacks(limit=1000):
    docs = list(collection.find().sort("submitted_at",-1).limit(limit))
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs

def get_feedback_by_id(id_str: str):
    from bson import ObjectId
    try:
        doc = collection.find_one({"_id": ObjectId(id_str)})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc
    except:
        return None

def delete_feedback(id_str: str):
    from bson import ObjectId
    result = collection.delete_one({"_id": ObjectId(id_str)})
    return result.deleted_count == 1

def feedbacks_to_excel_bytes(df: pd.DataFrame, sheet_name="feedbacks"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        writer.save()
    return output.getvalue()

def check_admin_password(pw: str):
    return pw == ADMIN_PASSWORD

# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="Feedback Analysis App", layout="wide")
st.title("Feedback Analysis App")

menu = st.sidebar.selectbox("Navigation", ["Submit Feedback", "Admin"])

# ---------------- User Form ----------------
if menu == "Submit Feedback":
    st.header("Submit Trainer Feedback")
    with st.form("feedback_form"):
        trainer = st.text_input("Trainer Name", placeholder="Enter trainer full name")
        subject = st.text_input("Subject / Topic", placeholder="E.g., Python for Data Analysis")
        duration = st.number_input("Duration (hours)", min_value=0.0, step=0.5, value=1.0)

        st.markdown("### Rate the trainer (0 = lowest, 10 = highest)")
        q1 = st.radio("1) Training delivery quality", options=list(range(0,11)), index=8, horizontal=True)
        q2 = st.radio("2) How understandable was the training?", options=list(range(0,11)), index=8, horizontal=True)
        q3 = st.radio("3) How relevant were the topics covered?", options=list(range(0,11)), index=8, horizontal=True)
        q4 = st.radio("4) Wish to continue with the same trainer?", options=list(range(0,11)), index=8, horizontal=True)

        comments = st.text_area("Comments (optional)", placeholder="Write your feedback here...")

        submitted = st.form_submit_button("Submit Feedback")

    if submitted:
        if not trainer.strip():
            st.warning("Please enter trainer name.")
        else:
            doc = {
                "trainer": trainer.strip(),
                "subject": subject.strip(),
                "duration_hours": float(duration),
                "q1_delivery_quality": int(q1),
                "q2_understandable": int(q2),
                "q3_relevance": int(q3),
                "q4_continue": int(q4),
                "comments": comments.strip()
            }
            inserted_id = save_feedback(doc)
            st.success("Thank you — your feedback has been recorded.")
            st.write("Reference ID:", inserted_id)

# ---------------- Admin ----------------
else:
    st.header("Admin Portal")
    if "admin_logged_in" not in st.session_state:
        st.session_state["admin_logged_in"] = False

    if not st.session_state["admin_logged_in"]:
        st.subheader("Login")
        pw = st.text_input("Admin password", type="password")
        if st.button("Login"):
            if check_admin_password(pw):
                st.session_state["admin_logged_in"] = True
                st.experimental_rerun()
            else:
                st.error("Invalid password.")
        st.stop()

    st.sidebar.success("Logged in as admin")
    col1, col2 = st.columns([3,1])
    with col1:
        search_trainer = st.text_input("Filter by trainer name (contains)", value="")
    with col2:
        refresh = st.button("Refresh list")

    all_docs = fetch_feedbacks(limit=2000)
    if search_trainer.strip():
        filtered = [d for d in all_docs if search_trainer.strip().lower() in d.get("trainer","").lower()]
    else:
        filtered = all_docs

    st.write(f"Showing {len(filtered)} feedback(s)")

    def show_table(docs):
        if not docs:
            st.info("No feedbacks found.")
            return
        df = pd.DataFrame([{
            "id": d["_id"],
            "trainer": d.get("trainer",""),
            "subject": d.get("subject",""),
            "duration_hours": d.get("duration_hours",""),
            "q1": d.get("q1_delivery_quality", ""),
            "q2": d.get("q2_understandable", ""),
            "q3": d.get("q3_relevance", ""),
            "q4": d.get("q4_continue", ""),
            "comments": d.get("comments",""),
            "submitted_at": d.get("submitted_at")
        } for d in docs])
        st.dataframe(df[["id","trainer","subject","duration_hours","q1","q2","q3","q4","submitted_at"]], height=300)
        return df

    df_all = show_table(filtered)

    st.write("---")
    st.subheader("Feedback management")
    id_to_view = st.text_input("Enter feedback id to view details")

    with st.expander("Click an ID to load it"):
        for d in filtered[:200]:
            st.write(f"- **{d['_id']}**  — {d.get('trainer','')} — {d.get('subject','')} — {d.get('submitted_at')}")

    if id_to_view.strip():
        doc = get_feedback_by_id(id_to_view.strip())
        if not doc:
            st.error("Feedback not found for that ID.")
        else:
            st.markdown("### Feedback detail")
            st.write(f"**Trainer:** {doc.get('trainer')}")
            st.write(f"**Subject:** {doc.get('subject')}")
            st.write(f"**Duration (hours):** {doc.get('duration_hours')}")
            st.write("**Ratings:**")
            st.write(f"- Delivery quality (Q1): {doc.get('q1_delivery_quality')}")
            st.write(f"- Understandable (Q2): {doc.get('q2_understandable')}")
            st.write(f"- Relevance (Q3): {doc.get('q3_relevance')}")
            st.write(f"- Continue (Q4): {doc.get('q4_continue')}")
            st.write("**Comments:**")
            st.write(doc.get("comments","(none)"))

            if st.button("Delete this feedback"):
                if delete_feedback(id_to_view.strip()):
                    st.success("Feedback deleted.")
                else:
                    st.error("Failed to delete feedback.")

            if st.button("Export this feedback to Excel"):
                df_doc = pd.DataFrame([doc])
                xlsx_bytes = feedbacks_to_excel_bytes(df_doc, sheet_name="feedback")
                st.download_button("Download Excel", xlsx_bytes, file_name=f"feedback_{doc['_id']}.xlsx")
