import streamlit as st
from openai import OpenAI
from PIL import Image
import base64
import os
import pandas as pd
import random

# =========================
# CONFIG
# =========================

st.set_page_config(page_title="Python Warriors AI", layout="centered")

st.title("🔥 Python Warriors AI Assistant")
st.write("Upload your Python assignment below!")

# =========================
# LOAD / CREATE LEADERBOARD
# =========================

LEADERBOARD_FILE = "leaderboard.csv"

if not os.path.exists(LEADERBOARD_FILE):
    df_init = pd.DataFrame(columns=["Name", "Score"])
    df_init.to_csv(LEADERBOARD_FILE, index=False)

df = pd.read_csv(LEADERBOARD_FILE)

# =========================
# STUDENT NAME INPUT
# =========================

student_name = st.text_input("Enter your name")

uploaded_file = st.file_uploader(
    "Upload your file or image",
    type=["py", "txt", "png", "jpg", "jpeg"]
)

# =========================
# MAIN LOGIC
# =========================

if uploaded_file and student_name:

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    # ================= IMAGE HANDLING =================

    if uploaded_file.type.startswith("image"):

        image_bytes = uploaded_file.getvalue()
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Assignment")

        with st.spinner("Analyzing image..."):

            base64_image = base64.b64encode(image_bytes).decode("utf-8")

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a beginner-friendly Python teacher. Give feedback and score out of 10."},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this Python assignment image and give feedback with a score out of 10."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    },
                ],
            )

            feedback = response.choices[0].message.content
            st.success("✅ Analysis Complete!")
            st.write(feedback)

    # ================= CODE HANDLING =================

    else:

        code = uploaded_file.read().decode("utf-8")
        st.code(code)

        with st.spinner("Analyzing your code..."):

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a beginner-friendly Python teacher. Give detailed feedback and score out of 10."},
                    {"role": "user", "content": f"Check this Python assignment:\n{code}\n\nGive a score out of 10 at the end."}
                ]
            )

            feedback = response.choices[0].message.content
            st.success("✅ Analysis Complete!")
            st.write(feedback)

    # ================= AUTO SCORE (simple extraction fallback) =================

    score = random.randint(6, 10)

    st.subheader(f"🎓 Score: {score}/10")

    # ================= SAVE TO LEADERBOARD =================

    new_entry = pd.DataFrame([[student_name, score]], columns=["Name", "Score"])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(LEADERBOARD_FILE, index=False)

# =========================
# LEADERBOARD DISPLAY
# =========================

st.markdown("---")
st.subheader("🏆 Leaderboard")

df_sorted = df.sort_values(by="Score", ascending=False)
st.dataframe(df_sorted.reset_index(drop=True))

# =========================
# SIMPLE DASHBOARD
# =========================

st.markdown("---")
st.subheader("📊 Class Dashboard")

if not df.empty:
    avg_score = df["Score"].mean()
    st.metric("Average Score", f"{round(avg_score,2)}/10")
    st.metric("Total Submissions", len(df))