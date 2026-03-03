"""
katbot_client.py — Katbot.ai API client for OpenClaw agents.
"""
import json
import os
import time
import requests
from eth_account import Account
from eth_account.messages import encode_defunct

BASE_URL = os.getenv("KATBOT_BASE_URL", "https://api.katbot.ai")
# Use environment variables for keys to follow OpenClaw security rules
WALLET_PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")
AGENT_PRIVATE_KEY = os.getenv("KATBOT_HL_AGENT_PRIVATE_KEY")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "katbot_token.json")

def authenticate() -> str:
    """Perform SIWE login and return a fresh JWT. Saves token to disk."""
    if not WALLET_PRIVATE_KEY:
        raise ValueError("WALLET_PRIVATE_KEY environment variable not set")
    
    account = Account.from_key(WALLET_PRIVATE_KEY)
    address = account.address

    # Step 1: Get nonce
    r = requests.get(f"{BASE_URL}/get-nonce/{address}?chain_id=42161")
    r.raise_for_status()
    message_text = r.json()["message"]

    # Step 2: Sign
    signable = encode_defunct(text=message_text)
    signed = Account.sign_message(signable, WALLET_PRIVATE_KEY)
    signature = signed.signature.hex()

    # Step 3: Login
    r = requests.post(f"{BASE_URL}/login", json={"address": address, "signature": signature, "chain_id": 42161})
    r.raise_for_status()
    token_data = r.json()

    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)

    return token_data["access_token"]

def get_token() -> str:
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            data = json.load(f)
        token = data.get("access_token", "")
        if token:
            r = requests.get(f"{BASE_URL}/me", headers=_auth(token))
            if r.status_code == 200:
                return token
    return authenticate()

def _auth(token: str, agent_key: str = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    if agent_key:
        headers["X-Agent-Private-Key"] = agent_key
    elif AGENT_PRIVATE_KEY:
        headers["X-Agent-Private-Key"] = AGENT_PRIVATE_KEY
    return headers

def list_portfolios(token: str) -> list:
    r = requests.get(f"{BASE_URL}/portfolio", headers=_auth(token))
    r.raise_for_status()
    return r.json()

def get_portfolio(token: str, portfolio_id: int, window: str = "1d") -> dict:
    r = requests.get(f"{BASE_URL}/portfolio/{portfolio_id}", params={"window": window}, headers=_auth(token))
    r.raise_for_status()
    return r.json()

def request_recommendation(token: str, portfolio_id: int, message: str) -> dict:
    payload = {"portfolio_id": portfolio_id, "message": message}
    r = requests.post(f"{BASE_URL}/agent/recommendation/message", json=payload, headers=_auth(token))
    r.raise_for_status()
    return r.json()

def poll_recommendation(token: str, ticket_id: str, max_wait: int = 60) -> dict:
    deadline = time.time() + max_wait
    while time.time() < deadline:
        r = requests.get(f"{BASE_URL}/agent/recommendation/poll/{ticket_id}", headers=_auth(token))
        r.raise_for_status()
        data = r.json()
        if data.get("status") in ("COMPLETED", "complete", "FAILED"):
            return data
        time.sleep(2)
    raise TimeoutError(f"Recommendation not ready after {max_wait}s")

def execute_recommendation(token: str, portfolio_id: int, rec_id: int) -> dict:
    r = requests.post(f"{BASE_URL}/portfolio/{portfolio_id}/execute",
                      json={"recommendation_id": rec_id}, headers=_auth(token))
    r.raise_for_status()
    return r.json()

def close_position(token: str, portfolio_id: int, symbol: str) -> dict:
    r = requests.post(f"{BASE_URL}/portfolio/{portfolio_id}/close-position",
                      json={"symbol": symbol}, headers=_auth(token))
    r.raise_for_status()
    return r.json()
