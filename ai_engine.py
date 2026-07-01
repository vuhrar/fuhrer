# ai_engine.py
"""
طبقة الاتصال بالذكاء الاصطناعي.
مستقلة تماماً عن باقي الملفات — يمكن استبدال المزود هنا فقط دون لمس أي ملف آخر.
"""

import json
import logging
import urllib.request
import urllib.error
from typing import List, Dict

logger = logging.getLogger("ai_engine")

PRESETS = {
    "Gemini 2.0 Flash — مجاني":    {"url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent", "model": "gemini-2.0-flash",        "fmt": "gemini"},
    "Gemini 1.5 Pro — مجاني":      {"url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent",   "model": "gemini-1.5-pro",          "fmt": "gemini"},
    "Groq LLaMA 3.3 — سريع مجاني": {"url": "https://api.groq.com/openai/v1/chat/completions",                                         "model": "llama-3.3-70b-versatile", "fmt": "openai"},
    "Claude Sonnet":                {"url": "https://api.anthropic.com/v1/messages",                                                    "model": "claude-sonnet-4-6",       "fmt": "anthropic"},
    "OpenAI GPT-4o":                {"url": "https://api.openai.com/v1/chat/completions",                                               "model": "gpt-4o",                  "fmt": "openai"},
    "⚙️ مخصص":                      {"url": "", "model": "", "fmt": "openai"},
}


def _post_json(url: str, payload: dict, headers: dict, timeout: int = 90) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req  = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")[:800]
        raise RuntimeError(f"HTTP {e.code}: {body}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"URLError: {e.reason}")


def call_ai(prompt: str, history: List[Dict], system: str,
            preset_name: str, api_key: str,
            custom_url: str = "", custom_model: str = "", custom_fmt: str = "openai") -> str:
    """
    نقطة الدخول الوحيدة لاستدعاء الذكاء الاصطناعي.
    لا تعتمد على أي session_state — كل شي يُمرَّر صراحة كمعاملات،
    عشان يسهل اختبارها واستبدال المزود لاحقاً دون أثر جانبي.
    """
    preset = PRESETS.get(preset_name, PRESETS["⚙️ مخصص"])
    url   = custom_url   if preset_name == "⚙️ مخصص" else preset["url"]
    model = custom_model if preset_name == "⚙️ مخصص" else preset["model"]
    fmt   = custom_fmt   if preset_name == "⚙️ مخصص" else preset["fmt"]

    if not api_key:
        return "❌ لم يُدخل مفتاح API. أدخله من زر «الاتصال بالخادم» بالشريط الجانبي."
    if not url:
        return "❌ لم يُحدد رابط API. راجع إعدادات الاتصال."

    clean_history = [{"role": m["role"], "content": m["content"]} for m in history]

    try:
        if fmt == "gemini":
            contents = []
            if system:
                contents.append({"role": "user",  "parts": [{"text": system}]})
                contents.append({"role": "model", "parts": [{"text": "حسناً، أنا جاهز للمساعدة."}]})
            for m in clean_history:
                role = "model" if m["role"] == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": m["content"]}]})
            contents.append({"role": "user", "parts": [{"text": prompt}]})
            payload = {"contents": contents, "generationConfig": {"maxOutputTokens": 4096, "temperature": 0.7}}
            resp = _post_json(f"{url}?key={api_key}", payload, {"Content-Type": "application/json"})
            return resp["candidates"][0]["content"]["parts"][0]["text"]

        elif fmt == "anthropic":
            messages = clean_history + [{"role": "user", "content": prompt}]
            payload  = {"model": model, "max_tokens": 4096, "system": system, "messages": messages}
            headers  = {"Content-Type": "application/json", "x-api-key": api_key, "anthropic-version": "2023-06-01"}
            resp = _post_json(url, payload, headers)
            return resp["content"][0]["text"]

        else:  # openai-compatible
            messages = [{"role": "system", "content": system}] + clean_history + [{"role": "user", "content": prompt}]
            payload  = {"model": model, "messages": messages, "max_tokens": 4096, "temperature": 0.7}
            headers  = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
            resp = _post_json(url, payload, headers)
            return resp["choices"][0]["message"]["content"]

    except RuntimeError as e:
        err = str(e)
        if "429" in err:
            return "⏳ الطلبات كثيرة جداً (Rate Limit). انتظر دقيقة ثم أعد المحاولة."
        if "401" in err or "403" in err:
            return "🔑 مفتاح API غير صحيح أو منتهي الصلاحية."
        if "404" in err:
            return f"🔗 رابط API غير صحيح أو النموذج غير موجود:\n`{url}`"
        return f"❌ خطأ في الاتصال:\n{err[:400]}"
    except KeyError as e:
        return f"❌ استجابة غير متوقعة من الخادم (مفتاح مفقود: {e})."
    except Exception as e:
        return f"❌ خطأ غير متوقع: {str(e)[:300]}"
