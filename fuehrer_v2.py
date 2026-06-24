"""
Führer
"""
import streamlit as st
import re, io, os, json, logging, hashlib
from datetime import datetime, timedelta
from typing import Dict, List
import urllib.request, urllib.error

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fuehrer")

st.set_page_config(
    page_title="⚖️ Führer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
*{box-sizing:border-box}
.stApp{background:#080c14;color:#e8e0d0;font-family:'Cairo',sans-serif;direction:rtl}
[data-testid="stSidebar"]{background:#0d1320!important;border-left:1px solid #1e2a40}
[data-testid="stSidebar"] *{color:#c8c0b0!important}
h1,h2,h3{color:#f0c040!important;font-weight:700}
.stTabs [data-baseweb="tab-list"]{background:#0d1320;border-bottom:2px solid #1e2a40;gap:3px;padding:4px;border-radius:8px 8px 0 0}
.stTabs [data-baseweb="tab"]{background:transparent!important;color:#8090a0!important;border:1px solid transparent!important;border-radius:6px!important;padding:7px 14px!important;font-size:13px;font-family:'Cairo',sans-serif}
.stTabs [data-baseweb="tab"][aria-selected="true"]{background:#1a2235!important;color:#f0c040!important;border-color:#f0c040!important;font-weight:700}
.stTabs [data-baseweb="tab-panel"]{background:#0a0f1a;border:1px solid #1e2a40;border-radius:0 0 8px 8px;padding:18px}
.stTextInput>div>div>input,.stTextArea textarea{background:#0d1320!important;color:#e8e0d0!important;border:1px solid #2a3a55!important;border-radius:6px!important;font-family:'Cairo',sans-serif!important}
.stButton>button{background:linear-gradient(135deg,#c8a020,#f0c040)!important;color:#0a0f1a!important;border:none!important;border-radius:6px!important;font-weight:700!important;font-family:'Cairo',sans-serif!important;padding:10px 18px!important}
[data-testid="stMetric"]{background:#0d1320;border:1px solid #1e2a40;border-radius:8px;padding:12px 16px}
[data-testid="stMetricLabel"]{color:#8090a0!important;font-size:12px}
[data-testid="stMetricValue"]{color:#f0c040!important;font-weight:700;font-size:22px}
.stSelectbox [data-baseweb="select"]>div{background:#0d1320!important;border-color:#2a3a55!important;color:#e8e0d0!important}
.chat-user{background:#1a2235;border:1px solid #2a3a55;border-radius:12px 12px 2px 12px;padding:12px 16px;margin:8px 0;max-width:82%;float:right;clear:both;direction:rtl}
.chat-ai{background:#0d1a2a;border:1px solid #1e3a50;border-radius:12px 12px 12px 2px;padding:12px 16px;margin:8px 0;max-width:88%;float:left;clear:both;direction:rtl;border-left:3px solid #f0c040}
.chat-wrap{overflow:hidden;min-height:60px}
.mem-card{background:#0d1320;border:1px solid #1e2a40;border-radius:8px;padding:12px;margin:5px 0;direction:rtl}
.ok-card{background:rgba(40,100,60,.15);border:1px solid rgba(64,192,96,.3);border-radius:6px;padding:9px 14px;margin:3px 0;direction:rtl}
.bad-card{background:rgba(100,30,30,.15);border:1px solid rgba(192,64,64,.3);border-radius:6px;padding:9px 14px;margin:3px 0;direction:rtl}
.rule-card{background:#0d1a2a;border-right:4px solid #f0c040;border-radius:0 6px 6px 0;padding:9px 14px;margin:3px 0;direction:rtl;font-size:14px}
.tl-item{border-right:2px solid #2a3a55;padding:8px 16px 8px 0;margin:7px 0;position:relative;direction:rtl}
.tl-item::before{content:'';width:10px;height:10px;background:#f0c040;border-radius:50%;position:absolute;right:-6px;top:12px}
.badge{display:inline-block;background:#1a2235;border:1px solid #f0c040;color:#f0c040;border-radius:4px;padding:2px 8px;font-size:11px;font-weight:600;margin:2px}
.hdr{background:linear-gradient(135deg,#0d1320,#1a2235);border:1px solid #1e2a40;border-bottom:2px solid #f0c040;border-radius:8px;padding:18px 24px;margin-bottom:16px;direction:rtl}
.session-card{background:#0d1320;border:1px solid #1e2a40;border-radius:8px;padding:10px;margin:4px 0;cursor:pointer;direction:rtl}
.session-card:hover{border-color:#f0c040}
hr{border-color:#1e2a40!important}
::-webkit-scrollbar{width:5px}
::-webkit-scrollbar-track{background:#080c14}
::-webkit-scrollbar-thumb{background:#2a3a55;border-radius:3px}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# ملفات التخزين المحلي
# ══════════════════════════════════════════════
DATA_DIR     = "fuehrer_data"
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")
MEMORY_FILE  = os.path.join(DATA_DIR, "memory.json")
SETTINGS_FILE= os.path.join(DATA_DIR, "settings.json")
LAW_FILE     = os.path.join(DATA_DIR, "law_db.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)

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
        return True
    except Exception as e:
        logger.error("save %s: %s", path, e)
        return False

def list_sessions():
    sessions = []
    try:
        for fname in sorted(os.listdir(SESSIONS_DIR), reverse=True):
            if fname.endswith(".json"):
                path = os.path.join(SESSIONS_DIR, fname)
                data = load_json(path, {})
                sessions.append({
                    "id": fname.replace(".json",""),
                    "name": data.get("name", fname),
                    "count": len(data.get("messages",[])),
                    "updated": data.get("updated",""),
                    "path": path,
                })
    except Exception:
        pass
    return sessions

def load_session(session_id):
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    return load_json(path, {"name":"جلسة جديدة","messages":[],"updated":""})

def save_session(session_id, data):
    data["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    return save_json(path, data)

def delete_session(session_id):
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    try:
        if os.path.exists(path):
            os.remove(path)
        return True
    except Exception:
        return False

def new_session_id():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# ══════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════
def _init():
    defs = {
        "memory":       load_json(MEMORY_FILE, []),
        "law_db":       load_json(LAW_FILE, []),
        "docs":         [],
        "pending_q":    "",
        "current_sid":  None,
        "current_msgs": [],
        "ai_provider":  "Gemini (Google) — مجاني",
        "gemini_key":   "",
        "claude_key":   "",
        "groq_key":     "",
        "case_type":    "قضية عمالية",
    }
    saved = load_json(SETTINGS_FILE, {})
    defs["ai_provider"] = saved.get("ai_provider", defs["ai_provider"])
    defs["gemini_key"]  = saved.get("gemini_key", "")
    defs["claude_key"]  = saved.get("claude_key", "")
    defs["groq_key"]    = saved.get("groq_key", "")
    for k,v in defs.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

def save_settings():
    save_json(SETTINGS_FILE, {
        "ai_provider": st.session_state.ai_provider,
        "gemini_key":  st.session_state.gemini_key,
        "claude_key":  st.session_state.claude_key,
        "groq_key":    st.session_state.groq_key,
    })

def save_memory():
    save_json(MEMORY_FILE, st.session_state.memory)

def save_law():
    save_json(LAW_FILE, st.session_state.law_db)

# ══════════════════════════════════════════════
# DOCUMENT INTELLIGENCE
# ══════════════════════════════════════════════
def _norm(t):
    return re.sub(r"\s+", " ", t or "").strip()

def _bytes(f):
    if hasattr(f, "getvalue"):
        return f.getvalue()
    try:
        p = f.tell(); d = f.read(); f.seek(p); return d
    except Exception:
        return f.read()

class DocIntel:
    def extract(self, f) -> str:
        ext = (getattr(f, "name", "") or "").rsplit(".", 1)[-1].lower()
        raw = _bytes(f)
        try:
            if ext == "pdf":        return self._pdf(raw)
            if ext == "docx":       return self._docx(raw)
            if ext in ("txt","md"): return _norm(raw.decode("utf-8", errors="ignore"))
            if ext == "json":
                return _norm(json.dumps(
                    json.loads(raw.decode("utf-8", errors="ignore")),
                    ensure_ascii=False))
            if ext == "csv":
                import csv
                rows = list(csv.reader(io.StringIO(raw.decode("utf-8", errors="ignore"))))
                return _norm("\n".join(" | ".join(r) for r in rows))
            return _norm(raw.decode("utf-8", errors="ignore"))
        except Exception:
            return ""

    def _pdf(self, raw):
        parts = []
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(raw)) as pdf:
                for pg in pdf.pages:
                    t = pg.extract_text() or ""
                    if t.strip(): parts.append(t)
        except Exception:
            try:
                import PyPDF2
                for pg in PyPDF2.PdfReader(io.BytesIO(raw)).pages:
                    t = pg.extract_text() or ""
                    if t.strip(): parts.append(t)
            except Exception:
                pass
        return _norm("\n".join(parts))

    def _docx(self, raw):
        try:
            from docx import Document
            return _norm("\n".join(
                p.text for p in Document(io.BytesIO(raw)).paragraphs if p.text))
        except Exception:
            return ""

    def entities(self, t):
        return {
            "parties":  list(set(re.findall(
                r"(?:المدعي|المدعى عليه|الشركة|المؤسسة|الموظف|الهيئة)", t or ""))),
            "amounts":  re.findall(r"[\d,]+\s*(?:ريال|درهم|دولار)", t or ""),
            "articles": re.findall(r"المادة\s*[\u0600-\u06FF\d]+", t or ""),
            "dates":    re.findall(r"\d{1,2}/\d{1,2}/\d{2,4}", t or ""),
        }

# ══════════════════════════════════════════════
# RULE ENGINE
# ══════════════════════════════════════════════
RULES = [
    {"c":"days_abandoned>30","o":"⚠️ انقطاع >30 يوم (ترك العمل)","cat":"عمل"},
    {"c":"days_abandoned>15 and days_abandoned<=30","o":"⚠️ انقطاع 15-30 يوم (إنذار)","cat":"عمل"},
    {"c":"days_since_firing>365","o":"⛔ مضى >سنة على الفصل (سقط حق التقاضي)","cat":"تقادم"},
    {"c":"days_since_firing>180 and days_since_firing<=365","o":"⏳ مضى >6 أشهر (تقادم جزئي)","cat":"تقادم"},
    {"c":"no_investigation","o":"⚖️ فصل بلا تحقيق (بطلان)","cat":"إجراءات"},
    {"c":"arbitrary_dismissal","o":"⚖️ فصل تعسفي (تعويض)","cat":"عمل"},
    {"c":"salary_delay","o":"⚖️ تأخير الراتب (تعويض)","cat":"عمل"},
    {"c":"eosb_not_paid","o":"⚖️ مكافأة نهاية الخدمة لم تُصرف","cat":"عمل"},
    {"c":"absence_days>30","o":"⚠️ غياب >30 يوم (فصل)","cat":"غياب"},
    {"c":"absence_days>20 and absence_days<=30","o":"⚠️ غياب 20-30 يوم (إنذار ثانٍ)","cat":"غياب"},
    {"c":"absence_days>15 and absence_days<=20","o":"⚠️ غياب 15-20 يوم (إنذار أول)","cat":"غياب"},
    {"c":"service_length<2","o":"📌 خدمة <2 سنة (نصف شهر/سنة)","cat":"مكافأة"},
    {"c":"service_length>=2 and service_length<5","o":"📌 خدمة 2-5 سنوات (شهر/سنة)","cat":"مكافأة"},
    {"c":"service_length>=5","o":"📌 خدمة ≥5 سنوات (شهر ونصف/سنة)","cat":"مكافأة"},
    {"c":"notification_late","o":"⚖️ تبليغ بعد 7 أيام (إخلال)","cat":"إجراءات"},
    {"c":"violation_date_missing","o":"⚖️ تاريخ المخالفة مجهول (لصالحك)","cat":"إجراءات"},
    {"c":"penalty_after_1_year","o":"⛔ سنة على المخالفة بلا عقوبة (سقط)","cat":"تقادم"},
    {"c":"judgment_without_hearing","o":"⚖️ حكم دون سماعك (بطلان)","cat":"إجراءات"},
    {"c":"no_response_90_days","o":"⚖️ 90 يوم بلا رد (موافقة ضمنية)","cat":"إجراءات"},
    {"c":"doc_unsigned","o":"⚖️ مستند غير موقع (لا حجية)","cat":"مستندات"},
    {"c":"forgery_proven","o":"🚨 تزوير مثبت (جريمة)","cat":"مستندات"},
    {"c":"opponent_hides_doc","o":"⚖️ الخصم يخفي مستنداً (يُحكم ضده)","cat":"مستندات"},
    {"c":"settlement_offer is True and risk_score>60","o":"🤝 الصلح أفضل","cat":"صلح"},
    {"c":"settlement_offer is True and risk_score<=40","o":"⚖️ الصلح ممكن والقضية قوية","cat":"صلح"},
    {"c":"reply_delay>30","o":"⏳ تأخير إداري >30 يوم","cat":"تأخير"},
    {"c":"ambiguous_count>3","o":"🔍 عبارات غامضة (طعن محتمل)","cat":"لغوي"},
    {"c":"contradictions>1","o":"⚡ تناقض في مراسلات الخصم","cat":"تناقضات"},
    {"c":"force_majeure is True and days_abandoned>60","o":"📌 عذر قاهر يبرر الانقطاع","cat":"أعذار"},
    {"c":"proven_illness","o":"📌 مرض مثبت (عذر مقبول)","cat":"أعذار"},
    {"c":"natural_disaster","o":"📌 كارثة طبيعية (قوة قاهرة)","cat":"أعذار"},
    {"c":"disproportionate_fine","o":"⚖️ غرامة غير متناسبة (تُخفَّض)","cat":"غرامات"},
    {"c":"fine_illegal","o":"⚖️ غرامة مخالفة للنظام (تُلغى)","cat":"غرامات"},
    {"c":"supreme_court_ruling","o":"⭐ سابقة من المحكمة العليا","cat":"سوابق"},
    {"c":"high_similarity_ruling","o":"⭐ سابقة مباشرة (تشابه 90%+)","cat":"سوابق"},
    {"c":"expert_request_denied","o":"⚖️ رفض الخبرة (إخلال بحق الدفاع)","cat":"إجراءات"},
    {"c":"unlawful_deduction","o":"⚖️ خصم بغير حق (يُرد)","cat":"عمل"},
    {"c":"non_judicial_acknowledgment","o":"📌 إقرار غير قضائي (حجة على المُقِر)","cat":"مستندات"},
    {"c":"opponent_threatens","o":"⚖️ تهديد متكرر (تعسف)","cat":"سلوك"},
    {"c":"death_of_relative","o":"📌 وفاة قريب (إجازة رسمية)","cat":"أعذار"},
    {"c":"travel_ban","o":"📌 منع السفر (قوة قاهرة)","cat":"أعذار"},
    {"c":"settlement_broken","o":"⚖️ نقض الصلح (تعويض)","cat":"صلح"},
    {"c":"two_vs_one_witness","o":"📌 شاهدان ضد واحد (مقبول)","cat":"شهادات"},
    {"c":"witnesses_conflict","o":"⚖️ تناقض الشهود","cat":"شهادات"},
    {"c":"new_evidence_late","o":"📌 أدلة جديدة بعد الميعاد (مقبولة)","cat":"مستندات"},
    {"c":"offer_rejected_by_opponent","o":"📌 رفض الخصم الصلح (تعويض لك)","cat":"صلح"},
]

def eval_rule(cond, ctx):
    try:
        for part in [p.strip() for p in cond.split(" and ")]:
            if not part: continue
            m = re.match(r"^(\w+)\s+is\s+(True|False)$", part)
            if m:
                if bool(ctx.get(m[1],False)) != (m[2]=="True"): return False
                continue
            m = re.match(r"^(\w+)$", part)
            if m:
                if not bool(ctx.get(m[1],False)): return False
                continue
            m = re.match(r"^(\w+)\s*(>=|<=|>|<)\s*([0-9.]+)$", part)
            if m:
                lhs=float(ctx.get(m[1],0)); rhs=float(m[3])
                if not {">":lhs>rhs,">=":lhs>=rhs,"<":lhs<rhs,"<=":lhs<=rhs}[m[2]]: return False
                continue
            m = re.match(r"^(\w+)=='([^']*)'$", part.replace(" ",""))
            if m:
                if str(ctx.get(m[1],"")) != m[2]: return False
                continue
            return False
        return True
    except Exception:
        return False

def apply_rules(ctx):
    return [{"text":r["o"],"cat":r["cat"]} for r in RULES if eval_rule(r["c"],ctx)]

# ══════════════════════════════════════════════
# TIMELINE
# ══════════════════════════════════════════════
def build_timeline(texts):
    evs = []
    for idx, txt in enumerate(texts):
        for d in re.findall(r"\d{1,2}/\d{1,2}/\d{2,4}", txt or ""):
            for fmt in ["%d/%m/%Y","%d/%m/%y"]:
                try:
                    dt = datetime.strptime(d, fmt)
                    evs.append({"date":dt,"text":(txt or "")[:200]})
                    break
                except ValueError:
                    pass
    return sorted(evs, key=lambda x: x["date"])

def calc_gaps(evs):
    out = []
    for i in range(len(evs)-1):
        diff = (evs[i+1]["date"]-evs[i]["date"]).days
        if diff > 30:
            out.append({"from":evs[i]["date"].strftime("%d/%m/%Y"),
                        "to":evs[i+1]["date"].strftime("%d/%m/%Y"),
                        "days":diff})
    return out

# ══════════════════════════════════════════════
# MEMORY
# ══════════════════════════════════════════════
def mem_add(text, tags=None, cat="عام"):
    m = {
        "id":  hashlib.md5(f"{text}{datetime.now().isoformat()}".encode()).hexdigest()[:8],
        "text":text, "tags":tags or [], "category":cat,
        "ts":  datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    st.session_state.memory.append(m)
    save_memory()
    return m["id"]

def mem_del(mid):
    st.session_state.memory = [m for m in st.session_state.memory if m["id"] != mid]
    save_memory()

def mem_edit(mid, new_text):
    for m in st.session_state.memory:
        if m["id"] == mid:
            m["text"] = new_text
            m["ts"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            break
    save_memory()

# ══════════════════════════════════════════════
# AI — Gemini + Claude + Groq
# ══════════════════════════════════════════════
def build_system():
    mem_ctx = ""
    if st.session_state.memory:
        mem_ctx = "\n\nالذاكرة:\n" + "\n".join(
            f"- {m['text'][:150]}" for m in st.session_state.memory[-20:])
    law_ctx = ""
    return f"""أنت محامٍ ومستشار قانوني سعودي خبير.
تخصصك: نظام العمل، المرافعات الشرعية، الأنظمة السعودية.
- استند للأنظمة السعودية واذكر المواد
- كن محدداً وعملياً
- أجب بالعربية الفصحى{mem_ctx}"""

def call_gemini(prompt, msgs, doc_ctx=""):
    key = st.session_state.gemini_key
    if not key: return "❌ أدخل Gemini API Key في الإعدادات"
    system = build_system()
    if doc_ctx: system += f"\n\nالمستندات:\n{doc_ctx[:4000]}"
    contents = [{"role":"user","parts":[{"text":system+"\n\nالسؤال: "+prompt}]}]
    for m in msgs[-30:]:
        role = "user" if m["role"]=="user" else "model"
        contents.append({"role":role,"parts":[{"text":m["content"]}]})
    payload = json.dumps({"contents":contents}).encode()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
    req = urllib.request.Request(url, data=payload,
          headers={"Content-Type":"application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            d = json.loads(r.read().decode())
            return d["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        return f"❌ Gemini {e.code}: {e.read().decode()[:200]}"
    except Exception as e:
        return f"❌ {e}"

def call_claude(prompt, msgs, doc_ctx=""):
    key = st.session_state.claude_key
    if not key: return "❌ أدخل Claude API Key في الإعدادات"
    system = build_system()
    if doc_ctx: system += f"\n\nالمستندات:\n{doc_ctx[:4000]}"
    messages = []
    for m in msgs[-30:]:
        messages.append({"role":m["role"],"content":m["content"]})
    messages.append({"role":"user","content":prompt})
    payload = json.dumps({
        "model":"claude-sonnet-4-6",
        "max_tokens":2048,
        "system":system,
        "messages":messages,
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={"Content-Type":"application/json",
                 "x-api-key":key,
                 "anthropic-version":"2023-06-01"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            d = json.loads(r.read().decode())
            return d["content"][0]["text"]
    except urllib.error.HTTPError as e:
        return f"❌ Claude {e.code}: {e.read().decode()[:200]}"
    except Exception as e:
        return f"❌ {e}"

def call_groq(prompt, msgs, doc_ctx=""):
    key = st.session_state.groq_key
    if not key: return "❌ أدخل Groq API Key في الإعدادات"
    system = build_system()
    if doc_ctx: system += f"\n\nالمستندات:\n{doc_ctx[:4000]}"
    messages = [{"role":"system","content":system}]
    for m in msgs[-30:]:
        messages.append({"role":m["role"],"content":m["content"]})
    messages.append({"role":"user","content":prompt})
    payload = json.dumps({
        "model":"llama-3.3-70b-versatile",
        "messages":messages,
        "max_tokens":2048,
    }).encode()
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={"Content-Type":"application/json",
                 "Authorization":f"Bearer {key}"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            d = json.loads(r.read().decode())
            return d["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        return f"❌ Groq {e.code}: {e.read().decode()[:200]}"
    except Exception as e:
        return f"❌ {e}"

def call_ai(prompt, doc_ctx=""):
    msgs = st.session_state.current_msgs
    p = st.session_state.ai_provider
    if "Gemini"  in p: return call_gemini(prompt, msgs, doc_ctx)
    if "Claude"  in p: return call_claude(prompt, msgs, doc_ctx)
    if "Groq"    in p: return call_groq(prompt, msgs, doc_ctx)
    return "❌ اختر نموذجاً"

# ══════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚖️ Führer")
    st.markdown("---")

    # النموذج والمفاتيح
    st.markdown("**🤖 النموذج**")
    provider = st.selectbox("النموذج", [
        "Gemini (Google) — مجاني",
        "Groq (مجاني وسريع)",
        "Claude (Anthropic)",
    ], label_visibility="collapsed",
       index=["Gemini (Google) — مجاني","Groq (مجاني وسريع)","Claude (Anthropic)"].index(
           st.session_state.ai_provider) if st.session_state.ai_provider in
           ["Gemini (Google) — مجاني","Groq (مجاني وسريع)","Claude (Anthropic)"] else 0)

    if provider != st.session_state.ai_provider:
        st.session_state.ai_provider = provider
        save_settings()

    if "Gemini" in provider:
        k = st.text_input("Gemini Key", value=st.session_state.gemini_key,
                          type="password", label_visibility="collapsed",
                          placeholder="AIza...")
        if k != st.session_state.gemini_key:
            st.session_state.gemini_key = k
            save_settings()
        st.markdown("[🔑 احصل على Key مجاني](https://aistudio.google.com/apikey)")
        if k: st.success("✅ محفوظ")

    elif "Groq" in provider:
        k = st.text_input("Groq Key", value=st.session_state.groq_key,
                          type="password", label_visibility="collapsed",
                          placeholder="gsk_...")
        if k != st.session_state.groq_key:
            st.session_state.groq_key = k
            save_settings()
        st.markdown("[🔑 احصل على Key مجاني](https://console.groq.com)")
        if k: st.success("✅ محفوظ")

    elif "Claude" in provider:
        k = st.text_input("Claude Key", value=st.session_state.claude_key,
                          type="password", label_visibility="collapsed",
                          placeholder="sk-ant-...")
        if k != st.session_state.claude_key:
            st.session_state.claude_key = k
            save_settings()
        st.markdown("[🔑 احصل على Key](https://console.anthropic.com)")
        if k: st.success("✅ محفوظ")

    st.markdown("---")

    # الجلسات
    st.markdown("**💬 الجلسات المحفوظة**")
    if st.button("➕ جلسة جديدة", use_container_width=True):
        sid = new_session_id()
        st.session_state.current_sid  = sid
        st.session_state.current_msgs = []
        save_session(sid, {"name":"جلسة جديدة","messages":[]})
        st.rerun()

    sessions = list_sessions()
    for s in sessions[:10]:
        col1, col2 = st.columns([4,1])
        with col1:
            label = f"{'🟢 ' if s['id']==st.session_state.current_sid else ''}{s['name'][:20]} ({s['count']})"
            if st.button(label, key=f"s_{s['id']}", use_container_width=True):
                data = load_session(s["id"])
                st.session_state.current_sid  = s["id"]
                st.session_state.current_msgs = data.get("messages", [])
                st.rerun()
        with col2:
            if st.button("🗑", key=f"ds_{s['id']}"):
                delete_session(s["id"])
                if st.session_state.current_sid == s["id"]:
                    st.session_state.current_sid  = None
                    st.session_state.current_msgs = []
                st.rerun()

    st.markdown("---")
    st.markdown("**📋 نوع القضية**")
    ct = st.selectbox("النوع",[
        "قضية عمالية","نزاع تجاري","قضية عقارية",
        "نزاع إداري","قضية جنائية","إفلاس وتصفية",
    ], label_visibility="collapsed")
    st.session_state.case_type = ct

    st.markdown("---")
    c1,c2 = st.columns(2)
    with c1: st.metric("الذاكرة", len(st.session_state.memory))
    with c2: st.metric("الجلسات", len(sessions))
    st.metric("مواد قانونية", len(st.session_state.law_db))

# ══════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════
st.markdown("""
<div class="hdr">
<h1 style="margin:0;font-size:24px">⚖️ Führer </h1>
<p style="color:#8090a0;margin:4px 0 0;font-size:12px">
سري تماماً • سياق طويل • حفظ دائم • Gemini / Claude / Groq
</p>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════
tabs = st.tabs(["🤖 المستشار","📂 الملفات","📅 الجدول","⚖️ التحليل",
                "📜 القواعد","📄 التقارير","🧠 الذاكرة","📚 القانون"])
t_ai,t_files,t_tl,t_analysis,t_rules,t_reports,t_mem,t_law = tabs

# ── TAB 1: المستشار ─────────────────────────
with t_ai:
    st.subheader(f"🤖 {st.session_state.ai_provider}")

    if not st.session_state.current_sid:
        st.info("👈 اضغط 'جلسة جديدة' من الشريط الجانبي للبدء")
    else:
        # تسمية الجلسة
        sess_data = load_session(st.session_state.current_sid)
        new_name = st.text_input("اسم الجلسة",
                                  value=sess_data.get("name","جلسة جديدة"),
                                  key="sess_name")
        if new_name != sess_data.get("name"):
            sess_data["name"] = new_name
            sess_data["messages"] = st.session_state.current_msgs
            save_session(st.session_state.current_sid, sess_data)

        # Quick prompts
        qp_cols = st.columns(4)
        for i,(col,q) in enumerate(zip(qp_cols,[
            "حلل وضعي القانوني",
            "ما نقاط قوتي؟",
            "ما المواعيد النظامية؟",
            "اقترح استراتيجية",
        ])):
            with col:
                if st.button(q, key=f"qp{i}", use_container_width=True):
                    st.session_state.pending_q = q

        st.markdown("---")

        # عرض المحادثة
        st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
        for msg in st.session_state.current_msgs:
            cls = "chat-user" if msg["role"]=="user" else "chat-ai"
            ico = "👤" if msg["role"]=="user" else "⚖️"
            content = msg["content"].replace("\n","<br>")
            ts = msg.get("ts","")
            st.markdown(
                f'<div class="{cls}">{ico} {content}'
                f'<br><small style="color:#556;font-size:10px">⏱ {ts}</small></div>',
                unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        oc1,oc2 = st.columns(2)
        with oc1: use_docs = st.checkbox("📄 استخدم المستندات", value=True)
        with oc2: auto_mem = st.checkbox("🧠 حفظ في الذاكرة", value=True)

        user_inp = st.text_area(
            "سؤالك",
            value=st.session_state.pending_q,
            height=100,
            placeholder="مثال: تأخر راتبي 3 أشهر — ما حقوقي؟",
            key="chat_input",
        )

        sc1,sc2,sc3 = st.columns([3,1,1])
        with sc1: send_btn = st.button("📤 إرسال", use_container_width=True)
        with sc2:
            if st.button("🗑️ مسح الجلسة", use_container_width=True):
                st.session_state.current_msgs = []
                sess_data["messages"] = []
                save_session(st.session_state.current_sid, sess_data)
                st.rerun()
        with sc3:
            if st.button("💾 حفظ", use_container_width=True):
                sess_data["messages"] = st.session_state.current_msgs
                save_session(st.session_state.current_sid, sess_data)
                st.success("✅")

        if send_btn and user_inp.strip():
            st.session_state.pending_q = ""
            doc_ctx = "\n\n".join(st.session_state.docs[:3])[:5000] if use_docs else ""
            ts = datetime.now().strftime("%H:%M")

            st.session_state.current_msgs.append({
                "role":"user","content":user_inp,"ts":ts})

            with st.spinner("⚖️ يحلل..."):
                resp = call_ai(user_inp, doc_ctx=doc_ctx)

            st.session_state.current_msgs.append({
                "role":"assistant","content":resp,"ts":ts})

            # حفظ تلقائي
            sess_data["messages"] = st.session_state.current_msgs
            save_session(st.session_state.current_sid, sess_data)

            if auto_mem and len(resp)>80 and "❌" not in resp:
                mem_add(f"س: {user_inp[:80]} | ج: {resp[:150]}...",
                       tags=["محادثة", st.session_state.case_type],
                       cat="محادثة")
            st.rerun()

        # تصدير المحادثة
        if st.session_state.current_msgs:
            chat_export = "\n\n".join(
                f"{'أنت' if m['role']=='user' else 'المستشار'} [{m.get('ts','')}]:\n{m['content']}"
                for m in st.session_state.current_msgs)
            st.download_button(
                "⬇️ تحميل المحادثة",
                data=chat_export.encode("utf-8"),
                file_name=f"محادثة_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain")

# ── TAB 2: الملفات ──────────────────────────
with t_files:
    st.subheader("📂 رفع وتحليل المستندات")
    uploaded = st.file_uploader(
        "PDF · DOCX · TXT · JSON · CSV",
        type=["pdf","docx","txt","json","csv"],
        accept_multiple_files=True,
    )
    if uploaded:
        if st.button("🔍 استخراج وتحليل", use_container_width=True):
            di = DocIntel()
            texts = []
            for f in uploaded:
                with st.expander(f"📄 {f.name}"):
                    txt = di.extract(f)
                    if txt:
                        texts.append(txt)
                        ents = di.entities(txt)
                        st.text(txt[:500]+("..." if len(txt)>500 else ""))
                        if ents["articles"]:
                            st.markdown("**المواد:** " + " ".join(
                                f'<span class="badge">{a}</span>'
                                for a in ents["articles"][:5]),
                                unsafe_allow_html=True)
                        if ents["dates"]:
                            st.markdown(f"**تواريخ:** {', '.join(ents['dates'][:5])}")
                        if ents["amounts"]:
                            st.markdown(f"**مبالغ:** {', '.join(ents['amounts'][:5])}")
                    else:
                        st.warning("⚠️ لم يُستخرج نص")
            st.session_state.docs = texts
            st.success(f"✅ {len(texts)} ملف | {sum(len(t) for t in texts):,} حرف")

# ── TAB 3: الجدول الزمني ────────────────────
with t_tl:
    st.subheader("📅 الجدول الزمني")
    if not st.session_state.docs:
        st.info("⚠️ ارفع الملفات أولاً")
    else:
        tl   = build_timeline(st.session_state.docs)
        gaps = calc_gaps(tl)
        m1,m2 = st.columns(2)
        with m1: st.metric("الأحداث", len(tl))
        with m2: st.metric("الفجوات", len(gaps))
        for ev in tl:
            st.markdown(
                f'<div class="tl-item"><strong>{ev["date"].strftime("%d/%m/%Y")}</strong>'
                f'<br><span style="color:#a0b0c0;font-size:13px">{ev["text"][:120]}...</span></div>',
                unsafe_allow_html=True)
        if gaps:
            st.markdown("### ⚠️ الفجوات")
            for g in gaps:
                st.error(f"⏰ {g['days']} يوم — من {g['from']} إلى {g['to']}")

# ── TAB 4: التحليل ──────────────────────────
with t_analysis:
    st.subheader("⚖️ التحليل")
    if not st.session_state.docs:
        st.info("⚠️ ارفع الملفات أولاً")
    else:
        texts   = st.session_state.docs
        tl      = build_timeline(texts)
        gaps    = calc_gaps(tl)
        contras = []
        for i,t in enumerate(texts):
            dates = re.findall(r"\d{1,2}/\d{1,2}/\d{2,4}", t or "")
            if len(dates)>=2 and dates[0]==dates[1]:
                contras.append(f"تناقض في التواريخ بالملف {i+1}")
        ss = sum(1 for t in texts for k in ["تهديد","فوراً","عاجل"] if k in t)
        risk = min(max(len(gaps)*2 + len(contras)*5 + ss + (10 if len(tl)<2 else 0),0),100)
        cred = max(100 - sum(5 for t in texts if "نحن نؤكد" in t)
                       - sum(10 for t in texts if "مادة" in t and "خطأ" in t), 0)

        mc = st.columns(4)
        with mc[0]: st.metric("مستوى الخطر", f"{risk}/100")
        with mc[1]: st.metric("مصداقية الخصم", f"{cred}/100")
        with mc[2]: st.metric("التناقضات", len(contras))
        with mc[3]: st.metric("الفجوات", len(gaps))

        color = "#c04040" if risk>70 else "#c08020" if risk>40 else "#40c060"
        st.markdown(
            f'<div style="background:#0d1320;border:1px solid #1e2a40;border-radius:6px;'
            f'padding:8px;margin:8px 0"><div style="background:{color};width:{risk}%;'
            f'height:8px;border-radius:4px"></div>'
            f'<small style="color:#8090a0">الخطر: {risk}%</small></div>',
            unsafe_allow_html=True)

        sc1,sc2 = st.columns(2)
        strs,weaks = [],[]
        for ev in tl:
            t = (ev.get("text") or "").lower()
            full = ev.get("text") or ""
            if "أقر" in t or "اعترف" in t: weaks.append("اعتراف ضمني")
            if any(k in t for k in ["عذر","مرض","ظروف"]): strs.append("أعذار رسمية")
            if "المادة" in full: strs.append("استشهاد بمواد نظامية")
            if "تهديد" in t: weaks.append("لغة تهديدية")
        strs = list(set(strs)); weaks = list(set(weaks))
        with sc1:
            st.markdown("### ✅ نقاط القوة")
            for s in strs: st.markdown(f'<div class="ok-card">✅ {s}</div>', unsafe_allow_html=True)
            if not strs: st.info("لا توجد")
        with sc2:
            st.markdown("### ❌ نقاط الضعف")
            for w in weaks: st.markdown(f'<div class="bad-card">⚠️ {w}</div>', unsafe_allow_html=True)
            if not weaks: st.success("لا توجد")

# ── TAB 5: القواعد ──────────────────────────
with t_rules:
    st.subheader(f"📜 محرك القواعد — {len(RULES)} قاعدة")
    with st.expander("⚙️ بيانات القضية", expanded=True):
        rc1,rc2,rc3 = st.columns(3)
        with rc1:
            d_aban  = st.number_input("أيام الانقطاع",0,3000,0)
            d_fire  = st.number_input("أيام منذ الفصل",0,3000,0)
            d_reply = st.number_input("تأخر رد الخصم",0,365,0)
            d_abs   = st.number_input("أيام الغياب",0,365,0)
        with rc2:
            svc    = st.number_input("سنوات الخدمة",0.0,50.0,0.0,0.5)
            rscore = st.number_input("درجة الخطر",0,100,50)
        with rc3:
            no_inv  = st.checkbox("فصل بلا تحقيق")
            arb_dis = st.checkbox("فصل تعسفي")
            fm      = st.checkbox("عذر قاهر")
            settl   = st.checkbox("عرض صلح")
            sal_del = st.checkbox("تأخير الراتب")
            eosb    = st.checkbox("مكافأة لم تُصرف")
            ill     = st.checkbox("مرض مثبت")
            no_resp = st.checkbox("90 يوم بلا رد")

    if st.button("🔍 تطبيق القواعد", use_container_width=True):
        ctx = {
            "days_abandoned":d_aban,"days_since_firing":d_fire,
            "reply_delay":d_reply,"absence_days":d_abs,
            "service_length":svc,"risk_score":rscore,
            "no_investigation":no_inv,"arbitrary_dismissal":arb_dis,
            "force_majeure":fm,"settlement_offer":settl,
            "salary_delay":sal_del,"eosb_not_paid":eosb,
            "proven_illness":ill,"no_response_90_days":no_resp,
        }
        alerts = apply_rules(ctx)
        if alerts:
            cats = {}
            for a in alerts: cats.setdefault(a["cat"],[]).append(a["text"])
            for cat,items in cats.items():
                st.markdown(f"**{cat}**")
                for item in items:
                    st.markdown(f'<div class="rule-card">{item}</div>',unsafe_allow_html=True)
        else:
            st.success("✅ لا تنبيهات")

# ── TAB 6: التقارير ─────────────────────────
with t_reports:
    st.subheader("📄 التقارير واللوائح")
    rp1,rp2 = st.columns(2)
    with rp1:
        st.markdown("### 📊 تقرير شامل")
        if st.button("🖨️ إنشاء", use_container_width=True):
            if not st.session_state.docs:
                st.warning("ارفع الملفات أولاً")
            else:
                texts  = st.session_state.docs
                tl     = build_timeline(texts)
                gaps   = calc_gaps(tl)
                report = f"""تقرير قانوني — {datetime.now().strftime('%d/%m/%Y %H:%M')}
نوع القضية: {st.session_state.case_type}
{'='*40}
الأحداث: {len(tl)} | الفجوات: {len(gaps)}

المحادثات المحفوظة: {len(list_sessions())}
الذاكرة: {len(st.session_state.memory)} سجل

الفجوات الزمنية:
""" + "".join(f"• {g['days']} يوم: {g['from']} → {g['to']}\n" for g in gaps)
                st.text_area("التقرير", report, height=300)
                st.download_button("⬇️ تحميل",
                    data=report.encode("utf-8"),
                    file_name=f"تقرير_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain")

    with rp2:
        st.markdown("### ✍️ مسودة اللائحة")
        tmpl = st.selectbox("النوع",["مذكرة دفاع","صحيفة دعوى","عريضة اعتراض","إنذار رسمي"])
        court_n  = st.text_input("المحكمة","محكمة العمل")
        case_n   = st.text_input("رقم القضية","___/___/____")
        client_n = st.text_input("الموكل","")
        oppon_n  = st.text_input("الخصم","")
        facts_n  = st.text_area("الوقائع","",height=100)
        reqs_n   = st.text_area("الطلبات","إلغاء القرار والتعويض",height=100)
        if st.button("✍️ إنشاء المسودة", use_container_width=True):
            date_now = datetime.now().strftime("%d/%m/%Y")
            drafts = {
"مذكرة دفاع": f"""بسم الله الرحمن الرحيم
السيد/ رئيس {court_n} المحترم
الموضوع: مذكرة دفاع — الدعوى رقم ({case_n})
المقدم من: {client_n}  ضد: {oppon_n}

أولاً — الوقائع:
{facts_n}

ثانياً — الطلبات:
{reqs_n}

المقدم: {client_n}
التاريخ: {date_now}""",
"صحيفة دعوى": f"""بسم الله الرحمن الرحيم
السيد/ رئيس {court_n} المحترم
المدعي: {client_n}
المدعى عليه: {oppon_n}
الوقائع: {facts_n}
الطلبات: {reqs_n}
التاريخ: {date_now}""",
"عريضة اعتراض": f"""بسم الله الرحمن الرحيم
المقام الكريم/ رئيس {court_n}
الموضوع: اعتراض على القرار رقم ({case_n})
مقدم من: {client_n}
أسباب الاعتراض: {facts_n}
الطلبات: {reqs_n}
التاريخ: {date_now}""",
"إنذار رسمي": f"""بسم الله الرحمن الرحيم
إلى: {oppon_n}  من: {client_n}
التاريخ: {date_now}
أُنذركم بشأن: {facts_n}
في حال عدم الاستجابة خلال 15 يوماً ستُتَّخذ الإجراءات القانونية.
{reqs_n}""",
            }
            draft = drafts.get(tmpl,"")
            st.text_area("المسودة", draft, height=400)
            st.download_button("⬇️ تحميل",
                data=draft.encode("utf-8"),
                file_name=f"مسودة_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain")

# ── TAB 7: الذاكرة ──────────────────────────
with t_mem:
    st.subheader("🧠 الذاكرة الدائمة")
    with st.expander("➕ إضافة"):
        mt   = st.text_area("النص",height=100,placeholder="مثال: الموكل يعمل منذ 2019")
        mcat = st.selectbox("الفئة",["قضية","موكل","حكم","ملاحظة","استراتيجية","قانون","عام"])
        mtags = st.text_input("وسوم (فاصلة)")
        if st.button("💾 حفظ"):
            if mt.strip():
                tags = [x.strip() for x in mtags.split(",") if x.strip()]
                mid  = mem_add(mt, tags, mcat)
                st.success(f"✅ محفوظ (ID: {mid})")
                st.rerun()

    mq = st.text_input("🔍 بحث")
    q  = mq.lower()
    mems = [m for m in st.session_state.memory
            if not mq or q in m["text"].lower()
            or any(q in t.lower() for t in m.get("tags",[]))]

    st.markdown(f"**{len(mems)} ذاكرة**")
    for m in reversed(mems):
        ec1,ec2,ec3 = st.columns([8,1,1])
        with ec1:
            badges = "".join(f'<span class="badge">{t}</span>' for t in m.get("tags",[]))
            st.markdown(
                f'<div class="mem-card">'
                f'<small style="color:#8090a0">{m.get("ts","")} · {m.get("category","")}</small>'
                f'<br>{m["text"]}<br>{badges}</div>',
                unsafe_allow_html=True)
        with ec2:
            if st.button("✏️",key=f"e_{m['id']}"):
                st.session_state[f"edit_{m['id']}"] = True
        with ec3:
            if st.button("🗑",key=f"d_{m['id']}"):
                mem_del(m["id"]); st.rerun()
        if st.session_state.get(f"edit_{m['id']}"):
            new_t = st.text_area("تعديل",value=m["text"],key=f"et_{m['id']}",height=100)
            if st.button("✅ حفظ",key=f"sv_{m['id']}"):
                mem_edit(m["id"],new_t)
                del st.session_state[f"edit_{m['id']}"]
                st.rerun()

    st.markdown("---")
    ex1,ex2 = st.columns(2)
    with ex1:
        if st.button("📤 تصدير الذاكرة"):
            d = json.dumps(st.session_state.memory, ensure_ascii=False, indent=2)
            st.download_button("⬇️ JSON",d.encode("utf-8"),"memory.json","application/json")
    with ex2:
        mf = st.file_uploader("📥 استيراد",type=["json"],key="mf_up")
        if mf:
            try:
                imported = json.loads(mf.read())
                existing = {m["id"] for m in st.session_state.memory}
                new_ones = [m for m in imported if m.get("id") not in existing]
                st.session_state.memory.extend(new_ones)
                save_memory()
                st.success(f"✅ {len(new_ones)} ذاكرة مستوردة")
            except Exception as e:
                st.error(f"❌ {e}")

# ── TAB 8: القانون ──────────────────────────
with t_law:
    st.subheader("📚 قاعدة الأنظمة السعودية")
    lc1,lc2 = st.columns(2)
    with lc1:
        st.markdown("**➕ إضافة مادة**")
        ma_text = st.text_area("نص المادة",height=100,key="ma_t")
        ma_art  = st.text_input("اسم المادة",key="ma_a")
        ma_law  = st.text_input("اسم النظام",key="ma_l")
        if st.button("➕ إضافة"):
            if ma_text.strip():
                st.session_state.law_db.append({
                    "text":ma_text,"article":ma_art,
                    "law_name":ma_law or "نظام يدوي",
                    "ts":datetime.now().strftime("%Y-%m-%d"),
                })
                save_law()
                st.success("✅")
    with lc2:
        law_import = st.file_uploader("📥 استيراد JSON",type=["json"],key="law_imp")
        if law_import:
            try:
                imported = json.loads(law_import.read())
                st.session_state.law_db.extend(imported)
                save_law()
                st.success(f"✅ {len(imported)} مادة")
            except Exception as e:
                st.error(f"❌ {e}")

    if st.session_state.law_db:
        st.metric("إجمالي المواد", len(st.session_state.law_db))
        law_q = st.text_input("🔍 ابحث")
        if law_q:
            q_words = set(re.findall(r"[\u0600-\u06FF]{3,}", law_q))
            results = sorted(
                [(sum(1 for w in q_words if w in r.get("text","")),r)
                 for r in st.session_state.law_db],
                reverse=True)
            for sc,r in results[:10]:
                if sc > 0:
                    with st.expander(f"📜 {r.get('article','')} — {r.get('law_name','')}"):
                        st.write(r["text"])
                        if st.button("💾 حفظ في الذاكرة",key=f"ls_{hash(r['text'])%99999}"):
                            mem_add(f"[{r.get('law_name','')}] {r['text'][:200]}",
                                   tags=["قانون"],cat="قانون")
                            st.success("✅")

        if st.button("📤 تصدير القانون"):
            d = json.dumps(st.session_state.law_db, ensure_ascii=False, indent=2)
            st.download_button("⬇️ JSON",d.encode("utf-8"),"law_db.json","application/json")

st.markdown('<hr><p style="text-align:center;color:#303848;font-size:11px">Führer v2.0 | سري • دائم • Gemini · Claude · Groq</p>', unsafe_allow_html=True)
