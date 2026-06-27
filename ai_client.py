# ai_client.py
"""
فصل استدعاءات واجهات نماذج الذكاء الاصطناعي مع تخصيص الشخصية العمالية.
"""
import json, urllib.request, urllib.error, logging
from typing import List, Dict
import config

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

        # تأكد من تضمين الشخصية العمالية في الـ system
        full_system = config.SYSTEM_PROMPT_TEMPLATE
        if system:
            full_system += f"\n\nسياق إضافي: {system}"

        if self.fmt == "gemini":
            contents = []
            for m in messages:
                role = m.get("role", "user")
                contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})
            payload = json.dumps({"contents": contents}).encode()
            url = f"{self.endpoint}?key={self.api_key}"
            d = self._post(url, payload, {"Content-Type": "application/json"})
            return d["candidates"][0]["content"]["parts"][0]["text"]

        elif self.fmt == "anthropic":
            payload = json.dumps({"model": self.model, "messages": messages, "system": full_system}).encode()
            headers = {"Content-Type": "application/json", "x-api-key": self.api_key, "anthropic-version": "2023-06-01"}
            d = self._post(self.endpoint, payload, headers)
            return d.get("content", [{}])[0].get("text", "")

        else:  # openai compatible
            full_messages = [{"role": "system", "content": full_system}] + messages
            payload = json.dumps({"model": self.model, "messages": full_messages, "max_tokens": 4096}).encode()
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
            d = self._post(self.endpoint, payload, headers)
            return d["choices"][0]["message"]["content"]

    def generate_stream(self, system: str, messages: List[Dict]):
        """دعم التدفق (لتجنب تجميد الواجهة)"""
        import requests
        full_system = config.SYSTEM_PROMPT_TEMPLATE
        if system:
            full_system += f"\n\nسياق إضافي: {system}"

        if self.fmt == "openai":
            full_messages = [{"role": "system", "content": full_system}] + messages
            payload = {"model": self.model, "messages": full_messages, "stream": True, "max_tokens": 4096}
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            try:
                with requests.post(self.endpoint, json=payload, headers=headers, stream=True, timeout=self.timeout) as r:
                    for line in r.iter_lines():
                        if line:
                            decoded = line.decode('utf-8').replace('data: ', '')
                            if decoded and decoded != '[DONE]':
                                try:
                                    chunk = json.loads(decoded)
                                    if chunk.get('choices'):
                                        delta = chunk['choices'][0].get('delta', {})
                                        if 'content' in delta:
                                            yield delta['content']
                                except:
                                    pass
            except Exception as e:
                yield f"❌ خطأ: {str(e)[:200]}"
        else:
            # للأنواع الأخرى، نستخدم طريقة التوليد العادية
            try:
                result = self.generate(system, messages)
                yield result
            except Exception as e:
                yield f"❌ خطأ: {str(e)[:200]}"
