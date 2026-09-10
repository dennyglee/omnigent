# Neon AI Gateway

Neon AI Gateway is an OpenAI-compatible proxy scoped to a Neon branch. Its
models are hosted by Databricks. Use a named Omnigent gateway provider to keep
the branch endpoint and credential out of agent files.

## Get the endpoint and credential

You need two credentials with different purposes:

1. A Neon management API key, set as `NEON_API_KEY`. Create it in the Neon
   Console under Account settings, API keys. It discovers the branch endpoint
   and issues the inference credential. Do not configure it as the model API
   key.
2. A branch-scoped inference credential, set as
   `NEON_AI_GATEWAY_TOKEN`. It must include the `ai_gateway:invoke` scope. The
   returned `api_token` starts with `nt_live_` and is the bearer token Omnigent
   sends to the gateway.

Set the management key and the project and branch IDs:

```bash
export NEON_API_KEY="your-neon-management-api-key"
export NEON_PROJECT_ID="your-project-id"
export NEON_BRANCH_ID="your-branch-id"
```

Discover the AI Gateway host for the branch:

```bash
export NEON_AI_GATEWAY_HOST="$(
  curl --fail --silent --show-error \
    --header "Authorization: Bearer ${NEON_API_KEY}" \
    "https://console.neon.tech/api/v2/projects/${NEON_PROJECT_ID}/branches/${NEON_BRANCH_ID}/ai_gateway" \
  | jq -r '.base_url'
)"
```

Issue the branch-scoped inference credential:

```bash
export NEON_AI_GATEWAY_TOKEN="$(
  curl --fail --silent --show-error \
    --request POST \
    --header "Authorization: Bearer ${NEON_API_KEY}" \
    --header "Content-Type: application/json" \
    --data '{"name":"omnigent-ai-gateway","scopes":["ai_gateway:invoke"],"principal_type":"user"}' \
    "https://console.neon.tech/api/v2/projects/${NEON_PROJECT_ID}/branches/${NEON_BRANCH_ID}/credentials" \
  | jq -r '.api_token'
)"
```

Neon returns the inference credential only once when it is issued. Store it
securely and export `NEON_AI_GATEWAY_TOKEN` in the environment that starts
Omnigent. The management key is not needed for inference after the endpoint
and inference credential have been obtained.

## Configure Omnigent

Add the provider to `~/.omnigent/config.yaml`. Replace the example host with
the value of `NEON_AI_GATEWAY_HOST` that you discovered above.

```yaml
providers:
  neon:
    kind: gateway
    default: [openai]
    openai:
      base_url: https://br-example-api.ai.c-2.us-east-2.aws.neon.tech/v1
      api_key_ref: env:NEON_AI_GATEWAY_TOKEN
      wire_api: chat
      models:
        default: gpt-5-mini
```

The `/v1` base URL is the Chat Completions API. Neon serves its Responses API
at a different path, `/openai/v1`, so `wire_api: chat` is required for this
configuration. Available model IDs are listed at
[`https://neon.com/models.json`](https://neon.com/models.json). Examples
include `gpt-5-mini` and `claude-opus-4-8`.

Reference the provider by name in an agent file:

```yaml
name: neon_agent
prompt: |
  You are a concise assistant.
executor:
  harness: codex
  model: gpt-5-mini
  auth:
    type: provider
    name: neon
```

Use the model ID as published. Do not add a `neon/` prefix. Provider routing is
selected by `auth.name`, not by a model-name prefix.

## Inline alternative

For a self-contained agent file, put the API key reference and base URL in
`executor.auth`. The OpenAI Agents harness also needs `use_responses: false`
to select Chat Completions.

```yaml
name: neon_inline_agent
prompt: |
  You are a concise assistant.
executor:
  harness: openai-agents
  model: gpt-5-mini
  use_responses: false
  auth:
    type: api_key
    api_key: ${NEON_AI_GATEWAY_TOKEN}
    base_url: https://br-example-api.ai.c-2.us-east-2.aws.neon.tech/v1
```

Prefer the named provider when several agents share the same Neon branch.

The Cursor and Kimi harnesses cannot be routed through this provider. They use
their own CLI authentication and provider configuration. Choose `codex`,
`openai-agents`, or another harness that supports Omnigent gateway providers.
