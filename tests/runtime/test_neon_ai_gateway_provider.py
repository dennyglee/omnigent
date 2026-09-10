"""Offline regression test for the documented Neon AI Gateway provider."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from omnigent.runtime.workflow import _build_codex_spawn_env, _resolve_provider_for_build
from omnigent.spec.types import AgentSpec, ExecutorSpec, ProviderAuth


def test_neon_ai_gateway_provider_resolves_offline(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The documented Neon provider resolves its env token and Chat wire API."""
    fake_token = "nt_live_fake_offline_test_token"
    monkeypatch.setenv("OMNIGENT_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("NEON_AI_GATEWAY_TOKEN", fake_token)
    config = {
        "providers": {
            "neon": {
                "kind": "gateway",
                "default": ["openai"],
                "openai": {
                    "base_url": "https://br-example-api.ai.c-2.us-east-2.aws.neon.tech/v1",
                    "api_key_ref": "env:NEON_AI_GATEWAY_TOKEN",
                    "wire_api": "chat",
                    "models": {"default": "gpt-5-mini"},
                },
            }
        }
    }
    (tmp_path / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
    spec = AgentSpec(
        spec_version=1,
        name="neon-offline-test",
        instructions="Use the configured Neon AI Gateway.",
        executor=ExecutorSpec(
            type="omnigent",
            config={"harness": "codex"},
            auth=ProviderAuth(name="neon"),
        ),
    )

    provider = _resolve_provider_for_build(spec, harness_type="codex")

    assert provider is not None
    assert provider.kind == "gateway"
    openai = provider.family("openai")
    assert openai is not None
    assert openai.base_url.endswith("/v1")
    assert openai.api_key == fake_token
    assert openai.wire_api == "chat"

    env = _build_codex_spawn_env(spec, workdir=None)

    assert env["HARNESS_CODEX_GATEWAY_BASE_URL"].endswith("/v1")
    assert env["HARNESS_CODEX_GATEWAY_AUTH_COMMAND"] == f"printf %s {fake_token}"
    assert env["HARNESS_CODEX_WIRE_API"] == "chat"
