# ai_client.py
"""
فصل استدعاءات واجهات نماذج الذكاء الاصطناعي في صف واحد.
لا يتعامل هذا الملف مع التخزين أو مفاتيح API — مرّر المفتاح كوسيط.
"""
import json, urllib.request, urllib.error, logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class AIClient:
    def __init__(self, endpoint: str, model: str, fmt: str, api_key: str, timeout: int = 90):
        self.endpoint = endpoint
        self.model = model
        self.fmt = fmt
        self.api_key = api_key
        self.timeout = timeout

    def _post(self, url: str, payload: bytes, headers: Dict):
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="ignore")[:1000]
            logger.warning("HTTPError %s %s", e.code, body)
            raise
        except Exception:
            logger.exception("AI request failed")
            raise

    def generate(self, system: str, messages: List[Dict]):
        if not self.api_key:
            raise ValueError("Missing API key")

        if self.fmt == "gemini":
            contents = []
            # messages is expected to be list of dicts with role/content
            for m in messages:
                role = "model" if m.get("role") == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": m.get("content", "")} ]})
            # the last message is the user prompt
            payload = json.dumps({"contents": contents}).encode()
            url = f"{self.endpoint}?key={self.api_key}"
            d = self._post(url, payload, {"Content-Type": "application/json"})
            return d["candidates"][0]["content"]["parts"][0]["text"]

        elif self.fmt == "anthropic":
            payload = json.dumps({
    "model": self.model,
    "messages": messages,
    "system": system,
    "max_tokens": 2048  
}).encode()
            headers = {"Content-Type": "application/json", "x-api-key": self.api_key, "anthropic-version": "2023-06-01"}
            d = self._post(self.endpoint, payload, headers)
            return d.get("content", [{}])[0].get("text", "")

        else:  # openai compatible
            payload = json.dumps({"model": self.model, "messages": messages, "max_tokens": 2048}).encode()
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
            d = self._post(self.endpoint, payload, headers)
            return d["choices"][0]["message"]["content"]
