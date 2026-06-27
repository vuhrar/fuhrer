
import streamlit as st
import re, os, json, logging, hashlib, base64
from datetime import datetime
from typing import Dict, List, Any
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

st.set_page_config(page_title="Führer", page_icon="⚖️", layout="wide", initial_sidebar_state="collapsed")

# ==================== CSS ====================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap');
* { box-sizing: border-box; font-family: 'Cairo', sans-serif; direction: rtl; }
html, body, .stApp { background: #f5f5f5; }
[data-testid="stSidebar"], [data-testid="stSidebarNav"] { display: none !important; }
.hdr { background: #ffffff; border: 1px solid #d0d0d0; border-radius: 6px; padding: 12px 16px; margin-bottom: 14px; text-align: center; }
.hdr h1 { font-size: 24px; color: #1a1a1a; font-weight: 700; margin: 0; }
.stTabs [data-baseweb="tab-list"] { background: #e8e8e8; border-bottom: 1px solid #d0d0d0; gap: 2px; padding: 4px; border-radius: 6px 6px 0 0; flex-wrap: wrap; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: #444 !important; border: 1px solid transparent !important; border-radius: 4px !important; padding: 6px 12px !important; font-size: 13px !important; }
.stTabs [data-baseweb="tab"][aria-selected="true"] { background: #ffffff !important; color: #1a1a1a !important; border-color: #d0d0d0 !important; font-weight: 600; }
.stTabs [data-baseweb="tab-panel"] { background: #ffffff; border: 1px solid #d0d0d0; border-radius: 0 0 6px 6px; padding: 16px; }
.stButton button { background: #e8e8e8 !important; color: #1a1a1a !important; border: 1px solid #cccccc !important; border-radius: 4px !important; font-weight: 600 !important; padding: 8px 16px !important; }
.stButton button:hover { background: #d5d5d5 !important; }
.stTextInput input, .stTextArea textarea, .stSelectbox select { background: #fafafa !important; color: #1a1a1a !important; border: 1px solid #d0d0d0 !important; border-radius: 4px !important; font-size: 14px !important; }
[data-testid="stFileUploader"] { background: #fafafa !important; border: 1px dashed #cccccc !important; border-radius: 4px !important; }
.chat-user { background: #e8e8e8; border: 1px solid #d0d0d0; border-radius: 12px 12px 2px 12px; padding: 10px 14px; margin: 6px 0; max-width: 82%; float: right; clear: both; color: #1a1a1a; font-size: 14px; }
.chat-ai { background: #ffffff; border: 1px solid #d0d0d0; border-radius: 12px 12px 12px 2px; padding: 10px 14px; margin: 6px 0; max-width: 88%; float: left; clear: both; border-right: 3px solid #888888; color: #1a1a1a; font-size: 14px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
.chat-wrap { overflow: hidden; min-height: 60px; }
.result-card { background: #f8f8f8; border: 1px solid #e0e0e0; border-radius: 4px; padding: 12px 16px; margin: 6px 0; }
.badge { display: inline-block; background: #e8e8e8; border: 1px solid #d0d0d0; color: #1a1a1a; border-radius: 3px; padding: 2px 8px; font-size: 11px; font-weight: 600; margin: 2px; }
@media (max-width: 768px) { .hdr h1 { font-size: 20px; } .stTabs [data-baseweb="tab"] { font-size: 11px; padding: 4px 8px; } }
@media (max-width: 480px) { .hdr h1 { font-size: 17px; } .stTabs [data-baseweb="tab"] { font-size: 10px; padding: 3px 6px; } }
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
        background: rgba(245,245,245,0.92);
        z-index: 0;
        pointer-events: none;
    }}
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="hdr"><h1>Führer</h1></div>', unsafe_allow_html=True)

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

# ==================== دوال التحليل المتكاملة ====================
def extract_entities(text: str) -> Dict:
    return {
        "employee_name": re.search(r'(?:الموظف|السيد)\s*([\u0600-\u06ff\s]{2,30})', text),
        "employer_name": re.search(r'(?:صاحب العمل|الشركة)\s*([\u0600-\u06ff\s]{2,30})', text),
        "basic_salary": re.search(r'(?:الراتب الأساسي|الأساسي)\s*[:]?\s*([\d,]+)', text),
        "total_salary": re.search(r'(?:الراتب الإجمالي|الإجمالي)\s*[:]?\s*([\d,]+)', text),
        "service_years": re.search(r'(\d+\.?\d*)\s*(?:سنوات|سنة)', text),
        "termination_date": re.search(r'(?:فصل|إنهاء|تاريخ الفصل)\s*[:]?\s*(\d{1,2}/\d{1,2}/\d{2,4})', text),
        "mentioned_articles": re.findall(r'المادة\s*([\u0660-\u0669\d]+)', text),
    }

def generate_analysis(text: str) -> Dict:
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

# ==================== التبويبات ====================
tabs = st.tabs(["📊", "📄", "📋", "⚖️", "📚", "🧠", "⚙️"])
t_dashboard, t_files, t_audit, t_docs, t_law, t_mem, t_settings = tabs

# ------ لوحة التحكم ------
with t_dashboard:
    st.subheader("لوحة التحكم")
    if st.session_state.analysis_result is None:
        st.info("قم برفع الملفات في تبويب 'الملفات' أو الصق النص في تبويب 'التدقيق' لبدء التحليل.")
        quick_text = st.text_area("الصق النص للتحليل السريع", height=150)
        if st.button("تحليل سريع") and quick_text.strip():
            with st.spinner("جاري التحليل..."):
                analysis = generate_analysis(quick_text)
                st.session_state.analysis_result = analysis
                st.session_state.uploaded_texts = [quick_text]
                st.rerun()
    else:
        analysis = st.session_state.analysis_result
        extracted = analysis.get("extracted", {})
        
        st.markdown("### الملخص التنفيذي")
        st.markdown(f"""
        <div style="background:#f8f9fa;padding:15px;border-radius:8px;border-right:4px solid #1a1a1a;">
        <strong>الموظف:</strong> {extracted.get('employee_name', 'غير محدد') or 'غير محدد'}<br>
        <strong>صاحب العمل:</strong> {extracted.get('employer_name', 'غير محدد') or 'غير محدد'}<br>
        <strong>الراتب الأساسي:</strong> {extracted.get('basic_salary', 'غير محدد')}<br>
        <strong>مدة الخدمة:</strong> {extracted.get('service_years', 'غير محدد')} سنوات<br>
        <strong>قوة الموقف:</strong> {analysis.get('strength_score', 50)}%<br>
        <strong>المخاطر:</strong> {analysis.get('risk_level', 'متوسطة')}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### مصفوفة الحجج")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**نقاط القوة**")
            if analysis.get("has_acknowledgment"):
                st.success("✅ يوجد إقرار من الخصم")
            if analysis.get("is_arbitrary"):
                st.success("✅ فصل تعسفي (المادة 81)")
            if not analysis.get("has_investigation") and analysis.get("has_termination_letter"):
                st.success("✅ فصل دون تحقيق (المادة 80)")
        with col2:
            st.markdown("**نقاط الضعف**")
            if analysis.get("has_threat"):
                st.warning("⚠️ لغة تهديدية من الخصم")
            if not analysis.get("has_termination_letter"):
                st.warning("⚠️ لا يوجد خطاب فصل رسمي")

        st.markdown("---")
        st.markdown("### التوصيات")
        if analysis.get("is_arbitrary"):
            st.warning("⚠️ فصل تعسفي - يُنصح برفع دعوى فورية")
        if not analysis.get("has_investigation") and analysis.get("has_termination_letter"):
            st.info("💡 الفصل دون تحقيق باطل - قدم اعتراض لمكتب العمل")
        if extracted.get("mentioned_articles"):
            st.success(f"📜 المواد المستشهد بها: {', '.join(extracted['mentioned_articles'][:5])}")

# ------ تبويب الملفات ------
with t_files:
    st.subheader("الملفات")
    uploaded = st.file_uploader("", type=None, accept_multiple_files=True, label_visibility="collapsed")
    if uploaded:
        di = DocIntel()
        texts = []
        for f in uploaded:
            with st.expander(f"📄 {f.name}"):
                txt = di.extract(f)
                if txt:
                    texts.append(txt)
                    st.text(txt[:500])
                else:
                    st.warning("⚠️ لم يُستخرج نص")
        if texts:
            st.session_state.docs = texts
            if st.button("🔍 تحليل شامل"):
                with st.spinner("جاري التحليل..."):
                    combined = "\n\n".join(texts)
                    analysis = generate_analysis(combined)
                    st.session_state.analysis_result = analysis
                    st.session_state.uploaded_texts = texts
                    st.success("✅ تم التحليل، انتقل إلى لوحة التحكم")

# ------ باقي التبويبات (مختصرة) ------
with t_audit:
    st.subheader("التدقيق")
    text_input = st.text_area("", height=200, placeholder="الصق النص هنا...")
    if st.button("تدقيق") and text_input.strip():
        with st.spinner("..."):
            analysis = generate_analysis(text_input)
            st.session_state.analysis_result = analysis
            st.session_state.uploaded_texts = [text_input]
            st.success("✅ تم التحليل، انتقل إلى لوحة التحكم")

with t_docs:
    st.subheader("توليد الدعوى")
    with st.form("doc_form"):
        plaintiff = st.text_input("المدعي")
        defendant = st.text_input("المدعى عليه")
        amount = st.number_input("المبلغ", min_value=0.0, value=0.0)
        facts = st.text_area("الوقائع")
        if st.form_submit_button("توليد"):
            from legal_document_generator import LegalDocumentGenerator
            case_data = {
                "plaintiff": plaintiff or "المدعي",
                "defendant": defendant or "المدعى عليه",
                "claim_amount": amount,
                "facts": [facts] if facts else ["لا توجد وقائع"],
                "laws": ["المادة 84", "المادة 77"],
                "attachments": ["المستندات"]
            }
            generator = LegalDocumentGenerator(case_data)
            doc = generator.generate_lawsuit()
            st.text_area("صحيفة الدعوى", doc, height=300)

with t_law:
    st.subheader("القانون")
    st.caption(f"المواد: {len(st.session_state.law_db):,}")
    search = st.text_input("🔍 بحث")
    if search:
        results = [i for i in st.session_state.law_db if search in i.get("text", "")]
        for r in results[:5]:
            with st.expander(f"{r.get('law_name', '')} - {r.get('article', '')}"):
                st.text(r['text'][:500])

with t_mem:
    st.subheader("الذاكرة")
    with st.expander("✏️ إضافة"):
        mt = st.text_area("", height=100)
        if st.button("حفظ") and mt.strip():
            mem_add(mt, [], "عام")
            st.rerun()
    for m in reversed(st.session_state.memory[-20:]):
        st.markdown(f'<div class="result-card">{m["text"][:200]}</div>', unsafe_allow_html=True)

with t_settings:
    st.subheader("الإعدادات")
    preset_names = ["Gemini 2.0 Flash — مجاني", "Gemini 1.5 Pro — مجاني",
                    "Groq LLaMA 3.3 — مجاني وسريع", "Claude Sonnet", "OpenAI GPT-4o",
                    "Together AI — مجاني جزئياً", "Ollama محلي", "⚙️ مخصص"]
    preset_name = st.selectbox("", preset_names, index=0)
    st.session_state.ai_preset = preset_name
    new_key = st.text_input("API Key", value=st.session_state.ai_key, type="password")
    st.session_state.ai_key = new_key
    
    st.markdown("---")
    if st.button("➕ جلسة جديدة", use_container_width=True):
        sid = new_sid()
        st.session_state.current_sid = sid
        st.session_state.current_msgs = []
        save_session(sid, {"name": "جلسة جديدة", "messages": []})
        st.rerun()
    for s in list_sessions()[:5]:
        if st.button(f"{s['name']} ({s['count']})", key=f"s_{s['id']}"):
            data = load_session(s["id"])
            st.session_state.current_sid = s["id"]
            st.session_state.current_msgs = data.get("messages", [])
            st.rerun()
