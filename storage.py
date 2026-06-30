# storage.py
"""
إدارة الجلسات والإعدادات على نظام الملفات المحلي.
ملاحظة هامة لبيئة Streamlit Cloud: نظام الملفات هناك غير دائم بين عمليات
إعادة التشغيل (لا يُضمن بقاء الملفات بعد سكون التطبيق وإعادة تنشيطه).
لذلك تُحفظ الجلسات هنا للاستخدام أثناء الجلسة الحالية، وللاستمرارية الكاملة
يُنصح المستخدم لاحقاً بإضافة تخزين خارجي (مثل قاعدة بيانات) إن احتاج ضمان البقاء الدائم.
"""

import json
import os
from datetime import datetime
from typing import Dict, List

DATA_DIR     = "fuehrer_data"
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

for d in (DATA_DIR, SESSIONS_DIR):
    os.makedirs(d, exist_ok=True)


def _load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def _save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_settings() -> Dict:
    return _load_json(SETTINGS_FILE, {})


def save_settings(settings: Dict):
    # لا نحفظ مفتاح API على القرص لأسباب أمنية —
    # يبقى فقط داخل session_state أثناء الجلسة الحالية.
    safe = {k: v for k, v in settings.items() if k != "api_key"}
    _save_json(SETTINGS_FILE, safe)


def list_sessions() -> List[Dict]:
    out = []
    try:
        for f in sorted(os.listdir(SESSIONS_DIR), reverse=True)[:12]:
            if f.endswith(".json"):
                d = _load_json(os.path.join(SESSIONS_DIR, f), {})
                out.append({
                    "id": f[:-5],
                    "name": d.get("name", "جلسة"),
                    "count": len(d.get("messages", [])),
                    "persona": d.get("persona", "lawyer"),
                })
    except Exception:
        pass
    return out


def load_session(sid: str) -> Dict:
    return _load_json(os.path.join(SESSIONS_DIR, f"{sid}.json"),
                       {"name": "جلسة جديدة", "messages": [], "persona": "lawyer"})


def save_session(sid: str, data: Dict):
    data["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    _save_json(os.path.join(SESSIONS_DIR, f"{sid}.json"), data)


def delete_session(sid: str):
    path = os.path.join(SESSIONS_DIR, f"{sid}.json")
    if os.path.exists(path):
        os.remove(path)


def new_session_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
