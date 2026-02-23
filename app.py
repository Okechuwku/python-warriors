import streamlit as st
from openai import OpenAI
from PIL import Image
import base64
import os

st.title("🔥 Python Warriors AI Assistant")
st.write("Upload your Python assignment below!")

uploaded_file = st.file_uploader(
    "Upload your file or image",
    type=["py", "txt", "png", "jpg", "jpeg"]
)

if uploaded_file:

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    if uploaded_file.type.startswith("image"):
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Assignment")

        st.write("Analyzing image...")

        buffered = uploaded_file.read()
        base64_image = base64.b64encode(buffered).decode("utf-8")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a beginner-friendly Python teacher."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this Python assignment image and give feedback."},
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

        st.write(response.choices[0].message.content)

    else:
        code = uploaded_file.read().decode("utf-8")
        st.code(code)

        st.write("Analyzing your code...")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a beginner-friendly Python teacher."},
                {"role": "user", "content": f"Check this Python assignment:\n{code}"}
            ]
        )

        st.write(response.choices[0].message.content)