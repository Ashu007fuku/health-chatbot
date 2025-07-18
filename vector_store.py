import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from load_docs import load_docs_from_folder

def create_faiss_index(doc_folder="docs"):
    """Load documents, split into chunks, embed, and save FAISS index. Does not skip if content is empty."""
    print("📄 Loading and processing documents...")

    all_text = load_docs_from_folder(doc_folder)
    if not all_text.strip():
        print(f"⚠️ Warning: No text loaded from folder: {doc_folder}. Proceeding to create an (empty) index.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,        # Increased for more context
        chunk_overlap=150
    )
    chunks = splitter.split_text(all_text)
    print(f"🧩 Total chunks created: {len(chunks)}")

    # Always proceed, even if chunks is empty
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print("💾 Building FAISS index...")
    vectorstore = FAISS.from_texts(chunks, embedding=embeddings)
    vectorstore.save_local("faiss_index")
    print("✅ FAISS index saved successfully.")

if __name__ == "__main__":
    create_faiss_index()
