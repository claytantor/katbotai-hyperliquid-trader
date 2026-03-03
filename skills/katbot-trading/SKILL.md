---
name: katbot-trading
description: Live crypto trading on Hyperliquid via Katbot.ai. Includes BMI market analysis, token selection, and AI-powered trade execution.
metadata:
  {
    "openclaw":
      {
        "emoji": "📈",
        "requires": { "bins": ["python3", "uv"], "env": ["WALLET_PRIVATE_KEY", "KATBOT_HL_AGENT_PRIVATE_KEY"] },
        "primaryEnv": "KATBOT_HL_AGENT_PRIVATE_KEY",
        "homepage": "https://github.com/claytantor/katbotai-hyperliquid-trader"
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
- **Environment Variables**:
  - `WALLET_PRIVATE_KEY`: Your MetaMask wallet private key (used for SIWE login).
  - `KATBOT_HL_AGENT_PRIVATE_KEY`: The agent private key from your Katbot portfolio.
- **Config**: 
  - An identity file at `{baseDir}/identity/katbot_config.json` containing `wallet_address`, `portfolio_id`, and `chain_id`.

## Usage Rules

- **ALWAYS** check the BMI before suggesting a new trade.
- **NEVER** execute a trade without explicit user confirmation (e.g., "Confirm execution of LONG AAVE?").
- **NEVER** log or reveal private keys in the chat.
- **ALWAYS** report the risk/reward ratio and leverage for any recommendation.

## Tools

The skill provides access to the following scripts located in `{baseDir}/tools/`:

- `katbot_client.py`: Core API client for authentication and portfolio state.
- `katbot_workflow.py`: End-to-end trading workflow (BMI -> Recommendation).
- `token_selector.py`: Momentum-based token selection via CoinGecko.

To run these tools, use `exec` with `PYTHONPATH={baseDir}/tools` and the appropriate environment variables.
