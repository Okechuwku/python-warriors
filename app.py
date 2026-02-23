import streamlit as st
from openai import OpenAI
from PIL import Image
import base64
import os
import pandas as pd
import re
import hashlib
import smtplib
from email.message import EmailMessage
from difflib import SequenceMatcher

# =========================
# CONFIG
# =========================

st.set_page_config(page_title="Python Warriors AI", layout="centered")

# ✅ Using Streamlit secrets instead of os.environ
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

LEADERBOARD_FILE = "leaderboard.csv"
USERS_FILE = "users.csv"
SUBMISSIONS_FILE = "submissions.csv"

# =========================
# FILE INITIALIZATION
# =========================

for file, columns in [
    (LEADERBOARD_FILE, ["Name", "Score"]),
    (USERS_FILE, ["Username", "Password", "Role"]),
    (SUBMISSIONS_FILE, ["Username", "Code"]),
]:
    if not os.path.exists(file):
        pd.DataFrame(columns=columns).to_csv(file, index=False)

# =========================
# PASSWORD HASHING
# =========================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    users = pd.read_csv(USERS_FILE)
    hashed = hash_password(password)
    return users[(users["Username"] == username) & (users["Password"] == hashed)]

# =========================
# LOGIN SYSTEM
# =========================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.daily_usage = 0

if not st.session_state.logged_in:

    st.title("🔐 Python Warriors Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate(username, password)
        if not user.empty:
            st.session_state.logged_in = True
            st.session_state.role = user.iloc[0]["Role"]
            st.session_state.username = username
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

# =========================
# MAIN APP
# =========================

st.title("🔥 Python Warriors AI Assistant")
st.write(f"Welcome {st.session_state.username}")

# =========================
# USAGE LIMITER
# =========================

DAILY_LIMIT = 5

if st.session_state.daily_usage >= DAILY_LIMIT:
    st.warning("⚠️ Daily AI limit reached.")
    st.stop()

# =========================
# FILE UPLOAD
# =========================

uploaded_file = st.file_uploader(
    "Upload your Python file or image",
    type=["py", "txt", "png", "jpg", "jpeg"]
)

# =========================
# AI FUNCTION
# =========================

@st.cache_data(show_spinner=False)
def analyze_with_ai(messages):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=300
    )
    return response.choices[0].message.content

# =========================
# SCORE EXTRACTION
# =========================

def extract_score(text):
    match = re.search(r'(\d{1,2})\s*/\s*10', text)
    if match:
        return min(int(match.group(1)), 10)
    return 5

# =========================
# PLAGIARISM CHECK
# =========================

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

# =========================
# EMAIL FUNCTION (UPDATED)
# =========================

def send_email(feedback, score):
    try:
        EMAIL_USER = st.secrets["EMAIL_USER"]
        EMAIL_PASS = st.secrets["EMAIL_PASS"]

        msg = EmailMessage()
        msg["Subject"] = "Your Python Assignment Result"
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_USER  # Change to student email later

        msg.set_content(f"""
Student: {st.session_state.username}

Score: {score}/10

Feedback:
{feedback}
""")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg)

    except Exception as e:
        st.error(f"Email error: {e}")

# =========================
# ANALYSIS BUTTON
# =========================

if uploaded_file:

    if st.button("🚀 Analyze Assignment"):

        try:

            # IMAGE HANDLING
            if uploaded_file.type.startswith("image"):

                image_bytes = uploaded_file.getvalue()
                image = Image.open(uploaded_file)
                st.image(image)

                base64_image = base64.b64encode(image_bytes).decode("utf-8")

                messages = [
                    {"role": "system", "content": "You are a beginner Python teacher. Give feedback and end with Score: X/10"},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this Python assignment image."},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ]
                    }
                ]

                with st.spinner("Analyzing image..."):
                    feedback = analyze_with_ai(messages)

            # CODE HANDLING
            else:

                code = uploaded_file.read().decode("utf-8")
                st.code(code)

                submissions = pd.read_csv(SUBMISSIONS_FILE)

                for old_code in submissions["Code"]:
                    if similarity(code, old_code) > 0.85:
                        st.error("⚠️ Possible plagiarism detected!")
                        st.stop()

                messages = [
                    {"role": "system", "content": "You are a beginner Python teacher. Give feedback and end with Score: X/10"},
                    {"role": "user", "content": f"Check this Python assignment:\n{code}"}
                ]

                with st.spinner("Analyzing code..."):
                    feedback = analyze_with_ai(messages)

                new_sub = pd.DataFrame(
                    [[st.session_state.username, code]],
                    columns=["Username", "Code"]
                )
                submissions = pd.concat([submissions, new_sub], ignore_index=True)
                submissions.to_csv(SUBMISSIONS_FILE, index=False)

            # DISPLAY RESULTS
            st.success("✅ Analysis Complete!")
            st.write(feedback)

            score = extract_score(feedback)
            st.subheader(f"🎓 Score: {score}/10")

            if score == 10:
                st.balloons()

            leaderboard = pd.read_csv(LEADERBOARD_FILE)
            new_entry = pd.DataFrame(
                [[st.session_state.username, score]],
                columns=["Name", "Score"]
            )
            leaderboard = pd.concat([leaderboard, new_entry], ignore_index=True)
            leaderboard.to_csv(LEADERBOARD_FILE, index=False)

            send_email(feedback, score)

            st.session_state.daily_usage += 1

        except Exception as e:
            st.error(f"⚠️ Error: {e}")

# =========================
# LEADERBOARD
# =========================

st.markdown("---")
st.subheader("🏆 Leaderboard")

leaderboard = pd.read_csv(LEADERBOARD_FILE)

if not leaderboard.empty:
    sorted_df = leaderboard.sort_values(by="Score", ascending=False)
    st.dataframe(sorted_df.reset_index(drop=True))

# =========================
# TEACHER DASHBOARD
# =========================

if st.session_state.role == "teacher":

    st.markdown("---")
    st.subheader("📊 Teacher Dashboard")

    if not leaderboard.empty:
        st.metric("Total Submissions", len(leaderboard))
        st.metric("Class Average", round(leaderboard["Score"].mean(), 2))
        st.metric("Top Score", leaderboard["Score"].max())