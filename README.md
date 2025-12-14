# finnie-chat

Small local FastAPI-based assistant project.

Quick start (PowerShell):

```powershell
# create venv if you haven't
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# run server
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Notes:
- `.env` holds `OPENAI_API_KEY` (don't commit it).
- Project already uses a local TF-IDF RAG store; to switch to semantic embeddings you will need to install additional dependencies (torch, sentence-transformers) and VC++ redistributable on Windows.

To push to a remote once you have a repo created:

```powershell
git remote add origin <your-repo-url>
git push -u origin main
```
