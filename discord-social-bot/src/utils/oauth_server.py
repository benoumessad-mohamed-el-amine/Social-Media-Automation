# discord-social-bot/utils/oauth_server.py

from fastapi import FastAPI, Request
import uvicorn
import sys
import os

# Permet d'importer correctement instagram_oauth_handler
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.oauth import instagram_oauth_handler

app = FastAPI()

@app.get("/oauth/callback")
async def oauth_callback(request: Request):
    """Endpoint de redirection OAuth pour Instagram/Facebook"""
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    result = await instagram_oauth_handler.handle_callback(code, state)
    return {"status": "ok", "details": result}


if __name__ == "__main__":
    print("✅ Serveur OAuth lancé sur http://localhost:8000")
    uvicorn.run("utils.oauth_server:app", host="0.0.0.0", port=8000)
