# Nebius OpenClaw Skill

Codex skill for getting OpenClaw running quickly with Nebius.

It is optimized for the simplest path first:

- keep OpenClaw local
- use Nebius Token Factory for model inference
- discover or select current models
- configure OpenClaw safely with env-backed API keys
- verify that the chosen Nebius model is actually usable

## What is in this repo

- `SKILL.md`: the skill instructions Codex uses
- `scripts/setup_openclaw_nebius.py`: helper for model discovery and OpenClaw config generation or application
- `references/tokenfactory.md`: notes for the Token Factory path
- `references/serverless.md`: notes for the Nebius Serverless path

## Intended workflow

1. Export `NEBIUS_API_KEY`
2. Install OpenClaw if needed: `npm install -g openclaw@latest`
3. List Nebius models: `python3 scripts/setup_openclaw_nebius.py --list-models`
4. Apply config: `python3 scripts/setup_openclaw_nebius.py --apply`
5. Verify: `openclaw models list`, `openclaw models status`, `openclaw dashboard`

## Install as a local Codex skill

Place this folder under:

```bash
${CODEX_HOME:-$HOME/.codex}/skills/openclaw-nebius
```

Then invoke it with:

```text
$openclaw-nebius
```

## Notes

- Token Factory is the default path because it is the fastest setup.
- Serverless is kept as a separate branch for users who want hosted OpenClaw, not just hosted inference.
- API keys should stay in environment variables, not committed config files.
- If global npm install hits permissions, use a local prefix install such as `npm install -g --prefix ~/.openclaw openclaw@latest`.
