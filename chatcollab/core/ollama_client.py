"""
Ollama HTTP Client for local LLM inference.
Provides model discovery, generation, structured JSON extraction with Pydantic,
retry fallback healing, and latency/token instrumentation.
"""
import urllib.request
import urllib.error
import json
import time
import re
from typing import List, Dict, Any, Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError
from .config import OLLAMA_BASE_URL, DEFAULT_MODEL, OLLAMA_REQUEST_TIMEOUT

T = TypeVar("T", bound=BaseModel)


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, default_model: str = DEFAULT_MODEL):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model

    def check_health(self) -> Dict[str, Any]:
        """Check if Ollama server is running and reachable."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("name") for m in data.get("models", [])]
                    return {
                        "status": "connected",
                        "url": self.base_url,
                        "models": models,
                        "default_model": self.default_model,
                        "has_default_model": any(self.default_model in m for m in models)
                    }
        except Exception as e:
            return {
                "status": "error",
                "url": self.base_url,
                "error": str(e),
                "models": []
            }
        return {"status": "error", "url": self.base_url, "models": []}

    def list_models(self) -> List[str]:
        """Return list of model names currently installed in Ollama."""
        res = self.check_health()
        return res.get("models", [])

    def generate(self, prompt: str, system: Optional[str] = None,
                 model: Optional[str] = None, temperature: float = 0.3) -> Dict[str, Any]:
        """Direct text generation via /api/generate."""
        selected_model = model or self.default_model
        payload = {
            "model": selected_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": 4096
            }
        }
        if system:
            payload["system"] = system

        t0 = time.time()
        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=OLLAMA_REQUEST_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                latency = time.time() - t0
                return {
                    "text": data.get("response", ""),
                    "latency": latency,
                    "prompt_eval_count": data.get("prompt_eval_count", 0),
                    "eval_count": data.get("eval_count", 0),
                    "model": selected_model,
                    "success": True
                }
        except Exception as e:
            latency = time.time() - t0
            return {
                "text": "",
                "latency": latency,
                "error": str(e),
                "model": selected_model,
                "success": False
            }

    def generate_structured(self, prompt: str, response_model: Type[T],
                            system: Optional[str] = None,
                            model: Optional[str] = None,
                            temperature: float = 0.2,
                            max_retries: int = 2) -> Optional[T]:
        """
        Generate response conforming to a Pydantic model with schema enforcement,
        markdown code-block extraction, and retry fallback healing.
        """
        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        system_instruction = (
            f"{system or ''}\n\n"
            "CRITICAL FORMAT REQUIREMENT: Respond ONLY with a valid JSON object matching this schema:\n"
            f"```json\n{schema_json}\n```\n"
            "Do NOT include markdown narrative before or after the JSON. Provide raw JSON only."
        )

        current_prompt = prompt
        for attempt in range(max_retries + 1):
            res = self.generate(
                prompt=current_prompt,
                system=system_instruction,
                model=model,
                temperature=temperature
            )
            if not res["success"] or not res["text"]:
                continue

            cleaned_json = self._extract_json_substring(res["text"])
            if cleaned_json:
                try:
                    parsed_dict = json.loads(cleaned_json)
                    return response_model.model_validate(parsed_dict)
                except (json.JSONDecodeError, ValidationError) as err:
                    # Retry with targeted healing prompt
                    current_prompt = (
                        f"Your previous output failed validation: {str(err)}.\n"
                        f"Previous output was:\n{res['text'][:300]}\n"
                        "Please fix the format and output ONLY valid JSON matching the schema."
                    )
        return None

    @staticmethod
    def _extract_json_substring(raw: str) -> Optional[str]:
        """Strip markdown fences and isolate first complete JSON object/array."""
        raw = raw.strip()
        # Look for ```json ... ``` or ``` ... ```
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
        if fence_match:
            candidate = fence_match.group(1).strip()
            if candidate.startswith("{") or candidate.startswith("["):
                return candidate

        # Look for first { to matching }
        start = raw.find("{")
        if start != -1:
            stack = 0
            for i in range(start, len(raw)):
                if raw[i] == "{":
                    stack += 1
                elif raw[i] == "}":
                    stack -= 1
                    if stack == 0:
                        return raw[start:i+1]

        return None
