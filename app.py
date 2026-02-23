import streamlit as st
from openai import OpenAI
from PIL import Image
import base64

st.title("🔥 Python Warriors AI Assistant")

st.write("Upload your Python assignment below!")

uploaded_file = st.file_uploader("Upload your file or image", type=["py", "txt", "png", "jpg", "jpeg"])

if uploaded_file:
    if uploaded_file.type.startswith("image"):
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Assignment")
        st.write("Analyzing image...")
    else:
        code = uploaded_file.read().decode("utf-8")
        st.code(code)

        st.write("Analyzing your code...")

        client = OpenAI(api_key="YOUR_API_KEY")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a beginner-friendly Python teacher. Encourage students and correct them gently."},
                {"role": "user", "content": f"Check this Python assignment:\n{code}"}
            ]
        )

        st.write(response.choices[0].message.content)