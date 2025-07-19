from fastapi import Depends, HTTPException, Header
from sqlmodel import Session
from typing import Optional
import os
from src.models.database import get_session

API_KEY = os.getenv("API_KEY", "development-key")

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="无效的API密钥")
    return x_api_key

def get_db(api_key: str = Depends(verify_api_key)) -> Session:
    return next(get_session())