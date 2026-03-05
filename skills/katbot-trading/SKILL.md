---
name: katbot-trading
version: 0.2.9
description: Live crypto trading on Hyperliquid via Katbot.ai. Includes BMI market analysis, token selection, and AI-powered trade execution.
# Note: Homepage URL removed to avoid GitHub API rate limit errors during publish
metadata:
  {
    "openclaw":
      {
        "emoji": "📈",
        "requires": { "bins": ["python3"], "env": ["WALLET_PRIVATE_KEY", "KATBOT_HL_AGENT_PRIVATE_KEY"] },
        "primaryEnv": "KATBOT_HL_AGENT_PRIVATE_KEY",
        "install": "pip install -r requirements.txt"
      }
  }
---

# Katbot Trading Skill

This skill teaches the agent how to use the Katbot.ai API to manage a Hyperliquid trading portfolio.

## Capabilities

1. **Market Analysis**: Check the BTC Momentum Index (BMI) and 24h gainers/losers.
2. **Token Selection**: Automatically pick the best tokens for the current market direction.
3. **Recommendations**: Get AI-powered trade setups (Entry, TP, SL, Leverage).
4. **Execution**: Execute and close trades on Hyperliquid with user confirmation.
5. **Portfolio Tracking**: Monitor open positions, uPnL, and balances.

## Setup Requirements

- **Katbot API**: `https://api.katbot.ai`
- **Tools**: This skill uses standard Python packages. Run the install command to set up the environment.
- **Environment Variables**:
  - `WALLET_PRIVATE_KEY`: Your MetaMask wallet private key. **Used only for onboarding (SIWE login).** It is ephemeral and should NOT be persisted in shell history or env files. If the session expires, re-run onboarding.
  - `KATBOT_HL_AGENT_PRIVATE_KEY`: The agent private key for the Katbot portfolio. **Primary key for daily trading operations.** 
    - The onboarding script saves this key securely to `~/.openclaw/workspace/katbot-identity/katbot_secrets.json` (mode 600) for persistence.
    - Alternatively, you can set it as an environment variable for purely ephemeral execution.
- **Config**:
  - Identity files are stored in `~/.openclaw/workspace/katbot-identity/` (configurable via `KATBOT_IDENTITY_DIR`).
  - `katbot_config.json`: Contains `wallet_address`, `portfolio_id`, and `chain_id`.
  - `katbot_token.json`: Contains both `access_token` and `refresh_token` (mode 600).

## Authentication Flow

The skill manages tokens automatically via `katbot_client.get_token()`:

1. **Check access token expiry**: Decode the JWT `exp` claim from `katbot_token.json`. If valid (not expiring within 60s), use it directly.
2. **Refresh if expired**: If the access token is expired but the `refresh_token` is still valid, call `POST /refresh` with `{"refresh_token": "<token>"}`. On success, save the new `access_token` and `refresh_token` back to `katbot_token.json` (mode 600) automatically.
3. **Re-authenticate if refresh fails**: If the refresh token is also expired or missing, fall back to full SIWE re-authentication via `POST /login`. This requires `WALLET_PRIVATE_KEY` to be available.

**Never call `/login` if `/refresh` can succeed first.**

## Usage Rules

- **ALWAYS** check the BMI before suggesting a new trade.
- **NEVER** execute a trade without explicit user confirmation (e.g., "Confirm execution of LONG AAVE?").
- **NEVER** log or reveal private keys in the chat.
- **ALWAYS** report the risk/reward ratio and leverage for any recommendation.
- **ALWAYS** let `get_token()` handle token refresh automatically — do not manually manage tokens.

## Tools

All scripts are in `{baseDir}/tools/` (dependencies in `requirements.txt`):

- `ensure_env.sh`: **Run before any tool.** Checks if dependencies are installed for the current skill version and re-installs if needed. Safe to call every time — it exits immediately if already up to date.
- `katbot_onboard.py`: **First-time setup wizard.** Authenticates via SIWE using your Wallet Key, creates/selects a portfolio, and saves the Agent Key locally to the secure identity directory.
- `katbot_client.py`: Core API client for authentication and portfolio state. Reads credentials from the identity directory.
- `katbot_workflow.py`: End-to-end trading workflow (BMI -> Recommendation).
- `token_selector.py`: Momentum-based token selection via CoinGecko.

## Environment Management

This skill tracks its installed dependency version using a stamp file at `{baseDir}/.installed_version`. When the skill is upgraded, the stamp version will not match the skill version, and `ensure_env.sh` will automatically re-run `pip install`.

**The agent MUST run `ensure_env.sh` before every tool invocation:**

```bash
bash {baseDir}/tools/ensure_env.sh {baseDir}
```

- If the stamp matches the current version: exits immediately (fast, no pip call).
- If the skill was upgraded or never installed: runs `pip install -r requirements.txt` and writes the new stamp.
- If `python3` is missing: prints a clear error and exits with code 1.

### Detecting an Upgrade

If the user says the skill was updated or if a tool fails with an `ImportError` or `ModuleNotFoundError`, always run `ensure_env.sh` first to sync dependencies before retrying.

## First-Time Setup

When a user first installs this skill, guide them through onboarding:

```bash
# Ensure dependencies are installed
bash {baseDir}/tools/ensure_env.sh {baseDir}

# Run onboarding wizard
python3 {baseDir}/tools/katbot_onboard.py
```

The wizard will:
1. Prompt for `WALLET_PRIVATE_KEY` (hidden input) if not set in environment.
2. Authenticate with api.katbot.ai via SIWE.
3. List existing portfolios or create a new one.
4. Save the `KATBOT_HL_AGENT_PRIVATE_KEY` and config to `~/.openclaw/workspace/katbot-identity/`.
5. Print instructions for authorizing the agent on Hyperliquid.

After onboarding, the skill runs autonomously using the saved credentials.

To run these tools, use `exec` with `PYTHONPATH={baseDir}/tools`.
