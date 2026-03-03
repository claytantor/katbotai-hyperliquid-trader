# katbotai-hyperliquid-trader

> Add live Hyperliquid trading superpowers to any OpenClaw agent using [Katbot.ai](https://katbot.ai).

This repository contains the **OpenClaw skill** for Katbot.ai trading — giving your agent the ability to:

- Monitor the **BTC Momentum Index (BMI)** for directional trade signals
- Automatically select the best-performing tokens from Hyperliquid
- Request **AI-powered trade recommendations** from the Katbot agent
- Execute and manage live trades on Hyperliquid — all from natural conversation

⚠️ Live trading involves real financial risk. Start with testnet. Never risk more than you can afford to lose.

---

## Requirements

| Requirement | Notes |
|---|---|
| [OpenClaw](https://docs.openclaw.ai) | Installed and running |
| [Katbot.ai account](https://katbot.ai) | Whitelisted (pre-alpha) |
| [MetaMask](https://metamask.io) | Connected to Arbitrum network |
| [Hyperliquid account](https://app.hyperliquid.xyz) | Testnet or Mainnet |
| Python 3.11+ + uv | For running the trading scripts |

---

## How It Works

```
You (chat) ──→ OpenClaw Agent ──→ https://api.katbot.ai ──→ Hyperliquid
```

Your OpenClaw agent uses the Katbot API to get recommendations and execute trades.
The agent **never holds your private keys in memory** — they live in environment variables and are only used to sign trade requests.

---

## Repository Structure

```
katbotai-hyperliquid-trader/
├── README.md                          ← You are here
├── scripts/
│   ├── katbot_client.py               ← API client (SIWE auth, all API ops)
│   ├── katbot_workflow.py             ← Full trading workflow (BMI → trade)
│   └── token_selector.py             ← CoinGecko token selection by momentum
└── skills/
    └── katbot-trading/
        ├── SKILL.md                   ← OpenClaw skill definition
        └── tools/                     ← Symlinks to scripts (used by the skill)
```

---

## Installation

### 1. Install the Skill via ClawHub

```bash
clawhub install katbot-trading
```

Or clone manually and point your agent at `skills/katbot-trading/SKILL.md`.

### 2. Install Python Dependencies

```bash
pip install requests eth-account
# or with uv:
uv add requests eth-account
```

### 3. Create Your Identity Config

Create an identity folder for your agent:

```bash
mkdir -p ~/.openclaw/workspace/katbot-identity
```

Create `~/.openclaw/workspace/katbot-identity/katbot_config.json`:

```json
{
  "base_url": "https://api.katbot.ai",
  "wallet_address": "0xYourMetaMaskWalletAddress",
  "portfolio_id": 5,
  "portfolio_name": "my-hl-mainnet",
  "chain_id": 42161
}
```

Copy the client script:

```bash
cp scripts/katbot_client.py ~/.openclaw/workspace/katbot-identity/
```

### 4. Set Environment Variables

```bash
export WALLET_PRIVATE_KEY=0xYourWalletPrivateKey
export KATBOT_HL_AGENT_PRIVATE_KEY=0xYourAgentPrivateKey
```

Add these to `~/.bashrc` or `~/.zshrc` to persist them.

### 5. Test Authentication

```bash
python3 scripts/katbot_client.py
# Should print: ✅ Authenticated as 0xYour...
# Then list your portfolios and show portfolio state
```

---

## Creating a Portfolio

If you don't have a Katbot portfolio yet:

```bash
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from katbot_client import get_token, _auth
import requests

token = get_token()
r = requests.post('https://api.katbot.ai/portfolio', json={
  'name': 'my-hl-mainnet',
  'description': 'OpenClaw agent-managed portfolio',
  'initial_balance': 1000.0,
  'portfolio_type': 'HYPERLIQUID',
  'is_testnet': False,
  'tokens_selected': ['BTC', 'ETH', 'SOL']
}, headers=_auth(token))
data = r.json()
print(f'Portfolio ID: {data[\"id\"]}')
print(f'Agent Address: {data[\"agent_address\"]}')
print(f'Agent Priv Key: {data[\"agent_private_key\"]}')
print('Save the Agent Private Key as KATBOT_HL_AGENT_PRIVATE_KEY!')
"
```

⚠️ The `agent_private_key` is shown **once**. Save it immediately as your `KATBOT_HL_AGENT_PRIVATE_KEY`.

Then authorize the agent on Hyperliquid:
1. Copy the `agent_address` from the response
2. Go to [app.hyperliquid.xyz](https://app.hyperliquid.xyz) → Settings → API
3. Add agent address as an API Wallet with trading permissions
4. Set expiry to 180 days and confirm the MetaMask transaction

---

## Running the Trading Workflow

```bash
KATBOT_HL_AGENT_PRIVATE_KEY=0x... \
python3 scripts/katbot_workflow.py \
  --portfolio-id 5 \
  --bmi-threshold 15 \
  --top 5
```

This will:
1. Check the BMI — exits cleanly if neutral (no low-conviction trades)
2. Select top/worst 5 tokens based on market direction
3. Update your portfolio token list
4. Request a recommendation from the Katbot AI agent
5. Present the recommendation with entry, TP, SL, R/R, and leverage
6. **Ask you to confirm before executing**

---

## Agent Setup

Tell your OpenClaw agent about this skill by adding to your `MEMORY.md`:

```markdown
## Katbot Trading Setup
- API: https://api.katbot.ai
- Identity: ~/.openclaw/workspace/katbot-identity/
- Client: katbot_client.py
- Portfolio ID: 5 (my-hl-mainnet)
- Skill: katbotai-hyperliquid-trader/skills/katbot-trading/SKILL.md
```

Then just talk to your agent naturally:

> "How's the market looking?"
> → Agent checks BMI and reports BTC momentum + top movers

> "Run the trading workflow"
> → Agent checks BMI, selects tokens, gets recommendation, asks to confirm

> "How's the portfolio doing?"
> → Agent queries API and reports positions + uPnL

> "Close the position"
> → Agent closes via API after your confirmation

---

## BMI Signal Reference

The BTC Momentum Index (BMI) tells us whether the market is trending strongly enough to trade.

| BMI | Signal | Action |
|---|---|---|
| ≥ +15 | 🟢 BULLISH | Select top gainers → get LONG recommendation |
| ≤ -15 | 🔴 BEARISH | Select worst performers → get SHORT recommendation |
| -15 to +15 | ⚪ NEUTRAL | Stay flat. No trade. |

---

## Leverage Guidelines

| Condition | Leverage |
|---|---|
| RSI < 20 or > 80 (extreme) | 1x only |
| Clear trend, BMI ±15–30 | 1–2x |
| Strong momentum, BMI ±30+ | 2–5x |
| Textbook breakout, high volume | Up to 5x |

> At 5x leverage, a 5% stop loss = 25% of your margin at risk. Always honor your stops.

---

## API Reference

Full Swagger docs: [https://api.katbot.ai/docs](https://api.katbot.ai/docs)

| Operation | Method | Endpoint |
|---|---|---|
| Get nonce | GET | `/get-nonce/{address}?chain_id=42161` |
| Login | POST | `/login` |
| Verify auth | GET | `/me` |
| List portfolios | GET | `/portfolio` |
| Create portfolio | POST | `/portfolio` |
| Portfolio state | GET | `/portfolio/{id}` |
| Update tokens | PUT | `/portfolio/{id}` |
| Request recommendation | POST | `/agent/recommendation/message` |
| Poll recommendation | GET | `/agent/recommendation/poll/{ticket_id}` |
| Execute trade | POST | `/portfolio/{id}/execute` |
| Close position | POST | `/portfolio/{id}/close-position` |

---

## Troubleshooting

**401 Unauthorized** — JWT expired. `katbot_client.py` auto-refreshes. If it fails, delete `katbot_token.json` and re-run.

**403 / Agent key rejected** — Verify `KATBOT_HL_AGENT_PRIVATE_KEY` matches the agent address added to Hyperliquid.

**Recommendation FAILED** — Check your Katbot subscription includes AI recommendations. Contact support on Discord.

**Trade won't fill** — On testnet, some pairs have thin orderbooks. Try mainnet or switch to BTC/ETH.

**BMI always neutral** — BMI is based on BTC 4h momentum. In choppy sideways markets this is expected — it's protecting you from bad trades.

---

## Contributing

Found a bug? Have an improvement? PRs welcome.

This repo is the living configuration for an agent that trades real money. Every improvement helps real users make better decisions.

---

## Links

- [Katbot.ai](https://katbot.ai)
- [Katbot API Docs](https://api.katbot.ai/docs)
- [OpenClaw Docs](https://docs.openclaw.ai)
- [ClawHub — katbot-trading skill](https://clawhub.com)
- [Hyperliquid](https://app.hyperliquid.xyz)
- [Katbot Discord](https://discord.gg/ZP73Y8zn)
- [OpenClaw Discord](https://discord.com/invite/clawd)

---

Built by [Tubman Clawbot](https://github.com/tubmanclaw) 😼 — the OpenClaw agent that trades its own portfolio.
