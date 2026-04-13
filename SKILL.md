---
name: openclaw-nebius
description: Bootstrap and verify OpenClaw against Nebius Token Factory or Nebius Serverless using current model discovery, env-backed API keys, and OpenClaw provider configuration. Use when Codex needs to install OpenClaw, connect it to Nebius-hosted open-source models, generate or apply ~/.openclaw config changes, allowlist Nebius models, verify the gateway, or troubleshoot provider errors such as "model not allowed".
---

# OpenClaw on Nebius

Install OpenClaw, wire it to Nebius Token Factory, and verify a working model quickly. Default to Token Factory because it is the simplest pay-per-token path. Only switch to Nebius Serverless when the user explicitly wants a hosted OpenClaw endpoint.

## Quick Start

1. Confirm `NEBIUS_API_KEY` is available. If it is missing, have the user create a Token Factory API key and export it first. Never commit the key.
2. Detect `openclaw` with `which openclaw`. If it is missing, install it with `npm install -g openclaw@latest`.
3. Use `python3 scripts/setup_openclaw_nebius.py --apply` to discover Nebius models and configure OpenClaw. Add `--primary-model` and repeated `--model MODEL_ID:alias` flags when the user wants specific models.
4. Restart the gateway only if the helper reports changed config or if the models are still missing: `openclaw gateway restart`.
5. Verify with `openclaw models list`, `openclaw models status`, and `openclaw dashboard`.

## Workflow

### 1. Prefer Token Factory first

- Use Token Factory when the user wants local OpenClaw plus Nebius-hosted inference.
- Read `references/tokenfactory.md` when current command syntax or doc-backed detail matters.
- Read `references/serverless.md` only when the user explicitly asks to deploy OpenClaw itself on Nebius.

### 2. Check prerequisites

- Require `python3`, `npm`, and a Nebius API key in `NEBIUS_API_KEY`.
- Accept `NEBIUS_TOKEN_FACTORY_API_KEY` only as a compatibility fallback. Normalize back to `NEBIUS_API_KEY` when possible.
- Keep secrets in env vars or env substitution strings such as `${NEBIUS_API_KEY}`. Do not write raw keys into repo files.
- If global npm install fails on permissions, prefer a user-local install such as `npm install -g --prefix ~/.openclaw openclaw@latest` and use `~/.openclaw/bin/openclaw`.

### 3. Discover or pick models

- Prefer live discovery by running `python3 scripts/setup_openclaw_nebius.py --list-models`.
- If the environment blocks live discovery but the model ids are already known, rerun with `--offline --model ...`.
- If the user does not care, use the workshop defaults when they are available:
  - `moonshotai/Kimi-K2.5` as primary
  - `meta-llama/Llama-3.3-70B-Instruct-fast` as a fast fallback
  - `deepseek-ai/DeepSeek-R1-0528` as a reasoning option
- If live discovery does not find those ids, pick equivalent current Token Factory models and keep aliases readable, for example `kimi`, `llama70b`, and `deepseek`.

### 4. Configure OpenClaw

- Prefer the helper over hand-editing config.
- Default command:

```bash
python3 scripts/setup_openclaw_nebius.py --apply
```

- Explicit-model example:

```bash
python3 scripts/setup_openclaw_nebius.py \
  --apply \
  --primary-model moonshotai/Kimi-K2.5 \
  --model moonshotai/Kimi-K2.5:kimi \
  --model meta-llama/Llama-3.3-70B-Instruct-fast:llama70b \
  --model deepseek-ai/DeepSeek-R1-0528:deepseek
```

- Let the helper manage:
  - `models.mode = merge`
  - `models.providers.nebius.*`
  - `agents.defaults.model.primary`
  - `agents.defaults.models`
- Keep the allowlist under `agents.defaults.models`. If it is missing, OpenClaw can reject the model even when the provider exists.

### 5. Verify

- Run `openclaw models list` and confirm the `nebius/...` models exist.
- Run `openclaw models status` to check the resolved default.
- Open `openclaw dashboard` or `openclaw tui`.
- If the chosen model still fails, run `openclaw gateway restart` and inspect `openclaw logs --follow`.

### 6. Troubleshoot

- `"model not allowed"`: rebuild the allowlist with the helper or add the missing entry under `agents.defaults.models`.
- Models do not show up: confirm the API key is exported and the base URL matches the intended Token Factory endpoint.
- Need a regional or private endpoint: rerun the helper with `--base-url`.
- Need Docker: keep inference on Nebius while the gateway runs locally in Docker. Read `references/tokenfactory.md` before changing the runtime layout.
- Need hosted OpenClaw on Nebius: switch to `references/serverless.md`.

## Resources

- `scripts/setup_openclaw_nebius.py`: discover Token Factory models, print exact `openclaw config set` commands, or apply them directly.
- `references/tokenfactory.md`: current Token Factory and OpenClaw notes, including the doc-backed custom-provider flow.
- `references/serverless.md`: Nebius Serverless deployment path and the extra decisions it requires.
