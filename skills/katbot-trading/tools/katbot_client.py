"""
katbot_client.py — Katbot.ai API client for agents and CLI tools.

Supports two configuration modes:
1. Environment variables (for OpenClaw skills)
2. .env file (for tubman-bobtail-py CLI usage)

Features:
- SIWE authentication
- Token refresh with JWT expiry checking
- Portfolio management
- Recommendation workflow
- Trade execution
- Position closing
"""
import base64
import json
import os
import time
import requests
from pathlib import Path
from eth_account import Account
from eth_account.messages import encode_defunct

# Configuration: support both env vars and .env file
BASE_URL = os.getenv("KATBOT_BASE_URL")
IDENTITY_DIR = os.getenv("KATBOT_IDENTITY_DIR")

# If not set via env vars, try loading from .env file (tubman-bobtail-py mode)
ENV_FILE = None

# 1. (user homedir)/katbot_client.env
# 2. (openclaw_home)/katbot_identity/katbot_client.env
if not BASE_URL or not IDENTITY_DIR:
    env_candidates = [
        Path("/home/clay/tubman-bobtail-py/env/local/katbot_client.env"),
        Path(__file__).parent.parent.parent / "env" / "local" / "katbot_client.env",
        Path(__file__).parent.parent / "env" / "local" / "katbot_client.env",
        Path(__file__).parent / "katbot_client.env",
        Path.home() / "katbot_client.env",
    ]

    # Add the second candidate only if OPENCLAW_HOME is defined
    openclaw_home = os.environ.get("OPENCLAW_HOME")
    if openclaw_home:
        env_candidates.append(Path(openclaw_home) / "katbot_identity" / "katbot_client.env")


    for candidate in env_candidates:
        if candidate.exists():
            ENV_FILE = candidate
            break
    
    if ENV_FILE and ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"')
                    if key == "KATBOT_BASE_URL" and not BASE_URL:
                        BASE_URL = val
                    elif key == "KATBOT_IDENTITY_DIR" and not IDENTITY_DIR:
                        IDENTITY_DIR = val
                    elif key == "CHAIN_ID" and not os.getenv("CHAIN_ID"):
                        os.environ["CHAIN_ID"] = val
                    # WALLET_PRIVATE_KEY and KATBOT_HL_AGENT_PRIVATE_KEY are intentionally
                    # NOT loaded from .env files — private keys must be supplied via
                    # environment variables or the identity directory only.

# Default fallbacks
if not BASE_URL:
    BASE_URL = os.getenv("KATBOT_BASE_URL", "https://api.katbot.ai")
if not IDENTITY_DIR:
    IDENTITY_DIR = os.getenv("KATBOT_IDENTITY_DIR", os.path.expanduser("~/.openclaw/workspace/katbot-identity"))

# File paths
TOKEN_FILE = os.path.join(IDENTITY_DIR, "katbot_token.json")
SECRETS_FILE = os.path.join(IDENTITY_DIR, "katbot_secrets.json")
CONFIG_FILE = os.path.join(IDENTITY_DIR, "katbot_config.json")

# Load keys from env vars or secrets file
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

CHAIN_ID = int(os.getenv("CHAIN_ID", "42161"))


def get_config() -> dict:
    """Load configuration from the identity file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _jwt_expiry(token: str) -> float:
    """Decode JWT payload (no signature verification) and return exp as a Unix timestamp.
    Returns 0 if the token is malformed or has no exp claim."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return 0
        # Add padding so base64 decodes cleanly
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return float(payload.get("exp", 0))
    except Exception:
        return 0


def _token_is_valid(token: str, margin_seconds: int = 60) -> bool:
    """Return True if the token exists and won't expire within margin_seconds."""
    if not token:
        return False
    exp = _jwt_expiry(token)
    if exp == 0:
        return False  # can't determine expiry — treat as invalid
    return time.time() < (exp - margin_seconds)


def _refresh_access_token(refresh_token: str) -> str | None:
    """Exchange a refresh token for a new access token and refresh token.
    Both tokens are saved to disk. Returns the new access token, or None if refresh fails."""
    if not refresh_token:
        return None
    try:
        r = requests.post(
            f"{BASE_URL}/refresh",
            json={"refresh_token": refresh_token},
            timeout=15,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        new_access = data.get("access_token", "")
        new_refresh = data.get("refresh_token", "")
        if not new_access or not new_refresh:
            return None
        os.makedirs(IDENTITY_DIR, exist_ok=True)
        with open(TOKEN_FILE, "w") as f:
            json.dump({"access_token": new_access, "refresh_token": new_refresh}, f, indent=2)
        try:
            os.chmod(TOKEN_FILE, 0o600)
        except Exception:
            pass
        return new_access
    except Exception:
        return None


def authenticate() -> str:
    """Perform SIWE login and return a fresh JWT. Saves token to disk."""
    if not WALLET_PRIVATE_KEY:
        raise ValueError(
            "\n❌ Session expired and WALLET_PRIVATE_KEY not set.\n"
            "   Please re-run the onboarding script to refresh your session:\n"
            "   python3 skills/katbot-trading/tools/katbot_onboard.py"
        )

    account = Account.from_key(WALLET_PRIVATE_KEY)
    address = account.address

    # Step 1: Get nonce
    r = requests.get(f"{BASE_URL}/get-nonce/{address}?chain_id={CHAIN_ID}")
    r.raise_for_status()
    message_text = r.json()["message"]

    # Step 2: Sign
    signable = encode_defunct(text=message_text)
    signed = Account.sign_message(signable, WALLET_PRIVATE_KEY)
    signature = signed.signature.hex()

    # Step 3: Login
    r = requests.post(f"{BASE_URL}/login", json={"address": address, "signature": signature, "chain_id": CHAIN_ID})
    r.raise_for_status()
    token_data = r.json()

    os.makedirs(IDENTITY_DIR, exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)
    try:
        os.chmod(TOKEN_FILE, 0o600)
    except Exception:
        pass

    return token_data["access_token"]


def get_token() -> str:
    """Return a valid access token, using refresh or re-auth as needed.

    Token resolution order:
    1. Use the saved access token if it is not yet expired.
    2. If expired, call POST /refresh with the saved refresh token.
       The API rotates the refresh token on every call, so both tokens are
       written to disk immediately before returning — the old refresh token
       is invalid the moment the response arrives.
    3. If refresh fails (token expired, revoked, or missing), fall back to
       full SIWE re-authentication via POST /login.
    """
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE) as f:
                data = json.load(f)
        except Exception:
            data = {}

        access_token = data.get("access_token", "")
        refresh_token = data.get("refresh_token", "")

        if _token_is_valid(access_token):
            return access_token

        # Access token expired — attempt refresh regardless of refresh token
        # expiry (refresh tokens may be opaque and lack a decodable exp claim).
        if refresh_token:
            new_token = _refresh_access_token(refresh_token)
            if new_token:
                return new_token

    return authenticate()


def _auth(token: str, agent_key: str = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    if agent_key:
        headers["X-Agent-Private-Key"] = agent_key
    elif AGENT_PRIVATE_KEY:
        headers["X-Agent-Private-Key"] = AGENT_PRIVATE_KEY
    return headers


def list_portfolios(token: str) -> list:
    """List all portfolios for the authenticated user."""
    r = requests.get(f"{BASE_URL}/portfolio", headers=_auth(token))
    r.raise_for_status()
    return r.json()


def get_portfolio(token: str, portfolio_id: int, window: str = "1d") -> dict:
    """Get portfolio state with optional time window."""
    r = requests.get(f"{BASE_URL}/portfolio/{portfolio_id}", params={"window": window}, headers=_auth(token))
    r.raise_for_status()
    return r.json()


def request_recommendation(token: str, portfolio_id: int, message: str) -> dict:
    """Submit a recommendation request to the agent (async, returns ticket)."""
    payload = {
        "portfolio_id": portfolio_id,
        "message": message,
    }
    # Include agent_private_key in body for HYPERLIQUID portfolios
    if AGENT_PRIVATE_KEY:
        payload["agent_private_key"] = AGENT_PRIVATE_KEY
    r = requests.post(f"{BASE_URL}/agent/recommendation/message", json=payload, headers=_auth(token))
    r.raise_for_status()
    return r.json()


def poll_recommendation(token: str, ticket_id: str, max_wait: int = 60) -> dict:
    """Poll until recommendation is ready or timeout."""
    deadline = time.time() + max_wait
    while time.time() < deadline:
        r = requests.get(f"{BASE_URL}/agent/recommendation/poll/{ticket_id}", headers=_auth(token))
        r.raise_for_status()
        data = r.json()
        if data.get("status") in ("COMPLETED", "complete", "FAILED"):
            return data
        time.sleep(2)
    raise TimeoutError(f"Recommendation not ready after {max_wait}s")


def execute_recommendation(token: str, portfolio_id: int, rec_id: int, 
                           execute_onchain: bool = False, 
                           user_master_address: str = None) -> dict:
    """Execute an existing recommendation by ID."""
    payload = {"recommendation_id": rec_id}
    if execute_onchain is not None:
        payload["execute_onchain"] = execute_onchain
    if AGENT_PRIVATE_KEY:
        payload["agent_private_key"] = AGENT_PRIVATE_KEY
    if user_master_address:
        payload["user_master_address"] = user_master_address
    r = requests.post(f"{BASE_URL}/portfolio/{portfolio_id}/execute",
                      json=payload, headers=_auth(token))
    r.raise_for_status()
    return r.json()


def close_position(token: str, portfolio_id: int, symbol: str, 
                   user_master_address: str = None) -> dict:
    """Close an open position by symbol."""
    payload = {"symbol": symbol}
    if user_master_address:
        payload["user_master_address"] = user_master_address
    r = requests.post(f"{BASE_URL}/portfolio/{portfolio_id}/close-position",
                      json=payload, headers=_auth(token))
    r.raise_for_status()
    return r.json()


def get_recommendations(token: str, portfolio_id: int) -> list:
    """Get existing recommendations for a portfolio."""
    r = requests.get(f"{BASE_URL}/portfolio/{portfolio_id}/recommendation", headers=_auth(token))
    r.raise_for_status()
    return r.json()


def update_portfolio(token: str, portfolio_id: int, 
                     name: str = None, 
                     tokens_selected: list = None,
                     max_history_messages: int = None) -> dict:
    """Update portfolio settings (name, tokens, history limit).
    
    Args:
        token: Auth token
        portfolio_id: Portfolio ID
        name: New portfolio name (optional)
        tokens_selected: List of token symbols (e.g., ["BTC", "ETH", "SOL"])
        max_history_messages: Conversation history limit
    
    Returns:
        Updated portfolio info
    """
    payload = {}
    if name is not None:
        payload["name"] = name
    if tokens_selected is not None:
        payload["tokens_selected"] = tokens_selected
    if max_history_messages is not None:
        payload["max_history_messages"] = max_history_messages
    
    r = requests.put(f"{BASE_URL}/portfolio/{portfolio_id}",
                     json=payload, headers=_auth(token))
    r.raise_for_status()
    return r.json()


def chat(token: str, portfolio_id: int, message: str) -> dict:
    """Send a chat message to the portfolio agent (async, returns ticket)."""
    payload = {"portfolio_id": portfolio_id, "message": message}
    r = requests.post(f"{BASE_URL}/agent/chat/message", json=payload, headers=_auth(token))
    r.raise_for_status()
    return r.json()


def poll_chat(token: str, ticket_id: str, max_wait: int = 60) -> dict:
    """Poll until chat response is ready."""
    deadline = time.time() + max_wait
    while time.time() < deadline:
        r = requests.get(f"{BASE_URL}/agent/chat/poll/{ticket_id}", headers=_auth(token))
        r.raise_for_status()
        data = r.json()
        if data.get("status") in ("COMPLETED", "complete", "FAILED"):
            return data
        time.sleep(2)
    raise TimeoutError(f"Chat response not ready after {max_wait}s")


# CLI mode for tubman-bobtail-py usage
def main():
    """CLI entry point for katbot_client.py script."""
    import sys
    
    # Reload env if running as CLI
    env = {}
    if ENV_FILE and ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, val = line.split("=", 1)
                    env[key.strip()] = val.strip().strip('"')
    env.update(os.environ)  # Allow env var overrides
    
    if len(sys.argv) < 2:
        print("Usage: katbot_client.py <action> [args]")
        print("Actions: portfolio-state, execute, close-position, recommendations, request-recommendation, poll-recommendation, update-portfolio")
        sys.exit(1)
    
    action = sys.argv[1]
    portfolio_id = env.get("PORTFOLIO_ID")
    
    if not portfolio_id:
        print("ERROR: PORTFOLIO_ID must be set in katbot_client.env or environment")
        sys.exit(1)
    
    print(f"Using Portfolio ID: {portfolio_id}")
    token = get_token()
    
    if action == "portfolio-state":
        result = get_portfolio(token, int(portfolio_id), window="1d")
        print(json.dumps(result, indent=2))
    
    elif action == "execute":
        recommendation_id = sys.argv[2] if len(sys.argv) > 2 else None
        if not recommendation_id:
            print("ERROR: recommendation_id required")
            sys.exit(1)
        result = execute_recommendation(
            token, int(portfolio_id), int(recommendation_id),
            execute_onchain=False,
            user_master_address=env.get("WALLET_ADDRESS")
        )
        print(json.dumps(result, indent=2))
    
    elif action == "close-position":
        symbol = sys.argv[2] if len(sys.argv) > 2 else None
        if not symbol:
            print("ERROR: symbol required (e.g., ETH)")
            sys.exit(1)
        result = close_position(token, int(portfolio_id), symbol, user_master_address=env.get("WALLET_ADDRESS"))
        print(json.dumps(result, indent=2))
    
    elif action == "recommendations":
        result = get_recommendations(token, int(portfolio_id))
        print(json.dumps(result, indent=2))
    
    elif action == "request-recommendation":
        message = sys.argv[2] if len(sys.argv) > 2 else "Analyze portfolio tokens and generate recommendations based on the current market."
        result = request_recommendation(token, int(portfolio_id), message)
        print(json.dumps(result, indent=2))
    
    elif action == "poll-recommendation":
        ticket_id = sys.argv[2] if len(sys.argv) > 2 else None
        if not ticket_id:
            print("ERROR: ticket_id required")
            sys.exit(1)
        result = poll_recommendation(token, ticket_id)
        print(json.dumps(result, indent=2))
    
    elif action == "update-portfolio":
        # Parse args: --tokens BTC,ETH,SOL or --name "New Name"
        tokens_arg = None
        name_arg = None
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--tokens" and i + 1 < len(sys.argv):
                tokens_arg = sys.argv[i + 1].split(",")
                i += 2
            elif sys.argv[i] == "--name" and i + 1 < len(sys.argv):
                name_arg = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        if not tokens_arg and not name_arg:
            print("Usage: update-portfolio --tokens BTC,ETH,SOL [--name \"New Name\"]")
            sys.exit(1)
        
        result = update_portfolio(token, int(portfolio_id), name=name_arg, tokens_selected=tokens_arg)
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
