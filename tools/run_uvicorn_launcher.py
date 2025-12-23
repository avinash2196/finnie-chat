import sys
sys.path.append(r"C:\Users\avina\Codes\finnie-chat")
from app.main import app
import uvicorn
import os

if __name__ == '__main__':
    # write pid so orchestrator can find and attach
    try:
        with open('uvicorn.pid', 'w') as f:
            f.write(str(os.getpid()))
    except Exception:
        pass
    uvicorn.run(app, host='127.0.0.1', port=8000)
