# Führer🦾
import streamlit as st
import re, os, json, logging, hashlib, base64
from datetime import datetime

from utils import _bytes, _norm, new_sid
from storage import (
    load_json, save_json, list_sessions, load_session, save_session, delete_session,
    load_settings, save_settings, DATA_DIR, SESSIONS_DIR, MEMORY_FILE, LAW_FILE, BG_FILE
)
from doc_processing import DocIntel, extract_laws_from_pdf, extract_laws_from_docx, extract_laws_from_text
from rules_engine import RULES, apply_rules
from ai_client import AIClient
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fuehrer")

st.set_page_config(
    page_title="Führer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ========== CSS النهائي ==========
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800;900&display=swap');

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Cairo', sans-serif;
    direction: rtl;
}
html, body, .stApp {
    background: #f0f2f5 !important;
}

[data-testid="stSidebar"],
[data-testid="stSidebarNav"] {
    display: none !important;
}

.hdr {
    background: #2c2c3e;
    border-bottom: 3px solid rgb(212, 168, 32);
    padding: 28px 32px;
    margin-bottom: 28px;
    text-align: center;
    border-radius: 0 0 16px 16px;
}
.hdr h1 {
    font-size: 52px !important;
    font-weight: 900 !important;
    color: #ffffff !important;
    letter-spacing: 6px;
    margin: 0;
    text-transform: uppercase;
}
.hdr h1::after {
    content: '';
    display: block;
    width: 80px;
    height: 4px;
    background: rgb(212, 168, 32);
    margin: 12px auto 0;
    border-radius: 2px;
}

.stTabs [data-baseweb="tab-list"] {
    background: #ffffff;
    border-bottom: 2px solid #e0e0e0;
    gap: 8px;
    padding: 10px 16px;
    border-radius: 12px 12px 0 0;
    flex-wrap: wrap;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #555555 !important;
    border: 1.5px solid transparent !important;
    border-radius: 8px !important;
    padding: 10px 22px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    white-space: nowrap;
}
.stTabs [data-baseweb="tab"]:hover {
    background: rgba(212, 168, 32, 0.06) !important;
    color: rgb(212, 168, 32) !important;
    border-color: rgb(212, 168, 32) !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: #2c2c3e !important;
    color: #ffffff !important;
    border-color: rgb(212, 168, 32) !important;
    font-weight: 700 !important;
}
.stTabs [data-baseweb="tab-panel"] {
    background: #ffffff;
    border: 1px solid #e8e8e8;
    border-radius: 0 0 14px 14px;
    padding: 28px 32px;
}

.stButton button {
    background: #2c2c3e !important;
    color: #ffffff !important;
    border: 1.5px solid rgb(212, 168, 32) !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    padding: 12px 28px !important;
    font-size: 15px !important;
    transition: all 0.3s ease !important;
}
.stButton button:hover {
    background: rgb(212, 168, 32) !important;
    color: #1a1a2e !important;
    border-color: rgb(212, 168, 32) !important;
}

.stTextInput input,
.stTextArea textarea,
.stSelectbox select {
    background: #fafafa !important;
    color: #1a1a2e !important;
    border: 1.5px solid #d0d0d0 !important;
    border-radius: 8px !important;
    font-size: 15px !important;
    padding: 14px 18px !important;
}
.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: rgb(212, 168, 32) !important;
}

[data-testid="stFileUploader"] {
    background: #fafafa !important;
    border: 2px dashed rgb(212, 168, 32) !important;
    border-radius: 12px !important;
    padding: 32px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgb(196, 154, 26) !important;
}

.chat-user {
    background: #2c2c3e;
    border: 1px solid rgb(212, 168, 32);
    border-radius: 16px 16px 2px 16px;
    padding: 16px 20px;
    margin: 12px 0;
    max-width: 78%;
    float: right;
    clear: both;
    color: #ffffff !important;
    font-size: 15px;
    line-height: 1.7;
}
.chat-ai {
    background: #ffffff;
    border: 1px solid #e8e8e8;
    border-radius: 16px 16px 16px 2px;
    padding: 16px 20px;
    margin: 12px 0;
    max-width: 84%;
    float: left;
    clear: both;
    border-right: 4px solid rgb(212, 168, 32);
    color: #1a1a2e;
    font-size: 15px;
    line-height: 1.7;
}

.result-card {
    background: #f8f9fa;
    border: 1px solid #e8e8e8;
    border-radius: 10px;
    padding: 18px 22px;
    margin: 10px 0;
    border-right: 4px solid rgb(212, 168, 32);
}

.badge {
    display: inline-block;
    background: #f0f1f3;
    border: 1px solid rgb(212, 168, 32);
    color: #1a1a2e;
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 700;
    margin: 3px 2px;
}

.metric-card {
    background: #ffffff;
    border: 1px solid #e8e8e8;
    border-radius: 10px;
    padding: 18px 22px;
    text-align: center;
    border-top: 3px solid rgb(212, 168, 32);
}
.metric-card .label {
    font-size: 13px;
    color: #777777;
    font-weight: 600;
}
.metric-card .value {
    font-size: 30px;
    font-weight: 800;
    color: #2c2c3e;
    margin-top: 4px;
}

@media (max-width: 768px) {
    .hdr h1 { font-size: 34px !important; }
    .stTabs [data-baseweb="tab"] { font-size: 13px !important; padding: 8px 14px !important; }
    .stTabs [data-baseweb="tab-panel"] { padding: 18px 16px; }
}
@media (max-width: 480px) {
    .hdr h1 { font-size: 26px !important; }
    .stTabs [data-baseweb="tab"] { font-size: 11px !important; padding: 6px 10px !important; }
    .stTabs [data-baseweb="tab-panel"] { padding: 14px 12px; }
}
</style>
""", unsafe_allow_html=True)

# ==================== التهيئة ====================
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
        "uploaded_texts": [],
        "analysis_result": None,
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
        background: rgba(240,242,245,0.92);
        z-index: 0;
        pointer-events: none;
    }}
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="hdr">
<h1>Führer</h1>
</div>
""", unsafe_allow_html=True)

# ==================== دوال مساعدة ====================
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
    doc_ctx = ""
    if st.session_state.docs:
        doc_ctx = f"\n\nالمستندات:\n" + "\n".join(st.session_state.docs[:3])[:3000]
    return (config.SYSTEM_PROMPT_TEMPLATE + f"\n\n{mem_ctx}{doc_ctx}")

def call_ai(prompt: str) -> str:
    endpoint, model, fmt = get_active_preset()
    key = st.session_state.ai_key
    msgs = st.session_state.current_msgs
    if not key:
        return "❌ أدخل API Key في الإعدادات"
    if not endpoint:
        return "❌ أدخل رابط API في الإعدادات"
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

def extract_entities(text: str) -> dict:
    return {
        "employee_name": re.search(r'(?:الموظف|السيد)\s*([\u0600-\u06ff\s]{2,30})', text),
        "employer_name": re.search(r'(?:صاحب العمل|الشركة)\s*([\u0600-\u06ff\s]{2,30})', text),
        "basic_salary": re.search(r'(?:الراتب الأساسي|الأساسي)\s*[:]?\s*([\d,]+)', text),
        "total_salary": re.search(r'(?:الراتب الإجمالي|الإجمالي)\s*[:]?\s*([\d,]+)', text),
        "service_years": re.search(r'(\d+\.?\d*)\s*(?:سنوات|سنة)', text),
        "termination_date": re.search(r'(?:فصل|إنهاء|تاريخ الفصل)\s*[:]?\s*(\d{1,2}/\d{1,2}/\d{2,4})', text),
        "mentioned_articles": re.findall(r'المادة\s*([\u0660-\u0669\d]+)', text),
    }

def generate_analysis(text: str) -> dict:
    extracted = extract_entities(text)
    return {
        "extracted": extracted,
        "has_investigation": "تحقيق" in text or "استجواب" in text,
        "has_warning": "إنذار" in text or "تنبيه" in text,
        "has_termination_letter": "فصل" in text or "إنهاء" in text,
        "has_threat": "تهديد" in text or "عقاب" in text,
        "has_acknowledgment": "أقر" in text or "اعترف" in text,
        "is_arbitrary": ("فصل" in text) and ("تحقيق" not in text),
        "risk_level": "مرتفعة" if ("فصل" in text and "تحقيق" not in text) else "متوسطة",
        "strength_score": 70 if ("فصل" in text and "تحقيق" not in text) else 50,
    }

def calculate_eosb(basic_salary, service_years, absence_days=0):
    years_5 = min(service_years, 5)
    years_after = max(0, service_years - 5)
    total = (basic_salary / 2) * years_5 + basic_salary * years_after
    deduction = (basic_salary / 30) * max(0, absence_days - 15)
    return round(total - deduction, 2)

def calculate_compensation(total_salary, service_years):
    months = min(12, max(3, int(service_years * 0.8)))
    return round(total_salary * months, 2)

def calculate_total(bs, ts, sy, absence=0, delay=0, is_arbitrary=False):
    eosb = calculate_eosb(bs, sy, absence)
    comp = calculate_compensation(ts, sy) if is_arbitrary else 0
    delay_comp = ts * 0.05 * delay
    total = eosb + comp + delay_comp
    gosi = ts * 0.09
    return {
        "eosb": eosb,
        "compensation": comp,
        "delay_comp": delay_comp,
        "gosi": gosi,
        "total_gross": round(total, 2),
        "total_net": round(total - gosi, 2)
    }

# ==================== التبويبات ====================
tabs = st.tabs(["💬 المستشار", "📄 الملفات", "📋 التدقيق", "⚖️ الدعوى", "📚 القانون", "🧠 الذاكرة", "⚙️ الإعدادات"])
t_ai, t_files, t_audit, t_docs, t_law, t_mem, t_settings = tabs

# ------ 1. المستشار (الدردشة) ------
with t_ai:
    st.subheader("💬 المستشار العمالي")
    st.caption("اطرح سؤالك القانوني واحصل على إجابة مدعومة بالنظام.")

    if not st.session_state.current_sid:
        st.info("📌 ابدأ جلسة جديدة من تبويب الإعدادات.")
    else:
        sess = load_session(st.session_state.current_sid)
        new_name = st.text_input("📝 اسم الجلسة", value=sess.get("name", "جلسة"), key="sess_name_inp")
        if new_name != sess.get("name", ""):
            sess["name"] = new_name
            sess["messages"] = st.session_state.current_msgs
            save_session(st.session_state.current_sid, sess)

        for msg in st.session_state.current_msgs:
            cls = "chat-user" if msg["role"] == "user" else "chat-ai"
            ico = "👤" if msg["role"] == "user" else "⚖️"
            content = msg["content"].replace("\n", "<br>")
            ts = msg.get("ts", "")
            st.markdown(f'<div class="{cls}">{ico} {content}<br><small style="color:#999;font-size:10px">⏱ {ts}</small></div>', unsafe_allow_html=True)

        user_inp = st.text_area("✏️ اسأل هنا", value=st.session_state.pending_q, height=100, placeholder="مثال: ما هي مكافأة نهاية الخدمة؟")
        col1, col2 = st.columns([3, 1])
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

# ------ 2. الملفات ------
with t_files:
    st.subheader("📄 رفع وتحليل المستندات")
    st.caption("ارفع ملفات PDF، DOCX، TXT، JSON لاستخراج النصوص والقوانين.")

    uploaded = st.file_uploader("اختر الملفات", type=["pdf", "docx", "txt", "json"], accept_multiple_files=True, label_visibility="collapsed")
    if uploaded:
        st.info(f"✅ تم رفع {len(uploaded)} ملف")
        di = DocIntel()
        texts = []
        for f in uploaded:
            with st.expander(f"📄 {f.name}"):
                txt = di.extract(f)
                if txt:
                    texts.append(txt)
                    st.text_area("النص المستخرج", txt[:500] + ("..." if len(txt) > 500 else ""), height=150)
                    ents = di.entities(txt)
                    if ents.get("articles"):
                        st.markdown("**المواد:** " + "".join(f'<span class="badge">{a}</span>' for a in ents["articles"][:6]), unsafe_allow_html=True)
                    if ents.get("dates"):
                        st.markdown(f"**تواريخ:** {', '.join(ents['dates'][:5])}")
                    if ents.get("amounts"):
                        st.markdown(f"**مبالغ:** {', '.join(ents['amounts'][:5])}")
                    if ents.get("basic_salary"):
                        st.metric("الراتب الأساسي", f"{ents['basic_salary']} ريال")
                    if ents.get("service_years"):
                        st.metric("مدة الخدمة", f"{ents['service_years']} سنوات")
                else:
                    st.warning("⚠️ لم يُستخرج نص من هذا الملف")
        if texts:
            st.session_state.docs = texts
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔍 تحليل شامل", use_container_width=True):
                    with st.spinner("جاري التحليل..."):
                        combined = "\n\n".join(texts)
                        analysis = generate_analysis(combined)
                        st.session_state.analysis_result = analysis
                        st.session_state.uploaded_texts = texts
                        st.success("✅ تم التحليل، انتقل إلى 'المستشار' لطرح الأسئلة")
            with col2:
                if st.button("📚 استخراج القوانين", use_container_width=True):
                    total = 0
                    for f in uploaded:
                        raw = _bytes(f)
                        ext = (f.name or "").rsplit(".", 1)[-1].lower()
                        if ext == "pdf":
                            records = extract_laws_from_pdf(raw, f.name)
                        elif ext == "docx":
                            records = extract_laws_from_docx(raw, f.name)
                        else:
                            records = extract_laws_from_text(raw.decode("utf-8", errors="ignore"), f.name)
                        st.session_state.law_db.extend(records)
                        total += len(records)
                    save_json(LAW_FILE, st.session_state.law_db)
                    st.success(f"✅ تم استخراج {total} مادة قانونية وإضافتها للقاعدة")
            with col3:
                if st.button("💰 حساب المستحقات", use_container_width=True):
                    # استخراج البيانات من النصوص
                    all_text = "\n\n".join(texts)
                    ents = di.entities(all_text)
                    bs = ents.get("basic_salary") or 8000
                    sy = ents.get("service_years") or 5
                    result = calculate_total(bs, bs * 1.25, sy, 0, 0, True)
                    st.session_state.calculator_result = result
                    st.success("✅ تم الحساب، انتقل إلى 'المستشار' لمشاهدة النتائج")

# ------ 3. التدقيق ------
with t_audit:
    st.subheader("📋 التدقيق الإداري والقانوني")
    text_input = st.text_area("✏️ الصق النص هنا", height=200, placeholder="مثال: تم فصل الموظف محمد بدون تحقيق...")
    if st.button("📋 تدقيق", use_container_width=True) and text_input.strip():
        with st.spinner("جاري التحليل..."):
            from procedural_analyzer import ProceduralAnalyzer
            from discrepancy_analyzer import DiscrepancyAnalyzer
            proc_analyzer = ProceduralAnalyzer()
            proc_result = proc_analyzer.analyze(text_input)
            disc_analyzer = DiscrepancyAnalyzer()
            disc_result = disc_analyzer.analyze_documents([{"text": text_input, "source": "النص"}])
            ctx = {
                "has_investigation": proc_result.get("has_investigation", False),
                "has_notice": proc_result.get("has_notice", False),
                "has_termination_letter": proc_result.get("has_termination_letter", False),
                "has_warning": proc_result.get("has_warning", False),
                "is_arbitrary": proc_result.get("is_arbitrary", False),
                "notice_period_days": proc_result.get("notice_period_days", 0),
            }
            alerts = apply_rules(ctx)
            st.markdown("### نتائج التدقيق")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**⚖️ الإجراءات الإدارية**")
                if proc_result.get("is_arbitrary"):
                    st.error("❌ فصل تعسفي (المادة 81)")
                if not proc_result.get("has_investigation"):
                    st.warning("⚠️ لا يوجد تحقيق مسبق (المادة 80)")
                if not proc_result.get("has_warning"):
                    st.warning("⚠️ لا يوجد إنذار سابق (المادة 75)")
                if proc_result.get("has_termination_letter") and proc_result.get("has_investigation"):
                    st.success("✅ الإجراءات سليمة شكلاً")
            with col2:
                st.markdown("**📜 المواد المخالفة**")
                if alerts:
                    for alert in alerts:
                        st.error(f"⚠️ {alert['text']}")
                else:
                    st.success("✅ لا توجد مخالفات نظامية واضحة")
            st.markdown("---")
            st.markdown("**📌 التوصيات**")
            for rec in proc_result.get("recommendations", []):
                st.markdown(f"- {rec}")
            if disc_result.get("discrepancies"):
                st.markdown("---")
                st.markdown("**⚠️ التناقضات المكتشفة**")
                for d in disc_result["discrepancies"][:5]:
                    st.warning(f"• {d.get('message', '')}")
            if proc_result.get("legal_references"):
                st.markdown("---")
                st.markdown("**📚 المراجع القانونية**")
                for ref in proc_result["legal_references"]:
                    st.markdown(f"- {ref}")

# ------ 4. توليد الدعوى ------
with t_docs:
    st.subheader("⚖️ توليد المستندات القانونية")
    with st.form("doc_form"):
        col1, col2 = st.columns(2)
        with col1:
            plaintiff = st.text_input("👤 اسم المدعي")
            plaintiff_id = st.text_input("🆔 رقم الهوية")
            work_location = st.text_input("📍 مكان العمل", value="الرياض")
        with col2:
            defendant = st.text_input("🏢 اسم المدعى عليه")
            defendant_id = st.text_input("🆔 رقم المنشأة")
            claim_amount = st.number_input("💰 المبلغ المطلوب", min_value=0.0, value=0.0, step=1000.0)
        facts = st.text_area("📝 الوقائع", height=100)
        laws = st.text_input("📜 المواد", value="المادة 84, المادة 77")
        if st.form_submit_button("⚖️ توليد"):
            from legal_document_generator import LegalDocumentGenerator
            case_data = {
                "plaintiff": plaintiff or "المدعي",
                "plaintiff_id": plaintiff_id or "غير محدد",
                "defendant": defendant or "المدعى عليه",
                "defendant_id": defendant_id or "غير محدد",
                "work_location": work_location,
                "claim_amount": claim_amount,
                "facts": [f.strip() for f in facts.split("\n") if f.strip()] or ["لم يتم إدخال وقائع"],
                "laws": [l.strip() for l in laws.split(",") if l.strip()],
                "attachments": ["المستندات المرفقة"],
                "subject": "خلاف عمالي"
            }
            generator = LegalDocumentGenerator(case_data)
            docs = {
                "📄 إنذار رسمي": generator.generate_notice(),
                "⚖️ صحيفة دعوى": generator.generate_lawsuit(),
                "📝 مذكرة قانونية": generator.generate_legal_memo()
            }
            for title, content in docs.items():
                with st.expander(title):
                    st.text_area(f"نص {title}", content, height=200, key=f"doc_{title}")
                    st.download_button(f"⬇️ تحميل {title}", data=content.encode("utf-8"), file_name=f"{title}.txt", mime="text/plain")

# ------ 5. القانون ------
with t_law:
    st.subheader("📚 قاعدة الأنظمة السعودية")
    st.caption(f"إجمالي المواد: {len(st.session_state.law_db):,}")
    if st.session_state.law_db:
        st.success(f"✅ القاعدة تحتوي على {len(st.session_state.law_db)} مادة قانونية")
    else:
        st.warning("⚠️ القاعدة فارغة. ارفع ملفات قانونية واستخرج القوانين من تبويب 'الملفات'.")
    search_term = st.text_input("🔍 بحث في المواد")
    if search_term:
        results = [i for i in st.session_state.law_db if search_term.lower() in i.get("text", "").lower() or search_term.lower() in i.get("law_name", "").lower()]
        st.info(f"✅ تم العثور على {len(results)} نتيجة")
        for r in results[:5]:
            with st.expander(f"{r.get('law_name', 'غير معروف')} - {r.get('article', 'مادة')}"):
                st.markdown(f"**النص:** {r['text'][:600]}...")
                st.caption(f"**المصدر:** {r.get('source', 'غير معروف')}")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("الأنظمة", len(set(r.get("law_name", "") for r in st.session_state.law_db)))
        with col2:
            st.metric("المواد", len(st.session_state.law_db))

# ------ 6. الذاكرة ------
with t_mem:
    st.subheader("🧠 الذاكرة الدائمة")
    with st.expander("✏️ إضافة ملاحظة"):
        mt = st.text_area("النص", height=100)
        mcat = st.selectbox("الفئة", ["قضية", "موكل", "حكم", "ملاحظة", "استراتيجية", "قانون", "عام"])
        mtags = st.text_input("وسوم")
        if st.button("💾 حفظ") and mt.strip():
            tags = [x.strip() for x in mtags.split(",") if x.strip()]
            mem_add(mt, tags, mcat)
            st.rerun()
    for m in reversed(st.session_state.memory[-15:]):
        st.markdown(f'<div class="result-card"><small>{m.get("ts", "")} · {m.get("category", "")}</small><br>{m["text"][:200]}</div>', unsafe_allow_html=True)

# ------ 7. الإعدادات ------
with t_settings:
    st.subheader("⚙️ الإعدادات والجلسات")
    st.markdown("**🤖 النموذج**")
    preset_names = ["Gemini 2.0 Flash — مجاني", "Gemini 1.5 Pro — مجاني",
                    "Groq LLaMA 3.3 — مجاني وسريع", "Claude Sonnet", "OpenAI GPT-4o",
                    "Together AI — مجاني جزئياً", "Ollama محلي", "⚙️ مخصص"]
    preset_name = st.selectbox("", preset_names,
                               index=preset_names.index(st.session_state.ai_preset) if st.session_state.ai_preset in preset_names else 0,
                               label_visibility="collapsed")
    if preset_name != st.session_state.ai_preset:
        st.session_state.ai_preset = preset_name
        save_settings({"ai_preset": st.session_state.ai_preset,
                       "ai_key": st.session_state.ai_key,
                       "ai_endpoint": st.session_state.ai_endpoint,
                       "ai_model": st.session_state.ai_model,
                       "ai_format": st.session_state.ai_format})

    st.markdown("**🔑 API Key**")
    new_key = st.text_input("", value=st.session_state.ai_key, type="password",
                            placeholder="AIza... أو sk-...", label_visibility="collapsed")
    if new_key != st.session_state.ai_key:
        st.session_state.ai_key = new_key

    if preset_name == "⚙️ مخصص":
        st.session_state.ai_endpoint = st.text_input("رابط API", value=st.session_state.ai_endpoint)
        st.session_state.ai_model = st.text_input("اسم النموذج", value=st.session_state.ai_model)
        st.session_state.ai_format = st.selectbox("الصيغة", ["openai", "gemini", "anthropic"], index=0)

    st.markdown("---")
    st.markdown("**💬 الجلسات**")
    if st.button("➕ جلسة جديدة", use_container_width=True):
        sid = new_sid()
        st.session_state.current_sid = sid
        st.session_state.current_msgs = []
        save_session(sid, {"name": "جلسة جديدة", "messages": []})
        st.rerun()

    for s in list_sessions()[:8]:
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
    st.session_state.case_type = st.selectbox("", ["قضية عمالية", "نزاع تجاري", "قضية عقارية", "نزاع إداري", "قضية جنائية", "إفلاس وتصفية"], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("**🖼️ صورة الخلفية**")
    bg_file = st.file_uploader("ارفع صورة (PNG, JPG)", type=["png", "jpg", "jpeg"])
    if bg_file:
        b64 = base64.b64encode(_bytes(bg_file)).decode()
        st.session_state.bg_b64 = b64
        with open(BG_FILE, "w") as f:
            f.write(b64)
        st.rerun()
    if st.session_state.bg_b64 and st.button("🗑️ إزالة الخلفية"):
        st.session_state.bg_b64 = ""
        if os.path.exists(BG_FILE):
            os.remove(BG_FILE)
        st.rerun()

    st.markdown("---")
    st.markdown("**📦 تصدير البيانات**")
    if st.button("📦 تصدير النسخة الاحتياطية", use_container_width=True):
        export = {"memory": st.session_state.memory, "law_db": st.session_state.law_db, "exported_at": datetime.now().isoformat()}
        st.download_button("⬇️ تحميل", json.dumps(export, ensure_ascii=False, indent=2).encode("utf-8"), "backup.json", "application/json")
