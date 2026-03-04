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
| Python 3.11+ | For running the trading scripts |

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

## Quick Start (6 Steps to Your First Trade)

**1. Get OpenClaw running**
Install [OpenClaw](https://docs.openclaw.ai) and have an agent running. That's your AI assistant that will do the trading.

**2. Install the skill**
```bash
clawhub install katbot-trading
```

**3. Install Python deps**
```bash
pip install requests eth-account
```

**4. Run the onboarding wizard**
```bash
python3 ~/.openclaw/workspace/skills/katbot-trading/tools/katbot_onboard.py
```
It will ask for your MetaMask private key (hidden, never saved to disk). It logs you into Katbot.ai, creates your Hyperliquid portfolio, and saves your agent key locally.

**5. Authorize the agent on Hyperliquid**
The wizard prints your agent address. Go to [app.hyperliquid.xyz](https://app.hyperliquid.xyz) → Settings → API, add that address with trading permissions. One-time setup.

**6. Start trading — just talk to your agent**
> "How's the market looking?"
> "Run the trading workflow"
> "How's my portfolio doing?"
> "Close the position"

The agent checks the BMI, picks tokens, gets a recommendation, and asks you to confirm before executing anything. Your keys never leave your machine.

> The only manual part is step 5 — the Hyperliquid agent authorization requires a MetaMask signature in the browser. Everything else is automated.

---

## Installation (Detailed)

### 1. Install the Skill via ClawHub

```bash
clawhub install katbot-trading
```

Or clone manually and point your agent at `skills/katbot-trading/SKILL.md`.

### 2. Install Python Dependencies

```bash
pip install -r skills/katbot-trading/requirements.txt
```

### 3. Run the Onboarding Wizard

Instead of manually configuring files and env vars, run the interactive wizard:

```bash
python3 scripts/katbot_onboard.py
```

The wizard will:
1. **Prompt for your MetaMask private key** (hidden input — never saved to disk)
2. **Authenticate** with `api.katbot.ai` via SIWE (Sign-In with Ethereum)
3. **List existing portfolios** or walk you through creating a new one
4. **Save the agent private key and config** to `~/.openclaw/workspace/katbot-identity/` (mode 600)
5. **Print the Hyperliquid agent authorization steps** and env var export lines

After onboarding your identity files will be at:

```
~/.openclaw/workspace/katbot-identity/
├── katbot_config.json     ← portfolio config (wallet address, portfolio ID, chain)
├── katbot_secrets.json    ← agent private key (chmod 600, never commit)
└── katbot_token.json      ← JWT token cache (chmod 600)
```

### 4. Set Environment Variables (Headless / Automated Setups Only)

For normal interactive use, **you don't need to set any env vars** — the wizard saves everything locally and the JWT token is reused automatically.

If you're running in a **headless or automated environment** (e.g. a server, CI, or scheduled cron job), set these in your `~/.bashrc` or `~/.zshrc`:

```bash
# Wallet key — only needed for unattended token refresh (never store in files)
export WALLET_PRIVATE_KEY=0xYourMetaMaskPrivateKey

# Agent key — saved locally by the wizard, but can also be set here for portability
export KATBOT_HL_AGENT_PRIVATE_KEY=0xYourAgentPrivateKey
```

> ⚠️ Never commit these values to git. Use a secrets manager or your shell profile only.

### 5. Authorize the Agent on Hyperliquid

The wizard prints your agent address. Then:
1. Go to [app.hyperliquid.xyz](https://app.hyperliquid.xyz) → Settings → API
2. Add agent address as an API Wallet with trading permissions
3. Set expiry to 180 days and confirm the MetaMask transaction

---

## Running the Trading Workflow

```bash
python3 scripts/katbot_workflow.py \
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
