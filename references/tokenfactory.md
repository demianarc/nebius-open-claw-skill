# Token Factory Path

Use this path when the user wants OpenClaw to stay local while model inference runs on Nebius.

## Current facts

- OpenClaw supports non-interactive onboarding for custom OpenAI-compatible providers via `openclaw onboard --non-interactive --auth-choice custom-api-key --custom-base-url ... --custom-model-id ... --custom-compatibility openai`.
- OpenClaw custom provider config lives under `models.providers.<provider-id>`, and current config docs list `api`, `baseUrl`, `apiKey`, and `models` as the relevant keys.
- OpenClaw config values support env substitution strings such as `${NEBIUS_API_KEY}`.
- Current OpenClaw CLI docs use `openclaw models list`, `openclaw models status`, and `openclaw models set <model-or-alias>` for model verification and switching.
- Nebius Token Factory examples use the OpenAI-compatible base URL `https://api.tokenfactory.nebius.com/v1`.

## Base URL note

- Nebius docs currently show both the global base URL above and some regional `eu-west1` examples.
- Treat the global URL as the default unless the user explicitly asks for a regional or private endpoint.
- If a request must stay in a specific region or route through a private endpoint, override the helper with `--base-url`.

This regional fallback is an inference from the docs rather than a single explicit recommendation.

## Default setup sequence

1. Export `NEBIUS_API_KEY`.
2. Install OpenClaw if `openclaw` is missing with `npm install -g openclaw@latest`.
3. Run `python3 scripts/setup_openclaw_nebius.py --list-models` when model ids are unknown.
4. Run `python3 scripts/setup_openclaw_nebius.py --apply` to set the provider, model catalog, primary model, and allowlist.
5. Restart the gateway only when needed.
6. Verify with `openclaw models list`, `openclaw models status`, and `openclaw dashboard`.

If global npm install fails on permissions, use a local prefix install:

```bash
npm install -g --prefix ~/.openclaw openclaw@latest
~/.openclaw/bin/openclaw --version
```

## Workshop defaults

The workshop used these Token Factory models:

- `moonshotai/Kimi-K2.5`
- `meta-llama/Llama-3.3-70B-Instruct-fast`
- `deepseek-ai/DeepSeek-R1-0528`

Use them when they still exist. If live discovery returns different ids, prefer the current ids over stale workshop ids.

## Known failure modes

- `"model not allowed"` usually means the provider exists but the model is missing from `agents.defaults.models`.
- Missing models in `openclaw models list` usually means the provider config did not apply, the API key is absent, or the base URL is wrong.
- If onboarding already wrote a different custom provider, merge with it instead of replacing the whole custom-provider section blindly.

## Source links

- OpenClaw onboarding docs: `https://docs.openclaw.ai/cli/onboard`
- OpenClaw config docs: `https://docs.openclaw.ai/gateway/configuration`
- OpenClaw configuration reference: `https://docs.openclaw.ai/gateway/configuration-reference`
- OpenClaw models docs: `https://docs.openclaw.ai/cli/models`
- Nebius Token Factory docs: `https://docs.tokenfactory.nebius.com/`
