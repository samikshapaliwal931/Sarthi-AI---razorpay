from __future__ import annotations

import json
import time
from typing import Any, Protocol

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger()

OPENROUTER_BASE = "https://openrouter.ai/api/v1"


class LLMProvider(Protocol):
    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict[str, Any] | None = None,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> dict[str, Any]: ...

    async def generate_text(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> dict[str, Any]: ...

    async def embed(
        self,
        texts: list[str],
        model: str | None = None,
    ) -> list[list[float]]: ...

    async def classify(
        self,
        text: str,
        labels: list[str],
        model: str | None = None,
    ) -> dict[str, float]: ...


def _extract_json(content: str | None) -> dict[str, Any]:
    if not content:
        return {"raw_response": ""}
    text = content.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract the first JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
        logger.warning("llm_invalid_json", content=text[:300])
        return {"raw_response": text}


class OpenRouterProvider:
    """OpenRouter provider using httpx with model fallback on rate limits.

    Primary model is `z-ai/glm-5.2:free` (supports reasoning). On a 429 or 5xx
    the provider transparently retries with the fallback models in sequence
    (`openrouter/free` auto-router, gemma, minimax) so the demo never stalls.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.openrouter_api_key
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=OPENROUTER_BASE,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
        return self._client

    def _model_chain(self, model: str | None) -> list[str]:
        chain: list[str] = []
        if model:
            chain.append(model)
        elif settings.default_llm_model:
            chain.append(settings.default_llm_model)
        for m in settings.openrouter_fallback_list:
            if m not in chain:
                chain.append(m)
        return chain

    async def _chat(
        self,
        messages: list[dict[str, Any]],
        model: str | None,
        temperature: float,
        max_tokens: int,
        json_mode: bool,
        reasoning: bool = True,
    ) -> dict[str, Any]:
        client = self._get_client()
        chain = self._model_chain(model)
        last_error: Exception | None = None

        for candidate in chain:
            payload: dict[str, Any] = {
                "model": candidate,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if json_mode:
                payload["response_format"] = {"type": "json_object"}
            if reasoning:
                payload["reasoning"] = {"enabled": True}

            try:
                resp = await client.post("/chat/completions", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    choice = data["choices"][0]
                    msg = choice.get("message", {})
                    logger.info(
                        "openrouter_chat_success",
                        model=candidate,
                        reasoning=(data.get("usage", {}) or {}).get("completion_tokens_details", {}).get("reasoning_tokens", 0),
                    )
                    return {
                        "content": msg.get("content"),
                        "reasoning_details": msg.get("reasoning_details"),
                        "model": candidate,
                        "raw": data,
                    }
                elif resp.status_code in (429, 500, 502, 503, 504):
                    logger.warning("openrouter_model_unavailable", model=candidate, status=resp.status_code)
                    last_error = Exception(f"Model {candidate} returned {resp.status_code}")
                    continue
                else:
                    text = resp.text[:300]
                    logger.error("openrouter_error", model=candidate, status=resp.status_code, body=text)
                    last_error = Exception(f"OpenRouter error {resp.status_code}: {text}")
                    continue
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                logger.warning("openrouter_http_error", model=candidate, error=str(e))
                last_error = e
                continue

        raise last_error or Exception("All OpenRouter models failed")

    async def generate_text(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> dict[str, Any]:
        result = await self._chat(messages, model, temperature, max_tokens, json_mode=False)
        return result

    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict[str, Any] | None = None,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> dict[str, Any]:
        result = await self._chat(
            [{"role": "user", "content": prompt}],
            model,
            temperature,
            max_tokens,
            json_mode=True,
        )
        return _extract_json(result.get("content"))

    async def embed(
        self,
        texts: list[str],
        model: str | None = None,
    ) -> list[list[float]]:
        # OpenRouter embeddings; deterministic hash-based fallback if unavailable.
        client = self._get_client()
        try:
            resp = await client.post(
                "/embeddings",
                json={
                    "model": "openai/text-embedding-3-small",
                    "input": texts,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                return [item["embedding"] for item in data["data"]]
        except Exception as e:
            logger.warning("embedding_failed", error=str(e))
        # Deterministic fallback embedding (128-dim hash-based) so pgvector paths never break.
        dims = 128
        embeddings = []
        for text in texts:
            vec = [0.0] * dims
            tokens = text.lower().split()
            for token in tokens:
                h = hash(token)
                idx = h % dims
                vec[idx] += 1.0
            norm = (sum(v * v for v in vec) ** 0.5) or 1.0
            embeddings.append([v / norm for v in vec])
        return embeddings

    async def classify(
        self,
        text: str,
        labels: list[str],
        model: str | None = None,
    ) -> dict[str, float]:
        prompt = (
            f"Classify the following text into exactly one of these categories: {', '.join(labels)}.\n"
            f'Return strict JSON with format: {{"label": "<one of the categories>", "confidence": 0.95}}\n\n'
            f"Text: {text}"
        )
        result = await self.generate_structured(prompt, model=model, temperature=0.1, max_tokens=200)
        label = result.get("label", labels[0])
        if label not in labels:
            label = labels[0]
        try:
            confidence = float(result.get("confidence", 0.5))
        except (TypeError, ValueError):
            confidence = 0.5
        return {label: confidence}


class OpenAIProvider:
    """Thin wrapper kept for backwards compatibility. Routes to OpenRouter."""
    def __init__(self, api_key: str | None = None) -> None:
        self._inner = OpenRouterProvider(api_key)

    async def generate_structured(self, prompt, response_schema=None, model=None, temperature=0.3, max_tokens=1000):
        return await self._inner.generate_structured(prompt, response_schema, model, temperature, max_tokens)

    async def generate_text(self, messages, model=None, temperature=0.3, max_tokens=1000):
        return await self._inner.generate_text(messages, model, temperature, max_tokens)

    async def embed(self, texts, model=None):
        return await self._inner.embed(texts, model)

    async def classify(self, text, labels, model=None):
        return await self._inner.classify(text, labels, model)


class AnthropicProvider(OpenRouterProvider):
    """Alias — Sarthi currently serves all providers through OpenRouter."""
    pass


class ModelRouter:
    def __init__(self) -> None:
        self._providers: dict[str, LLMProvider] = {}

    def get_provider(self, provider_name: str | None = None) -> LLMProvider:
        name = provider_name or settings.default_llm_provider
        if name not in self._providers:
            if name in ("openrouter", "openai", "anthropic"):
                self._providers[name] = OpenRouterProvider()
            else:
                raise ValueError(f"Unknown LLM provider: {name}")
        return self._providers[name]

    def get_small_model(self) -> str:
        return settings.default_llm_model

    def get_large_model(self) -> str:
        return settings.default_llm_model


model_router = ModelRouter()


async def record_agent_run(
    session: Any,
    merchant_id: Any,
    *,
    agent_type: str,
    agent_name: str,
    status: str = "completed",
    input_data: dict[str, Any] | None = None,
    output_data: dict[str, Any] | None = None,
    error: str | None = None,
    duration_ms: int | None = None,
    correlation_id: str | None = None,
    model_used: str | None = None,
) -> None:
    """Log a real agent run so the Agent Activity feed reflects what Sarthi actually did.

    Gets-or-creates the (merchant, agent_type) Agent row, then inserts one AgentRun.
    Best-effort: never raises — a logging failure shouldn't break the caller's real work.
    """
    from sqlalchemy import select

    from app.core import utcnow
    from app.models import Agent, AgentRun, AgentRunStatus

    try:
        stmt = select(Agent).where(Agent.merchant_id == merchant_id, Agent.agent_type == agent_type)
        result = await session.execute(stmt)
        agent = result.scalar_one_or_none()
        if agent is None:
            agent = Agent(merchant_id=merchant_id, name=agent_name, agent_type=agent_type)
            session.add(agent)
            await session.flush()

        now = utcnow()
        run = AgentRun(
            agent_id=agent.id,
            merchant_id=merchant_id,
            status=AgentRunStatus(status),
            input_data=input_data,
            output_data=output_data,
            error=error,
            model_used=model_used,
            duration_ms=duration_ms,
            correlation_id=correlation_id,
            started_at=now,
            completed_at=now,
        )
        session.add(run)
        await session.flush()
    except Exception as e:
        logger.warning("agent_run_logging_failed", agent_type=agent_type, error=str(e))
