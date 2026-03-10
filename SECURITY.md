# Security Review Response: katbot-trading Skill

This document is a technical response to the security flag raised against the `katbot-trading` skill on the OpenClaw/OpenHub registry. It explains what the skill does, why certain credential-handling patterns are architecturally necessary, and what specific steps have been taken to protect users.

---

## What the Skill Does

`katbot-trading` is an OpenClaw skill that connects an AI agent to [Katbot.ai](https://api.katbot.ai), a portfolio management service for trading perpetual futures on [Hyperliquid](https://hyperliquid.xyz). The skill allows an agent to:

1. Authenticate with the Katbot API using Sign-In with Ethereum (SIWE)
2. Retrieve AI-generated trade recommendations (entry, take-profit, stop-loss, leverage)
3. Execute those trades on Hyperliquid, with mandatory explicit user confirmation
4. Monitor open positions and portfolio performance

The skill does **not** interact with Hyperliquid directly. All on-chain interactions are delegated to the Katbot API, which uses a scoped **agent wallet** — not the user's primary MetaMask wallet — to sign and submit transactions.

---

## Why Credential Handling Is Required

### The Hyperliquid Agent Wallet Model

Hyperliquid's security architecture supports a concept called an **API wallet** (agent wallet): a separate, limited-scope keypair that a user explicitly authorizes to trade on behalf of their main wallet. This is a first-party Hyperliquid feature documented at [app.hyperliquid.xyz → Settings → API](https://app.hyperliquid.xyz).

The agent wallet:
- Has trading permissions only — it cannot withdraw funds to external addresses
- Has a configurable expiry (typically 180 days)
- Can be revoked instantly by the user at any time from the Hyperliquid UI
- Is a **separate keypair from the user's MetaMask wallet** — the main wallet's funds are not directly accessible to it

This design means the blast radius of a compromised agent key is bounded: an attacker could place or close trades, but cannot drain the underlying wallet to an arbitrary address.

### Why the Agent Key Must Be Transmitted to the API

Hyperliquid's on-chain transaction submission requires the agent wallet to sign each order. The Katbot API operates as a server-side execution engine: it constructs the transaction, signs it using the agent key, and submits it to Hyperliquid.

This means the agent key must be available to the Katbot API at execution time. There is no local-signing alternative in this architecture — Hyperliquid's on-chain order format requires the signing to happen at the point of submission, and the submission happens server-side.

**This is the same model used by all server-side trading bots and API-connected trading platforms** (e.g., 3Commas, Pionex, Bitsgap) — the trading key is shared with the platform's server in exchange for automated execution. The scoped agent wallet model limits what that key can do.

The key is transmitted only on two API calls:
- `POST /agent/recommendation/message` — to request a trade recommendation
- `POST /portfolio/{id}/execute` — to execute a confirmed trade

It is sent as both an HTTP header (`X-Agent-Private-Key`) and in the JSON body. It is **never** logged, stored in browser state, or included in read-only calls (portfolio state, chat, polling).

### Why the MetaMask Wallet Key Is Handled Differently

The MetaMask wallet key (`WALLET_PRIVATE_KEY`) is used exclusively for SIWE (Sign-In with Ethereum) authentication. SIWE is an industry-standard login protocol (EIP-4361) used across the Web3 ecosystem.

The key signing happens **entirely locally** using the `eth_account` library. Only the resulting signature is sent to the API — the private key itself is never transmitted over the network. The skill enforces this with hard rules: the wallet key must not be persisted to disk, must not be set in environment profiles, and is only accepted via interactive hidden input during onboarding.

---

## What Has Been Done to Protect Users

The following measures have been implemented specifically in response to security review feedback:

### 1. Removed Silent Private Key Injection from `.env` Loader

An earlier version of `katbot_client.py` would load `WALLET_PRIVATE_KEY` and `KATBOT_HL_AGENT_PRIVATE_KEY` from a `.env` file into `os.environ` at import time. This was removed. The `.env` loader now reads **only non-secret config** (`KATBOT_BASE_URL`, `KATBOT_IDENTITY_DIR`, `CHAIN_ID`). Private keys cannot be loaded from any file path at import time.

### 2. Narrowed `.env` Search Paths

The original `.env` loader searched three project-relative paths, any of which could be silently populated by placing a file in the repository tree. The search paths have been narrowed to:
- `~/katbot_client.env` (user home directory)
- `$OPENCLAW_HOME/katbot_identity/katbot_client.env` (only if `OPENCLAW_HOME` is explicitly set)

This eliminates the risk of a project-committed file silently loading secrets.

### 3. Removed `WALLET_PRIVATE_KEY` from Registry Required Env Vars

The OpenClaw metadata previously declared `WALLET_PRIVATE_KEY` as a required environment variable, implying it should be set before skill installation. This was incorrect and has been removed. The registry now declares only `KATBOT_HL_AGENT_PRIVATE_KEY` as required, accurately reflecting that the wallet key is an emergency fallback used only during re-authentication.

### 4. Identity Files Written with Mode 600

All files containing secrets (`katbot_token.json`, `katbot_secrets.json`) are written with Unix file mode `0o600` (owner read/write only). The `WALLET_PRIVATE_KEY` is explicitly never written to any file on disk.

### 5. Explicit Credential Transmission Notice in SKILL.md

`SKILL.md` contains a dedicated **Credential Transmission Notice** section that the agent is instructed to present to the user before the first onboarding or trading operation. The notice includes a complete table of what credentials leave the machine, on which calls, and why. The agent is instructed not to proceed without affirmative user confirmation.

### 6. Agent Rules in SKILL.md Enforce Conservative Key Handling

`SKILL.md` contains explicit, enumerated rules for the AI agent:
- Never pre-set `WALLET_PRIVATE_KEY` in the environment
- Never create a `.env` file containing private keys
- Never log, print, or reveal any key or token in chat
- Never read or summarize identity directory files
- Warn the user if `WALLET_PRIVATE_KEY` is found already set in the environment outside of an active re-auth session

---

## Summary of Credential Behavior

| Credential | Stored where | Transmitted to | When |
|------------|-------------|----------------|------|
| `WALLET_PRIVATE_KEY` | Memory only (never to disk) | Never (signature only is sent) | Onboarding / re-auth only |
| `KATBOT_HL_AGENT_PRIVATE_KEY` | `~/.openclaw/workspace/katbot-identity/katbot_secrets.json` (mode 600) | `api.katbot.ai` | Recommendation requests and trade execution |
| `access_token` / `refresh_token` | `~/.openclaw/workspace/katbot-identity/katbot_token.json` (mode 600) | `api.katbot.ai` | All authenticated API calls (Bearer header) |

---

## Residual Trust Requirement

This skill requires the user to trust `api.katbot.ai` with their Hyperliquid agent trading key. This is an explicit, documented, user-consented trust grant — not a hidden behavior. The skill makes this trust requirement clear before any credential is used. Users who do not wish to extend this trust to the Katbot API should not install this skill.

The Katbot API is the intended recipient of the agent key. This is the designed purpose of the Hyperliquid agent wallet model, and is consistent with how all API-connected trading automation works.
