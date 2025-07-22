import streamlit as st
from langdetect import detect
import os
from chatbot_rag import central_chat_system

st.set_page_config(page_title="Health Chatbot", page_icon="🤖")
st.title("🤖 Health Chatbot")
st.write("Ask anything about your health, diet, or the Obesity Killer kit.")
st.write("Upload a diet log image and ask a question, or just chat.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def handle_user_input(user_input, lang):
    response = central_chat_system(user_input, lang)
    if response:
        st.session_state.chat_history.append(("user", user_input))
        st.session_state.chat_history.append(("bot", response))

# Chat input
user_input = st.text_input("Type your message:", key="user_input")
if st.button("Send", key="send_btn") and user_input.strip():
    try:
        lang = detect(user_input)
    except:
        lang = "en"
    handle_user_input(user_input, lang)

# Image upload
uploaded_file = st.file_uploader("Upload a diet log image (jpg/png)", type=["jpg", "jpeg", "png"])
question = st.text_input("Ask a question about the uploaded image (optional):", key="img_question")
if uploaded_file and st.button("Analyze Image", key="analyze_btn"):
    image_path = f"temp_{uploaded_file.name}"
    with open(image_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    user_input = f"image: {image_path}"
    if question.strip():
        user_input += f" | {question.strip()}"
    try:
        lang = detect(question) if question.strip() else "en"
    except:
        lang = "en"
    handle_user_input(user_input, lang)
    os.remove(image_path)

# Display chat history
for role, msg in st.session_state.chat_history:
    if role == "user":
        st.markdown(f"**You:** {msg}")
    else:
        st.markdown(f"**🤖 Bot:** {msg}")
        st.markdown(f"**🤖 Bot:** {msg}")
