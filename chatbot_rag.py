# chatbot_rag.py
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from google.cloud import vision
import io
from PIL import Image
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langdetect import detect
from load_docs import load_docs_from_folder

# 🌍 Load env vars and API keys
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# 🧠 Load Gemini + FAISS
model = genai.GenerativeModel("models/gemini-2.5-pro")
chat = model.start_chat()
try:
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
except Exception as e:
    vectorstore = None
    print("❌ FAISS index not found or failed to load. Please build and upload the faiss_index folder with index.faiss and index.pkl.")
    print(f"Error details: {e}")

# Fallback knowledge
def fetch_website_summary():
    try:
        import requests
        r = requests.get("https://theobesitykiller.com/")
        if r.status_code == 200:
            return ("Obesity Killer Kit is a 100% natural Ayurvedic solution for safe weight loss. "
                    "Contains 39 herbs. Reduces hunger, promotes digestion. Over 60,000 users.")
    except: return ""
    return ""

# OCR diet log using Google Vision API

def extract_table_google_vision(image_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "obesity-bot-train-00c737889aa7.json"
    client = vision.ImageAnnotatorClient()
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if not texts:
        return '', None
    full_text = texts[0].description
    rows = [row.split() for row in full_text.split('\n') if row.strip()]
    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(f"ocr_logs/{today}", exist_ok=True)
    path = f"ocr_logs/{today}/{os.path.basename(image_path).split('.')[0]}_ocr.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    structured = "\n".join([" | ".join(r) for r in rows])
    return structured, path

# Diet prompt (with markdown table formatting request)
def generate_diet_prompt(structured_text, context_text, question=None, lang='en'):
    prompt = (
        "You're a personal wellness coach. The user uploaded a handwritten diet log:\n\n"
        f"{structured_text}\n\n"
        "Reference context from official docs:\n\n"
        f"{context_text}\n\n"
        "Instructions:\n"
        "- ONLY use the information and rules present in the reference docs.\n"
        "- Do NOT give advice, corrections, or suggestions that are not explicitly written in the docs.\n"
        "- If the user breaks a rule or makes a mistake according to the docs, highlight and correct it.\n"
        "- Highlight mistakes, missing items, or unhealthy patterns ONLY if they are mentioned in the docs, but dont mention dates of mistake.\n"
        "- Answer in a professional, friendly tone but keeping a product customer care approach.\n"
        "- Do NOT give any generic advice.\n"
        "- If there is no rule or info in the docs about a mistake, DO NOT correct or suggest anything.\n"
        "- Summarize issues as bullet points.\n"
        "- don't mention dates of mistake.\n"
        "- Compliment the user for what they did right in the log.\n"
        "- Answer in brief as the user has no prior knowledge.\n"
    )
    # Force response language
    if lang == 'hi':
        prompt += "\nउत्तर हिंदी या हिंग्लिश में दें।"
    elif lang == 'hi-en' or lang == 'hinglish':
        prompt += "\nRespond in Hinglish (mix of Hindi and English) only."
    elif lang == 'en':
        prompt += "\nRespond in English only."
    # Add question if present
    if question:
        prompt += f"\nAlso answer: '{question}' based only on the above log and docs."
    return prompt

# Save chats
def save_chat(user_msg, bot_msg):
    os.makedirs("chat_logs", exist_ok=True)
    path = "chat_logs/chat_history.json"
    history = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try: history = json.load(f)
            except: pass
    history.append({
        "timestamp": datetime.now().isoformat(),
        "user": user_msg,
        "bot": bot_msg
    })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

# CLI helpers
def color(text, code): return f"\033[{code}m{text}\033[0m"
def print_bot(msg): print(color("🤖 " + msg, '36'))
def print_user(msg): print(color("You: " + msg, '33'))
def print_error(msg): print(color("❌ " + msg, '31'))
def print_help():
    print(color("""
Commands:
/help     Show this help menu
/history  Show last 10 chats
/clear    Delete chat history
/save     Save last bot response to a file
/lang     Show last detected language
image: path.jpg | question  → Analyze image & ask question
exit/quit → Exit bot
""", '35'))

def show_history():
    path = "chat_logs/chat_history.json"
    if not os.path.exists(path): print(color("No chat history yet.", '90')); return
    with open(path, "r", encoding="utf-8") as f:
        try: history = json.load(f)
        except: print(color("Couldn't read history.", '90')); return
    print(color("\n--- Last 10 Chats ---", '35'))
    for entry in history[-10:]:
        print(color(f"[{entry['timestamp']}]", '90'))
        print_user(entry['user'])
        print_bot(entry['bot'])
    print(color("----------------------\n", '35'))

def clear_history():
    path = "chat_logs/chat_history.json"
    if os.path.exists(path): os.remove(path); print(color("History cleared!", '32'))
    else: print(color("No history found.", '90'))

def show_feedback_options():
    print(color("\n🤖 Does this answer your question? (type /helpme for support)", '36'))
    print(color("  (1) Yes, it does", '32'))
    print(color("  (2) No, I need help", '31'))
    print(color("(You can ignore and just continue chatting.)", '90'))

def show_customer_service():
    print(color("\n🔗 Connecting you to customer service...", '35'))
    print(color("📧 Email: support@yourcompany.com", '36'))
    print(color("📞 Phone: +91-12345-67890", '36'))
    print(color("🌐 Website: https://yourcompany.com", '36'))

last_bot_response = None
last_lang = None

# --- Verbose and pricing/token tracking ---
VERBOSE = True  # Set to True to enable debug info
TOKEN_ESTIMATE_PER_CHAR = 0.25  # Rough estimate: 1 token ≈ 4 chars

def estimate_tokens(text):
    return int(len(text) * TOKEN_ESTIMATE_PER_CHAR)

# --- Central Chat System ---
def central_chat_system(user_input, lang):
    """
    Handles all chat logic (OCR, QA, commands) in one place.
    Returns bot response and any extra info.
    """
    # Command handling
    if user_input.lower() == "/help":
        print_help()
        return None
    if user_input.lower() == "/helpme":
        show_customer_service()
        return None
    if user_input.lower() == "/history":
        show_history()
        return None
    if user_input.lower().startswith("/save"):
        parts = user_input.split()
        if len(parts) == 2 and last_bot_response:
            filename = parts[1]
            with open(filename, "w", encoding="utf-8") as f:
                f.write(last_bot_response)
            print(color(f"Saved last answer to {filename}", '32'))
        else:
            print_error("Usage: /save filename.md (after a bot answer)")
        return None
    if user_input.lower() == "/lang":
        print(color(f"Detected language: {lang}", '35'))
        return None
    if user_input.lower() == "/clear":
        confirm = input(color("Are you sure you want to clear chat history? (y/n): ", '31')).strip().lower()
        if confirm == 'y': clear_history()
        else: print(color("Cancelled.", '90'))
        return None

    # OCR Mode
    if user_input.lower().startswith("image:"):
        parts = user_input.split("|", 1)
        image_path = parts[0].replace("image:", "").strip()
        question = parts[1].strip() if len(parts) > 1 else None
        if not os.path.exists(image_path):
            print_error("Image not found."); return None
        print(color(f"📸 Reading image: {image_path}", '34'))
        structured_text, saved_path = extract_table_google_vision(image_path)
        print(color(f"📄 OCR saved to: {saved_path}", '90'))
        # Load docs context
        context_text = load_docs_from_folder("docs")
        prompt = generate_diet_prompt(structured_text, context_text, question, lang)
        if VERBOSE:
            print(color(f"\n--- Gemini Prompt ---\n{prompt}\n---------------------", '90'))
            print(color(f"Prompt chars: {len(prompt)} | Est. tokens: {estimate_tokens(prompt)}", '90'))
        response = chat.send_message(prompt)
        print_bot(response.text)
        usage = getattr(response, 'usage_metadata', None)
        if usage:
            print(color(f"[Gemini usage] Input tokens: {usage.prompt_token_count}, Output tokens: {usage.candidates_token_count}, Total: {usage.total_token_count}", '90'))
        else:
            resp_tokens = estimate_tokens(response.text)
            print(color(f"Response chars: {len(response.text)} | Est. tokens: {resp_tokens}", '90'))
            print(color(f"Total est. tokens (prompt+response): {estimate_tokens(prompt) + resp_tokens}", '90'))
        save_chat(user_input, response.text)
        show_feedback_options()
        return response.text

    # QA mode
    if vectorstore is None:
        # Always return a visible response in the web UI
        return "❌ FAISS index not found. Please contact the admin to upload the required index files."
    docs = vectorstore.similarity_search(user_input, k=6)
    context = "\n\n".join([doc.page_content for doc in docs])
    site = fetch_website_summary()
    prompt = (
        f"Use only the info below to answer the user:\n\n"
        f"Website:\n{site}\n\nDocs:\n{context}\n\nUser: {user_input}"
    )
    # Force response language for QA mode
    if lang == 'hi':
        prompt += "\nउत्तर हिंदी या हिंग्लिश में दें।"
    elif lang == 'hi-en' or lang == 'hinglish':
        prompt += "\nRespond in Hinglish (mix of Hindi and English) only."
    elif lang == 'en':
        prompt += "\nRespond in English only."
    try:
        response = chat.send_message(prompt)
    except Exception as e:
        return f"❌ Gemini API error: {e}"
    print_bot(response.text)
    if docs and hasattr(docs[0], 'metadata') and 'source' in docs[0].metadata:
        print(color("\nSources:", '90'))
        for doc in docs:
            if 'source' in doc.metadata:
                print(color(f"- {doc.metadata['source']}", '90'))
    usage = getattr(response, 'usage_metadata', None)
    if usage:
        print(color(f"[Gemini usage] Input tokens: {usage.prompt_token_count}, Output tokens: {usage.candidates_token_count}, Total: {usage.total_token_count}", '90'))
    else:
        resp_tokens = estimate_tokens(response.text)
        print(color(f"Response chars: {len(response.text)} | Est. tokens: {resp_tokens}", '90'))
        print(color(f"Total est. tokens (prompt+response): {estimate_tokens(prompt) + resp_tokens}", '90'))
    save_chat(user_input, response.text)
    show_feedback_options()
    return response.text

# Start chat (only when run directly, not when imported)
if __name__ == "__main__":
    print(color("""
🤖 Welcome to the Health Chatbot!
- Ask anything about your health, diet, or the Obesity Killer kit.
- Upload a diet log image: image: yourfile.jpg | your question
- Type /help for all commands.
""", '36'))

    while True:
        user_input = input(color("You: ", '33')).strip()
        if user_input.lower() in ["exit", "quit"]:
            print(color("👋 Bye!", '32'))
            break
        # Detect language for auto-switch
        lang = 'en'
        try:
            lang = detect(user_input)
        except:
            lang = 'en'
        central_chat_system(user_input, lang)
