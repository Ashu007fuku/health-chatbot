# health-chatbot

## Overview
This is a health chatbot that analyzes diet logs (including handwritten images via OCR), answers health and product questions, and strictly follows official documentation rules. It uses Google Gemini, Google Vision OCR, and FAISS for document search.

## Features
- Upload handwritten diet log images and get structured analysis
- Ask health, diet, or product questions
- All answers strictly follow official docs
- Language detection and response
- Web interface via Streamlit

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone https://github.com/Ashu007fuku/health-chatbot.git
   cd health-chatbot
   ```

2. **Create and activate a virtual environment:**
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   - Create a `.env` file in the project root with your Google API key:
     ```
     GOOGLE_API_KEY=your_google_gemini_api_key
     ```
   - Place your Google Vision service account JSON in the project root (update the filename in code if needed).

5. **Run the Streamlit app:**
   ```
   streamlit run app_streamlit.py
   ```

## Notes
- Do **not** commit your `venv/` folder or any large files to the repository.
- All dependencies are managed via `requirements.txt`.
- For deployment on Streamlit Community Cloud, push only your code and requirements (not venv or data files).

## License
MIT
