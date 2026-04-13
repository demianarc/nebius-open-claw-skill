# Nebius Serverless Path

Use this path only when the user explicitly wants OpenClaw itself deployed on Nebius instead of keeping the agent local and sending inference traffic to Token Factory.

## What changes here

- Token Factory-only setup keeps the OpenClaw gateway local and uses Nebius only for model inference.
- Serverless setup deploys an OpenClaw container as a Nebius endpoint.
- This path needs more inputs: image name, platform, container port, public/private exposure, and endpoint environment variables.

## Workshop direction

The workshop flow used the Nebius CLI and an endpoint create command shaped like this:

```bash
curl -sSL https://storage.ai.nebius.cloud/ncp/install.sh | bash

nebius ai endpoint create \
  --name "$ENDPOINT_NAME" \
  --image "$IMAGE" \
  --platform "$PLATFORM" \
  --container-port "$CONTAINER_PORT" \
  --env "TOKEN_FACTORY_API_KEY=${TOKEN_FACTORY_API_KEY}" \
  --env "TOKEN_FACTORY_URL=${TOKEN_FACTORY_URL}" \
  --env "INFERENCE_MODEL=${INFERENCE_MODEL}" \
  --public
```

Treat that as a starting point, not a universal one-liner. The exact image, platform, and env var contract depend on the container being deployed.

## How to use this branch

1. Confirm the user wants hosted OpenClaw, not just hosted inference.
2. Confirm the target container image and runtime contract.
3. Install or authenticate the Nebius CLI before making infrastructure changes.
4. Prefer an infrastructure-specific workflow or repo once the user crosses into deployment automation.

## Related workshop references

The workshop also pointed to:

- `https://github.com/colygon/openclaw-deploy`
- `https://github.com/colygon/nebius-skill`

Treat those as workshop-side references. They are not official Nebius documentation.
