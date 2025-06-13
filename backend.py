# backend.py
import excel_functions
from fastapi import FastAPI, Request
from pydantic import BaseModel
from kiteconnect import KiteConnect
from fastapi.middleware.cors import CORSMiddleware

import config

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend URL: ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TokenRequest(BaseModel):
    request_token: str

@app.get("/login_url")
def get_login_url():
    kite = KiteConnect(api_key=config.config_keys[config.ID]["api_key"])
    return {"login_url": kite.login_url()}

@app.post("/save_token")
def save_token(data: TokenRequest):
    kite = KiteConnect(api_key=config.config_keys[config.ID]["api_key"])
    session = kite.generate_session(data.request_token, api_secret=config.config_keys[config.ID]["api_secret"])
    access_token = session["access_token"]
    excel_functions.set_access_token(access_token)
    return {"status": "success", "access_token": access_token}

@app.post("/start_trading")
def start_trading():
    # Import and run your trading logic here, using the saved access_token
    # Example: subprocess.Popen(["python", "multiple_trading.py"])
    import multiple_trading
    multiple_trading.multiple_trading(config.shares_quantity, "NSE", 3)
    return {"status": "trading_started"}
