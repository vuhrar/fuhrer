
import streamlit as st
import re, os, json, logging, hashlib, base64
from datetime import datetime
from typing import Dict, List, Any

from utils import _bytes, _norm, new_sid
from storage import (
    load_json, save_json, list_sessions, load_session, save_session, delete_session,
    load_settings, save_settings, DATA_DIR, SESSIONS_DIR, MEMORY_FILE, LAW_FILE, BG_FILE,
    get_law_db_cached
)
from doc_processing import DocIntel, extract_laws_from_pdf, extract_laws_from_docx, extract_laws_from_text, extract_labor_entities
from rules_engine import RULES, eval_rule_v2, apply_rules
from ai_client import AIClient
import config

from forensics import DigitalForensicsAnalyzer
from labor_calculator import LaborCalculator
from sentiment_analyzer import SentimentAnalyzer
from legal_document_generator import LegalDocumentGenerator
from legal_rag_engine import LegalRAGEngine
from ocr_fallback import OCRFallback
from discrepancy_analyzer import DiscrepancyAnalyzer
from procedural_analyzer import ProceduralAnalyzer
from strategy_engine import StrategyEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fuehrer")

st.set_page_config(
    page_title="🦾 Führer  ",
    page_icon="🦾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================
# CSS — تصميم الهامبرغر
# ============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap');
* {
    box-sizing: border-box;
    font-family: 'Cairo', sans-serif;
    direction: rtl;
}
html, body, .stApp {
    background: #f0f2f5;
}
/* زر الهامبرغر */
.hamburger-btn {
    position: fixed;
    top: 12px;
    right: 12px;
    z-index: 999;
    background: #ffffff;
    border: 1px solid #d0d4da;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 1.8rem;
    line-height: 1;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    cursor: pointer;
    transition: all 0.2s;
}
.hamburger-btn:hover {
    background: #f5f7fa;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
/* الشريط الجانبي */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-left: 1px solid #d0d4da;
    box-shadow: -4px 0 20px rgba(0,0,0,0.08);
    padding-top: 1rem;
    min-width: 320px !important;
    max-width: 400px !important;
}
[data-testid="stSidebar"] * {
    color: #1a1a2e !important;
}
/* رأس الصفحة */
.hdr {
    background: linear-gradient(135deg, #ffffff, #f5f7fa);
    border: 1.5px solid #d0d4da;
    border-bottom: 3px solid #d4a820;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 14px;
    direction: rtl;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
}
.hdr h1 {
    font-size: 20px !important;
    color: #1a1a2e !important;
    font-weight: 700;
    margin: 0;
}
.hdr p {
    font-size: 12px !important;
    color: #6a6a8a;
    margin: 3px 0 0;
}
/* لوحة المؤشرات */
.metrics-container {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    justify-content: space-around;
    background: #ffffff;
    border: 1px solid #d0d4da;
    border-radius: 10px;
    padding: 12px 10px;
    margin-bottom: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    direction: rtl;
}
.metric-item {
    text-align: center;
    flex: 1 1 100px;
    min-width: 80px;
}
.metric-item .label {
    font-size: 12px !important;
    color: #6a6a8a;
    font-weight: 600;
}
.metric-item .value {
    font-size: 24px !important;
    font-weight: 700;
    margin-top: 2px;
}
.metric-item .value.green { color: #2e7d32; }
.metric-item .value.red { color: #c62828; }
.metric-item .value.orange { color: #e65100; }
.metric-item .sub {
    font-size: 10px !important;
    color: #9a9aaa;
}
/* التبويبات */
.stTabs [data-baseweb="tab-list"] {
    background: #e0e3e8;
    border-bottom: 2px solid #c0c5cc;
    gap: 3px;
    padding: 4px;
    border-radius: 8px 8px 0 0;
    flex-wrap: wrap;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #5a5a7a !important;
    border: 1px solid transparent !important;
    border-radius: 6px !important;
    padding: 5px 10px !important;
    font-size: 13px !important;
    font-family: 'Cairo', sans-serif;
    white-space: nowrap;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: #ffffff !important;
    color: #1a1a2e !important;
    border-color: #a0a8b5 !important;
    font-weight: 700;
}
.stTabs [data-baseweb="tab-panel"] {
    background: #ffffff;
    border: 1px solid #d0d4da;
    border-radius: 0 0 8px 8px;
    padding: 14px;
}
/* المحادثة */
.chat-user {
    background: #e8f0fe;
    border: 1px solid #c0d0f0;
    border-radius: 12px 12px 2px 12px;
    padding: 10px 14px;
    margin: 6px 0;
    max-width: 82%;
    float: right;
    clear: both;
    direction: rtl;
}
.chat-ai {
    background: #ffffff;
    border: 1px solid #d0d4da;
    border-radius: 12px 12px 12px 2px;
    padding: 10px 14px;
    margin: 6px 0;
    max-width: 88%;
    float: left;
    clear: both;
    direction: rtl;
    border-right: 4px solid #d4a820;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}
.chat-wrap { overflow: hidden; min-height: 60px; }
/* أزرار */
.stButton>button {
    background: linear-gradient(135deg, #d4a820, #f0c040) !important;
    color: #000000 !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
    padding: 8px 14px !important;
    transition: all .2s !important;
}
.stButton>button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(212,168,32,0.4) !important;
}
/* بطاقات */
.result-card {
    background: #f8f9fa;
    border: 1px solid #e0e3e8;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 6px 0;
    direction: rtl;
}
.badge {
    display: inline-block;
    background: #e8f0fe;
    border: 1px solid #a0b8f0;
    color: #1a3a8f;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
    margin: 2px;
}
/* شاشات صغيرة */
@media (max-width: 768px) {
    .hdr h1 { font-size: 17px !important; }
    .metric-item .value { font-size: 20px !important; }
    .stTabs [data-baseweb="tab"] { font-size: 11px !important; padding: 4px 8px !important; }
    [data-testid="stSidebar"] { min-width: 260px !important; }
}
@media (max-width: 480px) {
    .hdr h1 { font-size: 15px !important; }
    .metric-item .value { font-size: 17px !important; }
    .stTabs [data-baseweb="tab"] { font-size: 10px !important; padding: 3px 6px !important; }
}
</style>
""", unsafe_allow_html=True)

# ============================
# تهيئة حالة الجلسة
# ============================
_saved = load_settings()

def _init():
    defs = {
        "memory": load_json(MEMORY_FILE, []),
        "law_db": load_json(LAW_FILE, []),
        "docs": [],
        "pending_q": "",
        "current_sid": None,
        "current_msgs": [],
        "ai_preset": _saved.get("ai_preset", "Gemini 2.0 Flash — مجاني"),
        "ai_key": _saved.get("ai_key", ""),
        "ai_endpoint": _saved.get("ai_endpoint", ""),
        "ai_model": _saved.get("ai_model", ""),
        "ai_format": _saved.get("ai_format", "gemini"),
        "case_type": "قضية عمالية",
        "bg_b64": "",
        "sidebar_open": False,
        "forensics_result": None,
        "calculator_result": None,
        "sentiment_result": None,
        "legal_docs": None,
    }
    for k, v in defs.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if not st.session_state.bg_b64 and os.path.exists(BG_FILE):
        with open(BG_FILE, "r") as f:
            st.session_state.bg_b64 = f.read().strip()
_init()

# ============================
# زر الهامبرغر
# ============================
with st.container():
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("☰", key="hamburger", help="فتح/غلق القائمة"):
            st.session_state.sidebar_open = not st.session_state.sidebar_open
            st.rerun()

# ============================
# القائمة الجانبية (منزلقة)
# ============================
if st.session_state.sidebar_open:
    with st.sidebar:
        st.markdown("### ⚖️ القائمة")
        st.markdown("---")

        # النموذج
        st.markdown("**🤖 النموذج**")
        preset_names = ["Gemini 2.0 Flash — مجاني", "Gemini 1.5 Pro — مجاني",
                        "Groq LLaMA 3.3 — مجاني وسريع", "Claude Sonnet", "OpenAI GPT-4o",
                        "Together AI — مجاني جزئياً", "Ollama محلي", "⚙️ مخصص"]
        preset_name = st.selectbox("النموذج", preset_names,
                                   index=preset_names.index(st.session_state.ai_preset) if st.session_state.ai_preset in preset_names else 0,
                                   label_visibility="collapsed")
        if preset_name != st.session_state.ai_preset:
            st.session_state.ai_preset = preset_name
            save_settings({"ai_preset": st.session_state.ai_preset,
                           "ai_key": st.session_state.ai_key,
                           "ai_endpoint": st.session_state.ai_endpoint,
                           "ai_model": st.session_state.ai_model,
                           "ai_format": st.session_state.ai_format})

        # API Key
        st.markdown("**🔑 API Key**")
        new_key = st.text_input("المفتاح", value=st.session_state.ai_key, type="password",
                                placeholder="AIza... أو sk-...", label_visibility="collapsed")
        if new_key != st.session_state.ai_key:
            st.session_state.ai_key = new_key

        if preset_name == "⚙️ مخصص":
            st.session_state.ai_endpoint = st.text_input("رابط API", value=st.session_state.ai_endpoint)
            st.session_state.ai_model = st.text_input("اسم النموذج", value=st.session_state.ai_model)
            st.session_state.ai_format = st.selectbox("الصيغة", ["openai", "gemini", "anthropic"], index=0)

        st.markdown("---")

        # الجلسات
        st.markdown("**💬 الجلسات**")
        if st.button("➕ جلسة جديدة", use_container_width=True):
            sid = new_sid()
            st.session_state.current_sid = sid
            st.session_state.current_msgs = []
            save_session(sid, {"name": "جلسة جديدة", "messages": []})
            st.rerun()

        for s in list_sessions()[:10]:
            c1, c2 = st.columns([5, 1])
            with c1:
                active = "🟢 " if s["id"] == st.session_state.current_sid else ""
                if st.button(f"{active}{s['name'][:16]} ({s['count']})", key=f"s_{s['id']}", use_container_width=True):
                    data = load_session(s["id"])
                    st.session_state.current_sid = s["id"]
                    st.session_state.current_msgs = data.get("messages", [])
                    st.rerun()
            with c2:
                if st.button("🗑", key=f"ds_{s['id']}"):
                    delete_session(s["id"])
                    if st.session_state.current_sid == s["id"]:
                        st.session_state.current_sid = None
                        st.session_state.current_msgs = []
                    st.rerun()

        st.markdown("---")
        st.markdown("**📋 نوع القضية**")
        st.session_state.case_type = st.selectbox("النوع",
            ["قضية عمالية", "نزاع تجاري", "قضية عقارية", "نزاع إداري", "قضية جنائية", "إفلاس وتصفية"],
            label_visibility="collapsed")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("الذاكرة", len(st.session_state.memory))
        with c2:
            st.metric("الجلسات", len(list_sessions()))
        st.metric("مواد القانون", len(st.session_state.law_db))

# ============================
# رأس الصفحة
# ============================
st.markdown(f"""
<div class="hdr">
<h1 style="margin:0;font-size:20px;color:#1a1a2e">🦾  Führer </h1>
<p style="color:#6a6a8a;margin:3px 0 0;font-size:12px">
متخصص في القانون العمالي السعودي • تحليل الحجية الإلكترونية • حاسبة المستحقات • توليد الدعاوى
</p>
</div>
""", unsafe_allow_html=True)

# ============================
# دوال مساعدة
# ============================
def get_active_preset():
    preset_name = st.session_state.ai_preset
    PRESETS = {
        "Gemini 2.0 Flash — مجاني": {"endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent", "model": "gemini-2.0-flash", "format": "gemini"},
        "Gemini 1.5 Pro — مجاني": {"endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent", "model": "gemini-1.5-pro", "format": "gemini"},
        "Groq LLaMA 3.3 — مجاني وسريع": {"endpoint": "https://api.groq.com/openai/v1/chat/completions", "model": "llama-3.3-70b-versatile", "format": "openai"},
        "Claude Sonnet": {"endpoint": "https://api.anthropic.com/v1/messages", "model": "claude-sonnet-4-6", "format": "anthropic"},
        "OpenAI GPT-4o": {"endpoint": "https://api.openai.com/v1/chat/completions", "model": "gpt-4o", "format": "openai"},
        "Together AI — مجاني جزئياً": {"endpoint": "https://api.together.xyz/v1/chat/completions", "model": "meta-llama/Llama-3-70b-chat-hf", "format": "openai"},
        "Ollama محلي": {"endpoint": "http://localhost:11434/v1/chat/completions", "model": "llama3", "format": "openai"},
        "⚙️ مخصص": {"endpoint": "", "model": "", "format": "openai"},
    }
    if preset_name in PRESETS and preset_name != "⚙️ مخصص":
        p = PRESETS[preset_name]
        return p["endpoint"], p["model"], p["format"]
    return (st.session_state.ai_endpoint, st.session_state.ai_model, st.session_state.ai_format)

def build_system():
    mem_ctx = ""
    if st.session_state.memory:
        mem_ctx = "\n\nالذاكرة:\n" + "\n".join(f"- {m['text'][:150]}" for m in st.session_state.memory[-20:])
    law_ctx = ""
    if st.session_state.law_db and st.session_state.current_msgs:
        last_q = next((m["content"] for m in reversed(st.session_state.current_msgs) if m["role"] == "user"), "")
        if last_q:
            rag = LegalRAGEngine(st.session_state.law_db)
            relevant = rag.retrieve(last_q, context="all", top_k=7)
            if relevant:
                law_ctx = "\n\n📜 **المواد القانونية ذات الصلة:**\n"
                for r in relevant:
                    article = r.get('article', '').strip()
                    law_name = r.get('law_name', '').strip()
                    text_preview = r['text'][:300].replace('\n', ' ')
                    law_ctx += f"• **{law_name}** - {article}: {text_preview}...\n"
    doc_ctx = ""
    if st.session_state.docs:
        doc_ctx = f"\n\n📄 **المستندات:**\n" + "\n".join(st.session_state.docs[:2])[:3000]
    return (config.SYSTEM_PROMPT_TEMPLATE + f"\n\n{mem_ctx}{law_ctx}{doc_ctx}")

def call_ai(prompt: str) -> str:
    endpoint, model, fmt = get_active_preset()
    key = st.session_state.ai_key
    msgs = st.session_state.current_msgs
    if not key:
        return "❌ أدخل API Key في القائمة"
    if not endpoint:
        return "❌ أدخل رابط API"
    system = build_system()
    try:
        client = AIClient(endpoint, model, fmt, key)
        return client.generate(system, msgs + [{"role": "user", "content": prompt}])
    except Exception as e:
        logger.exception("AI call failed")
        return f"❌ خطأ: {str(e)[:200]}"

def mem_add(text, tags=None, cat="عام"):
    m = {"id": hashlib.md5(f"{text}{datetime.now().isoformat()}".encode()).hexdigest()[:8],
         "text": text, "tags": tags or [], "category": cat,
         "ts": datetime.now().strftime("%Y-%m-%d %H:%M")}
    st.session_state.memory.append(m)
    save_json(MEMORY_FILE, st.session_state.memory)
    return m["id"]

def mem_del(mid):
    st.session_state.memory = [m for m in st.session_state.memory if m["id"] != mid]
    save_json(MEMORY_FILE, st.session_state.memory)

# ============================
# لوحة المؤشرات
# ============================
trust_score = 0
win_prob = 0
if st.session_state.get("forensics_result"):
    trust_score = st.session_state.forensics_result.get("overall_trust_score", 0)
if st.session_state.get("calculator_result"):
    win_prob = min(95, trust_score + 10)

st.markdown(f"""
<div class="metrics-container">
    <div class="metric-item">
        <div class="label">🛡️ حجية المستند</div>
        <div class="value {'green' if trust_score >= 80 else 'orange' if trust_score >= 50 else 'red'}">{trust_score}%</div>
        <div class="sub">بناءً على التحليل الإلكتروني</div>
    </div>
    <div class="metric-item">
        <div class="label">⏳ التقادم المتبقي</div>
        <div class="value red">غير محدد</div>
        <div class="sub">قبل سقوط الحق</div>
    </div>
    <div class="metric-item">
        <div class="label">🎯 احتمال الربح</div>
        <div class="value {'green' if win_prob >= 70 else 'orange' if win_prob >= 50 else 'red'}">{win_prob}%</div>
        <div class="sub">تقديري بناءً على الأدلة</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================
# التبويبات
# ============================
tabs = st.tabs(["🤖 المستشار", "📧 الحجية", "💰 الحاسبة", "📊 النبرة", "⚖️ الدعوى", "📚 القانون", "🧠 الذاكرة", "⚙️ الإعدادات"])
t_ai, t_forensics, t_calc, t_sentiment, t_docs, t_law, t_mem, t_settings = tabs

# تبويب المستشار
with t_ai:
    if not st.session_state.current_sid:
        st.markdown("""
        <div style="text-align:center;padding:60px;color:#6a6a8a">
        <h2 style="color:#1a1a2e">👈 ابدأ بجلسة جديدة</h2>
        <p>اضغط "جلسة جديدة" من القائمة (☰)</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        sess = load_session(st.session_state.current_sid)
        new_name = st.text_input("📝 اسم الجلسة", value=sess.get("name", "جلسة"), key="sess_name_inp")
        if new_name != sess.get("name", ""):
            sess["name"] = new_name
            sess["messages"] = st.session_state.current_msgs
            save_session(st.session_state.current_sid, sess)

        cols = st.columns(4)
        for i, (col, q) in enumerate(zip(cols, ["حلل وضعي القانوني", "ما نقاط قوتي؟", "ما المواعيد النظامية؟", "اقترح استراتيجية"])):
            with col:
                if st.button(q, key=f"qp{i}", use_container_width=True):
                    st.session_state.pending_q = q

        st.markdown("---")
        for msg in st.session_state.current_msgs:
            cls = "chat-user" if msg["role"] == "user" else "chat-ai"
            ico = "👤" if msg["role"] == "user" else "⚖️"
            content = msg["content"].replace("\n", "<br>")
            ts = msg.get("ts", "")
            st.markdown(f'<div class="{cls}">{ico} {content}<br><small style="color:#9a9aaa;font-size:10px">⏱ {ts}</small></div>', unsafe_allow_html=True)

        user_inp = st.text_area("سؤالك", value=st.session_state.pending_q, height=100, placeholder="مثال: تأخر راتبي 3 أشهر وأُشعرت بالفصل — ما حقوقي القانونية؟", key="chat_inp")
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            if st.button("📤 إرسال", use_container_width=True) and user_inp.strip():
                st.session_state.pending_q = ""
                ts = datetime.now().strftime("%H:%M")
                st.session_state.current_msgs.append({"role": "user", "content": user_inp, "ts": ts})
                with st.spinner("⚖️ يحلل..."):
                    resp = call_ai(user_inp)
                st.session_state.current_msgs.append({"role": "assistant", "content": resp, "ts": ts})
                sess["messages"] = st.session_state.current_msgs
                save_session(st.session_state.current_sid, sess)
                if len(resp) > 80 and "❌" not in resp:
                    mem_add(f"س: {user_inp[:80]} | ج: {resp[:150]}...", tags=["محادثة", st.session_state.case_type], cat="محادثة")
                st.rerun()
        with col2:
            if st.button("🗑️ مسح", use_container_width=True):
                st.session_state.current_msgs = []
                sess["messages"] = []
                save_session(st.session_state.current_sid, sess)
                st.rerun()
        with col3:
            if st.button("💾 حفظ", use_container_width=True):
                sess["messages"] = st.session_state.current_msgs
                save_session(st.session_state.current_sid, sess)
                st.success("✅")

# تبويب الحجية
with t_forensics:
    st.subheader("📧 محلل الحجية الإلكترونية")
    uploaded = st.file_uploader("ارفع ملفاً للتحليل (PDF, EML, TXT)", type=["pdf", "eml", "msg", "txt"])
    if uploaded and st.button("🔍 تحليل الحجية"):
        raw = _bytes(uploaded)
        ext = uploaded.name.rsplit(".", 1)[-1].lower()
        with st.spinner("جاري تحليل المستند..."):
            analyzer = DigitalForensicsAnalyzer()
            result = analyzer.analyze_document(raw, uploaded.name, ext)
            st.session_state.forensics_result = result
            st.metric("درجة الثقة", f"{result['overall_trust_score']}%")
            st.json(result)
            for rec in result.get("recommendations", []):
                st.markdown(f"- {rec}")

# تبويب الحاسبة
with t_calc:
    st.subheader("💰 حاسبة المستحقات")
    with st.form("calc_form"):
        col1, col2 = st.columns(2)
        with col1:
            basic_salary = st.number_input("الراتب الأساسي", min_value=0.0, value=8000.0, step=500.0)
            total_salary = st.number_input("الراتب الإجمالي", min_value=0.0, value=10000.0, step=500.0)
            service_years = st.number_input("مدة الخدمة (سنوات)", min_value=0.0, value=5.0, step=0.5)
        with col2:
            absence_days = st.number_input("أيام الغياب بدون عذر", min_value=0, value=0)
            salary_delay_months = st.number_input("أشهر تأخير الراتب", min_value=0, value=0)
            is_arbitrary = st.checkbox("فصل تعسفي")
            is_saudi = st.checkbox("موظف سعودي", value=True)
        if st.form_submit_button("💰 احسب"):
            calc = LaborCalculator(basic_salary, total_salary, service_years, absence_days, salary_delay_months, is_arbitrary, is_saudi)
            result = calc.calculate_total_entitlement()
            st.session_state.calculator_result = result
            st.metric("الإجمالي", f"{result['total_gross']:,.2f} ريال")
            st.metric("الصافي", f"{result['total_net']:,.2f} ريال")
            st.json(result)

# تبويب النبرة
with t_sentiment:
    st.subheader("📊 تحليل النبرة")
    uploaded = st.file_uploader("ارفع ملف مراسلات (TXT, PDF)", type=["txt", "pdf", "docx"])
    if uploaded and st.button("📊 تحليل"):
        raw = _bytes(uploaded)
        di = DocIntel()
        text = di.extract(uploaded)
        if text:
            analyzer = SentimentAnalyzer()
            messages = [{"content": line, "sender": "نظام", "ts": datetime.now().strftime("%H:%M")} for line in text.split("\n") if len(line) > 20]
            if messages:
                result = analyzer.analyze_conversation(messages[:20])
                st.session_state.sentiment_result = result
                st.metric("النبرة العامة", result["overall_tone"])
                st.line_chart(result["escalation_curve"])
                for risk in result.get("risks", []):
                    st.warning(risk)

# تبويب الدعوى
with t_docs:
    st.subheader("⚖️ توليد المستندات")
    with st.form("doc_form"):
        col1, col2 = st.columns(2)
        with col1:
            plaintiff = st.text_input("اسم المدعي", value="محمد بن عبد الله")
            plaintiff_id = st.text_input("رقم الهوية", value="1234567890")
            work_location = st.text_input("مكان العمل", value="الرياض")
        with col2:
            defendant = st.text_input("اسم المدعى عليه", value="شركة التقنية المحدودة")
            defendant_id = st.text_input("رقم المنشأة", value="9876543210")
            claim_amount = st.number_input("المبلغ المطلوب", min_value=0.0, value=25000.0, step=1000.0)
        facts = st.text_area("الوقائع", value="بدأت العمل في 1/1/2020\nتم فصلي في 1/1/2024")
        laws = st.text_input("المواد", value="المادة 84, المادة 77")
        if st.form_submit_button("⚖️ توليد"):
            case_data = {
                "plaintiff": plaintiff, "plaintiff_id": plaintiff_id,
                "defendant": defendant, "defendant_id": defendant_id,
                "work_location": work_location, "claim_amount": claim_amount,
                "facts": [f.strip() for f in facts.split("\n") if f.strip()],
                "laws": [l.strip() for l in laws.split(",") if l.strip()],
                "attachments": ["البريد الإلكتروني المؤرخ 1/1/2024", "عقد العمل"]
            }
            generator = LegalDocumentGenerator(case_data)
            docs = {"إنذار": generator.generate_notice(), "صحيفة دعوى": generator.generate_lawsuit()}
            st.session_state.legal_docs = docs
            for title, content in docs.items():
                with st.expander(f"📄 {title}"):
                    st.text_area(f"نص {title}", content, height=200, key=f"doc_{title}")
                    st.download_button(f"⬇️ تحميل {title}", data=content.encode("utf-8"), file_name=f"{title}.txt", mime="text/plain")

# تبويب القانون
with t_law:
    st.subheader("📚 قاعدة الأنظمة")
    st.caption(f"إجمالي المواد: {len(st.session_state.law_db):,}")
    search_term = st.text_input("🔍 بحث")
    if search_term:
        results = [i for i in st.session_state.law_db if search_term.lower() in i.get("text", "").lower() or search_term.lower() in i.get("law_name", "").lower()]
        st.info(f"وجد {len(results)} نتيجة")
        for r in results[:10]:
            with st.expander(f"{r.get('law_name', 'غير معروف')} - {r.get('article', 'مادة')}"):
                st.markdown(r['text'][:500])
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("الأنظمة", len(set(r.get("law_name", "") for r in st.session_state.law_db)))
        with col2:
            st.metric("المواد", len(st.session_state.law_db))

# تبويب الذاكرة
with t_mem:
    st.subheader("🧠 الذاكرة")
    with st.expander("✏️ إضافة"):
        mt = st.text_area("النص", height=100)
        mcat = st.selectbox("الفئة", ["قضية", "موكل", "حكم", "ملاحظة", "استراتيجية", "قانون", "عام"])
        mtags = st.text_input("وسوم")
        if st.button("💾 حفظ") and mt.strip():
            tags = [x.strip() for x in mtags.split(",") if x.strip()]
            mem_add(mt, tags, mcat)
            st.rerun()
    for m in reversed(st.session_state.memory[-20:]):
        st.markdown(f'<div class="result-card"><small>{m.get("ts", "")} · {m.get("category", "")}</small><br>{m["text"][:200]}</div>', unsafe_allow_html=True)

# تبويب الإعدادات
with t_settings:
    st.subheader("⚙️ الإعدادات")
    bg_file = st.file_uploader("صورة الخلفية", type=["png", "jpg", "jpeg"])
    if bg_file:
        b64 = base64.b64encode(_bytes(bg_file)).decode()
        st.session_state.bg_b64 = b64
        with open(BG_FILE, "w") as f:
            f.write(b64)
        st.rerun()
    if st.session_state.bg_b64 and st.button("🗑️ إزالة"):
        st.session_state.bg_b64 = ""
        if os.path.exists(BG_FILE):
            os.remove(BG_FILE)
        st.rerun()
    st.markdown("---")
    if st.button("📦 تصدير"):
        export = {"memory": st.session_state.memory, "law_db": st.session_state.law_db, "exported_at": datetime.now().isoformat()}
        st.download_button("⬇️ تحميل", json.dumps(export, ensure_ascii=False, indent=2).encode("utf-8"), "backup.json", "application/json")
