#  (Führer )
import streamlit as st
import re, os, json, logging, hashlib, base64, io
from datetime import datetime
from typing import Dict, List, Any

# استيرادات الوحدات الأساسية
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

# استيرادات المحركات الجديدة
from forensics import DigitalForensicsAnalyzer
from labor_calculator import LaborCalculator
from sentiment_analyzer import SentimentAnalyzer
from legal_document_generator import LegalDocumentGenerator
from legal_rag_engine import LegalRAGEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fuehrer")

st.set_page_config(
    page_title="⚖️ المستشار العمالي السعودي",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════
# CSS — تصميم حديث مع لوحة المؤشرات
# ══════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap');
* {
    box-sizing: border-box;
    font-family: 'Cairo', sans-serif;
}
html, body, .stApp {
    background: #f0f2f5;
    direction: rtl;
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
[data-testid="stSidebar"] h1, h2, h3 {
    color: #1a1a2e !important;
    font-weight: 700;
}
/* لوحة المؤشرات العلوية */
.metrics-container {
    display: flex;
    gap: 20px;
    justify-content: space-between;
    background: #ffffff;
    border: 1px solid #d0d4da;
    border-radius: 12px;
    padding: 16px 24px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    direction: rtl;
}
.metric-item {
    text-align: center;
    flex: 1;
}
.metric-item .label {
    font-size: 12px;
    color: #6a6a8a;
    font-weight: 600;
}
.metric-item .value {
    font-size: 24px;
    font-weight: 700;
    margin-top: 4px;
}
.metric-item .value.green { color: #2e7d32; }
.metric-item .value.red { color: #c62828; }
.metric-item .value.orange { color: #e65100; }
.metric-item .value.blue { color: #1a3a8f; }
.metric-item .sub {
    font-size: 11px;
    color: #9a9aaa;
}
/* أزرار التبويبات */
.stTabs [data-baseweb="tab-list"] {
    background: #e0e3e8;
    border-bottom: 2px solid #c0c5cc;
    gap: 3px;
    padding: 4px;
    border-radius: 8px 8px 0 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #5a5a7a !important;
    border: 1px solid transparent !important;
    border-radius: 6px !important;
    padding: 7px 14px !important;
    font-size: 13px;
    font-family: 'Cairo', sans-serif;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: #ffffff !important;
    color: #1a1a2e !important;
    border-color: #a0a8b5 !important;
    font-weight: 700;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.stTabs [data-baseweb="tab-panel"] {
    background: #ffffff;
    border: 1px solid #d0d4da;
    border-radius: 0 0 8px 8px;
    padding: 18px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
/* بطاقات النتائج */
.result-card {
    background: #f8f9fa;
    border: 1px solid #e0e3e8;
    border-radius: 8px;
    padding: 16px;
    margin: 8px 0;
    direction: rtl;
}
.result-card h4 {
    margin: 0 0 8px 0;
    color: #1a1a2e;
}
.result-card .success { color: #2e7d32; }
.result-card .danger { color: #c62828; }
.result-card .warning { color: #e65100; }
/* باقي الأنماط */
.chat-user {
    background: #e8f0fe;
    border: 1px solid #c0d0f0;
    border-radius: 12px 12px 2px 12px;
    padding: 12px 16px;
    margin: 8px 0;
    max-width: 82%;
    float: right;
    clear: both;
    direction: rtl;
    color: #1a1a2e;
}
.chat-ai {
    background: #ffffff;
    border: 1px solid #d0d4da;
    border-radius: 12px 12px 12px 2px;
    padding: 12px 16px;
    margin: 8px 0;
    max-width: 88%;
    float: left;
    clear: both;
    direction: rtl;
    border-right: 4px solid #d4a820;
    color: #1a1a2e;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}
.chat-wrap { overflow: hidden; min-height: 60px; }
.hdr {
    background: linear-gradient(135deg, #ffffff, #f5f7fa);
    border: 1.5px solid #d0d4da;
    border-bottom: 3px solid #d4a820;
    border-radius: 8px;
    padding: 18px 24px;
    margin-bottom: 16px;
    direction: rtl;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
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
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# تهيئة حالة الجلسة
# ══════════════════════════════════════════════
_saved = load_settings()

def _init():
    defs = {
        "memory":       load_json(MEMORY_FILE, []),
        "law_db":       load_json(LAW_FILE, []),
        "docs":         [],
        "pending_q":    "",
        "current_sid":  None,
        "current_msgs": [],
        "ai_preset":    _saved.get("ai_preset", "Gemini 2.0 Flash — مجاني"),
        "ai_key":       _saved.get("ai_key", ""),
        "ai_endpoint":  _saved.get("ai_endpoint", ""),
        "ai_model":     _saved.get("ai_model", ""),
        "ai_format":    _saved.get("ai_format", "gemini"),
        "case_type":    "قضية عمالية",
        "bg_b64":       "",
        "sidebar_open": False,
        # متغيرات جديدة للمخرجات
        "forensics_result": None,
        "calculator_result": None,
        "sentiment_result": None,
        "legal_docs": None,
        "uploaded_files": [],
    }
    for k, v in defs.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if not st.session_state.bg_b64 and os.path.exists(BG_FILE):
        with open(BG_FILE, "r") as f:
            st.session_state.bg_b64 = f.read().strip()

_init()

if st.session_state.bg_b64:
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{st.session_state.bg_b64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .stApp::before {{
        content: '';
        position: fixed;
        top:0; left:0; right:0; bottom:0;
        background: rgba(240,242,245,0.88);
        z-index: 0;
        pointer-events: none;
    }}
    </style>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# دوال مساعدة
# ══════════════════════════════════════════════
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
        "⚙️ مخصص — أدخل يدوياً": {"endpoint": "", "model": "", "format": "openai"},
    }
    if preset_name in PRESETS and preset_name != "⚙️ مخصص — أدخل يدوياً":
        p = PRESETS[preset_name]
        return p["endpoint"], p["model"], p["format"]
    return (st.session_state.ai_endpoint, st.session_state.ai_model, st.session_state.ai_format)

def build_system():
    """بناء سياق النظام باستخدام محرك الاسترجاع الذكي"""
    mem_ctx = ""
    if st.session_state.memory:
        mem_ctx = "\n\nالذاكرة:\n" + "\n".join(f"- {m['text'][:150]}" for m in st.session_state.memory[-20:])

    law_ctx = ""
    if st.session_state.law_db and st.session_state.current_msgs:
        last_q = next((m["content"] for m in reversed(st.session_state.current_msgs) if m["role"] == "user"), "")
        if last_q:
            # استخدام محرك الاسترجاع الذكي
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

    return (config.SYSTEM_PROMPT_TEMPLATE +
            f"\n\n{mem_ctx}{law_ctx}{doc_ctx}")

def call_ai(prompt: str) -> str:
    endpoint, model, fmt = get_active_preset()
    key = st.session_state.ai_key
    msgs = st.session_state.current_msgs
    if not key:
        return "❌ أدخل API Key في الإعدادات"
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

def mem_edit(mid, new_text):
    for m in st.session_state.memory:
        if m["id"] == mid:
            m["text"] = new_text
            m["ts"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            break
    save_json(MEMORY_FILE, st.session_state.memory)

# ══════════════════════════════════════════════
# SIDEBAR — الإعدادات والجلسات
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚖️ المستشار العمالي السعودي")
    st.markdown("---")

    st.markdown("**🤖 نموذج الذكاء الاصطناعي**")
    preset_names = ["Gemini 2.0 Flash — مجاني", "Gemini 1.5 Pro — مجاني", "Groq LLaMA 3.3 — مجاني وسريع", "Claude Sonnet", "OpenAI GPT-4o", "Together AI — مجاني جزئياً", "Ollama محلي", "⚙️ مخصص — أدخل يدوياً"]
    preset_name = st.selectbox("النموذج", preset_names, index=preset_names.index(st.session_state.ai_preset) if st.session_state.ai_preset in preset_names else 0, label_visibility="collapsed")
    if preset_name != st.session_state.ai_preset:
        st.session_state.ai_preset = preset_name
        save_settings({"ai_preset": st.session_state.ai_preset, "ai_key": st.session_state.ai_key, "ai_endpoint": st.session_state.ai_endpoint, "ai_model": st.session_state.ai_model, "ai_format": st.session_state.ai_format})

    st.markdown("**🔑 API Key**")
    new_key = st.text_input("key", value=st.session_state.ai_key, type="password", placeholder="AIza... أو sk-...", label_visibility="collapsed")
    if new_key != st.session_state.ai_key:
        st.session_state.ai_key = new_key

    if preset_name == "⚙️ مخصص — أدخل يدوياً":
        st.session_state.ai_endpoint = st.text_input("رابط API", value=st.session_state.ai_endpoint)
        st.session_state.ai_model = st.text_input("اسم النموذج", value=st.session_state.ai_model)
        st.session_state.ai_format = st.selectbox("صيغة API", ["openai", "gemini", "anthropic"], index=0)

    st.markdown("---")
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
    st.session_state.case_type = st.selectbox("النوع", ["قضية عمالية", "نزاع تجاري", "قضية عقارية", "نزاع إداري", "قضية جنائية", "إفلاس وتصفية"], label_visibility="collapsed")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("الذاكرة", len(st.session_state.memory))
    with c2:
        st.metric("الجلسات", len(list_sessions()))
    st.metric("مواد القانون", len(st.session_state.law_db))

# ══════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════
st.markdown(f"""
<div class="hdr">
<h1 style="margin:0;font-size:24px;color:#1a1a2e">⚖️ المستشار العمالي السعودي — Führer v3.0</h1>
<p style="color:#6a6a8a;margin:4px 0 0;font-size:12px">
متخصص في القانون العمالي السعودي • تحليل الحجية الإلكترونية • حاسبة المستحقات • توليد الدعاوى
</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# لوحة المؤشرات العلوية (تعتمد على تحليل المستندات)
# ══════════════════════════════════════════════
def render_metrics():
    """عرض لوحة المؤشرات العلوية"""
    trust_score = 0
    days_left = "غير محدد"
    win_prob = 0

    if st.session_state.get("forensics_result"):
        trust_score = st.session_state.forensics_result.get("overall_trust_score", 0)
    if st.session_state.get("calculator_result"):
        # تقدير احتمال الربح بناءً على صحة المستندات وقوة القضية
        win_prob = min(95, trust_score + 10)

    # تقدير أيام التقادم (محاكاة)
    days_left = "٤٥ يوم" if trust_score > 50 else "١٢٠ يوم"

    st.markdown(f"""
    <div class="metrics-container">
        <div class="metric-item">
            <div class="label">🛡️ حجية المستند</div>
            <div class="value {'green' if trust_score >= 80 else 'orange' if trust_score >= 50 else 'red'}">{trust_score}%</div>
            <div class="sub">بناءً على التحليل الإلكتروني</div>
        </div>
        <div class="metric-item">
            <div class="label">⏳ التقادم المتبقي</div>
            <div class="value red">{days_left}</div>
            <div class="sub">قبل سقوط الحق</div>
        </div>
        <div class="metric-item">
            <div class="label">🎯 احتمال الربح</div>
            <div class="value {'green' if win_prob >= 70 else 'orange' if win_prob >= 50 else 'red'}">{win_prob}%</div>
            <div class="sub">تقديري بناءً على الأدلة</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TABS — التبويبات الجديدة
# ══════════════════════════════════════════════
tabs = st.tabs(["🤖 المستشار", "📧 محلل الحجية", "💰 حاسبة المستحقات", "📊 تحليل النبرة", "⚖️ توليد الدعوى", "📚 القانون", "🧠 الذاكرة", "⚙️ الإعدادات"])
t_ai, t_forensics, t_calc, t_sentiment, t_docs, t_law, t_mem, t_settings = tabs

# ── TAB 1: المستشار العمالي ──────────────────
with t_ai:
    render_metrics()
    if not st.session_state.current_sid:
        st.markdown("""
        <div style="text-align:center;padding:60px;color:#6a6a8a">
        <h2 style="color:#1a1a2e">👈 ابدأ بجلسة جديدة</h2>
        <p>اضغط "جلسة جديدة" من الشريط الجانبي</p>
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
        st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
        for msg in st.session_state.current_msgs:
            cls = "chat-user" if msg["role"] == "user" else "chat-ai"
            ico = "👤" if msg["role"] == "user" else "⚖️"
            content = msg["content"].replace("\n", "<br>")
            ts = msg.get("ts", "")
            st.markdown(f'<div class="{cls}">{ico} {content}<br><small style="color:#9a9aaa;font-size:10px">⏱ {ts}</small></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")

        user_inp = st.text_area("سؤالك", value=st.session_state.pending_q, height=100, placeholder="مثال: تأخر راتبي 3 أشهر وأُشعرت بالفصل — ما حقوقي القانونية؟", key="chat_inp")

        bc1, bc2, bc3 = st.columns([3, 1, 1])
        with bc1:
            send_btn = st.button("📤 إرسال", use_container_width=True)
        with bc2:
            if st.button("🗑️ مسح", use_container_width=True):
                st.session_state.current_msgs = []
                sess["messages"] = []
                save_session(st.session_state.current_sid, sess)
                st.rerun()
        with bc3:
            if st.button("💾 حفظ", use_container_width=True):
                sess["messages"] = st.session_state.current_msgs
                save_session(st.session_state.current_sid, sess)
                st.success("✅")

        if send_btn and user_inp.strip():
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

# ── TAB 2: محلل الحجية ──────────────────────
with t_forensics:
    st.subheader("📧 محلل الحجية الإلكترونية")
    st.caption("تحليل سلامة المستندات، التوقيعات الإلكترونية، ورؤوس البريد الإلكتروني")
    uploaded = st.file_uploader("ارفع ملفاً للتحليل (PDF, EML, MSG, TXT)", type=["pdf", "eml", "msg", "txt"], accept_multiple_files=False)
    if uploaded:
        raw = _bytes(uploaded)
        ext = uploaded.name.rsplit(".", 1)[-1].lower()
        if st.button("🔍 تحليل الحجية"):
            with st.spinner("جاري تحليل المستند..."):
                analyzer = DigitalForensicsAnalyzer()
                result = analyzer.analyze_document(raw, uploaded.name, ext)
                st.session_state.forensics_result = result

                st.markdown("### 📋 تقرير الحجية")
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.metric("درجة الثقة", f"{result['overall_trust_score']}%")
                    st.metric("سلامة الملف", result["integrity"]["status"])
                with col2:
                    st.metric("التوقيع الإلكتروني", result["signature"]["status"])
                    if result["email_headers"]["is_email"]:
                        st.metric("مصدر البريد", result["email_headers"]["status"])

                st.markdown("### 🔍 التفاصيل")
                st.json(result)

                st.markdown("### 📜 المراجع القانونية")
                for ref in result.get("legal_references", []):
                    st.markdown(f"- {ref}")

                st.markdown("### ✅ التوصيات")
                for rec in result.get("recommendations", []):
                    st.markdown(f"- {rec}")

# ── TAB 3: حاسبة المستحقات ──────────────────
with t_calc:
    st.subheader("💰 حاسبة المستحقات العمالية")
    st.caption("حساب المكافأة، التعويض، والمتأخرات وفق نظام العمل")
    with st.form("calc_form"):
        col1, col2 = st.columns(2)
        with col1:
            basic_salary = st.number_input("الراتب الأساسي (ريال)", min_value=0.0, value=8000.0, step=500.0)
            total_salary = st.number_input("الراتب الإجمالي (ريال)", min_value=0.0, value=10000.0, step=500.0)
            service_years = st.number_input("مدة الخدمة (سنوات)", min_value=0.0, value=5.0, step=0.5)
        with col2:
            absence_days = st.number_input("أيام الغياب بدون عذر", min_value=0, value=0)
            salary_delay_months = st.number_input("أشهر تأخير الراتب", min_value=0, value=0)
            is_arbitrary = st.checkbox("فصل تعسفي")
            is_saudi = st.checkbox("موظف سعودي (لتطبيق خصم التأمينات)", value=True)

        submitted = st.form_submit_button("💰 احسب المستحقات")
        if submitted:
            calc = LaborCalculator(
                basic_salary=basic_salary,
                total_salary=total_salary,
                service_years=service_years,
                absence_days=absence_days,
                salary_delay_months=salary_delay_months,
                is_arbitrary_dismissal=is_arbitrary,
                is_saudi=is_saudi
            )
            result = calc.calculate_total_entitlement()
            st.session_state.calculator_result = result

            st.markdown("### 📊 نتيجة الحساب")
            st.metric("إجمالي المستحقات (الإجمالي)", f"{result['total_gross']:,.2f} ريال")
            st.metric("إجمالي المستحقات (الصافي بعد التأمينات)", f"{result['total_net']:,.2f} ريال")

            with st.expander("📋 تفاصيل الحساب"):
                st.json(result)

# ── TAB 4: تحليل النبرة ─────────────────────
with t_sentiment:
    st.subheader("📊 تحليل النبرة والتصعيد")
    st.caption("تصنيف الرسائل، كشف التهديدات والإقرارات، وتحليل نبرة المستخدم")
    uploaded = st.file_uploader("ارفع ملف مراسلات (TXT, PDF, DOCX)", type=["txt", "pdf", "docx"], accept_multiple_files=False)
    if uploaded:
        raw = _bytes(uploaded)
        ext = uploaded.name.rsplit(".", 1)[-1].lower()
        di = DocIntel()
        text = di.extract(uploaded)
        if text:
            if st.button("📊 تحليل النبرة"):
                analyzer = SentimentAnalyzer()
                # محاكاة رسائل من النص
                messages = [{"content": line, "sender": "نظام", "ts": datetime.now().strftime("%H:%M")} for line in text.split("\n") if len(line) > 20]
                if messages:
                    result = analyzer.analyze_conversation(messages[:20])
                    st.session_state.sentiment_result = result

                    st.markdown("### 📋 ملخص التحليل")
                    st.metric("عدد الرسائل", len(result["messages"]))
                    st.metric("النبرة العامة", result["overall_tone"])

                    st.markdown("### 📈 منحنى التصعيد")
                    st.line_chart(result["escalation_curve"])

                    st.markdown("### 🔍 تفاصيل الرسائل")
                    for msg in result["messages"][:10]:
                        st.markdown(f"""
                        <div class="result-card">
                        <strong>{msg.get('sender', 'غير معروف')}</strong> — {msg.get('message_type', 'عام')}
                        <br><small>{msg.get('key_phrases', [''])[0][:100] if msg.get('key_phrases') else '...'}</small>
                        </div>
                        """, unsafe_allow_html=True)

                    if result.get("risks"):
                        st.markdown("### ⚠️ المخاطر المكتشفة")
                        for risk in result["risks"]:
                            st.warning(risk)

# ── TAB 5: توليد الدعوى ─────────────────────
with t_docs:
    st.subheader("⚖️ توليد المستندات القانونية")
    st.caption("إنشاء إنذار رسمي، صحيفة دعوى، ومذكرة قانونية")
    with st.form("doc_form"):
        col1, col2 = st.columns(2)
        with col1:
            plaintiff = st.text_input("اسم المدعي (الموظف)", value="محمد بن عبد الله")
            plaintiff_id = st.text_input("رقم الهوية", value="1234567890")
            work_location = st.text_input("مكان العمل", value="الرياض")
        with col2:
            defendant = st.text_input("اسم المدعى عليه (صاحب العمل)", value="شركة التقنية المحدودة")
            defendant_id = st.text_input("رقم المنشأة", value="9876543210")
            claim_amount = st.number_input("المبلغ المطلوب (ريال)", min_value=0.0, value=25000.0, step=1000.0)

        facts = st.text_area("الوقائع (سطر واحد لكل واقعة)", value="بدأت العمل في 1/1/2020\nتم فصلي في 1/1/2024\nلم يتم صرف المكافأة")
        laws = st.text_input("المواد النظامية المستندة", value="المادة 84, المادة 77, المادة 81")

        submitted = st.form_submit_button("⚖️ توليد المستندات")
        if submitted:
            case_data = {
                "plaintiff": plaintiff,
                "plaintiff_id": plaintiff_id,
                "defendant": defendant,
                "defendant_id": defendant_id,
                "work_location": work_location,
                "claim_amount": claim_amount,
                "facts": [f.strip() for f in facts.split("\n") if f.strip()],
                "laws": [l.strip() for l in laws.split(",") if l.strip()],
                "attachments": ["البريد الإلكتروني المؤرخ 1/1/2024", "عقد العمل", "كشف الراتب"]
            }
            generator = LegalDocumentGenerator(case_data)
            docs = {
                "إنذار رسمي": generator.generate_notice(),
                "صحيفة دعوى": generator.generate_lawsuit(),
                "مذكرة قانونية": generator.generate_legal_memo()
            }
            st.session_state.legal_docs = docs

            for title, content in docs.items():
                with st.expander(f"📄 {title}"):
                    st.text_area(f"نص {title}", content, height=300, key=f"doc_{title}")
                    st.download_button(f"⬇️ تحميل {title}", data=content.encode("utf-8"), file_name=f"{title}.txt", mime="text/plain")

# ── TAB 6: القانون ──────────────────────────
with t_law:
    st.subheader("📚 قاعدة الأنظمة السعودية")
    st.caption(f"إجمالي المواد: {len(st.session_state.law_db):,} مادة")
    search_term = st.text_input("🔍 بحث في المواد القانونية")
    if search_term:
        results = []
        for item in st.session_state.law_db:
            if search_term.lower() in item.get("text", "").lower() or search_term.lower() in item.get("law_name", "").lower():
                results.append(item)
        st.info(f"وجد {len(results)} نتيجة")
        for r in results[:10]:
            with st.expander(f"{r.get('law_name', 'غير معروف')} - {r.get('article', 'مادة')}"):
                st.markdown(f"**النص:** {r['text'][:500]}...")
                st.caption(f"المصدر: {r.get('source', 'غير معروف')}")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("عدد الأنظمة", len(set(r.get("law_name", "") for r in st.session_state.law_db)))
        with col2:
            st.metric("عدد المواد", len(st.session_state.law_db))
        with col3:
            st.metric("آخر تحديث", st.session_state.law_db[-1].get("ts", "غير معروف") if st.session_state.law_db else "لا يوجد")

    # رفع ملفات قانونية جديدة
    law_file = st.file_uploader("ارفع ملفاً قانونياً (PDF, DOCX, TXT, JSON)", type=["pdf", "docx", "txt", "json"], key="law_up")
    if law_file and st.button("📥 استخراج وإضافة"):
        raw = _bytes(law_file)
        ext = law_file.name.rsplit(".", 1)[-1].lower()
        with st.spinner("جاري الاستخراج..."):
            if ext == "pdf":
                records = extract_laws_from_pdf(raw, law_file.name)
            elif ext == "docx":
                records = extract_laws_from_docx(raw, law_file.name)
            elif ext == "json":
                try:
                    records = json.loads(raw.decode("utf-8", errors="ignore"))
                    if not isinstance(records, list):
                        records = []
                except:
                    records = []
            else:
                records = extract_laws_from_text(raw.decode("utf-8", errors="ignore"), law_file.name)
        if records:
            st.session_state.law_db.extend(records)
            save_json(LAW_FILE, st.session_state.law_db)
            st.success(f"✅ {len(records)} مادة أُضيفت")

# ── TAB 7: الذاكرة ──────────────────────────
with t_mem:
    st.subheader("🧠 الذاكرة الدائمة")
    with st.expander("✏️ إضافة يدوية"):
        mt = st.text_area("النص", height=100)
        mcat = st.selectbox("الفئة", ["قضية", "موكل", "حكم", "ملاحظة", "استراتيجية", "قانون", "عام"])
        mtags = st.text_input("وسوم (فاصلة)")
        if st.button("💾 حفظ"):
            if mt.strip():
                tags = [x.strip() for x in mtags.split(",") if x.strip()]
                mem_add(mt, tags, mcat)
                st.rerun()

    mq = st.text_input("🔍 بحث")
    q = mq.lower()
    mems = [m for m in st.session_state.memory if not mq or q in m["text"].lower() or any(q in t.lower() for t in m.get("tags", []))]
    st.markdown(f"**{len(mems)} ذاكرة**")
    for m in reversed(mems):
        ec1, ec2, ec3 = st.columns([8, 1, 1])
        with ec1:
            badges = "".join(f'<span class="badge">{t}</span>' for t in m.get("tags", []))
            st.markdown(f'<div class="result-card"><small style="color:#9a9aaa">{m.get("ts", "")} · {m.get("category", "")}</small><br>{m["text"][:200]}<br>{badges}</div>', unsafe_allow_html=True)
        with ec2:
            if st.button("✏️", key=f"e_{m['id']}"):
                st.session_state[f"edit_{m['id']}"] = True
        with ec3:
            if st.button("🗑", key=f"d_{m['id']}"):
                mem_del(m["id"])
                st.rerun()
        if st.session_state.get(f"edit_{m['id']}"):
            new_t = st.text_area("تعديل", value=m["text"], key=f"et_{m['id']}", height=100)
            if st.button("✅ حفظ", key=f"sv_{m['id']}"):
                mem_edit(m["id"], new_t)
                del st.session_state[f"edit_{m['id']}"]
                st.rerun()

# ── TAB 8: الإعدادات ────────────────────────
with t_settings:
    st.subheader("⚙️ الإعدادات")
    st.markdown("### 🖼️ صورة الخلفية")
    bg_file = st.file_uploader("ارفع صورة الخلفية", type=["png", "jpg", "jpeg"], key="bg_up")
    if bg_file:
        raw = _bytes(bg_file)
        b64 = base64.b64encode(raw).decode()
        st.session_state.bg_b64 = b64
        with open(BG_FILE, "w") as f:
            f.write(b64)
        st.rerun()
    if st.session_state.bg_b64:
        if st.button("🗑️ إزالة الخلفية"):
            st.session_state.bg_b64 = ""
            if os.path.exists(BG_FILE):
                os.remove(BG_FILE)
            st.rerun()

    st.markdown("---")
    st.markdown("### 📦 تصدير كامل")
    if st.button("📦 تصدير الأرشيف", use_container_width=True):
        export = {"memory": st.session_state.memory, "law_db": st.session_state.law_db, "exported_at": datetime.now().isoformat(), "version": "3.0"}
        d = json.dumps(export, ensure_ascii=False, indent=2)
        st.download_button("⬇️ تحميل", d.encode("utf-8"), f"fuehrer_backup_{datetime.now().strftime('%Y%m%d')}.json", "application/json")

    st.markdown("---")
    st.markdown("### ℹ️ معلومات")
    st.markdown(f"""
    | | |
    |--|--|
    | النموذج | {st.session_state.ai_preset} |
    | الذاكرة | {len(st.session_state.memory)} سجل |
    | القانون | {len(st.session_state.law_db)} مادة |
    | الجلسات | {len(list_sessions())} |
    """)

st.markdown('<hr><p style="text-align:center;color:#9a9aaa;font-size:11px">Führer v3.0 — منصة المستشار العمالي السعودي المتكامل</p>', unsafe_allow_html=True)
