import sys
import logging
from pathlib import Path

# Add parent directory to path so 'app' module can be found
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.rag.store import add_documents

def ingest():
    with open("data/finance_kb.txt", "r") as f:
        text = f.read()

    chunks = [c.strip() for c in text.split("\n") if c.strip()]
    add_documents(chunks)
    logging.info("RAG ingestion completed: %d documents loaded", len(chunks))

if __name__ == "__main__":
    ingest()
