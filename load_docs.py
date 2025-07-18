import os
import fitz  # PyMuPDF
import pandas as pd

def load_pdf_text(pdf_path):
    """Extract text from a PDF file using PyMuPDF."""
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text("text") + "\n"
    except Exception as e:
        print(f"❌ Failed to read PDF {pdf_path}: {e}")
    return text.strip()

def load_excel_text(excel_path):
    """Extract text from an Excel file, joining each row with |."""
    try:
        df = pd.read_excel(excel_path)
        return "\n".join(df.astype(str).apply(lambda x: ' | '.join(x), axis=1)).strip()
    except Exception as e:
        print(f"❌ Failed to read Excel {excel_path}: {e}")
        return ""

def load_csv_text(csv_path):
    """Extract text from a CSV file, joining each row with |."""
    try:
        df = pd.read_csv(csv_path)
        return "\n".join(df.astype(str).apply(lambda x: ' | '.join(x), axis=1)).strip()
    except Exception as e:
        print(f"❌ Failed to read CSV {csv_path}: {e}")
        return ""

def load_docs_from_folder(folder_path):
    """Load and concatenate text from all supported files in a folder."""
    all_text = ""
    if not os.path.isdir(folder_path):
        print(f"❌ Folder does not exist: {folder_path}")
        return all_text
    for file in os.listdir(folder_path):
        if file.startswith('.') or file.startswith('~'):
            continue  # Skip hidden or temp files
        path = os.path.join(folder_path, file)
        if not os.path.isfile(path):
            continue
        if file.lower().endswith(".pdf"):
            all_text += load_pdf_text(path) + "\n"
        elif file.lower().endswith((".xlsx", ".xls")):
            all_text += load_excel_text(path) + "\n"
        elif file.lower().endswith(".csv"):
            all_text += load_csv_text(path) + "\n"
        elif file.lower().endswith(".txt"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    all_text += f.read().strip() + "\n"
            except Exception as e:
                print(f"❌ Failed to read TXT {path}: {e}")
    return all_text.strip()
