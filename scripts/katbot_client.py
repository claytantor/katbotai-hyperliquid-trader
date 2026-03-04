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
IDENTITY_DIR = os.getenv("KATBOT_IDENTITY_DIR", os.path.expanduser("~/.openclaw/workspace/katbot-identity"))

# File paths
TOKEN_FILE = os.path.join(IDENTITY_DIR, "katbot_token.json")
SECRETS_FILE = os.path.join(IDENTITY_DIR, "katbot_secrets.json")
CONFIG_FILE = os.path.join(IDENTITY_DIR, "katbot_config.json")

# Use environment variables for keys to follow OpenClaw security rules
WALLET_PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")
AGENT_PRIVATE_KEY = os.getenv("KATBOT_HL_AGENT_PRIVATE_KEY")

# If agent key not in env, try loading from secrets file
if not AGENT_PRIVATE_KEY and os.path.exists(SECRETS_FILE):
    try:
        with open(SECRETS_FILE) as f:
            secrets = json.load(f)
            AGENT_PRIVATE_KEY = secrets.get("agent_private_key")
    except Exception:
        pass  # Fail silently if file is corrupt or unreadable

def get_config() -> dict:
    """Load configuration from the identity file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def authenticate() -> str:
    """Perform SIWE login and return a fresh JWT. Saves token to disk."""
    if not WALLET_PRIVATE_KEY:
        raise ValueError("WALLET_PRIVATE_KEY environment variable not set (required for re-authentication)")
    
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

    # Ensure directory exists
    os.makedirs(IDENTITY_DIR, exist_ok=True)
    
    # Save token with restricted permissions
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)
    try:
        os.chmod(TOKEN_FILE, 0o600)
    except Exception:
        pass

    return token_data["access_token"]

def get_token() -> str:
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE) as f:
                data = json.load(f)
            token = data.get("access_token", "")
            if token:
                # Verify token is still valid
                try:
                    r = requests.get(f"{BASE_URL}/me", headers=_auth(token), timeout=5)
                    if r.status_code == 200:
                        return token
                except Exception:
                    pass
        except Exception:
            pass
            
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
