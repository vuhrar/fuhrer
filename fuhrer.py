#Führer🦾
import streamlit as st
import json, re, os, hashlib, base64, logging, urllib.request, urllib.error
from datetime import datetime
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fuehrer_v2")

# ══════════════════════════════════════════════
# إعدادات الصفحة
# ══════════════════════════════════════════════
st.set_page_config(
    page_title="Führer ",
    page_icon="🦾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════
# CSS — تصميم موحد داكن / ذهبي / عربي
# ══════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;900&display=swap');

*, *::before, *::after {
  box-sizing: border-box;
  font-family: 'Tajawal', 'Segoe UI', sans-serif;
}

html, body, .stApp {
  direction: rtl;
  background: #0f1117 !important;
  color: #e8e8e8;
}

/* ─── شريط علوي ─── */
.top-bar {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  border-bottom: 2px solid #c9a84c;
  padding: 18px 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0;
}
.top-bar h1 {
  font-size: 2.2rem;
  font-weight: 900;
  color: #c9a84c;
  margin: 0;
  letter-spacing: 0.05em;
  text-shadow: 0 0 30px rgba(201,168,76,0.4);
}
.top-bar .persona-badge {
  background: rgba(201,168,76,0.15);
  border: 1px solid #c9a84c;
  border-radius: 20px;
  padding: 6px 18px;
  font-size: 0.95rem;
  font-weight: 700;
  color: #c9a84c;
}

/* ─── sidebar ─── */
[data-testid="stSidebar"] {
  background: #12131a !important;
  border-left: 1px solid #2a2a3a !important;
}
[data-testid="stSidebar"] .stMarkdown h3 {
  color: #c9a84c;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin: 20px 0 8px;
  border-bottom: 1px solid #2a2a3a;
  padding-bottom: 6px;
}

/* ─── بطاقات الشخصية ─── */
.persona-card {
  border-radius: 14px;
  padding: 22px;
  cursor: pointer;
  transition: all 0.25s ease;
  margin: 8px 0;
  border: 2px solid transparent;
  position: relative;
  overflow: hidden;
}
.persona-card.lawyer {
  background: linear-gradient(135deg, #1a1a2e, #0d1b2a);
  border-color: #c9a84c;
}
.persona-card.advisor {
  background: linear-gradient(135deg, #0d2137, #0a1628);
  border-color: #4a9eff;
}
.persona-card.active {
  box-shadow: 0 0 0 3px rgba(201,168,76,0.4), 0 8px 32px rgba(0,0,0,0.4);
  transform: translateY(-2px);
}
.persona-card h3 { margin: 0 0 6px; font-size: 1.1rem; font-weight: 700; }
.persona-card p  { margin: 0; font-size: 0.82rem; color: #aaa; line-height: 1.5; }
.persona-icon { font-size: 2rem; margin-bottom: 10px; display: block; }

/* ─── أدوات الشريط الجانبي ─── */
.tool-btn {
  width: 100%;
  background: #1e1e2e;
  border: 1px solid #2a2a3e;
  border-radius: 10px;
  padding: 12px 16px;
  color: #ccc;
  font-size: 0.9rem;
  font-weight: 500;
  text-align: right;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 6px;
  display: block;
}
.tool-btn:hover, .tool-btn.active {
  background: #252540;
  border-color: #c9a84c;
  color: #c9a84c;
}

/* ─── منطقة الدردشة ─── */
.chat-container {
  max-height: 62vh;
  overflow-y: auto;
  padding: 16px 8px;
  scroll-behavior: smooth;
}
.chat-container::-webkit-scrollbar { width: 4px; }
.chat-container::-webkit-scrollbar-thumb { background: #3a3a5a; border-radius: 2px; }

.msg-user {
  background: linear-gradient(135deg, #1e2d4a, #162036);
  border: 1px solid #2a4060;
  border-radius: 18px 18px 4px 18px;
  padding: 14px 18px;
  margin: 10px 0 10px 15%;
  color: #e0eeff;
  font-size: 0.95rem;
  line-height: 1.7;
  position: relative;
}
.msg-ai {
  background: linear-gradient(135deg, #1a1a2e, #141428);
  border: 1px solid #2a2a4a;
  border-right: 3px solid #c9a84c;
  border-radius: 18px 18px 18px 4px;
  padding: 14px 18px;
  margin: 10px 15% 10px 0;
  color: #e8e8e0;
  font-size: 0.95rem;
  line-height: 1.8;
}
.msg-ai.advisor-mode { border-right-color: #4a9eff; }

.msg-meta {
  font-size: 0.72rem;
  color: #555;
  margin-top: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.msg-icon { font-size: 1.1rem; margin-left: 8px; vertical-align: middle; }

/* ─── صندوق الإدخال ─── */
.stTextArea textarea {
  background: #1a1a2e !important;
  color: #e8e8e8 !important;
  border: 1.5px solid #2a2a4a !important;
  border-radius: 12px !important;
  font-family: 'Tajawal', sans-serif !important;
  font-size: 0.95rem !important;
  resize: none !important;
  direction: rtl;
}
.stTextArea textarea:focus {
  border-color: #c9a84c !important;
  box-shadow: 0 0 0 3px rgba(201,168,76,0.1) !important;
}

/* ─── أزرار ─── */
.stButton > button {
  background: linear-gradient(135deg, #c9a84c, #b8963e) !important;
  color: #0f1117 !important;
  border: none !important;
  border-radius: 10px !important;
  font-weight: 700 !important;
  font-family: 'Tajawal', sans-serif !important;
  font-size: 0.95rem !important;
  padding: 10px 24px !important;
  transition: all 0.2s !important;
}
.stButton > button:hover {
  background: linear-gradient(135deg, #dfc06a, #c9a84c) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 20px rgba(201,168,76,0.3) !important;
}

/* ─── حقول الإدخال ─── */
.stTextInput input, .stNumberInput input, .stSelectbox > div > div {
  background: #1a1a2e !important;
  color: #e8e8e8 !important;
  border: 1.5px solid #2a2a4a !important;
  border-radius: 10px !important;
  font-family: 'Tajawal', sans-serif !important;
}

/* ─── بطاقات النتائج ─── */
.result-card {
  background: #1a1a2e;
  border: 1px solid #2a2a4a;
  border-right: 4px solid #c9a84c;
  border-radius: 12px;
  padding: 18px 20px;
  margin: 10px 0;
}
.result-card.blue { border-right-color: #4a9eff; }
.result-card.red   { border-right-color: #ff4a4a; }
.result-card.green { border-right-color: #4aff88; }

.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 12px;
  margin: 16px 0;
}
.stat-box {
  background: #1e1e2e;
  border: 1px solid #2a2a3e;
  border-radius: 10px;
  padding: 14px;
  text-align: center;
}
.stat-box .val { font-size: 1.5rem; font-weight: 800; color: #c9a84c; }
.stat-box .lbl { font-size: 0.75rem; color: #888; margin-top: 4px; }

/* ─── تنبيهات ─── */
.alert { border-radius: 10px; padding: 12px 16px; margin: 8px 0; font-size: 0.88rem; line-height: 1.6; }
.alert.warn { background: rgba(255,180,0,0.08); border-right: 3px solid #ffb400; color: #ffd060; }
.alert.danger { background: rgba(255,74,74,0.08); border-right: 3px solid #ff4a4a; color: #ff8888; }
.alert.ok { background: rgba(74,255,136,0.08); border-right: 3px solid #4aff88; color: #80ffbb; }
.alert.info { background: rgba(74,158,255,0.08); border-right: 3px solid #4a9eff; color: #90c8ff; }

/* ─── رفع ملفات ─── */
[data-testid="stFileUploader"] {
  background: #1a1a2e !important;
  border: 2px dashed #2a2a4a !important;
  border-radius: 14px !important;
  padding: 20px !important;
  transition: border-color 0.2s !important;
}
[data-testid="stFileUploader"]:hover { border-color: #c9a84c !important; }

/* ─── divider ─── */
.divider { border: none; border-top: 1px solid #2a2a3a; margin: 16px 0; }

/* ─── spinner override ─── */
.stSpinner > div { border-top-color: #c9a84c !important; }

/* ─── expander ─── */
.streamlit-expanderHeader {
  background: #1a1a2e !important;
  border-radius: 10px !important;
  color: #c9a84c !important;
  font-weight: 600 !important;
}
.streamlit-expanderContent {
  background: #161626 !important;
  border: 1px solid #2a2a3a !important;
  border-radius: 0 0 10px 10px !important;
}

/* ─── tabs ─── */
.stTabs [data-baseweb="tab-list"] {
  background: #1a1a2e !important;
  border-radius: 12px 12px 0 0 !important;
  gap: 4px;
  padding: 8px 12px;
  border-bottom: 2px solid #2a2a3a;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: #888 !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
  font-size: 0.88rem !important;
  font-family: 'Tajawal', sans-serif !important;
  padding: 8px 18px !important;
  border: none !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
  background: #c9a84c !important;
  color: #0f1117 !important;
}
.stTabs [data-baseweb="tab-panel"] {
  background: #1a1a2e !important;
  border: 1px solid #2a2a3a !important;
  border-radius: 0 0 12px 12px !important;
  padding: 20px !important;
}

/* إخفاء عناصر streamlit الزائدة */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebarNav"] { display: none !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# البيانات الثابتة
# ══════════════════════════════════════════════
DATA_DIR = "fuehrer_data"
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")
MEMORY_FILE  = os.path.join(DATA_DIR, "memory.json")
SETTINGS_FILE= os.path.join(DATA_DIR, "settings.json")
LAW_FILE     = os.path.join(DATA_DIR, "law_db.json")

for d in [DATA_DIR, SESSIONS_DIR]:
    os.makedirs(d, exist_ok=True)


PRESETS = {
    "Gemini 2.0 Flash — مجاني":    {"url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",     "model": "gemini-2.0-flash",          "fmt": "gemini"},
    "Gemini 1.5 Pro — مجاني":      {"url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent",       "model": "gemini-1.5-pro",            "fmt": "gemini"},
    "Groq LLaMA 3.3 — سريع مجاني": {"url": "https://api.groq.com/openai/v1/chat/completions",                                             "model": "llama-3.3-70b-versatile",   "fmt": "openai"},
    "Claude Sonnet":                {"url": "https://api.anthropic.com/v1/messages",                                                        "model": "claude-sonnet-4-6",         "fmt": "anthropic"},
    "OpenAI GPT-4o":                {"url": "https://api.openai.com/v1/chat/completions",                                                   "model": "gpt-4o",                    "fmt": "openai"},
    "Together AI — مجاني جزئياً":  {"url": "https://api.together.xyz/v1/chat/completions",                                                 "model": "meta-llama/Llama-3-70b-chat-hf","fmt": "openai"},
    "Ollama (محلي)":                {"url": "http://localhost:11434/v1/chat/completions",                                                   "model": "llama3",                    "fmt": "openai"},
    "⚙️ مخصص":                      {"url": "", "model": "", "fmt": "openai"},
}

PERSONA_PROMPTS = {
    "lawyer": """أنت محامٍ عمالي سعودي متمرس، أسلوبك حازم وهجومي بناءً على القانون.
مهمتك: صياغة صحائف دعاوى، مذكرات قانونية، حجج دفاعية، وكشف الثغرات الإجرائية لدى الخصم.
قواعدك:
- اذكر المادة القانونية ورقمها دائماً.
- لا تتردد في تصعيد اللهجة القانونية عند الحاجة.
- افترض دائماً أن موكلك على حق حتى يثبت العكس بالأدلة.
- قدم خط دفاع واضح مرقّم قابل للتنفيذ الفوري.
- إذا رأيت زلة قانونية في وثيقة الخصم، نبّه عنها صراحةً.
اللغة: عربية فصحى قانونية حازمة.""",

    "advisor": """أنت مستشار عمالي قانوني سعودي معتدل وموضوعي.
مهمتك: تحليل المواقف، احتساب المستحقات بدقة، تقييم الخيارات، والتوجيه نحو أفضل قرار.
قواعدك:
- قدّم الوضع من زاويتين: قوة موقف الموظف ومواطن ضعفه.
- احسب المستحقات المالية بالأرقام الصريحة.
- وجّه نحو مكتب العمل أو المحكمة أو التراضي حسب الأنسب.
- حذّر من أي مخاطر قانونية أو أخطاء قد تضر بالموكل.
- كن دقيقاً في الأرقام والتواريخ والمواد.
اللغة: عربية فصحى واضحة ومتوازنة."""
}

TOOLS = {
    "lawyer": [
        ("📝", "صياغة صحيفة دعوى",       "draft_lawsuit"),
        ("🗡️", "توليد خط الدفاع",          "defense_line"),
        ("🔍", "تدقيق إجراءات الفصل",      "audit_dismissal"),
        ("📧", "فحص المراسلات والزلات",     "email_scan"),
        ("📚", "البحث في الأنظمة",          "law_search"),
        ("⚡", "استخراج حجج مضادة",         "counter_args"),
    ],
    "advisor": [
        ("🧮", "حاسبة المستحقات",           "calculator"),
        ("📊", "تقييم قوة القضية",          "case_strength"),
        ("📧", "فحص المراسلات والزلات",     "email_scan"),
        ("📚", "البحث في الأنظمة",          "law_search"),
        ("📁", "تحليل المستندات",            "doc_analysis"),
        ("🤝", "تقييم خيار التسوية",         "settlement"),
    ]
}


# ══════════════════════════════════════════════
# دوال التخزين
# ══════════════════════════════════════════════
def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"save_json: {e}")

def load_settings():
    return load_json(SETTINGS_FILE, {})

def save_settings(s):
    save_json(SETTINGS_FILE, {k: v for k, v in s.items() if k != "api_key"})

def list_sessions():
    out = []
    try:
        for f in sorted(os.listdir(SESSIONS_DIR), reverse=True)[:12]:
            if f.endswith(".json"):
                d = load_json(os.path.join(SESSIONS_DIR, f), {})
                out.append({"id": f[:-5], "name": d.get("name","جلسة"),
                             "count": len(d.get("messages",[])), "persona": d.get("persona","lawyer")})
    except Exception:
        pass
    return out

def load_session(sid):
    return load_json(os.path.join(SESSIONS_DIR, f"{sid}.json"),
                     {"name":"جلسة جديدة","messages":[],"persona":"lawyer"})

def save_session(sid, data):
    data["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_json(os.path.join(SESSIONS_DIR, f"{sid}.json"), data)

def new_sid():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ══════════════════════════════════════════════
# دوال الذكاء الاصطناعي — مباشرة وبدون وسيط
# ══════════════════════════════════════════════
def _post_json(url: str, payload: dict, headers: dict, timeout: int = 90) -> dict:
    """HTTP POST مباشر بـ urllib — لا يحتاج requests"""
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


def call_ai(prompt: str, history: List[Dict], system: str) -> str:
    """
    الدالة الرئيسية للاتصال بالذكاء.
    تدعم: gemini / openai / anthropic
    """
    preset_name = st.session_state.get("preset_name", list(PRESETS.keys())[0])
    api_key     = st.session_state.get("api_key", "")
    preset      = PRESETS[preset_name]

    url   = st.session_state.get("custom_url", preset["url"])   if preset_name == "⚙️ مخصص" else preset["url"]
    model = st.session_state.get("custom_model", preset["model"]) if preset_name == "⚙️ مخصص" else preset["model"]
    fmt   = st.session_state.get("custom_fmt",  preset["fmt"])  if preset_name == "⚙️ مخصص" else preset["fmt"]

    if not api_key:
        return "❌ لم يُدخل مفتاح API. أدخله في ⚙️ الإعدادات بالشريط الجانبي."
    if not url:
        return "❌ لم يُحدد رابط API. راجع الإعدادات."

    # نظّف history: نبقي فقط role+content
    clean_history = [{"role": m["role"], "content": m["content"]} for m in history]

    try:
        # ── Gemini ──────────────────────────────────────────────
        if fmt == "gemini":
            contents = []
            # أضف system كأول رسالة user
            if system:
                contents.append({"role": "user",  "parts": [{"text": system}]})
                contents.append({"role": "model", "parts": [{"text": "حسناً، أنا جاهز للمساعدة."}]})
            for m in clean_history:
                role = "model" if m["role"] == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": m["content"]}]})
            contents.append({"role": "user", "parts": [{"text": prompt}]})
            payload = {"contents": contents,
                       "generationConfig": {"maxOutputTokens": 4096, "temperature": 0.7}}
            resp = _post_json(f"{url}?key={api_key}", payload,
                              {"Content-Type": "application/json"})
            return resp["candidates"][0]["content"]["parts"][0]["text"]

        # ── Anthropic Claude ─────────────────────────────────────
        elif fmt == "anthropic":
            messages = clean_history + [{"role": "user", "content": prompt}]
            payload  = {"model": model, "max_tokens": 4096,
                        "system": system, "messages": messages}
            headers  = {"Content-Type": "application/json",
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01"}
            resp = _post_json(url, payload, headers)
            return resp["content"][0]["text"]

        # ── OpenAI-compatible (Groq, Together, Ollama, GPT…) ────
        else:
            messages = [{"role": "system", "content": system}] + clean_history + \
                       [{"role": "user", "content": prompt}]
            payload  = {"model": model, "messages": messages,
                        "max_tokens": 4096, "temperature": 0.7}
            headers  = {"Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}"}
            resp = _post_json(url, payload, headers)
            return resp["choices"][0]["message"]["content"]

    except RuntimeError as e:
        err = str(e)
        if "429" in err:
            return "⏳ الطلبات كثيرة جداً (Rate Limit). انتظر دقيقة ثم أعد المحاولة."
        if "401" in err or "403" in err:
            return "🔑 مفتاح API غير صحيح أو منتهي الصلاحية. راجع الإعدادات."
        if "404" in err:
            return f"🔗 رابط API غير صحيح أو النموذج غير موجود:\n`{url}`"
        return f"❌ خطأ في الاتصال:\n{err[:400]}"
    except KeyError as e:
        return f"❌ استجابة غير متوقعة من الخادم (مفتاح مفقود: {e}). تحقق من النموذج والرابط."
    except Exception as e:
        return f"❌ خطأ غير متوقع: {str(e)[:300]}"


# ══════════════════════════════════════════════
# دوال معالجة الملفات
# ══════════════════════════════════════════════
def extract_text_from_file(uploaded_file) -> str:
    """استخراج نص من PDF / DOCX / TXT بأعلى جودة ممكنة"""
    name = uploaded_file.name.lower()
    raw  = uploaded_file.read()
    uploaded_file.seek(0)

    if name.endswith(".txt"):
        for enc in ["utf-8", "utf-8-sig", "cp1256", "latin-1"]:
            try:
                return raw.decode(enc)
            except Exception:
                continue
        return raw.decode("utf-8", errors="replace")

    if name.endswith(".pdf"):
        # محاولة 1: PyMuPDF (أفضل للعربية)
        try:
            import fitz
            doc  = fitz.open(stream=raw, filetype="pdf")
            text = "\n".join(page.get_text("text") for page in doc)
            if len(text.strip()) > 50:
                return text
        except Exception as e:
            logger.warning(f"PyMuPDF failed: {e}")
        # محاولة 2: pypdf
        try:
            import io
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw))
            text   = "\n".join(p.extract_text() or "" for p in reader.pages)
            if len(text.strip()) > 50:
                return text
        except Exception as e:
            logger.warning(f"pypdf failed: {e}")
        return "⚠️ لم يُمكن استخراج النص من هذا الـ PDF (قد يكون مسح ضوئي)."

    if name.endswith(".docx"):
        try:
            import io
            from docx import Document
            doc  = Document(io.BytesIO(raw))
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            if len(text.strip()) > 10:
                return text
        except Exception as e:
            logger.warning(f"docx failed: {e}")
        return "⚠️ تعذّر قراءة الملف. تأكد أنه docx وليس doc قديم."

    if name.endswith(".json"):
        try:
            data = json.loads(raw)
            return json.dumps(data, ensure_ascii=False, indent=2)[:8000]
        except Exception:
            return raw.decode("utf-8", errors="replace")[:8000]

    return raw.decode("utf-8", errors="replace")[:5000]


def scan_for_slips(text: str) -> List[Dict]:
    """فحص النص عن زلات وتناقضات قانونية ضد صاحب العمل"""
    findings = []
    patterns = [
        (r"(أمرنا|أجبرنا|أكرهنا|اضطررنا)", "إقرار بالإكراه — دليل على التعسف", "danger"),
        (r"(لا نعترف|نرفض|تجاهلنا)", "رفض صريح — يقوي موقف الموظف", "warn"),
        (r"(بدون\s+تحقيق|دون\s+تحقيق|لم\s+يُجرَ\s+تحقيق)", "فصل بلا تحقيق — بطلان (م.80)", "danger"),
        (r"(بتاريخ\s+[\d/]+)(.*?)(بتاريخ\s+[\d/]+)", "تواريخ متعددة — احتمال تناقض زمني", "warn"),
        (r"(لم\s+يُبلَّغ|لم\s+يُخطَر|دون\s+إشعار)", "غياب الإشعار — إخلال إجرائي", "danger"),
        (r"(وافق|قبل|اعترف)\s+\w+\s+على", "إقرار ضمني — راجع السياق جيداً", "info"),
        (r"(تهديد|التهديد|هدّد|يهدد)", "تهديد موثق — دليل قابل للاحتجاج", "warn"),
        (r"(خطأ\s+في|أخطأنا|نقرّ\s+بخطأ)", "إقرار بالخطأ من الجهة — دليل مباشر", "danger"),
        (r"(لا\s+يستحق|حُرم\s+من|مُنع\s+من)", "حرمان صريح — مطالبة قانونية مباشرة", "danger"),
        (r"(نقل\s+تعسفي|نقل\s+عقابي|نُقل\s+بسبب)", "نقل تعسفي — بطلان محتمل (م.60)", "danger"),
    ]
    for pattern, msg, level in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        if matches:
            snippet = matches[0] if isinstance(matches[0], str) else " ".join(matches[0])
            findings.append({"msg": msg, "level": level,
                              "snippet": snippet[:120].strip()})
    return findings


def calculate_eosb(basic: float, total: float, years: float,
                   arbitrary: bool, delay_months: int) -> Dict:
    """حساب المستحقات العمالية الكاملة"""
    y5     = min(years, 5)
    y_plus = max(0, years - 5)
    eosb   = (basic / 2) * y5 + basic * y_plus
    arb    = (total * min(12, max(3, int(years)))) if arbitrary else 0
    delay  = total * 0.05 * delay_months if delay_months > 0 else 0
    grand  = eosb + arb + delay
    return {
        "eosb": round(eosb, 2),
        "arbitrary": round(arb, 2),
        "delay": round(delay, 2),
        "grand": round(grand, 2),
        "details": [
            f"مكافأة نهاية الخدمة (م.84): {eosb:,.2f} ريال",
            f"تعويض الفصل التعسفي (م.77): {arb:,.2f} ريال" if arbitrary else "",
            f"تعويض تأخير الراتب (م.90): {delay:,.2f} ريال" if delay_months > 0 else "",
        ]
    }


# ══════════════════════════════════════════════
# تهيئة session_state
# ══════════════════════════════════════════════
_saved = load_settings()

_defaults = {
    "persona":       "lawyer",
    "active_tool":   None,
    "current_sid":   None,
    "current_msgs":  [],
    "docs_text":     [],
    "law_db":        load_json(LAW_FILE, []),
    "memory":        load_json(MEMORY_FILE, []),
    "preset_name":   _saved.get("preset_name", list(PRESETS.keys())[0]),
    "api_key":       _saved.get("api_key", ""),
    "custom_url":    _saved.get("custom_url", ""),
    "custom_model":  _saved.get("custom_model", ""),
    "custom_fmt":    _saved.get("custom_fmt", "openai"),
    "pending_input": "",
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════
# ────────────── SIDEBAR ──────────────────────
# ══════════════════════════════════════════════
with st.sidebar:

    # شعار
    st.markdown("""
    <div style='text-align:center;padding:16px 0 8px;'>
      <span style='font-size:2.8rem;'>⚖️</span>
      <div style='font-size:1.5rem;font-weight:900;color:#c9a84c;letter-spacing:0.1em;'>Führer v2</div>
      <div style='font-size:0.75rem;color:#555;'>نظام الذكاء القانوني</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── اختيار الشخصية ──
    st.markdown("### 🎭 الشخصية")

    col_l, col_a = st.columns(2)
    with col_l:
        active_l = "✅ " if st.session_state.persona == "lawyer" else ""
        if st.button(f"{active_l}⚖️ محامي", use_container_width=True,
                     key="btn_lawyer"):
            st.session_state.persona = "lawyer"
            st.session_state.active_tool = None
            st.rerun()
    with col_a:
        active_a = "✅ " if st.session_state.persona == "advisor" else ""
        if st.button(f"{active_a}🧑‍💼 مستشار", use_container_width=True,
                     key="btn_advisor"):
            st.session_state.persona = "advisor"
            st.session_state.active_tool = None
            st.rerun()

    persona_color = "#c9a84c" if st.session_state.persona == "lawyer" else "#4a9eff"
    persona_label = "المحامي العمالي" if st.session_state.persona == "lawyer" else "المستشار العمالي"
    st.markdown(f"""
    <div style='background:rgba({"201,168,76" if st.session_state.persona=="lawyer" else "74,158,255"},0.08);
                border:1px solid {persona_color};border-radius:10px;
                padding:10px 14px;margin:8px 0;font-size:0.82rem;color:{persona_color};'>
      {'⚖️ هجومي | يكتب الدعاوى ويصيغ الحجج' if st.session_state.persona=="lawyer" else '🧑‍💼 تحليلي | يحسب ويوجّه ويوازن'}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── أدوات الشخصية ──
    st.markdown("### 🛠️ الأدوات")

    tools = TOOLS[st.session_state.persona]
    for icon, label, key in tools:
        is_active = st.session_state.active_tool == key
        btn_label = f"{'▶ ' if is_active else ''}{icon} {label}"
        if st.button(btn_label, key=f"tool_{key}", use_container_width=True):
            st.session_state.active_tool = None if is_active else key
            st.rerun()

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── الجلسات ──
    st.markdown("### 💬 الجلسات")

    if st.button("➕ جلسة جديدة", use_container_width=True, key="new_sess"):
        sid = new_sid()
        st.session_state.current_sid  = sid
        st.session_state.current_msgs = []
        save_session(sid, {"name": f"جلسة {persona_label}", "messages": [],
                           "persona": st.session_state.persona})
        st.rerun()

    sessions = list_sessions()
    for s in sessions[:6]:
        p_icon = "⚖️" if s.get("persona") == "lawyer" else "🧑‍💼"
        is_cur = s["id"] == st.session_state.current_sid
        c1, c2 = st.columns([5, 1])
        with c1:
            label = f"{'🟢 ' if is_cur else ''}{p_icon} {s['name'][:14]} ({s['count']})"
            if st.button(label, key=f"s_{s['id']}", use_container_width=True):
                d = load_session(s["id"])
                st.session_state.current_sid  = s["id"]
                st.session_state.current_msgs = d.get("messages", [])
                st.session_state.persona      = d.get("persona", "lawyer")
                st.rerun()
        with c2:
            if st.button("🗑", key=f"del_{s['id']}"):
                os.remove(os.path.join(SESSIONS_DIR, f"{s['id']}.json"))
                if st.session_state.current_sid == s["id"]:
                    st.session_state.current_sid  = None
                    st.session_state.current_msgs = []
                st.rerun()

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── الإعدادات ──
    st.markdown("### ⚙️ الإعدادات")

    new_preset = st.selectbox("النموذج", list(PRESETS.keys()),
                              index=list(PRESETS.keys()).index(st.session_state.preset_name)
                              if st.session_state.preset_name in PRESETS else 0,
                              key="sel_preset", label_visibility="collapsed")
    if new_preset != st.session_state.preset_name:
        st.session_state.preset_name = new_preset

    if new_preset == "⚙️ مخصص":
        st.session_state.custom_url   = st.text_input("رابط API", value=st.session_state.custom_url)
        st.session_state.custom_model = st.text_input("النموذج",  value=st.session_state.custom_model)
        st.session_state.custom_fmt   = st.selectbox("الصيغة", ["openai","gemini","anthropic"])

    new_key = st.text_input("🔑 مفتاح API", value=st.session_state.api_key,
                             type="password", placeholder="AIza... أو sk-...",
                             label_visibility="collapsed")
    if new_key != st.session_state.api_key:
        st.session_state.api_key = new_key

    key_ok = bool(st.session_state.api_key.strip())
    st.markdown(
        f"<div style='font-size:0.78rem;color:{'#4aff88' if key_ok else '#ff6060'};margin:4px 0;'>"
        f"{'✅ مفتاح مُدخل' if key_ok else '⚠️ أدخل مفتاح API'}</div>",
        unsafe_allow_html=True
    )

    if st.button("💾 حفظ الإعدادات", use_container_width=True):
        save_settings({"preset_name": st.session_state.preset_name,
                       "api_key": st.session_state.api_key,
                       "custom_url": st.session_state.custom_url,
                       "custom_model": st.session_state.custom_model,
                       "custom_fmt": st.session_state.custom_fmt})
        st.success("✅ تم الحفظ")


# ══════════════════════════════════════════════
# ────────────── MAIN AREA ────────────────────
# ══════════════════════════════════════════════

persona_color = "#c9a84c" if st.session_state.persona == "lawyer" else "#4a9eff"
persona_label = "المحامي العمالي ⚖️" if st.session_state.persona == "lawyer" else "المستشار العمالي 🧑‍💼"
model_name    = st.session_state.preset_name

st.markdown(f"""
<div class='top-bar'>
  <h1>Führer v2</h1>
  <div style='display:flex;align-items:center;gap:12px;'>
    <span style='color:#555;font-size:0.8rem;'>{model_name}</span>
    <span class='persona-badge' style='border-color:{persona_color};color:{persona_color};'>
      {persona_label}
    </span>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# لوحة الأداة النشطة
# ══════════════════════════════════════════════
active_tool = st.session_state.active_tool

if active_tool == "calculator":
    st.markdown("## 🧮 حاسبة المستحقات العمالية")
    with st.container():
        c1, c2, c3 = st.columns(3)
        with c1:
            basic  = st.number_input("الراتب الأساسي (ريال)", min_value=0.0, step=500.0, value=0.0, key="calc_basic")
        with c2:
            total  = st.number_input("الراتب الإجمالي (ريال)", min_value=0.0, step=500.0, value=0.0, key="calc_total")
        with c3:
            years  = st.number_input("سنوات الخدمة", min_value=0.0, step=0.5, value=0.0, key="calc_years")
        c4, c5 = st.columns(2)
        with c4:
            arbitrary = st.checkbox("فصل تعسفي (م.77)", key="calc_arb")
        with c5:
            delay_m   = st.number_input("أشهر تأخير الراتب", min_value=0, step=1, value=0, key="calc_delay")

        if st.button("احسب المستحقات ⚡", use_container_width=True):
            if basic > 0 and years > 0:
                res = calculate_eosb(basic, total if total > 0 else basic, years, arbitrary, delay_m)
                st.markdown(f"""
                <div class='stat-grid'>
                  <div class='stat-box'><div class='val'>{res['eosb']:,.0f}</div><div class='lbl'>مكافأة نهاية الخدمة</div></div>
                  <div class='stat-box'><div class='val'>{res['arbitrary']:,.0f}</div><div class='lbl'>تعويض تعسفي</div></div>
                  <div class='stat-box'><div class='val'>{res['delay']:,.0f}</div><div class='lbl'>تعويض التأخير</div></div>
                  <div class='stat-box' style='border-color:#c9a84c;'><div class='val' style='font-size:1.8rem;'>{res['grand']:,.0f}</div><div class='lbl'>الإجمالي (ريال)</div></div>
                </div>
                """, unsafe_allow_html=True)
                for d in res["details"]:
                    if d:
                        st.markdown(f"<div class='alert info'>📌 {d}</div>", unsafe_allow_html=True)
                # إرسال النتيجة للمحادثة
                summary = f"نتيجة الحاسبة:\n" + "\n".join(d for d in res["details"] if d)
                summary += f"\n\nالإجمالي: {res['grand']:,.2f} ريال"
                st.session_state.pending_input = f"احسب مستحقاتي:\n{summary}"
            else:
                st.warning("أدخل الراتب الأساسي وسنوات الخدمة على الأقل.")
    st.markdown("---")

elif active_tool == "email_scan":
    st.markdown("## 📧 فحص المراسلات واستخراج الزلات")
    uploaded_emails = st.file_uploader(
        "ارفع ملف المراسلات (PDF أو TXT أو DOCX)",
        type=["pdf", "txt", "docx"], accept_multiple_files=True, key="email_upload"
    )
    manual_text = st.text_area("أو الصق نص المراسلات مباشرة", height=150, key="email_manual")

    if st.button("🔍 فحص المراسلات الآن", use_container_width=True):
        combined = manual_text
        if uploaded_emails:
            for f in uploaded_emails:
                combined += "\n\n" + extract_text_from_file(f)
        if combined.strip():
            findings = scan_for_slips(combined)
            if findings:
                st.markdown(f"### ⚡ تم اكتشاف {len(findings)} نقطة قانونية")
                for f in findings:
                    level_map = {"danger": "🚨", "warn": "⚠️", "info": "📌"}
                    st.markdown(f"""
                    <div class='alert {f["level"]}'>
                      {level_map.get(f["level"],'📌')} <strong>{f["msg"]}</strong><br>
                      <small style='opacity:0.7;'>النص: «{f["snippet"]}»</small>
                    </div>
                    """, unsafe_allow_html=True)
                # أرسل للمحادثة
                summary = "نتائج فحص المراسلات:\n"
                for fi in findings:
                    summary += f"- {fi['msg']}: «{fi['snippet'][:60]}»\n"
                st.session_state.pending_input = f"{summary}\n\nحللها قانونياً واستخرج ما يفيد في القضية."
            else:
                st.markdown("<div class='alert ok'>✅ لم تُكتشف زلات صريحة. الملف نظيف أو يحتاج مراجعة يدوية.</div>", unsafe_allow_html=True)
        else:
            st.warning("ارفع ملف أو الصق النص أولاً.")
    st.markdown("---")

elif active_tool == "doc_analysis":
    st.markdown("## 📁 تحليل المستندات المرفوعة")
    uploaded_docs = st.file_uploader(
        "ارفع الملفات (PDF, DOCX, TXT)",
        type=["pdf", "docx", "txt"], accept_multiple_files=True, key="doc_upload"
    )
    if uploaded_docs:
        st.info(f"📎 تم رفع {len(uploaded_docs)} ملف")
        texts = []
        for f in uploaded_docs:
            with st.expander(f"📄 {f.name}"):
                txt = extract_text_from_file(f)
                texts.append(txt)
                preview = txt[:600] + ("..." if len(txt) > 600 else "")
                st.text_area("معاينة", preview, height=120, key=f"prev_{f.name}")
                # كشف التواريخ والمبالغ
                dates   = re.findall(r'\d{1,2}/\d{1,2}/\d{2,4}', txt)
                amounts = re.findall(r'[\d,]+(?:\.\d+)?\s*ريال', txt)
                arts    = re.findall(r'المادة\s+[\d\u0660-\u0669]+', txt)
                if dates:   st.markdown(f"📅 **تواريخ:** {' | '.join(set(dates[:5]))}")
                if amounts: st.markdown(f"💰 **مبالغ:** {' | '.join(set(amounts[:5]))}")
                if arts:    st.markdown(f"⚖️ **مواد:** {' | '.join(set(arts[:6]))}")
        if st.button("📤 إرسال للمحادثة للتحليل", use_container_width=True):
            combined = "\n\n---\n\n".join(texts)[:6000]
            st.session_state.docs_text = texts
            st.session_state.pending_input = f"حلّل هذه الوثائق قانونياً واستخرج:\n1. الوقائع الرئيسية\n2. النقاط القوية لصالح الموظف\n3. النقاط التي يحتج بها صاحب العمل\n4. توصياتك\n\n[الوثائق]:\n{combined}"
    st.markdown("---")

elif active_tool == "law_search":
    st.markdown("## 📚 البحث في قاعدة الأنظمة السعودية")
    law_db = st.session_state.law_db
    st.caption(f"المواد المتاحة: {len(law_db):,}")
    q = st.text_input("🔍 ابحث في الأنظمة", placeholder="مثال: مكافأة نهاية الخدمة", key="law_q")
    if q:
        results = [i for i in law_db
                   if q in i.get("text","") or q in i.get("law_name","") or q in i.get("article","")]
        st.info(f"نتائج: {len(results)}")
        for r in results[:6]:
            with st.expander(f"📖 {r.get('law_name','')} — {r.get('article','')}"):
                st.markdown(r.get("text","")[:500])
    if not law_db:
        st.markdown("<div class='alert warn'>⚠️ قاعدة الأنظمة فارغة. ارفع ملفات قانونية عبر أداة «تحليل المستندات».</div>", unsafe_allow_html=True)
    st.markdown("---")

elif active_tool in ("draft_lawsuit", "defense_line", "audit_dismissal",
                     "counter_args", "case_strength", "settlement"):
    labels = {
        "draft_lawsuit":   ("📝", "صياغة صحيفة الدعوى",      "اكتب صحيفة دعوى عمالية متكاملة بناءً على معطيات القضية. اذكر الوقائع والطلبات والأسس القانونية."),
        "defense_line":    ("🗡️", "توليد خط الدفاع",           "ضع خط دفاع قانوني مرقّماً ومفصلاً. ابدأ بالدفوع الشكلية ثم الموضوعية. اذكر المواد."),
        "audit_dismissal": ("🔍", "تدقيق إجراءات الفصل",       "دقق في إجراءات الفصل: هل سبقه تحقيق؟ إنذار؟ مهلة إشعار؟ هل هو تعسفي؟ اذكر المخالفات."),
        "counter_args":    ("⚡", "استخراج حجج مضادة",          "استخرج كل الحجج المضادة ضد موقف صاحب العمل. كن صريحاً ومفصلاً."),
        "case_strength":   ("📊", "تقييم قوة القضية",           "قيّم قوة القضية من 1-10 مع شرح النقاط القوية والضعيفة وتوصية بالخطوة التالية."),
        "settlement":      ("🤝", "تقييم خيار التسوية",         "قيّم جدوى التسوية الودية مقابل التقاضي. اذكر الأرقام المتوقعة والمخاطر والمزايا."),
    }
    icon, title, auto_prompt = labels[active_tool]
    st.markdown(f"## {icon} {title}")
    context = st.text_area("معطيات القضية (اختياري لتخصيص الأداة)", height=120, key=f"ctx_{active_tool}")
    if st.button(f"{icon} تشغيل الأداة", use_container_width=True):
        full = auto_prompt
        if context.strip():
            full += f"\n\nمعطيات القضية:\n{context}"
        st.session_state.pending_input = full
    st.markdown("---")


# ══════════════════════════════════════════════
# منطقة الدردشة الرئيسية
# ══════════════════════════════════════════════

if not st.session_state.current_sid:
    # شاشة ترحيب
    st.markdown(f"""
    <div style='text-align:center;padding:60px 20px;'>
      <div style='font-size:4rem;margin-bottom:16px;'>{'⚖️' if st.session_state.persona=='lawyer' else '🧑‍💼'}</div>
      <h2 style='color:{persona_color};font-size:1.8rem;margin-bottom:10px;'>{persona_label}</h2>
      <p style='color:#666;font-size:1rem;max-width:500px;margin:0 auto 28px;'>
        {'يصيغ الدعاوى، يكتب المذكرات، ويبني خط الدفاع القانوني.' if st.session_state.persona=='lawyer' else 'يحسب المستحقات، يحلل المخاطر، ويوجّه نحو القرار الأمثل.'}
      </p>
      <p style='color:#444;font-size:0.88rem;'>
        ▶ ابدأ بفتح <strong>جلسة جديدة</strong> من الشريط الجانبي
      </p>
    </div>
    """, unsafe_allow_html=True)
else:
    # رأس الجلسة
    sess_data = load_session(st.session_state.current_sid)
    col_name, col_clear = st.columns([5, 1])
    with col_name:
        new_name = st.text_input("", value=sess_data.get("name","جلسة"),
                                 placeholder="اسم الجلسة", label_visibility="collapsed",
                                 key="sess_name")
        if new_name != sess_data.get("name",""):
            sess_data["name"] = new_name
            sess_data["messages"] = st.session_state.current_msgs
            save_session(st.session_state.current_sid, sess_data)
    with col_clear:
        if st.button("🗑 مسح", key="clear_chat"):
            st.session_state.current_msgs = []
            sess_data["messages"] = []
            save_session(st.session_state.current_sid, sess_data)
            st.rerun()

    # ── عرض الرسائل ──
    chat_html = "<div class='chat-container' id='chat-scroll'>"
    ai_cls = "msg-ai advisor-mode" if st.session_state.persona == "advisor" else "msg-ai"
    for msg in st.session_state.current_msgs:
        content = msg["content"].replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        ts = msg.get("ts", "")
        if msg["role"] == "user":
            chat_html += f"""
            <div class='msg-user'>
              <span class='msg-icon'>👤</span>{content}
              <div class='msg-meta'><span></span><span>⏱ {ts}</span></div>
            </div>"""
        else:
            icon = "⚖️" if st.session_state.persona == "lawyer" else "🧑‍💼"
            chat_html += f"""
            <div class='{ai_cls}'>
              <span class='msg-icon'>{icon}</span>{content}
              <div class='msg-meta'><span></span><span>⏱ {ts}</span></div>
            </div>"""
    chat_html += "</div>"
    chat_html += "<script>setTimeout(()=>{const c=document.getElementById('chat-scroll');if(c)c.scrollTop=c.scrollHeight;},100);</script>"
    st.markdown(chat_html, unsafe_allow_html=True)

    # ── صندوق الإدخال ──
    pending = st.session_state.get("pending_input", "")
    user_input = st.text_area(
        "",
        value=pending,
        height=100,
        placeholder="اكتب سؤالك القانوني هنا... أو استخدم أداة من الشريط الجانبي",
        label_visibility="collapsed",
        key="chat_input"
    )
    if pending:
        st.session_state.pending_input = ""

    c_send, c_space = st.columns([1, 3])
    with c_send:
        send = st.button("إرسال ⚡", use_container_width=True, key="send_btn")

    if send and user_input.strip():
        ts = datetime.now().strftime("%H:%M")
        user_msg = {"role": "user", "content": user_input.strip(), "ts": ts}
        st.session_state.current_msgs.append(user_msg)

        system_prompt = PERSONA_PROMPTS[st.session_state.persona]
        if st.session_state.docs_text:
            docs_ctx = "\n\n".join(st.session_state.docs_text[:3])[:3000]
            system_prompt += f"\n\nالوثائق المرفوعة:\n{docs_ctx}"

        history = st.session_state.current_msgs[:-1]  # بدون الرسالة الجديدة

        with st.spinner("⚖️ جارٍ التحليل..."):
            response = call_ai(user_input.strip(), history, system_prompt)

        ai_msg = {"role": "assistant", "content": response, "ts": ts}
        st.session_state.current_msgs.append(ai_msg)

        sess_data["messages"] = st.session_state.current_msgs
        sess_data["persona"]  = st.session_state.persona
        save_session(st.session_state.current_sid, sess_data)

        st.rerun()

