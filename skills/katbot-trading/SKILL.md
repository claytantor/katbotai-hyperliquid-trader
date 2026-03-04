---
name: katbot-trading
version: 0.1.3
description: Live crypto trading on Hyperliquid via Katbot.ai. Includes BMI market analysis, token selection, and AI-powered trade execution.
# Note: Homepage URL removed to avoid GitHub API rate limit errors during publish
metadata:
  {
    "openclaw":
      {
        "emoji": "📈",
        "requires": { "bins": ["python3", "uv"], "env": ["WALLET_PRIVATE_KEY", "KATBOT_HL_AGENT_PRIVATE_KEY"] },
        "primaryEnv": "KATBOT_HL_AGENT_PRIVATE_KEY",
        "install": "uv pip install -r requirements.txt"
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
- **Tools**: This skill uses `uv` for fast Python dependency management. Run the install command to set up the environment.
- **Environment Variables**:
  - `WALLET_PRIVATE_KEY`: Your MetaMask wallet private key. **Used only for initial onboarding (SIWE login) or re-authentication.** It is **NEVER saved to disk** by the onboarding script.
  - `KATBOT_HL_AGENT_PRIVATE_KEY`: The agent private key for the Katbot portfolio. **Primary key for daily trading operations.** 
    - The onboarding script saves this key securely to `~/.openclaw/workspace/katbot-identity/katbot_secrets.json` (mode 600) for persistence.
    - Alternatively, you can set it as an environment variable for purely ephemeral execution.
- **Config**: 
  - Identity files are stored in `~/.openclaw/workspace/katbot-identity/` (configurable via `KATBOT_IDENTITY_DIR`).
  - `katbot_config.json`: Contains `wallet_address`, `portfolio_id`, and `chain_id`.
  - `katbot_token.json`: Contains the session JWT.

## Usage Rules

- **ALWAYS** check the BMI before suggesting a new trade.
- **NEVER** execute a trade without explicit user confirmation (e.g., "Confirm execution of LONG AAVE?").
- **NEVER** log or reveal private keys in the chat.
- **ALWAYS** report the risk/reward ratio and leverage for any recommendation.

## Tools

The skill includes the following scripts located in `{baseDir}/tools/` (dependencies defined in `requirements.txt`):

- `katbot_onboard.py`: **First-time setup wizard.** Authenticates via SIWE using your Wallet Key, creates/selects a portfolio, and saves the Agent Key locally to the secure identity directory.
- `katbot_client.py`: Core API client for authentication and portfolio state. Reads credentials from the identity directory.
- `katbot_workflow.py`: End-to-end trading workflow (BMI -> Recommendation).
- `token_selector.py`: Momentum-based token selection via CoinGecko.

## First-Time Setup

When a user first installs this skill, guide them through onboarding:

```bash
# Install dependencies
uv pip install -r requirements.txt

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
