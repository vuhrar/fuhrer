# storage.py
"""
وظائف التخزين مع إضافة فهرسة المواد القانونية.
"""
import os, json, hashlib
from typing import Any
from datetime import datetime

DATA_DIR     = "fuehrer_data"
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")
MEMORY_FILE  = os.path.join(DATA_DIR, "memory.json")
SETTINGS_FILE= os.path.join(DATA_DIR, "settings.json")
LAW_FILE     = os.path.join(DATA_DIR, "law_db.json")
BG_FILE      = os.path.join(DATA_DIR, "bg.b64")

for d in [DATA_DIR, SESSIONS_DIR]:
    os.makedirs(d, exist_ok=True)

def load_json(path: str, default: Any):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default

def save_json(path: str, data: Any):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"save_json error: {e}")

# ==========================
# دوال الفهرسة الجديدة
# ==========================

_LAW_DB_CACHE = None
_LAW_INDEX_CACHE = {}

def build_law_index(law_db: list) -> dict:
    """بناء فهرس سريع للبحث في المواد القانونية"""
    index = {}
    for idx, item in enumerate(law_db):
        text = item.get("text", "").lower()
        law_name = item.get("law_name", "").lower()
        article = item.get("article", "").lower()
        keywords = set()
        # إضافة اسم النظام ورقم المادة
        if law_name:
            keywords.add(law_name)
        if article:
            keywords.add(article)
        # إضافة كلمات من النص (أول 200 حرف)
        for word in text[:200].split():
            if len(word) > 3:
                keywords.add(word)
        index[idx] = keywords
    return index

def get_law_db_cached():
    """تحميل قاعدة القانون مع التخزين المؤقت"""
    global _LAW_DB_CACHE, _LAW_INDEX_CACHE
    if _LAW_DB_CACHE is None:
        _LAW_DB_CACHE = load_json(LAW_FILE, [])
        _LAW_INDEX_CACHE = build_law_index(_LAW_DB_CACHE)
    return _LAW_DB_CACHE, _LAW_INDEX_CACHE

# باقي دوال التخزين (list_sessions, load_session, save_session, delete_session, save_settings, load_settings)
# تبقى كما هي دون تعديل.
