"""Ollama LLM and Embeddings Client with token tracking, latency logging, and error handling."""
import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
import httpx
from pydantic import BaseModel, Field

from backend.config import settings

logger = logging.getLogger("graphrag.llm")

class LLMCallLog(BaseModel):
    call_type: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    status: str = "success"
    error_message: Optional[str] = None

class EmbeddingError(RuntimeError):
    """Raised when text embedding generation fails, connects to an unavailable service, or yields invalid vectors."""
    pass

MODEL_EMBEDDING_DIMENSIONS: Dict[str, int] = {
    "nomic-embed-text": 768,
    "all-minilm": 384,
    "bge-m3": 1024,
    "mxbai-embed-large": 1024,
    "snowflake-arctic-embed": 1024,
    "text-embedding-3-small": 1536,
}

def get_expected_embedding_dim(model_name: str) -> Optional[int]:
    """Return expected vector dimension for well-known models if available."""
    clean_name = model_name.split(":")[0].strip().lower()
    return MODEL_EMBEDDING_DIMENSIONS.get(clean_name)

def validate_embedding(
    vec: Any,
    expected_dim: Optional[int] = None,
    allow_empty: bool = False
) -> None:
    """Validate that an embedding is a nonempty, finite list of numeric floats matching expected dimensions."""
    import math
    if not isinstance(vec, list):
        raise EmbeddingError(f"Embedding must be a list of floats, got {type(vec).__name__}")
    if not vec:
        if allow_empty:
            return
        raise EmbeddingError("Embedding vector is empty")
    if expected_dim is not None and len(vec) != expected_dim:
        raise EmbeddingError(f"Embedding dimension mismatch: expected {expected_dim}, got {len(vec)}")
    for i, val in enumerate(vec):
        if not isinstance(val, (int, float)) or not math.isfinite(val):
            raise EmbeddingError(f"Embedding contains non-finite or non-numeric value at index {i}: {val!r}")

class OllamaClient:
    """Client for interacting with local Ollama service for completions and embeddings."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.small_model = settings.OLLAMA_SMALL_MODEL
        self.large_model = settings.OLLAMA_LARGE_MODEL
        self.embed_model = settings.OLLAMA_EMBED_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        self.call_logs: List[LLMCallLog] = []
        self._mock_mode: bool = False
        self._mock_dim: int = get_expected_embedding_dim(self.embed_model) or 768

    def set_mock_mode(self, enabled: bool = True, dim: Optional[int] = None):
        """Configure intentional mock embedding mode for unit testing without live daemons."""
        self._mock_mode = enabled
        if dim is not None:
            self._mock_dim = dim
        logger.info(f"OllamaClient mock embedding mode set to: {enabled} (dim={self._mock_dim})")

    def check_health(self) -> Dict[str, Any]:
        """Check if Ollama is accessible and list available models."""
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    return {
                        "status": "connected",
                        "base_url": self.base_url,
                        "available_models": models,
                        "has_small_model": any(self.small_model in m for m in models),
                        "has_large_model": any(self.large_model in m for m in models),
                        "has_embed_model": any(self.embed_model in m for m in models),
                    }
                return {
                    "status": "error",
                    "base_url": self.base_url,
                    "error": f"HTTP {res.status_code}: {res.text}"
                }
        except Exception as e:
            return {
                "status": "unreachable",
                "base_url": self.base_url,
                "error": str(e),
                "suggestion": f"Ensure Ollama is running (`ollama serve`) and models ({self.small_model}, {self.large_model}, {self.embed_model}) are pulled."
            }

    async def _generate_with_groq(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.2,
        format_json: bool = False,
        seed: Optional[int] = None,
        timeout: float = 25.0,
    ) -> Tuple[Optional[str], Optional[LLMCallLog]]:
        """Tier 1: Ultra-fast cloud inference via Groq."""
        groq_key = settings.GROQ_API_KEY
        if not groq_key:
            return None, None

        models_to_try = [
            settings.GROQ_MODEL or "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
        ]
        start_time = time.time()
        last_error = ""

        async with httpx.AsyncClient(timeout=timeout) as client:
            for groq_model in models_to_try:
                try:
                    payload: Dict[str, Any] = {
                        "model": groq_model,
                        "messages": [
                            *([{"role": "system", "content": system}] if system else []),
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": temperature,
                    }
                    if format_json:
                        payload["response_format"] = {"type": "json_object"}
                    if seed is not None:
                        payload["seed"] = int(seed)

                    res = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {groq_key}",
                        },
                        json=payload,
                    )
                    elapsed_ms = (time.time() - start_time) * 1000.0

                    if res.status_code == 200:
                        data = res.json()
                        choices = data.get("choices", [])
                        text = choices[0].get("message", {}).get("content", "") if choices else ""
                        if text:
                            usage = data.get("usage", {})
                            p_tok = usage.get("prompt_tokens", len(prompt.split()) * 4 // 3)
                            c_tok = usage.get("completion_tokens", len(text.split()) * 4 // 3)
                            log = LLMCallLog(
                                call_type="groq",
                                model=groq_model,
                                prompt_tokens=p_tok,
                                completion_tokens=c_tok,
                                total_tokens=usage.get("total_tokens", p_tok + c_tok),
                                latency_ms=round(elapsed_ms, 2),
                                status="success",
                            )
                            logger.info(f"[LLM Engine] Tier 1 (Groq) succeeded with {groq_model} in {elapsed_ms:.1f}ms ({len(text)} chars).")
                            return text, log
                    last_error = f"HTTP {res.status_code}: {res.text[:120]}"
                    logger.warning(f"[LLM Engine] Groq model {groq_model} returned {last_error}")
                except Exception as err:
                    last_error = str(err)
                    logger.warning(f"[LLM Engine] Groq attempt with {groq_model} failed: {err}")

        raise RuntimeError(f"Groq failed across all candidate models: {last_error}")

    async def _generate_with_gemini(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.2,
        format_json: bool = False,
        seed: Optional[int] = None,
        timeout: float = 30.0,
    ) -> Tuple[Optional[str], Optional[LLMCallLog]]:
        """Tier 2: High-accuracy cloud reasoning via Google Gemini API."""
        gemini_key = settings.GEMINI_API_KEY
        if not gemini_key:
            return None, None

        gemini_model = settings.GEMINI_MODEL or "gemini-2.5-flash"
        start_time = time.time()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_key}"

        gemini_body: Dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": temperature,
            },
        }
        if system:
            gemini_body["systemInstruction"] = {
                "parts": [{"text": system}]
            }
        if format_json:
            gemini_body["generationConfig"]["responseMimeType"] = "application/json"
        if seed is not None:
            gemini_body["generationConfig"]["seed"] = int(seed)

        async with httpx.AsyncClient(timeout=timeout) as client:
            res = await client.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "aistudio-build",
                },
                json=gemini_body,
            )
            elapsed_ms = (time.time() - start_time) * 1000.0

            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    text = "".join(p.get("text", "") for p in parts if "text" in p)
                    if text:
                        usage = data.get("usageMetadata", {})
                        p_tok = usage.get("promptTokenCount", len(prompt.split()) * 4 // 3)
                        c_tok = usage.get("candidatesTokenCount", len(text.split()) * 4 // 3)
                        log = LLMCallLog(
                            call_type="gemini",
                            model=gemini_model,
                            prompt_tokens=p_tok,
                            completion_tokens=c_tok,
                            total_tokens=usage.get("totalTokenCount", p_tok + c_tok),
                            latency_ms=round(elapsed_ms, 2),
                            status="success",
                        )
                        logger.info(f"[LLM Engine] Tier 2 (Gemini) succeeded with {gemini_model} in {elapsed_ms:.1f}ms ({len(text)} chars).")
                        return text, log

            raise RuntimeError(f"Gemini API returned HTTP {res.status_code}: {res.text[:140]}")

    async def _generate_with_ollama(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.2,
        format_json: bool = False,
        seed: Optional[int] = None,
    ) -> Tuple[Optional[str], Optional[LLMCallLog]]:
        """Tier 3: Local privacy-first inference via Ollama."""
        target_model = model or self.large_model
        payload: Dict[str, Any] = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if seed is not None:
            payload["options"]["seed"] = int(seed)
        if system:
            payload["system"] = system
        if format_json:
            payload["format"] = "json"

        start_time = time.time()
        call_log = LLMCallLog(call_type="ollama", model=target_model)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            res = await client.post(f"{self.base_url}/api/generate", json=payload)
            elapsed_ms = (time.time() - start_time) * 1000.0
            call_log.latency_ms = round(elapsed_ms, 2)

            if res.status_code == 200:
                data = res.json()
                response_text = data.get("response", "")
                prompt_tokens = data.get("prompt_eval_count", len(prompt.split()) * 4 // 3)
                completion_tokens = data.get("eval_count", len(response_text.split()) * 4 // 3)
                call_log.prompt_tokens = prompt_tokens
                call_log.completion_tokens = completion_tokens
                call_log.total_tokens = prompt_tokens + completion_tokens
                call_log.status = "success"
                logger.info(f"[LLM Engine] Tier 3 (Ollama) succeeded with {target_model} in {elapsed_ms:.1f}ms.")
                return response_text, call_log
            else:
                call_log.status = "failed"
                call_log.error_message = f"HTTP {res.status_code}: {res.text}"
                return "", call_log

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.2,
        format_json: bool = False,
        seed: Optional[int] = None,
    ) -> Tuple[str, LLMCallLog]:
        """Generate response with strict three-tier priority: Groq -> Gemini -> Ollama.
        
        1. Checks Groq first (sub-second cloud latency).
        2. If Groq fails or is unavailable, falls back to Gemini.
        3. If Gemini fails or is unavailable, falls back to local Ollama.
        """
        start_time = time.time()
        errors: List[str] = []

        # ==================== TIER 1: GROQ ====================
        try:
            text, log = await self._generate_with_groq(
                prompt=prompt,
                system=system,
                temperature=temperature,
                format_json=format_json,
                seed=seed,
            )
            if text and log:
                self.call_logs.append(log)
                return text, log
        except Exception as e:
            err_msg = f"Groq failed: {e}"
            logger.warning(f"[LLM Priority] {err_msg}. Falling back to Gemini...")
            errors.append(err_msg)

        # ==================== TIER 2: GEMINI ====================
        try:
            text, log = await self._generate_with_gemini(
                prompt=prompt,
                system=system,
                temperature=temperature,
                format_json=format_json,
                seed=seed,
            )
            if text and log:
                self.call_logs.append(log)
                return text, log
        except Exception as e:
            err_msg = f"Gemini failed: {e}"
            logger.warning(f"[LLM Priority] {err_msg}. Falling back to Ollama...")
            errors.append(err_msg)

        # ==================== TIER 3: OLLAMA ====================
        try:
            text, log = await self._generate_with_ollama(
                prompt=prompt,
                model=model,
                system=system,
                temperature=temperature,
                format_json=format_json,
                seed=seed,
            )
            if text and log and log.status == "success":
                self.call_logs.append(log)
                return text, log
            elif log and log.error_message:
                errors.append(f"Ollama failed: {log.error_message}")
        except Exception as e:
            err_msg = f"Ollama failed: {e}"
            logger.error(f"[LLM Priority] {err_msg}. All three tiers exhausted.")
            errors.append(err_msg)

        # All tiers exhausted
        elapsed_ms = (time.time() - start_time) * 1000.0
        combined_error = " | ".join(errors) if errors else "No LLM provider available"
        logger.error(f"[LLM Fallback Exhausted] Groq -> Gemini -> Ollama failed: {combined_error}")
        failed_log = LLMCallLog(
            call_type="exhausted_fallback",
            model=model or self.large_model,
            latency_ms=round(elapsed_ms, 2),
            status="error",
            error_message=f"All tiers failed (Groq -> Gemini -> Ollama): {combined_error}",
        )
        self.call_logs.append(failed_log)
        return "", failed_log

    async def get_embedding(
        self,
        text: str,
        model: Optional[str] = None,
        expected_dim: Optional[int] = None,
        raise_on_error: bool = True
    ) -> Tuple[List[float], LLMCallLog]:
        """Generate text embedding vector with telemetry and strict validation.

        Args:
            text: Input text string to embed.
            model: Optional model override. Defaults to self.embed_model.
            expected_dim: Optional explicit expected vector length.
            raise_on_error: If True (default), raises EmbeddingError on HTTP, connection, or validation failures.
                            If False, returns ([], call_log) with call_log.status='failed' or 'error'.
        """
        import math
        import hashlib

        target_model = model or self.embed_model
        exp_dim = expected_dim if expected_dim is not None else get_expected_embedding_dim(target_model)
        start_time = time.time()
        call_log = LLMCallLog(call_type="embedding", model=target_model)

        # 1. Intentional Mock Mode (strictly for unit tests explicitly requesting mocks)
        if self._mock_mode:
            elapsed_ms = (time.time() - start_time) * 1000.0
            call_log.latency_ms = round(elapsed_ms, 2)
            call_log.prompt_tokens = len(text.split()) * 4 // 3
            call_log.total_tokens = call_log.prompt_tokens
            call_log.status = "mock"
            dim = exp_dim or self._mock_dim
            vec = [0.0] * dim
            for word in text.lower().split():
                h = int(hashlib.md5(word.encode()).hexdigest(), 16)
                idx = h % dim
                sign = 1.0 if (h >> 6) & 1 else -1.0
                vec[idx] += sign
            norm = math.sqrt(sum(x * x for x in vec)) or 1.0
            norm_vec = [round(x / norm, 6) for x in vec]
            validate_embedding(norm_vec, expected_dim=dim)
            self.call_logs.append(call_log)
            return norm_vec, call_log

        payload = {"model": target_model, "prompt": text}

        # 2. Live HTTP Generation
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(f"{self.base_url}/api/embeddings", json=payload)
                elapsed_ms = (time.time() - start_time) * 1000.0
                call_log.latency_ms = round(elapsed_ms, 2)

                if res.status_code == 200:
                    try:
                        data = res.json()
                    except Exception as json_err:
                        err_msg = f"Malformed JSON from Ollama embeddings endpoint: {json_err}"
                        call_log.status = "failed"
                        call_log.error_message = err_msg
                        self.call_logs.append(call_log)
                        if raise_on_error:
                            raise EmbeddingError(err_msg) from json_err
                        return [], call_log

                    if not isinstance(data, dict) or "embedding" not in data:
                        err_msg = "Malformed response from Ollama embeddings API: missing 'embedding' field"
                        call_log.status = "failed"
                        call_log.error_message = err_msg
                        self.call_logs.append(call_log)
                        if raise_on_error:
                            raise EmbeddingError(err_msg)
                        return [], call_log

                    embedding = data.get("embedding")
                    try:
                        validate_embedding(embedding, expected_dim=exp_dim)
                    except EmbeddingError as val_err:
                        call_log.status = "failed"
                        call_log.error_message = str(val_err)
                        self.call_logs.append(call_log)
                        if raise_on_error:
                            raise
                        return [], call_log

                    call_log.prompt_tokens = len(text.split()) * 4 // 3
                    call_log.total_tokens = call_log.prompt_tokens
                    call_log.status = "success"
                    self.call_logs.append(call_log)
                    return embedding, call_log
                else:
                    err_msg = f"HTTP {res.status_code}: {res.text}"
                    call_log.status = "failed"
                    call_log.error_message = err_msg
                    self.call_logs.append(call_log)
                    if raise_on_error:
                        raise EmbeddingError(f"Ollama embedding request failed with {err_msg}")
                    return [], call_log
        except EmbeddingError:
            raise
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000.0
            call_log.latency_ms = round(elapsed_ms, 2)
            call_log.status = "error"
            call_log.error_message = str(e)
            self.call_logs.append(call_log)
            # NEVER return silent pseudo-embeddings in experiments or production!
            if raise_on_error:
                raise EmbeddingError(f"Failed to generate embedding from Ollama service: {e}") from e
            return [], call_log

# Singleton instance
ollama_client = OllamaClient()
