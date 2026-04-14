import os
from fastapi import Header, HTTPException
from dotenv import load_dotenv

load_dotenv()

def verify_api_key(x_api_key: str = Header(None)):
    expected_key = os.getenv("API_KEY")

    if not expected_key:
        raise HTTPException(status_code=500, detail="API_KEY not configured in environment")

    if not x_api_key or x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")