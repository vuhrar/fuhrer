# app.py
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
.hdr h1 { font-size: 28px; color: #1a1a1a; font-weight: 700; margin: 0; letter-spacing: 2px; }
.stTabs [data-baseweb="tab-list"] { background: #e8e8e8; border-bottom: 1px solid #d0d0d0; gap: 2px; padding: 4px; border-radius: 6px 6px 0 0; flex-wrap: wrap; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: #444 !important; border: 1px solid transparent !important; border-radius: 4px !important; padding: 8px 16px !important; font-size: 14px !important; font-weight: 500; }
.stTabs [data-baseweb="tab"][aria-selected="true"] { background: #ffffff !important; color: #1a1a1a !important; border-color: #d0d0d0 !important; font-weight: 700; box-shadow: 0 1px 4px rgba(0,0,0,0.05); }
.stTabs [data-baseweb="tab-panel"] { background: #ffffff; border: 1px solid #d0d0d0; border-radius: 0 0 6px 6px; padding: 20px; }
.stButton button { background: #e8e8e8 !important; color: #1a1a1a !important; border: 1px solid #cccccc !important; border-radius: 4px !important; font-weight: 600 !important; padding: 8px 20px !important; transition: 0.2s; }
.stButton button:hover { background: #d5d5d5 !important; border-color: #aaaaaa !important; }
.stTextInput input, .stTextArea textarea, .stSelectbox select { background: #fafafa !important; color: #1a1a1a !important; border: 1px solid #d0d0d0 !important; border-radius: 4px !important; font-size: 14px !important; }
.stTextInput input:focus, .stTextArea textarea:focus { border-color: #888888 !important; box-shadow: none !important; }
[data-testid="stFileUploader"] { background: #fafafa !important; border: 1px dashed #bbbbbb !important; border-radius: 4px !important; }
.chat-user { background: #e8e8e8; border: 1px solid #d0d0d0; border-radius: 12px 12px 2px 12px; padding: 10px 14px; margin: 6px 0; max-width: 82%; float: right; clear: both; color: #1a1a1a; font-size: 14px; }
.chat-ai { background: #ffffff; border: 1px solid #d0d0d0; border-radius: 12px 12px 12px 2px; padding: 10px 14px; margin: 6px 0; max-width: 88%; float: left; clear: both; border-right: 3px solid #888888; color: #1a1a1a; font-size: 14px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
.chat-wrap { overflow: hidden; min-height: 60px; }
.result-card { background: #f8f8f8; border: 1px solid #e0e0e0; border-radius: 4px; padding: 12px 16px; margin: 6px 0; }
.badge { display: inline-block; background: #e8e8e8; border: 1px solid #d0d0d0; color: #1a1a1a; border-radius: 3px; padding: 2px 8px; font-size: 11px; font-weight: 600; margin: 2px; }
@media (max-width: 768px) { .hdr h1 { font-size: 22px; } .stTabs [data-baseweb="tab"] { font-size: 12px; padding: 6px 10px; } }
@media (max-width: 480px) { .hdr h1 { font-size: 18px; } .stTabs [data-baseweb="tab"] { font-size: 11px; padding: 4px 8px; } }
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

# ==================== التبويبات (مع أوصاف كاملة) ====================
tabs = st.tabs([
    "📊 لوحة التحكم", 
    "📄 الملفات", 
    "📋 التدقيق", 
    "⚖️ الدعوى", 
    "📚 القانون", 
    "🧠 الذاكرة", 
    "⚙️ الإعدادات"
])
t_dashboard, t_files, t_audit, t_docs, t_law, t_mem, t_settings = tabs

# ------ 1. لوحة التحكم ------
with t_dashboard:
    st.subheader("لوحة التحكم")
    st.caption("ملخص شامل للقضية، نقاط القوة والضعف، والتوصيات الفورية.")
    
    if st.session_state.analysis_result is None:
        st.info("📌 لا يوجد تحليل حالي. قم برفع الملفات في تبويب 'الملفات' أو الصق النص في تبويب 'التدقيق' لبدء التحليل.")
        quick_text = st.text_area("✏️ الصق النص للتحليل السريع", height=150, placeholder="مثال: تم فصلي من العمل بدون تحقيق مسبق...")
        if st.button("🚀 تحليل سريع", use_container_width=False) and quick_text.strip():
            with st.spinner("جاري التحليل..."):
                analysis = generate_analysis(quick_text)
                st.session_state.analysis_result = analysis
                st.session_state.uploaded_texts = [quick_text]
                st.rerun()
    else:
        analysis = st.session_state.analysis_result
        extracted = analysis.get("extracted", {})
        
        # الملخص التنفيذي
        st.markdown("### الملخص التنفيذي")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style="background:#f8f9fa;padding:15px;border-radius:8px;border-right:4px solid #1a1a1a;">
            <strong>👤 الموظف:</strong> {extracted.get('employee_name', 'غير محدد') or 'غير محدد'}<br>
            <strong>🏢 صاحب العمل:</strong> {extracted.get('employer_name', 'غير محدد') or 'غير محدد'}<br>
            <strong>💰 الراتب الأساسي:</strong> {extracted.get('basic_salary', 'غير محدد')}<br>
            <strong>📅 مدة الخدمة:</strong> {extracted.get('service_years', 'غير محدد')} سنوات
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="background:#f8f9fa;padding:15px;border-radius:8px;border-right:4px solid #1a1a1a;">
            <strong>⚖️ قوة الموقف:</strong> {analysis.get('strength_score', 50)}%<br>
            <strong>⚠️ المخاطر:</strong> {analysis.get('risk_level', 'متوسطة')}<br>
            <strong>📜 المواد المستشهد بها:</strong> {', '.join(extracted.get('mentioned_articles', ['لا يوجد']))[:50]}
            </div>
            """, unsafe_allow_html=True)

        # مصفوفة الحجج
        st.markdown("---")
        st.markdown("### مصفوفة الحجج")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**✅ نقاط القوة**")
            if analysis.get("has_acknowledgment"):
                st.success("يوجد إقرار من الخصم (حجة قاطعة)")
            if analysis.get("is_arbitrary"):
                st.success("فصل تعسفي واضح (المادة 81)")
            if not analysis.get("has_investigation") and analysis.get("has_termination_letter"):
                st.success("فصل دون تحقيق (المادة 80 - بطلان)")
            if not analysis.get("has_warning") and analysis.get("has_termination_letter"):
                st.success("فصل دون إنذار سابق (المادة 75)")
            if not any([analysis.get("has_acknowledgment"), analysis.get("is_arbitrary"), 
                       (not analysis.get("has_investigation") and analysis.get("has_termination_letter"))]):
                st.info("لم يتم اكتشاف نقاط قوة واضحة")
        with col2:
            st.markdown("**❌ نقاط الضعف**")
            if analysis.get("has_threat"):
                st.warning("لغة تهديدية من الخصم (تُستغل ضدهم)")
            if not analysis.get("has_termination_letter"):
                st.warning("لا يوجد خطاب فصل رسمي (ضعف إثباتي)")
            if analysis.get("risk_level") == "مرتفعة":
                st.warning("خطر التقادم أو ضعف الأدلة")
            if not any([analysis.get("has_threat"), not analysis.get("has_termination_letter"), 
                       analysis.get("risk_level") == "مرتفعة"]):
                st.success("لا توجد نقاط ضعف واضحة")

        # التوصيات
        st.markdown("---")
        st.markdown("### 💡 التوصيات")
        recs = []
        if analysis.get("is_arbitrary"):
            recs.append("⚡ فصل تعسفي - يُنصح برفع دعوى فورية مع طلب تعويض (المادة 81)")
        if not analysis.get("has_investigation") and analysis.get("has_termination_letter"):
            recs.append("📋 الفصل دون تحقيق باطل - قدم اعتراض رسمي لدى مكتب العمل خلال 15 يوماً")
        if not analysis.get("has_warning") and analysis.get("has_termination_letter"):
            recs.append("📢 عدم وجود إنذار سابق - يُعزز موقفك في المطالبة بالتعويض")
        if analysis.get("has_threat"):
            recs.append("🛡️ التهديدات تُعتبر تعسفاً - وثقها كدليل")
        if not recs:
            recs.append("✅ الإجراءات تبدو سليمة. يُنصح بالاستمرار في جمع الأدلة والتواصل مع مكتب العمل.")
        
        for rec in recs:
            st.info(rec)

# ------ 2. الملفات ------
with t_files:
    st.subheader("📄 رفع وتحليل المستندات")
    st.caption("ارفع خطابات الفصل، قرارات الإدارة، عقود العمل، أو أي مستندات ذات صلة (PDF, DOCX, TXT, صور).")
    
    uploaded = st.file_uploader("اختر الملفات", type=None, accept_multiple_files=True, label_visibility="collapsed")
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
                else:
                    st.warning("⚠️ لم يُستخرج نص من هذا الملف (قد يكون ممسوحاً ضوئياً)")
        
        if texts:
            st.session_state.docs = texts
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔍 تحليل شامل", use_container_width=True):
                    with st.spinner("جاري التحليل..."):
                        combined = "\n\n".join(texts)
                        analysis = generate_analysis(combined)
                        st.session_state.analysis_result = analysis
                        st.session_state.uploaded_texts = texts
                        st.success("✅ تم التحليل، انتقل إلى 'لوحة التحكم' لمشاهدة النتائج")
            with col2:
                if st.button("📚 إضافة للقاعدة القانونية", use_container_width=True):
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
                    st.success(f"✅ {total} مادة أُضيفت للقاعدة")

# ------ 3. التدقيق ------
with t_audit:
    st.subheader("📋 التدقيق الإداري والقانوني")
    st.caption("الصق نص الخطاب، القرار، أو المراسلة للكشف عن المخالفات النظامية والأخطاء الإجرائية.")
    
    text_input = st.text_area("✏️ الصق النص هنا", height=200, placeholder="مثال: تم فصل الموظف محمد بدون تحقيق...")
    use_uploaded = False
    if st.session_state.get("uploaded_texts"):
        if st.checkbox("استخدام النص المستخرج من الملفات المرفوعة"):
            use_uploaded = True
            combined = "\n\n".join(st.session_state.uploaded_texts)
            st.text_area("النص المستخرج", combined, height=150)

    text_to_analyze = ""
    if use_uploaded and st.session_state.get("uploaded_texts"):
        text_to_analyze = "\n\n".join(st.session_state.uploaded_texts)
    else:
        text_to_analyze = text_input

    if st.button("📋 تدقيق", use_container_width=True) and text_to_analyze.strip():
        with st.spinner("جاري التحليل..."):
            from procedural_analyzer import ProceduralAnalyzer
            from discrepancy_analyzer import DiscrepancyAnalyzer
            proc_analyzer = ProceduralAnalyzer()
            proc_result = proc_analyzer.analyze(text_to_analyze)

            disc_analyzer = DiscrepancyAnalyzer()
            disc_result = disc_analyzer.analyze_documents([{"text": text_to_analyze, "source": "النص"}])

            ctx = {
                "has_investigation": proc_result.get("has_investigation", False),
                "has_notice": proc_result.get("has_notice", False),
                "has_termination_letter": proc_result.get("has_termination_letter", False),
                "has_warning": proc_result.get("has_warning", False),
                "is_arbitrary": proc_result.get("is_arbitrary", False),
                "notice_period_days": proc_result.get("notice_period_days", 0),
            }
            alerts = apply_rules(ctx)

            # عرض النتائج
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
    st.caption("أنشئ إنذاراً رسمياً، صحيفة دعوى، أو مذكرة قانونية جاهزة للتقديم.")
    
    with st.form("doc_form"):
        col1, col2 = st.columns(2)
        with col1:
            plaintiff = st.text_input("👤 اسم المدعي (الموظف)", value="", placeholder="أدخل اسم الموظف")
            plaintiff_id = st.text_input("🆔 رقم الهوية", value="", placeholder="أدخل رقم الهوية")
            work_location = st.text_input("📍 مكان العمل", value="الرياض", placeholder="المدينة")
        with col2:
            defendant = st.text_input("🏢 اسم المدعى عليه (صاحب العمل)", value="", placeholder="أدخل اسم الشركة")
            defendant_id = st.text_input("🆔 رقم المنشأة", value="", placeholder="أدخل رقم المنشأة")
            claim_amount = st.number_input("💰 المبلغ المطلوب (ريال)", min_value=0.0, value=0.0, step=1000.0)
        
        facts = st.text_area("📝 الوقائع (سطر لكل واقعة)", height=100, placeholder="مثال:\nبدأت العمل في 1/1/2020\nتم فصلي في 1/1/2024\nلم يتم صرف المكافأة")
        laws = st.text_input("📜 المواد النظامية المستندة (مفصولة بفاصلة)", value="المادة 84, المادة 77", placeholder="المادة 84, المادة 77")
        
        if st.form_submit_button("⚖️ توليد المستند", use_container_width=True):
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
    st.caption(f"إجمالي المواد القانونية في القاعدة: {len(st.session_state.law_db):,} مادة")
    
    search_term = st.text_input("🔍 بحث في المواد", placeholder="اكتب كلمة مفتاحية (مثل: مكافأة، فصل، تعويض)")
    if search_term:
        results = [i for i in st.session_state.law_db if search_term.lower() in i.get("text", "").lower() or search_term.lower() in i.get("law_name", "").lower()]
        st.info(f"✅ تم العثور على {len(results)} نتيجة")
        for r in results[:10]:
            with st.expander(f"{r.get('law_name', 'غير معروف')} - {r.get('article', 'مادة')}"):
                st.markdown(f"**النص:** {r['text'][:600]}...")
                st.caption(f"**المصدر:** {r.get('source', 'غير معروف')}")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("عدد الأنظمة", len(set(r.get("law_name", "") for r in st.session_state.law_db)))
        with col2:
            st.metric("عدد المواد", len(st.session_state.law_db))
        st.info("💡 استخدم شريط البحث أعلاه للوصول السريع إلى المواد القانونية.")

# ------ 6. الذاكرة ------
with t_mem:
    st.subheader("🧠 الذاكرة الدائمة")
    st.caption("تخزين الملاحظات والحجج والأفكار المتعلقة بالقضية.")
    
    with st.expander("✏️ إضافة ملاحظة جديدة"):
        mt = st.text_area("النص", height=100, placeholder="مثال: لاحظت أن صاحب العمل لم يرسل إنذاراً قبل الفصل.")
        mcat = st.selectbox("الفئة", ["قضية", "موكل", "حكم", "ملاحظة", "استراتيجية", "قانون", "عام"])
        mtags = st.text_input("وسوم (مفصولة بفاصلة)", placeholder="فصل تعسفي, مكافأة")
        if st.button("💾 حفظ الملاحظة") and mt.strip():
            tags = [x.strip() for x in mtags.split(",") if x.strip()]
            mem_add(mt, tags, mcat)
            st.success("✅ تم الحفظ")
            st.rerun()
    
    st.markdown("---")
    st.markdown("**الملاحظات المحفوظة**")
    for m in reversed(st.session_state.memory[-20:]):
        st.markdown(f"""
        <div class="result-card">
            <small style="color:#888;">{m.get('ts', '')} · {m.get('category', '')}</small>
            <br>{m['text'][:200]}{'...' if len(m['text']) > 200 else ''}
            <br><span style="color:#888;font-size:11px;">وسوم: {', '.join(m.get('tags', []))}</span>
        </div>
        """, unsafe_allow_html=True)

# ------ 7. الإعدادات ------
with t_settings:
    st.subheader("⚙️ الإعدادات والجلسات")
    st.caption("إدارة النماذج، مفاتيح API، الجلسات، والخلفية.")
    
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
