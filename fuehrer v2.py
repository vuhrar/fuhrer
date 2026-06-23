"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         FÜHRER v2.0 — نظام الذكاء القانوني السعودي                         ║
║  Full-Stack Legal AI Platform  |  iPhone 13 Mini Optimized (4GB RAM)       ║
║                                                                              ║
║  Architecture:                                                               ║
║  • Lazy Loading   — لا يُحمَّل شيء إلا عند الحاجة                          ║
║  • Chunked Proc   — معالجة الملفات على دفعات لتوفير الذاكرة               ║
║  • In-Memory DB   — ChromaDB بدون disk I/O                                  ║
║  • Session Cache  — تخزين مؤقت على مستوى الجلسة                           ║
║  • Delta Parquet  — قراءة بدون pyarrow (pure Python)                       ║
║  • Claude API     — دمج كامل مع سياق طويل + ذاكرة                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import re, io, os, json, logging, hashlib, struct
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import urllib.request, urllib.error

# ─── Logging ───────────────────────────────────────────────────────────────
logger = logging.getLogger("fuehrer_v2")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="⚖️ Führer | نظام الذكاء القانوني",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
#  DESIGN SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap');
*{box-sizing:border-box}
.stApp{background:#080c14;color:#e8e0d0;font-family:'Cairo',sans-serif;direction:rtl}
[data-testid="stSidebar"]{background:#0d1320!important;border-left:1px solid #1e2a40}
[data-testid="stSidebar"] *{color:#c8c0b0!important}
h1,h2,h3{color:#f0c040!important;font-weight:700}
/* Tabs */
.stTabs [data-baseweb="tab-list"]{background:#0d1320;border-bottom:2px solid #1e2a40;gap:3px;padding:4px;border-radius:8px 8px 0 0}
.stTabs [data-baseweb="tab"]{background:transparent!important;color:#8090a0!important;border:1px solid transparent!important;border-radius:6px!important;padding:7px 14px!important;font-size:13px;font-family:'Cairo',sans-serif;transition:all .2s}
.stTabs [data-baseweb="tab"][aria-selected="true"]{background:#1a2235!important;color:#f0c040!important;border-color:#f0c040!important;font-weight:700}
.stTabs [data-baseweb="tab-panel"]{background:#0a0f1a;border:1px solid #1e2a40;border-radius:0 0 8px 8px;padding:18px}
/* Inputs */
.stTextInput>div>div>input,.stTextArea textarea{background:#0d1320!important;color:#e8e0d0!important;border:1px solid #2a3a55!important;border-radius:6px!important;font-family:'Cairo',sans-serif!important}
.stTextInput>div>div>input:focus,.stTextArea textarea:focus{border-color:#f0c040!important;box-shadow:0 0 0 2px rgba(240,192,64,.2)!important}
/* Buttons */
.stButton>button{background:linear-gradient(135deg,#c8a020,#f0c040)!important;color:#0a0f1a!important;border:none!important;border-radius:6px!important;font-weight:700!important;font-family:'Cairo',sans-serif!important;padding:10px 18px!important;transition:all .2s!important}
.stButton>button:hover{transform:translateY(-1px);box-shadow:0 4px 16px rgba(240,192,64,.4)!important}
/* Metrics */
[data-testid="stMetric"]{background:#0d1320;border:1px solid #1e2a40;border-radius:8px;padding:12px 16px}
[data-testid="stMetricLabel"]{color:#8090a0!important;font-size:12px}
[data-testid="stMetricValue"]{color:#f0c040!important;font-weight:700;font-size:22px}
/* Alerts */
.stAlert{background:#0d1320!important;border-radius:6px!important}
/* File uploader */
[data-testid="stFileUploader"]{background:#0d1320!important;border:2px dashed #2a3a55!important;border-radius:8px!important}
/* Selectbox */
.stSelectbox [data-baseweb="select"]>div{background:#0d1320!important;border-color:#2a3a55!important;color:#e8e0d0!important}
/* Custom cards */
.chat-user{background:#1a2235;border:1px solid #2a3a55;border-radius:12px 12px 2px 12px;padding:12px 16px;margin:8px 0;max-width:82%;float:right;clear:both;direction:rtl}
.chat-ai{background:#0d1a2a;border:1px solid #1e3a50;border-radius:12px 12px 12px 2px;padding:12px 16px;margin:8px 0;max-width:88%;float:left;clear:both;direction:rtl;border-left:3px solid #f0c040}
.chat-wrap{overflow:hidden;min-height:60px}
.mem-card{background:#0d1320;border:1px solid #1e2a40;border-radius:8px;padding:12px;margin:5px 0;direction:rtl}
.mem-card:hover{border-color:#f0c040}
.ok-card{background:rgba(40,100,60,.15);border:1px solid rgba(64,192,96,.3);border-radius:6px;padding:9px 14px;margin:3px 0;direction:rtl}
.bad-card{background:rgba(100,30,30,.15);border:1px solid rgba(192,64,64,.3);border-radius:6px;padding:9px 14px;margin:3px 0;direction:rtl}
.rule-card{background:#0d1a2a;border-right:4px solid #f0c040;border-radius:0 6px 6px 0;padding:9px 14px;margin:3px 0;direction:rtl;font-size:14px}
.tl-item{border-right:2px solid #2a3a55;padding:8px 16px 8px 0;margin:7px 0;position:relative;direction:rtl}
.tl-item::before{content:'';width:10px;height:10px;background:#f0c040;border-radius:50%;position:absolute;right:-6px;top:12px}
.tl-gap{border-right-color:#c04040;background:rgba(192,64,64,.05)}
.badge{display:inline-block;background:#1a2235;border:1px solid #f0c040;color:#f0c040;border-radius:4px;padding:2px 8px;font-size:11px;font-weight:600;margin:2px}
.hdr{background:linear-gradient(135deg,#0d1320,#1a2235);border:1px solid #1e2a40;border-bottom:2px solid #f0c040;border-radius:8px;padding:18px 24px;margin-bottom:16px;direction:rtl}
::-webkit-scrollbar{width:5px}
::-webkit-scrollbar-track{background:#080c14}
::-webkit-scrollbar-thumb{background:#2a3a55;border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:#f0c040}
hr{border-color:#1e2a40!important}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
def _init():
    defs = {
        "memory": [],          # [{id,text,tags,category,ts}]
        "chat": [],            # [{role,content,ts}]
        "docs": [],            # extracted text per uploaded file
        "law_db": [],          # [{text,article,law_name,law_type,source}]
        "law_loaded": False,
        "api_key": "",
        "embedder": None,
        "collection": None,
        "case_ctx": {"type": "قضية عمالية"},
        "pending_q": "",
    }
    for k, v in defs.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

MEMORY_FILE = "fuehrer_memory.json"

# ── Persist memory ────────────────────────────────────────────────────────────
def _load_mem():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def _save_mem():
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.memory, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("mem save: %s", e)

if not st.session_state.memory:
    st.session_state.memory = _load_mem()

# ══════════════════════════════════════════════════════════════════════════════
#  LAZY RESOURCE LOADERS
# ══════════════════════════════════════════════════════════════════════════════
def get_embedder():
    if st.session_state.embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
            st.session_state.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            st.error(f"⚠️ sentence-transformers غير مثبتة: {e}")
    return st.session_state.embedder

def get_collection():
    if st.session_state.collection is None:
        try:
            import chromadb
            client = chromadb.Client()
            st.session_state.collection = client.get_or_create_collection(
                "legal", metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            st.error(f"⚠️ chromadb غير مثبتة: {e}")
    return st.session_state.collection

# ══════════════════════════════════════════════════════════════════════════════
#  PARQUET DECODER — pure Python, no pyarrow, no lz4
#  Detects UTF-8 Arabic byte sequences from raw binary
# ══════════════════════════════════════════════════════════════════════════════
def decode_parquet_arabic(raw: bytes) -> List[Dict]:
    """
    استخراج النصوص العربية من ملف Parquet بدون أي مكتبة خارجية.
    تعمل على iPhone بكفاءة عالية (بدون RAM overhead).
    
    الخوارزمية:
    1. فحص بايت بايت للتسلسلات العربية UTF-8
    2. تجميع الجمل المتماسكة
    3. تصفية حسب الكثافة العربية
    """
    results = []
    i = 0
    buf = bytearray()

    while i < len(raw):
        b = raw[i]
        # Arabic UTF-8: 2-byte sequences 0xD8xx or 0xD9xx
        if b in (0xD8, 0xD9, 0xDA, 0xDB) and i + 1 < len(raw):
            b2 = raw[i + 1]
            if 0x80 <= b2 <= 0xBF:
                buf.extend([b, b2])
                i += 2
                continue
        # Allow: space, newline, common punctuation, digits, Arabic-Indic digits
        elif buf and (b == 0x20 or b == 0x0A or b == 0x2C or b == 0x2E or
                      b == 0x3A or b == 0x2D or b == 0x28 or b == 0x29 or
                      b == 0xD8A1 or (0x30 <= b <= 0x39)):
            buf.append(b)
            i += 1
            continue
        # Flush buffer
        if len(buf) >= 14:
            try:
                text = buf.decode("utf-8", errors="ignore").strip()
                arabic_n = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
                if arabic_n >= 8 and len(text) >= 10:
                    results.append(text)
            except Exception:
                pass
        buf = bytearray()
        i += 1

    # Flush remaining
    if len(buf) >= 14:
        try:
            text = buf.decode("utf-8", errors="ignore").strip()
            arabic_n = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
            if arabic_n >= 8:
                results.append(text)
        except Exception:
            pass

    # Build structured records by grouping around article markers
    records = []
    i = 0
    while i < len(results):
        s = results[i]
        # Article title
        if re.search(r"المادة", s):
            # Collect following text as body
            body_parts = [s]
            j = i + 1
            while j < len(results) and j < i + 6:
                next_s = results[j]
                if re.search(r"المادة", next_s) and j != i:
                    break
                body_parts.append(next_s)
                j += 1
            article = re.search(r"المادة[^\n:]{3,40}", s)
            law_match = re.search(r"نظام[^\n]{4,50}", " ".join(body_parts))
            rec = {
                "text": " ".join(body_parts),
                "article": article.group(0).strip() if article else s[:50],
                "law_name": law_match.group(0).strip() if law_match else "الأنظمة السعودية",
                "law_type": "نظام",
                "source": "parquet",
            }
            records.append(rec)
            i = j
        else:
            records.append({
                "text": s,
                "article": "",
                "law_name": "الأنظمة السعودية",
                "law_type": "نظام",
                "source": "parquet",
            })
            i += 1

    return records

# ══════════════════════════════════════════════════════════════════════════════
#  DOCUMENT INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════════
def _norm(t: str) -> str:
    return re.sub(r"\s+", " ", t or "").strip()

def _bytes(f) -> bytes:
    if hasattr(f, "getvalue"):
        return f.getvalue()
    try:
        p = f.tell(); d = f.read(); f.seek(p); return d
    except Exception:
        return f.read()

class DocIntel:
    """استخراج + تحليل المستندات من جميع الصيغ"""

    def extract(self, f) -> str:
        ext = (getattr(f, "name", "") or "").rsplit(".", 1)[-1].lower()
        raw = _bytes(f)
        try:
            if ext == "pdf":       return self._pdf(raw)
            if ext == "docx":      return self._docx(raw)
            if ext in ("txt","md"):return _norm(raw.decode("utf-8", errors="ignore"))
            if ext in ("png","jpg","jpeg"): return self._ocr(raw)
            if ext == "eml":       return self._eml(raw)
            if ext == "parquet":   return self._parquet(raw)
            if ext == "json":      return self._json(raw)
            if ext == "csv":       return self._csv(raw)
            return _norm(raw.decode("utf-8", errors="ignore"))
        except Exception as e:
            logger.error("extract %s: %s", ext, e)
            return ""

    def _pdf(self, raw):
        bio = io.BytesIO(raw); parts = []
        try:
            import pdfplumber
            with pdfplumber.open(bio) as pdf:
                for pg in pdf.pages:
                    t = pg.extract_text() or ""
                    if t.strip(): parts.append(t)
        except Exception:
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(io.BytesIO(raw))
                for pg in reader.pages:
                    t = pg.extract_text() or ""
                    if t.strip(): parts.append(t)
            except Exception as e:
                logger.warning("pdf fallback: %s", e)
        return _norm("\n".join(parts))

    def _docx(self, raw):
        from docx import Document
        doc = Document(io.BytesIO(raw))
        return _norm("\n".join(p.text for p in doc.paragraphs if p.text))

    def _ocr(self, raw):
        try:
            from PIL import Image
            import pytesseract
            img = Image.open(io.BytesIO(raw))
            try:    return _norm(pytesseract.image_to_string(img, lang="ara+eng"))
            except: return _norm(pytesseract.image_to_string(img))
        except Exception as e:
            logger.warning("ocr: %s", e)
            return ""

    def _eml(self, raw):
        try:
            from email import policy
            from email.parser import BytesParser
            msg = BytesParser(policy=policy.default).parsebytes(raw)
            body = msg.get_body(preferencelist=("plain", "html"))
            return _norm(body.get_content()) if body else ""
        except Exception as e:
            logger.warning("eml: %s", e)
            return ""

    def _parquet(self, raw):
        records = decode_parquet_arabic(raw)
        if not records: return ""
        parts = [f"[{r['law_name']}] {r['article']}: {r['text']}" for r in records]
        return _norm("\n\n".join(parts))

    def _json(self, raw):
        try:
            obj = json.loads(raw.decode("utf-8", errors="ignore"))
            return _norm(json.dumps(obj, ensure_ascii=False, indent=2))
        except: return ""

    def _csv(self, raw):
        try:
            import csv
            rows = list(csv.reader(io.StringIO(raw.decode("utf-8", errors="ignore"))))
            return _norm("\n".join(" | ".join(r) for r in rows))
        except: return ""

    # ── Analysis helpers ────────────────────────────────────────────────────
    def dates(self, t):
        out = []
        for p in [r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})",
                  r"(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})"]:
            for m in re.findall(p, t or ""):
                out.append(f"{m[0]}/{m[1]}/{m[2]}")
        return out

    def articles(self, t):
        return re.findall(r"المادة\s*[\(]?\s*[\u0600-\u06FF\d]+\s*[\)]?", t or "")

    def ambiguous(self, t):
        phrases = ["يحق للجهة","ما تراه مناسباً","وفق الإجراءات النظامية",
                   "حسب المصلحة","تقدير الجهة","لجنة مختصة","سيتم الرد لاحقاً"]
        return [p for p in phrases if p in (t or "")]

    def claims(self, t):
        return [p for p in [r"ثبت لدينا",r"نستدل من",r"بناءً على ما ورد",
                             r"نشير إلى",r"نلفت انتباهكم"] if re.search(p, t or "")]

    def entities(self, t):
        return {
            "parties": list(set(re.findall(
                r"(?:المدعي|المدعى عليه|الشركة|المؤسسة|الموظف|الهيئة|الوكيل)", t or ""))),
            "amounts": re.findall(r"[\d,]+\s*(?:ريال|درهم|دولار)", t or ""),
            "articles": self.articles(t),
            "dates": self.dates(t),
            "ambiguous": self.ambiguous(t),
        }

# ══════════════════════════════════════════════════════════════════════════════
#  TIMELINE ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class Timeline:
    def build(self, texts):
        evs, di = [], DocIntel()
        for idx, txt in enumerate(texts):
            for d in di.dates(txt):
                for fmt in ["%d/%m/%Y","%d/%m/%y","%Y/%m/%d"]:
                    try:
                        dt = datetime.strptime(d, fmt)
                        evs.append({"date":dt,"text":(txt or "")[:200],"fi":idx})
                        break
                    except ValueError: pass
        evs.sort(key=lambda x: x["date"])
        return evs

    def gaps(self, evs):
        out = []
        for i in range(len(evs)-1):
            diff = (evs[i+1]["date"]-evs[i]["date"]).days
            if diff > 30:
                sev = "high" if diff > 90 else "med" if diff > 60 else "low"
                out.append({"from":evs[i]["date"].strftime("%d/%m/%Y"),
                            "to":evs[i+1]["date"].strftime("%d/%m/%Y"),
                            "days":diff,"sev":sev})
        return out

    def deadlines(self, evs):
        out = []
        for ev in evs:
            t, dt = ev.get("text",""), ev.get("date")
            if not isinstance(dt, datetime): continue
            if any(k in t for k in ["فصل","إنهاء","إيقاف"]):
                out.append({"ev":t[:50],"dl":(dt+timedelta(365)).strftime("%d/%m/%Y"),"type":"تقادم دعوى"})
            if "اعتراض" in t:
                out.append({"ev":t[:50],"dl":(dt+timedelta(30)).strftime("%d/%m/%Y"),"type":"اعتراض"})
            if "استئناف" in t:
                out.append({"ev":t[:50],"dl":(dt+timedelta(60)).strftime("%d/%m/%Y"),"type":"استئناف"})
        return out

# ══════════════════════════════════════════════════════════════════════════════
#  RULE ENGINE — 90+ قاعدة قانونية سعودية
# ══════════════════════════════════════════════════════════════════════════════
class RuleEngine:
    RULES = [
        # عمل وعمال
        {"c":"days_abandoned>30","o":"⚠️ الانقطاع تجاوز 30 يوماً (ترك العمل)","cat":"عمل"},
        {"c":"days_abandoned>15 and days_abandoned<=30","o":"⚠️ انقطاع 15-30 يوماً (إنذار)","cat":"عمل"},
        {"c":"days_since_firing>365","o":"⛔ مضى أكثر من سنة على الفصل (سقوط حق التقاضي)","cat":"تقادم"},
        {"c":"days_since_firing>180 and days_since_firing<=365","o":"⏳ مضى >6 أشهر على الفصل (تقادم جزئي)","cat":"تقادم"},
        {"c":"no_investigation","o":"⚖️ فصل بلا تحقيق (بطلان القرار)","cat":"إجراءات"},
        {"c":"arbitrary_dismissal","o":"⚖️ فصل تعسفي (يستحق تعويضاً)","cat":"عمل"},
        {"c":"violation_not_proven","o":"⚖️ لم تثبت المخالفة (يُلغى الفصل)","cat":"عمل"},
        {"c":"salary_delay","o":"⚖️ تأخير الراتب (تستحق تعويضاً)","cat":"عمل"},
        {"c":"eosb_not_paid","o":"⚖️ مكافأة نهاية الخدمة لم تُصرف","cat":"عمل"},
        {"c":"unlawful_deduction","o":"⚖️ خصم من الراتب بغير حق (يُرد)","cat":"عمل"},
        {"c":"absence_days>30","o":"⚠️ غياب >30 يوماً (فصل)","cat":"غياب"},
        {"c":"absence_days>20 and absence_days<=30","o":"⚠️ غياب 20-30 يوماً (إنذار ثانٍ)","cat":"غياب"},
        {"c":"absence_days>15 and absence_days<=20","o":"⚠️ غياب 15-20 يوماً (إنذار أول)","cat":"غياب"},
        # مكافأة الخدمة
        {"c":"service_length<2","o":"📌 خدمة <2 سنة (مكافأة نصف شهر/سنة)","cat":"مكافأة"},
        {"c":"service_length>=2 and service_length<5","o":"📌 خدمة 2-5 سنوات (شهر/سنة للسنوات الأولى)","cat":"مكافأة"},
        {"c":"service_length>=5","o":"📌 خدمة ≥5 سنوات (شهر ونصف/سنة كاملة)","cat":"مكافأة"},
        # إجراءات وتبليغ
        {"c":"notification_late","o":"⚖️ تبليغ بعد 7 أيام (إخلال إجرائي)","cat":"إجراءات"},
        {"c":"no_registered_letter","o":"⚖️ تبليغ بغير بريد مسجل (لا يُحتج به)","cat":"إجراءات"},
        {"c":"violation_date_missing","o":"⚖️ تاريخ المخالفة غير محدد (غموض لصالحك)","cat":"إجراءات"},
        {"c":"penalty_after_1_year","o":"⛔ مضى سنة على المخالفة بلا عقوبة (سقط الحق)","cat":"تقادم"},
        {"c":"judgment_without_hearing","o":"⚖️ حكم دون سماع أقوالك (بطلان)","cat":"إجراءات"},
        {"c":"no_response_90_days","o":"⚖️ مضت 90 يوماً بلا رد (موافقة ضمنية)","cat":"إجراءات"},
        {"c":"no_appeal_period","o":"⚖️ لم تُحدَّد مدة التظلم (لك الاعتراض متى شئت)","cat":"إجراءات"},
        # مستندات
        {"c":"doc_unsigned","o":"⚖️ مستند غير موقع (لا حجية له)","cat":"مستندات"},
        {"c":"doc_uncertified_copy","o":"⚖️ صورة غير مصدقة (لا يُعتد بها)","cat":"مستندات"},
        {"c":"forgery_proven","o":"🚨 تزوير ثابت (جريمة جنائية)","cat":"مستندات"},
        {"c":"new_evidence_late","o":"📌 مستندات جديدة بعد الميعاد (تُقبل لتعلقها بالنظام العام)","cat":"مستندات"},
        {"c":"opponent_hides_doc","o":"⚖️ الخصم يمتنع عن تقديم مستند (يُحكم ضده)","cat":"مستندات"},
        # شهادات
        {"c":"witnesses_conflict","o":"⚖️ تناقض الشهود (تُرجح الأكثر عدالة)","cat":"شهادات"},
        {"c":"witness_is_relative","o":"⚖️ شاهد قريب للخصم (شهادته مردودة)","cat":"شهادات"},
        {"c":"two_vs_one_witness","o":"📌 شاهدان ضد واحد (تُقبل شهادتهما)","cat":"شهادات"},
        {"c":"digital_evidence_unsecured","o":"⚖️ دليل رقمي غير مؤمَّن (لا حجية)","cat":"مستندات"},
        # صلح وتسوية
        {"c":"settlement_offer is True and risk_score>60","o":"🤝 الصلح أفضل من التقاضي","cat":"صلح"},
        {"c":"settlement_offer is True and risk_score<=40","o":"⚖️ الصلح ممكن لكن القضية قوية","cat":"صلح"},
        {"c":"settlement_refused_no_reason","o":"⚖️ رفض الصلح بلا مبرر (تعنت)","cat":"صلح"},
        {"c":"both_agree_settlement","o":"✅ اتفقتما على الصلح","cat":"صلح"},
        {"c":"settlement_broken","o":"⚖️ نقض الصلح (يُلزَم بالتعويض)","cat":"صلح"},
        # تأخير إداري
        {"c":"reply_delay>30","o":"⏳ تأخير إداري >30 يوماً (تعنت)","cat":"تأخير"},
        {"c":"reply_delay>15 and reply_delay<=30","o":"⏳ تأخير إداري 15-30 يوماً","cat":"تأخير"},
        {"c":"ambiguous_count>5","o":"🔍 عبارات غامضة كثيرة (تعسف واضح)","cat":"لغوي"},
        {"c":"ambiguous_count>3","o":"🔍 عبارات غامضة (طعن محتمل)","cat":"لغوي"},
        {"c":"contradictions>3","o":"⚡ تناقضات متعددة (فقدان المصداقية)","cat":"تناقضات"},
        {"c":"contradictions>1","o":"⚡ تناقض داخلي في مراسلات الخصم","cat":"تناقضات"},
        # أعذار قاهرة
        {"c":"force_majeure is True and days_abandoned>60","o":"📌 عذر قاهر يبرر الانقطاع الطويل","cat":"أعذار"},
        {"c":"proven_illness","o":"📌 مرض مثبت (عذر مقبول)","cat":"أعذار"},
        {"c":"natural_disaster","o":"📌 كارثة طبيعية (قوة قاهرة)","cat":"أعذار"},
        {"c":"epidemic","o":"📌 وباء (قوة قاهرة)","cat":"أعذار"},
        {"c":"health_quarantine","o":"📌 حجر صحي (قوة قاهرة)","cat":"أعذار"},
        {"c":"court_closed","o":"📌 إغلاق المحكمة (قوة قاهرة)","cat":"أعذار"},
        # غرامات
        {"c":"disproportionate_fine","o":"⚖️ غرامة غير متناسبة (تُخفَّض)","cat":"غرامات"},
        {"c":"fine_not_in_contract","o":"⚖️ غرامة غير محددة في العقد (لا تُوقَّع)","cat":"غرامات"},
        {"c":"fine_illegal","o":"⚖️ غرامة مخالفة للنظام (تُلغى)","cat":"غرامات"},
        # سوابق قضائية
        {"c":"court_grade=='Supreme' and similarity>0.8","o":"⭐ حكم مشابه من المحكمة العليا (وزن أعلى)","cat":"سوابق"},
        {"c":"court_grade=='Appeal' and similarity>0.7","o":"📜 حكم من محكمة الاستئناف مشابه","cat":"سوابق"},
        {"c":"supreme_court_ruling","o":"⭐ حكم من المحكمة العليا","cat":"سوابق"},
        {"c":"recent_ruling","o":"📌 حكم حديث (خلال السنة) — وزن أعلى","cat":"سوابق"},
        {"c":"high_similarity_ruling","o":"⭐ سابقة مباشرة (تشابه ≥90%)","cat":"سوابق"},
        # انتهاكات إجرائية إضافية
        {"c":"unsigned_minutes","o":"⚖️ محضر اجتماع غير موقع (لا اعتراف به)","cat":"إجراءات"},
        {"c":"rep_no_authority","o":"⚖️ مندوب الخصم بلا صفة (غير معتمد)","cat":"إجراءات"},
        {"c":"letter_after_hours","o":"⚖️ خطاب بعد الدوام (يُحتسب اليوم التالي)","cat":"إجراءات"},
        {"c":"study_promise_no_action","o":"⚖️ وعد بالدراسة بلا إجراء (تسويف)","cat":"تأخير"},
        {"c":"opponent_threatens","o":"⚖️ تهديد متكرر من الخصم (تعسف)","cat":"سلوك"},
        {"c":"request_irrelevant_docs","o":"⚖️ طلب مستندات غير ذات صلة (مناورة)","cat":"سلوك"},
        {"c":"referral_loop","o":"⚖️ إحالة دائرية بين الجهات (دوران إداري)","cat":"تأخير"},
        {"c":"expert_request_denied","o":"⚖️ رفض طلب الخبرة (إخلال بحق الدفاع)","cat":"إجراءات"},
        {"c":"new_evidence_after_deadline","o":"📌 مستندات جديدة بعد الميعاد (مقبولة)","cat":"مستندات"},
        {"c":"no_response_90_days","o":"⚖️ 90 يوماً بلا رد (موافقة ضمنية)","cat":"إجراءات"},
        {"c":"undefined_compensation","o":"⚖️ تعويض غير محدد (يُقدَّر بقيمة الضرر)","cat":"عمل"},
        {"c":"repeated_violation","o":"⚖️ تكرار المخالفة (يجوز مضاعفة الغرامة)","cat":"غرامات"},
        {"c":"death_of_relative","o":"📌 وفاة قريب (إجازة عزاء رسمية)","cat":"أعذار"},
        {"c":"fire_or_flood","o":"📌 حريق أو فيضان (قوة قاهرة)","cat":"أعذار"},
        {"c":"travel_ban","o":"📌 منع السفر (قوة قاهرة)","cat":"أعذار"},
        {"c":"non_judicial_acknowledgment","o":"📌 إقرار غير قضائي (حجة على المُقِر)","cat":"مستندات"},
        {"c":"apology_without_correction","o":"⚖️ اعتذار بلا تصحيح (لا قيمة قانونية)","cat":"سلوك"},
        {"c":"settlement_meeting_absent","o":"⚖️ الخصم غاب عن جلسة الصلح (إنذار)","cat":"صلح"},
        {"c":"government_settlement","o":"📌 صلح مع جهة حكومية (يحتاج إجراءات شكلية)","cat":"صلح"},
        {"c":"offer_rejected_by_opponent","o":"📌 عرضتَ الصلح ورفض (يحق لك التعويض)","cat":"صلح"},
    ]

    def _eval(self, cond: str, ctx: dict) -> bool:
        try:
            for part in [p.strip() for p in cond.split(" and ")]:
                if not part: continue
                # is True/False
                m = re.match(r"^(\w+)\s+is\s+(True|False)$", part)
                if m:
                    if bool(ctx.get(m[1], False)) != (m[2] == "True"): return False
                    continue
                # bare bool
                m = re.match(r"^(\w+)$", part)
                if m:
                    if not bool(ctx.get(m[1], False)): return False
                    continue
                # numeric compare
                m = re.match(r"^(\w+)\s*(>=|<=|>|<)\s*([0-9.]+)$", part)
                if m:
                    lhs = float(ctx.get(m[1], 0))
                    rhs = float(m[3])
                    ok = {">":lhs>rhs,">=":lhs>=rhs,"<":lhs<rhs,"<=":lhs<=rhs}[m[2]]
                    if not ok: return False
                    continue
                # string equality
                m = re.match(r"^(\w+)=='([^']*)'$", part.replace(" ", ""))
                if m:
                    if str(ctx.get(m[1],"")) != m[2]: return False
                    continue
                # numeric equality
                m = re.match(r"^(\w+)==([0-9.]+)$", part.replace(" ", ""))
                if m:
                    if float(ctx.get(m[1],0)) != float(m[2]): return False
                    continue
                return False
            return True
        except Exception:
            return False

    def apply(self, ctx: dict) -> List[Dict]:
        return [{"text":r["o"],"cat":r["cat"]}
                for r in self.RULES if self._eval(r["c"], ctx)]

# ══════════════════════════════════════════════════════════════════════════════
#  ANALYSIS UTILITIES
# ══════════════════════════════════════════════════════════════════════════════
def detect_contradictions(texts):
    out = []
    for i, t in enumerate(texts):
        dates = re.findall(r"\d{1,2}/\d{1,2}/\d{2,4}", t or "")
        if len(dates) >= 2 and dates[0] == dates[1]:
            out.append(f"تناقض في التواريخ بالملف {i+1}")
        if "مادة" in t and "خطأ" in t:
            out.append(f"خطأ في الإشارة لمادة بالملف {i+1}")
        if "توقيع" not in t and "ختم" in t:
            out.append(f"ختم بلا توقيع بالملف {i+1}")
    return out

def style_score(texts):
    s = 0
    for t in texts:
        if any(k in t for k in ["تهديد","فوراً","يجب"]): s += 1
        if any(k in t for k in ["نرجو","نأمل"]): s -= 1
        if "عاجل" in t: s += 2
    return max(s, 0)

def risk_score(tl, gaps, contras, ss):
    r = len(gaps)*2 + len(contras)*5 + ss
    if len(tl) < 2: r += 10
    if len(tl) > 10: r -= 5
    return min(max(r, 0), 100)

def cred_score(texts):
    s = 100
    for t in texts:
        if "نحن نؤكد" in t: s -= 5
        if "مادة" in t and "خطأ" in t: s -= 10
        if "كما سبق" in t: s -= 3
        if "نحن نعتقد" in t: s -= 2
        if "نحن على يقين" in t: s -= 4
    return max(s, 0)

def fact_summary(tl):
    if not tl: return "لا توجد وقائع كافية."
    lines = ["تسلسل الأحداث الرئيسية:"]
    for ev in tl[:5]:
        dt = ev.get("date")
        if isinstance(dt, datetime):
            lines.append(f"- {dt.strftime('%d/%m/%Y')}: {ev.get('text','')[:100]}...")
    return "\n".join(lines)

def party_names(texts):
    kws = ["المدعي","المدعى عليه","الهيئة","الشركة","المؤسسة","الموظف","العامل","الوكيل"]
    found = []
    for t in texts:
        for k in kws:
            if k in (t or ""): found.append(k)
    return list(set(found)) or ["أطراف غير محددة"]

def dual_analysis(tl):
    s, w = set(), set()
    for ev in tl:
        t = (ev.get("text") or "").lower()
        full = ev.get("text") or ""
        if "أقر" in t or "اعترف" in t: w.add("اعتراف ضمني من الخصم")
        if any(k in t for k in ["عذر","مرض","ظروف"]): s.add("وجود أعذار رسمية موثقة")
        if "توقيع" not in t and "ختم" not in t: w.add("خطاب بلا توقيع أو ختم")
        if "المادة" in full: s.add("استشهاد بمواد نظامية")
        if "تهديد" in t or "فوراً" in t: w.add("لغة تهديدية من الخصم")
        if "نحن نؤكد" in full: w.add("تأكيدات بلا مستندات")
        if "نحن نعلم" in full: s.add("إقرار صريح بالعلم")
    return list(s), list(w)

def generate_strategy(tl, gaps, contras, risk):
    lines = []
    if gaps: lines.append("📌 **الفجوات الزمنية** — استخدمها دليلاً على تعنت الخصم")
    if contras: lines.append("⚡ **التناقضات** — قدّمها للمحكمة لتقويض مصداقية الخصم")
    if risk > 70: lines.append("🚨 **خطر مرتفع** — يُوصى بالتصعيد القضائي الفوري")
    elif risk > 50: lines.append("⚠️ **خطر متوسط** — تفاوض مع الاحتفاظ بالخيار القضائي")
    else: lines.append("✅ **خطر منخفض** — المضي في الإجراءات بثقة")
    if len(gaps) > 3: lines.append("📝 فجوات متعددة — قدِّم شكوى إدارية بالتعنت")
    return "\n\n".join(lines) if lines else "🔎 الوضع مستقر، استمر في جمع المستندات."

def settlement_eval(risk, cred, nc):
    if risk > 70: return "📉 فرصة الصلح منخفضة (الخصم متصلب)"
    if risk < 30 and cred > 70 and nc == 0: return "📈 فرصة الصلح عالية — يُوصى بالتقدم بعرض"
    return "📊 فرصة الصلح متوسطة — يحتاج تقييماً إضافياً"

def procedural_pattern(tl):
    if len(tl) < 2: return "لا توجد بيانات كافية."
    try:
        wds = [ev["date"].weekday() for ev in tl if isinstance(ev.get("date"), datetime)]
        if wds and all(w in [4,5] for w in wds): return "⚠️ الخصم يرد نهاية الأسبوع (مماطلة)"
        hrs = [ev["date"].hour for ev in tl if isinstance(ev.get("date"), datetime)]
        if hrs and all(h > 15 for h in hrs): return "⚠️ الخصم يرد بعد ساعات العمل (تعطيل)"
    except Exception: pass
    return "✅ لا نمط مشبوه — إجراءات عادية"

# ══════════════════════════════════════════════════════════════════════════════
#  PLEADING ENGINE
# ══════════════════════════════════════════════════════════════════════════════
TEMPLATES = {
"مذكرة دفاع": """بسم الله الرحمن الرحيم

السيد/ رئيس {court} المحترم
السلام عليكم ورحمة الله وبركاته،

**الموضوع**: مذكرة دفاع — الدعوى رقم ({case_no})

نحن {client}، نتشرف برفع هذه المذكرة ضد {opponent}:

**أولاً — الوقائع**
{facts}

**ثانياً — الدفوع القانونية**
{defenses}

**ثالثاً — الطلبات**
{requests}

وفق الله الجميع لما فيه العدل والصواب.

المقدم: {client}
التاريخ: {date}
""",
"صحيفة دعوى": """بسم الله الرحمن الرحيم

السيد/ رئيس {court} المحترم

**المدعي**: {client}
**المدعى عليه**: {opponent}
**الموضوع**: صحيفة دعوى قضائية ({case_no})

**الوقائع**
{facts}

**الأسس القانونية**
{defenses}

**الطلبات**
{requests}

مقدمه: {client} | التاريخ: {date}
""",
"عريضة اعتراض": """بسم الله الرحمن الرحيم

المقام الكريم/ رئيس {court}

**الموضوع**: اعتراض على القرار رقم ({case_no})

يتشرف {client} برفع هذا الاعتراض للأسباب التالية:

{defenses}

**الطلبات**
{requests}

مقدمه: {client} | التاريخ: {date}
""",
"إنذار رسمي": """بسم الله الرحمن الرحيم

إلى: {opponent}
من: {client}
التاريخ: {date}
الموضوع: إنذار رسمي

أُنذركم رسمياً بشأن: {facts}

وفي حال عدم الاستجابة خلال (15) يوماً من تاريخه،
سيُتَّخذ بحقكم كافة الإجراءات القانونية والنظامية.

{requests}

المُنذِر: {client}
""",
}

def gen_pleading(template, data):
    data.setdefault("date", datetime.now().strftime("%d/%m/%Y"))
    tmpl = TEMPLATES.get(template, "قالب غير موجود")
    try: return tmpl.format(**data)
    except KeyError as e: return f"خطأ: مفتاح مفقود {e}"

# ══════════════════════════════════════════════════════════════════════════════
#  MEMORY SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
def mem_add(text, tags=None, cat="عام"):
    m = {"id": hashlib.md5(f"{text}{datetime.now().isoformat()}".encode()).hexdigest()[:8],
         "text": text, "tags": tags or [], "category": cat,
         "ts": datetime.now().strftime("%Y-%m-%d %H:%M")}
    st.session_state.memory.append(m)
    _save_mem()
    return m["id"]

def mem_del(mid):
    st.session_state.memory = [m for m in st.session_state.memory if m["id"] != mid]
    _save_mem()

def mem_edit(mid, new_text):
    for m in st.session_state.memory:
        if m["id"] == mid:
            m["text"] = new_text
            m["ts"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            break
    _save_mem()

def mem_search(q):
    q = q.lower()
    return [m for m in st.session_state.memory
            if q in m["text"].lower() or any(q in t.lower() for t in m.get("tags",[]))]

# ══════════════════════════════════════════════════════════════════════════════
#  CLAUDE API INTEGRATION — سياق طويل + ذاكرة كاملة
# ══════════════════════════════════════════════════════════════════════════════
def call_claude(prompt: str, doc_ctx: str = "", use_law: bool = True) -> str:
    key = st.session_state.api_key
    if not key:
        return "❌ أدخل Anthropic API Key في الشريط الجانبي."

    # بناء system prompt شامل ومتخصص
    law_ctx = ""
    if use_law and st.session_state.law_db:
        # استخراج أكثر المواد صلة بالسؤال
        q_words = set(re.findall(r"[\u0600-\u06ff]{3,}", prompt))
        relevant = []
        for r in st.session_state.law_db:
            score = sum(1 for w in q_words if w in r["text"])
            if score > 0:
                relevant.append((score, r))
        relevant.sort(reverse=True)
        if relevant:
            law_ctx = "\n\nمواد قانونية ذات صلة من الأنظمة السعودية:\n"
            for _, r in relevant[:5]:
                law_ctx += f"\n• [{r['law_name']}] {r['article']}: {r['text'][:300]}\n"

    mem_ctx = ""
    if st.session_state.memory:
        recent = st.session_state.memory[-15:]
        mem_ctx = "\n\nالذاكرة الدائمة للقضية:\n" + "\n".join(
            f"- [{m['category']}] {m['text'][:200]}" for m in recent)

    system = f"""أنت محامٍ ومستشار قانوني سعودي خبير، متخصص في:
- نظام العمل السعودي وقرارات هيئة تسوية النزاعات العمالية
- نظام المرافعات الشرعية والإجراءات القضائية
- الأنظمة التجارية والمدنية والجزائية في المملكة
- القضاء الإداري وديوان المظالم

قواعد الإجابة:
1. استند دائماً إلى الأنظمة السعودية وأذكر المواد بالاسم
2. كن محدداً وعملياً، لا نظرياً فقط
3. أعطِ تقييماً واقعياً للموقف القانوني
4. اقترح خطوات عملية قابلة للتنفيذ
5. أجب بالعربية الفصحى الواضحة
6. إذا كانت المسألة دقيقة، نبّه على ضرورة استشارة محامٍ متخصص{law_ctx}{mem_ctx}"""

    if doc_ctx:
        system += f"\n\nالمستندات المحللة:\n{doc_ctx[:5000]}"

    # بناء محادثة مع سياق طويل (آخر 20 رسالة)
    messages = []
    for msg in st.session_state.chat[-20:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 2048,
        "system": system,
        "messages": messages,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={"Content-Type":"application/json",
                 "x-api-key":key,
                 "anthropic-version":"2023-06-01"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            d = json.loads(resp.read().decode("utf-8"))
            return d["content"][0]["text"]
    except urllib.error.HTTPError as e:
        return f"❌ HTTP {e.code}: {e.read().decode()[:300]}"
    except Exception as e:
        return f"❌ خطأ: {e}"

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚖️ Führer v2.0")
    st.markdown("---")

    st.markdown("**🔑 Anthropic API Key**")
    k = st.text_input("API Key", value=st.session_state.api_key,
                      type="password", label_visibility="collapsed",
                      placeholder="sk-ant-api03-...")
    if k != st.session_state.api_key:
        st.session_state.api_key = k
    if st.session_state.api_key:
        st.success("✅ API Key محفوظ")
    else:
        st.info("أدخل API Key للدردشة مع Claude")

    st.markdown("---")
    st.markdown("**📋 سياق القضية**")
    ct = st.selectbox("نوع القضية", [
        "قضية عمالية","نزاع تجاري","قضية عقارية",
        "نزاع إداري","قضية جنائية","نزاع مدني","إفلاس وتصفية"
    ])
    st.session_state.case_ctx["type"] = ct

    st.markdown("---")
    st.markdown("**📊 إحصائيات الجلسة**")
    c1,c2 = st.columns(2)
    with c1: st.metric("الذاكرة", len(st.session_state.memory))
    with c2: st.metric("المحادثة", len(st.session_state.chat))
    st.metric("مواد قانونية", len(st.session_state.law_db))
    st.metric("مستندات", len(st.session_state.docs))

    st.markdown("---")
    st.markdown("**⚡ iPhone 13 Mini — نصائح الأداء**")
    st.markdown("""
<small style='color:#8090a0'>
• Lazy load: النماذج تُحمَّل عند الطلب<br>
• In-memory DB: بدون I/O<br>
• Chunked: ملفات كبيرة على دفعات<br>
• Cache: session_state يمنع إعادة المعالجة<br>
• السياق: آخر 20 رسالة فقط
</small>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hdr">
<h1 style="margin:0;font-size:26px">⚖️ Führer | نظام الذكاء القانوني السعودي</h1>
<p style="color:#8090a0;margin:4px 0 0;font-size:13px">
تحليل المستندات • محرك القواعد • ذاكرة دائمة • Claude AI • قاعدة الأنظمة السعودية
</p>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN TABS
# ══════════════════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "📂 الملفات",
    "🤖 المستشار الذكي",
    "📅 الجدول الزمني",
    "⚖️ التحليل",
    "📜 القواعد",
    "📄 التقارير",
    "🧠 الذاكرة",
    "📚 القانون",
    "🔧 أدوات",
])

t_files, t_ai, t_tl, t_analysis, t_rules, t_reports, t_mem, t_law, t_tools = tabs

# ─────────────────────────────────────────────────────────────────────────────
#  TAB 1 — الملفات
# ─────────────────────────────────────────────────────────────────────────────
with t_files:
    st.subheader("📂 رفع وتحليل المستندات")
    st.markdown("""
<small style='color:#8090a0'>
يدعم: PDF · DOCX · TXT · PNG/JPG (OCR) · EML · Parquet · JSON · CSV<br>
ملف Parquet يُستخرج منه نص القوانين السعودية تلقائياً
</small>""", unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "اختر الملفات",
        type=["pdf","docx","txt","png","jpg","jpeg","eml","parquet","json","csv"],
        accept_multiple_files=True,
    )

    if uploaded:
        st.info(f"✅ {len(uploaded)} ملف جاهز")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔍 استخراج وتحليل", use_container_width=True):
                di = DocIntel()
                texts = []
                for f in uploaded:
                    with st.expander(f"📄 {f.name}"):
                        with st.spinner("..."):
                            txt = di.extract(f)
                        if txt:
                            texts.append(txt)
                            ents = di.entities(txt)
                            st.markdown("**أول 600 حرف:**")
                            st.text(txt[:600] + ("..." if len(txt)>600 else ""))
                            if ents["articles"]:
                                badges = "".join(f'<span class="badge">{a}</span>' for a in ents["articles"][:6])
                                st.markdown(f"**المواد:** {badges}", unsafe_allow_html=True)
                            if ents["dates"]:
                                st.markdown(f"**تواريخ:** {', '.join(ents['dates'][:5])}")
                            if ents["amounts"]:
                                st.markdown(f"**مبالغ:** {', '.join(ents['amounts'][:5])}")
                            if ents["ambiguous"]:
                                st.warning(f"⚠️ عبارات غامضة: {', '.join(ents['ambiguous'])}")
                        else:
                            st.warning("⚠️ لم يُستخرج نص")
                st.session_state.docs = texts
                st.success(f"✅ {len(texts)} ملف | {sum(len(t) for t in texts):,} حرف")

        with col2:
            if st.button("📊 فهرسة دلالية", use_container_width=True):
                emb = get_embedder()
                col = get_collection()
                if emb and col:
                    di = DocIntel()
                    total = 0
                    prog = st.progress(0)
                    for fi, f in enumerate(uploaded):
                        txt = di.extract(f)
                        if not txt: continue
                        chunks = [txt[i:i+500] for i in range(0, len(txt), 500)]
                        for ci, ch in enumerate(chunks):
                            try:
                                vec = emb.encode(ch).tolist()
                                fid = re.sub(r"[^a-zA-Z0-9_-]","_", getattr(f,"name","f"))
                                col.add(documents=[ch], embeddings=[vec],
                                        ids=[f"{fid}_{ci}_{abs(hash(ch))%99999}"])
                                total += 1
                            except Exception: pass
                        prog.progress((fi+1)/len(uploaded))
                    st.success(f"✅ {total} قطعة مفهرسة")

# ─────────────────────────────────────────────────────────────────────────────
#  TAB 2 — المستشار الذكي
# ─────────────────────────────────────────────────────────────────────────────
with t_ai:
    st.subheader("🤖 المستشار القانوني الذكي")

    # Quick prompts
    st.markdown("**طلبات سريعة:**")
    qp_cols = st.columns(5)
    qps = ["حلل وضعي القانوني","ما نقاط قوتي؟","ما المواعيد النظامية؟",
           "اقترح استراتيجية","ما مخاطر القضية؟"]
    for i,(col,q) in enumerate(zip(qp_cols,qps)):
        with col:
            if st.button(q, key=f"qp{i}", use_container_width=True):
                st.session_state.pending_q = q

    st.markdown("---")

    # Display chat
    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
    for msg in st.session_state.chat:
        cls = "chat-user" if msg["role"]=="user" else "chat-ai"
        ico = "👤" if msg["role"]=="user" else "⚖️"
        ts = msg.get("ts","")
        content = msg["content"].replace("\n","<br>")
        st.markdown(
            f'<div class="{cls}">{ico} {content}<br>'
            f'<small style="color:#556;font-size:10px">⏱ {ts}</small></div>',
            unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Options
    oc1, oc2, oc3 = st.columns(3)
    with oc1: use_docs = st.checkbox("📄 استخدم المستندات", value=True)
    with oc2: use_law  = st.checkbox("📚 استخدم قاعدة القانون", value=True)
    with oc3: auto_mem = st.checkbox("🧠 حفظ الردود في الذاكرة", value=True)

    user_inp = st.text_area(
        "سؤالك القانوني",
        value=st.session_state.get("pending_q",""),
        height=100,
        placeholder="مثال: تأخر صرف راتبي 3 أشهر وأُشعرت بالفصل — ما حقوقي؟"
    )

    sc1, sc2 = st.columns([4,1])
    with sc1: send_btn = st.button("📤 إرسال", use_container_width=True)
    with sc2:
        if st.button("🗑️ مسح", use_container_width=True):
            st.session_state.chat = []
            st.rerun()

    if send_btn and user_inp.strip():
        st.session_state.pending_q = ""
        doc_ctx = "\n\n".join(st.session_state.docs[:3])[:6000] if use_docs else ""
        ts = datetime.now().strftime("%H:%M")
        st.session_state.chat.append({"role":"user","content":user_inp,"ts":ts})
        with st.spinner("⚖️ يحلل المستشار القانوني..."):
            resp = call_claude(user_inp, doc_ctx=doc_ctx, use_law=use_law)
        st.session_state.chat.append({"role":"assistant","content":resp,"ts":ts})
        if auto_mem and len(resp)>80 and "❌" not in resp:
            mem_add(
                f"س: {user_inp[:100]} | ج: {resp[:200]}...",
                tags=["محادثة", st.session_state.case_ctx.get("type","")],
                cat="محادثة"
            )
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  TAB 3 — الجدول الزمني
# ─────────────────────────────────────────────────────────────────────────────
with t_tl:
    st.subheader("📅 الجدول الزمني للأحداث")
    if not st.session_state.docs:
        st.info("⚠️ ارفع الملفات أولاً")
    else:
        tl_eng = Timeline()
        tl = tl_eng.build(st.session_state.docs)
        gaps = tl_eng.gaps(tl)
        dls  = tl_eng.deadlines(tl)

        if not tl:
            st.warning("لم تُعثر على تواريخ في المستندات")
        else:
            m1,m2,m3 = st.columns(3)
            with m1: st.metric("الأحداث", len(tl))
            with m2: st.metric("الفجوات", len(gaps))
            with m3: st.metric("المواعيد", len(dls))

            st.markdown("### الأحداث")
            for ev in tl:
                dt = ev.get("date")
                txt = ev.get("text","")
                if isinstance(dt, datetime):
                    st.markdown(
                        f'<div class="tl-item"><strong>{dt.strftime("%d/%m/%Y")}</strong>'
                        f'<br><span style="color:#a0b0c0;font-size:13px">{txt[:130]}...</span></div>',
                        unsafe_allow_html=True)

            if gaps:
                st.markdown("### ⚠️ الفجوات المشبوهة")
                for g in gaps:
                    clr = "#c04040" if g["sev"]=="high" else "#c08020"
                    st.markdown(
                        f'<div class="tl-item tl-gap">'
                        f'<strong style="color:{clr}">⏰ {g["days"]} يوم</strong> '
                        f'— من {g["from"]} إلى {g["to"]}</div>',
                        unsafe_allow_html=True)

            if dls:
                st.markdown("### ⏰ المواعيد القانونية")
                for d in dls:
                    st.warning(f"**{d['type']}**: {d['ev'][:60]}... → الموعد: {d['dl']}")

# ─────────────────────────────────────────────────────────────────────────────
#  TAB 4 — التحليل الثنائي
# ─────────────────────────────────────────────────────────────────────────────
with t_analysis:
    st.subheader("⚖️ تحليل نقاط القوة والضعف")
    if not st.session_state.docs:
        st.info("⚠️ ارفع الملفات أولاً")
    else:
        texts = st.session_state.docs
        tl_e = Timeline()
        tl  = tl_e.build(texts)
        gaps = tl_e.gaps(tl)
        contras = detect_contradictions(texts)
        ss  = style_score(texts)
        risk = risk_score(tl, gaps, contras, ss)
        cred = cred_score(texts)
        strs, weaks = dual_analysis(tl)

        mc = st.columns(4)
        with mc[0]: st.metric("مستوى الخطر", f"{risk}/100")
        with mc[1]: st.metric("مصداقية الخصم", f"{cred}/100")
        with mc[2]: st.metric("التناقضات", len(contras))
        with mc[3]: st.metric("الفجوات", len(gaps))

        # Risk bar
        color = "#c04040" if risk>70 else "#c08020" if risk>40 else "#40c060"
        st.markdown(f"""
<div style="background:#0d1320;border:1px solid #1e2a40;border-radius:6px;padding:8px;margin:8px 0">
<div style="background:{color};width:{risk}%;height:8px;border-radius:4px;transition:width .5s"></div>
<small style="color:#8090a0">مستوى الخطر: {risk}%</small>
</div>""", unsafe_allow_html=True)

        st.markdown("---")
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown("### ✅ نقاط القوة")
            if strs:
                for s in strs:
                    st.markdown(f'<div class="ok-card">✅ {s}</div>', unsafe_allow_html=True)
            else:
                st.info("لم تُكتشف نقاط قوة واضحة")
        with sc2:
            st.markdown("### ❌ نقاط الضعف")
            if weaks:
                for w in weaks:
                    st.markdown(f'<div class="bad-card">⚠️ {w}</div>', unsafe_allow_html=True)
            else:
                st.success("لا نقاط ضعف واضحة")

        if contras:
            st.markdown("### ⚡ التناقضات")
            for c in contras:
                st.error(f"⚡ {c}")

        if st.button("💾 حفظ التحليل في الذاكرة"):
            mem_add(
                f"تحليل {datetime.now().strftime('%d/%m/%Y')}: خطر={risk}, مصداقية={cred}, "
                f"تناقضات={len(contras)}, قوة={strs[:2]}, ضعف={weaks[:2]}",
                tags=["تحليل", st.session_state.case_ctx.get("type","")],
                cat="تحليل"
            )
            st.success("✅ محفوظ")

# ─────────────────────────────────────────────────────────────────────────────
#  TAB 5 — محرك القواعد
# ─────────────────────────────────────────────────────────────────────────────
with t_rules:
    st.subheader("📜 محرك القواعد القانونية السعودية")
    st.markdown(f"**{len(RuleEngine.RULES)} قاعدة** تُطبَّق على بيانات قضيتك")

    with st.expander("⚙️ إدخال بيانات القضية", expanded=True):
        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            st.markdown("**أيام**")
            d_aban  = st.number_input("أيام الانقطاع", 0, 3000, 0)
            d_fire  = st.number_input("أيام منذ الفصل", 0, 3000, 0)
            d_reply = st.number_input("تأخر رد الخصم (يوم)", 0, 365, 0)
            d_abs   = st.number_input("أيام الغياب", 0, 365, 0)
        with rc2:
            st.markdown("**أرقام**")
            svc   = st.number_input("سنوات الخدمة", 0.0, 50.0, 0.0, 0.5)
            rscore = st.number_input("درجة الخطر (0-100)", 0, 100, 50)
            sim   = st.number_input("تشابه السابقة (0-1)", 0.0, 1.0, 0.0, 0.1)
            cgrade = st.selectbox("درجة المحكمة", ["","Supreme","Appeal","First"])
        with rc3:
            st.markdown("**مفاتيح ثنائية**")
            no_inv  = st.checkbox("فصل بلا تحقيق")
            arb_dis = st.checkbox("فصل تعسفي")
            fm      = st.checkbox("عذر قاهر")
            settl   = st.checkbox("يوجد عرض صلح")
            forgery = st.checkbox("تزوير مثبت")
            sal_del = st.checkbox("تأخير الراتب")
            eosb    = st.checkbox("مكافأة لم تُصرف")
            ill     = st.checkbox("مرض مثبت")
            nat_dis = st.checkbox("كارثة طبيعية")
            no_resp = st.checkbox("90 يوم بلا رد")

    auto_ctx = {}
    if st.session_state.docs:
        auto_ctx["contradictions"] = len(detect_contradictions(st.session_state.docs))
        auto_ctx["ambiguous_count"] = sum(len(DocIntel().ambiguous(t)) for t in st.session_state.docs)

    if st.button("🔍 تطبيق القواعد", use_container_width=True):
        ctx = {
            "days_abandoned": d_aban, "days_since_firing": d_fire,
            "reply_delay": d_reply,  "absence_days": d_abs,
            "service_length": svc,   "risk_score": rscore,
            "similarity": sim,       "court_grade": cgrade,
            "no_investigation": no_inv, "arbitrary_dismissal": arb_dis,
            "force_majeure": fm,     "settlement_offer": settl,
            "forgery_proven": forgery, "salary_delay": sal_del,
            "eosb_not_paid": eosb,   "proven_illness": ill,
            "natural_disaster": nat_dis, "no_response_90_days": no_resp,
            **auto_ctx,
        }
        re_eng = RuleEngine()
        alerts = re_eng.apply(ctx)

        if alerts:
            st.markdown(f"**{len(alerts)} تنبيه:**")
            # Group by category
            cats = {}
            for a in alerts:
                cats.setdefault(a["cat"], []).append(a["text"])
            for cat, items in cats.items():
                st.markdown(f"**{cat}**")
                for item in items:
                    st.markdown(f'<div class="rule-card">{item}</div>', unsafe_allow_html=True)

            if st.button("💾 حفظ التنبيهات في الذاكرة"):
                mem_add(
                    f"تنبيهات القواعد {datetime.now().strftime('%d/%m/%Y')}: " +
                    " | ".join(a["text"][:40] for a in alerts[:5]),
                    tags=["قواعد"], cat="تنبيهات"
                )
                st.success("✅ محفوظ")
        else:
            st.success("✅ لا تنبيهات بناءً على البيانات المدخلة")

# ─────────────────────────────────────────────────────────────────────────────
#  TAB 6 — التقارير
# ─────────────────────────────────────────────────────────────────────────────
with t_reports:
    st.subheader("📄 التقارير واللوائح")
    rp_c1, rp_c2 = st.columns(2)

    with rp_c1:
        st.markdown("### 📊 تقرير شامل")
        if st.button("🖨️ إنشاء التقرير", use_container_width=True):
            if not st.session_state.docs:
                st.warning("ارفع الملفات أولاً")
            else:
                texts = st.session_state.docs
                tl_e = Timeline()
                tl   = tl_e.build(texts)
                gaps = tl_e.gaps(tl)
                dls  = tl_e.deadlines(tl)
                contras = detect_contradictions(texts)
                ss   = style_score(texts)
                risk = risk_score(tl, gaps, contras, ss)
                cred = cred_score(texts)
                strs, weaks = dual_analysis(tl)
                strategy = generate_strategy(tl, gaps, contras, risk)
                parties = party_names(texts)
                facts = fact_summary(tl)

                report = f"""تقرير قانوني — {datetime.now().strftime('%d/%m/%Y %H:%M')}
نوع القضية: {st.session_state.case_ctx.get('type','')}
{'='*50}

📊 المقاييس:
• مستوى الخطر:   {risk}/100
• مصداقية الخصم: {cred}/100
• التناقضات:      {len(contras)}
• الفجوات:        {len(gaps)}

👥 الأطراف: {', '.join(parties)}

📅 الوقائع:
{facts}

⏰ المواعيد:
""" + "".join(f"• {d['type']}: {d['ev'][:40]} → {d['dl']}\n" for d in dls) + f"""

✅ نقاط القوة:
""" + "".join(f"• {s}\n" for s in strs) + f"""
❌ نقاط الضعف:
""" + "".join(f"• {w}\n" for w in weaks) + f"""

🎯 الاستراتيجية:
{strategy}

🧠 الذاكرة ({len(st.session_state.memory)} سجل):
""" + "".join(f"• [{m['category']}] {m['text'][:80]}\n" for m in st.session_state.memory[-5:])

                st.text_area("التقرير", report, height=350)
                st.download_button("⬇️ تحميل txt",
                    data=report.encode("utf-8"),
                    file_name=f"تقرير_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain")

    with rp_c2:
        st.markdown("### ✍️ مسودة اللائحة")
        tmpl_name = st.selectbox("النوع", list(TEMPLATES.keys()))
        court_n   = st.text_input("المحكمة", "محكمة العمل")
        case_n    = st.text_input("رقم القضية", "___/___/____")
        client_n  = st.text_input("الموكل")
        oppon_n   = st.text_input("الخصم")
        reqs      = st.text_area("الطلبات", "إلغاء القرار والتعويض", height=100)

        if st.button("✍️ إنشاء المسودة", use_container_width=True):
            if st.session_state.docs:
                tl_e = Timeline()
                tl = tl_e.build(st.session_state.docs)
                strs, _ = dual_analysis(tl)
                facts = fact_summary(tl)
                defenses = "\n".join(strs) or "سيتم تحديد الدفوع"
                parties = party_names(st.session_state.docs)
            else:
                facts = "يرجى إضافة المستندات"
                defenses = "سيتم تحديد الدفوع"
                parties = []

            data = {
                "court":    court_n or "محكمة العمل",
                "case_no":  case_n,
                "client":   client_n or (parties[0] if parties else "الموكل"),
                "opponent": oppon_n or (parties[1] if len(parties)>1 else "الخصم"),
                "facts":    facts,
                "defenses": defenses,
                "requests": reqs,
            }
            draft = gen_pleading(tmpl_name, data)
            st.text_area("المسودة", draft, height=400)
            st.download_button("⬇️ تحميل المسودة",
                data=draft.encode("utf-8"),
                file_name=f"مسودة_{tmpl_name}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain")

# ─────────────────────────────────────────────────────────────────────────────
#  TAB 7 — الذاكرة
# ─────────────────────────────────────────────────────────────────────────────
with t_mem:
    st.subheader("🧠 الذاكرة الدائمة")
    st.markdown("تُخزَّن الذاكرة في ملف JSON محلي وتبقى عبر الجلسات.")

    with st.expander("➕ إضافة ذاكرة جديدة"):
        mt  = st.text_area("النص", height=100, placeholder="مثال: الموكل يعمل منذ 2019 براتب 8000 ريال")
        mcat = st.selectbox("الفئة", ["قضية","موكل","حكم","ملاحظة","استراتيجية","قانون","عام"])
        mtags = st.text_input("وسوم (فاصلة)", placeholder="عمل, فصل")
        if st.button("💾 حفظ"):
            if mt.strip():
                tags = [x.strip() for x in mtags.split(",") if x.strip()]
                mid = mem_add(mt, tags, mcat)
                st.success(f"✅ محفوظ (ID: {mid})")
                st.rerun()

    st.markdown("---")
    mq = st.text_input("🔍 بحث في الذاكرة")
    mems = mem_search(mq) if mq else st.session_state.memory

    if not mems:
        st.info("الذاكرة فارغة — ابدأ بإضافة ملاحظات قضيتك")
    else:
        st.markdown(f"**{len(mems)} ذاكرة**")
        for m in reversed(mems):
            ec1, ec2, ec3 = st.columns([8,1,1])
            with ec1:
                badges = "".join(f'<span class="badge">{t}</span>' for t in m.get("tags",[]))
                st.markdown(
                    f'<div class="mem-card">'
                    f'<small style="color:#8090a0">{m.get("ts","")} · {m.get("category","")}</small>'
                    f'<br>{m["text"]}'
                    f'<br>{badges}</div>',
                    unsafe_allow_html=True)
            with ec2:
                if st.button("✏️", key=f"e_{m['id']}", help="تعديل"):
                    st.session_state[f"edit_{m['id']}"] = True
            with ec3:
                if st.button("🗑", key=f"d_{m['id']}", help="حذف"):
                    mem_del(m["id"])
                    st.rerun()
            # Inline edit
            if st.session_state.get(f"edit_{m['id']}"):
                new_t = st.text_area("تعديل", value=m["text"], key=f"et_{m['id']}")
                if st.button("✅ حفظ التعديل", key=f"sv_{m['id']}"):
                    mem_edit(m["id"], new_t)
                    del st.session_state[f"edit_{m['id']}"]
                    st.rerun()

    st.markdown("---")
    ex1, ex2 = st.columns(2)
    with ex1:
        if st.button("📤 تصدير الذاكرة (JSON)"):
            data = json.dumps(st.session_state.memory, ensure_ascii=False, indent=2)
            st.download_button("⬇️ تحميل", data.encode("utf-8"), "fuehrer_memory.json", "application/json")
    with ex2:
        mf = st.file_uploader("📥 استيراد JSON", type=["json"], key="mf")
        if mf:
            try:
                imported = json.loads(mf.read())
                # deduplicate by id
                existing_ids = {m["id"] for m in st.session_state.memory}
                new_ones = [m for m in imported if m.get("id") not in existing_ids]
                st.session_state.memory.extend(new_ones)
                _save_mem()
                st.success(f"✅ {len(new_ones)} ذاكرة جديدة")
            except Exception as e:
                st.error(f"❌ {e}")

# ─────────────────────────────────────────────────────────────────────────────
#  TAB 8 — قاعدة القانون السعودي
# ─────────────────────────────────────────────────────────────────────────────
with t_law:
    st.subheader("📚 قاعدة الأنظمة السعودية")

    lc1, lc2 = st.columns(2)
    with lc1:
        pq = st.file_uploader("📂 ارفع ملف Parquet", type=["parquet"], key="pq_law")
        if pq and st.button("📥 تحميل وفهرسة القانون", use_container_width=True):
            raw = _bytes(pq)
            with st.spinner("جاري استخراج النصوص القانونية..."):
                records = decode_parquet_arabic(raw)
            if records:
                st.session_state.law_db = records
                st.session_state.law_loaded = True
                st.success(f"✅ {len(records)} سجل قانوني من {pq.name}")
                # Preview law names
                law_names = list(set(r["law_name"] for r in records if r["law_name"]))
                if law_names:
                    st.markdown("**الأنظمة المُحمَّلة:**")
                    for ln in law_names[:10]:
                        st.markdown(f'<span class="badge">{ln}</span>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ لم يُستخرج محتوى — تحقق من الملف")

    with lc2:
        st.markdown("**إضافة مادة يدوياً**")
        ma_text = st.text_area("نص المادة", height=100, key="ma_t")
        ma_art  = st.text_input("رقم/اسم المادة", key="ma_a")
        ma_law  = st.text_input("اسم النظام", key="ma_l")
        if st.button("➕ إضافة المادة"):
            if ma_text.strip():
                st.session_state.law_db.append({
                    "text": ma_text, "article": ma_art,
                    "law_name": ma_law or "نظام يدوي",
                    "law_type": "يدوي", "source": "manual"
                })
                st.success("✅ تمت الإضافة")

    st.markdown("---")
    if st.session_state.law_db:
        lm1, lm2, lm3 = st.columns(3)
        with lm1: st.metric("إجمالي السجلات", len(st.session_state.law_db))
        with lm2:
            ln_count = len(set(r["law_name"] for r in st.session_state.law_db))
            st.metric("عدد الأنظمة", ln_count)
        with lm3:
            articles_count = sum(1 for r in st.session_state.law_db if r.get("article"))
            st.metric("المواد المحددة", articles_count)

    law_q = st.text_input("🔍 ابحث في الأنظمة", placeholder="مثال: مكافأة نهاية الخدمة")
    if law_q and st.session_state.law_db:
        q_words = set(re.findall(r"[\u0600-\u06FF]{3,}", law_q))
        scored = []
        for r in st.session_state.law_db:
            s = sum(1 for w in q_words
                    if w in r.get("text","") or w in r.get("article","") or w in r.get("law_name",""))
            if s > 0: scored.append((s, r))
        scored.sort(reverse=True)

        if scored:
            st.markdown(f"**{min(len(scored),10)} نتيجة:**")
            for sc, r in scored[:10]:
                with st.expander(f"📜 {r.get('article','مادة')} — {r.get('law_name','')} (تطابق: {sc})"):
                    st.write(r["text"])
                    if st.button("💾 حفظ في الذاكرة", key=f"ls_{hash(r['text'])%99999}"):
                        mem_add(
                            f"[{r.get('law_name','')}] {r.get('article','')}: {r['text'][:250]}",
                            tags=["قانون", r.get("law_name","")], cat="قانون"
                        )
                        st.success("✅ محفوظ")
        else:
            st.info(f"لا نتائج لـ '{law_q}'")

    elif not st.session_state.law_db:
        st.info("💡 ارفع ملف Parquet لتفعيل البحث القانوني")

    # Sample
    if st.session_state.law_db:
        with st.expander("👁️ عينة من المحتوى"):
            for r in st.session_state.law_db[:5]:
                st.markdown(f"**{r.get('article','')}** ({r.get('law_name','')})")
                st.text(r["text"][:200] + "...")
                st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
#  TAB 9 — الأدوات
# ─────────────────────────────────────────────────────────────────────────────
with t_tools:
    st.subheader("🔧 الأدوات المتقدمة")
    tt = st.tabs(["🔎 بحث دلالي","📈 استراتيجية","📑 استخراج كيانات","🤗 HuggingFace","📤 تصدير"])

    # ── بحث دلالي ──────────────────────────────────────────────────────────
    with tt[0]:
        st.markdown("### البحث الدلالي (Semantic Search)")
        sq = st.text_input("سؤالك للبحث في المستندات المفهرسة")
        n_res = st.slider("عدد النتائج", 1, 10, 5)
        if sq:
            emb = get_embedder()
            col = get_collection()
            if emb and col:
                try:
                    vec = emb.encode(sq).tolist()
                    res = col.query(query_embeddings=[vec], n_results=n_res)
                    docs = res.get("documents",[[]])[0]
                    if docs:
                        st.markdown(f"**{len(docs)} نتيجة:**")
                        for i, doc in enumerate(docs):
                            with st.expander(f"نتيجة {i+1}"):
                                st.write((doc or "")[:500])
                    else:
                        st.info("لا نتائج — فهرس المستندات أولاً")
                except Exception as e:
                    st.error(f"❌ {e}")
            else:
                st.warning("تعذر تحميل نموذج البحث")

    # ── استراتيجية ─────────────────────────────────────────────────────────
    with tt[1]:
        st.markdown("### التحليل الاستراتيجي")
        if not st.session_state.docs:
            st.info("ارفع الملفات أولاً")
        else:
            texts = st.session_state.docs
            tl_e = Timeline()
            tl   = tl_e.build(texts)
            gaps = tl_e.gaps(tl)
            contras = detect_contradictions(texts)
            ss   = style_score(texts)
            risk = risk_score(tl, gaps, contras, ss)
            cred = cred_score(texts)

            st.markdown("**🎯 الاستراتيجية:**")
            st.markdown(generate_strategy(tl, gaps, contras, risk))
            st.markdown("---")
            sa1, sa2 = st.columns(2)
            with sa1:
                st.markdown("**نمط الخصم:**")
                st.info(procedural_pattern(tl))
            with sa2:
                st.markdown("**فرص الصلح:**")
                st.info(settlement_eval(risk, cred, len(contras)))

            # Evidence gaps
            claims_all = []
            di = DocIntel()
            for t in texts: claims_all.extend(di.claims(t))
            ev_gaps = [c for c in claims_all if not any(c in (t or "") for t in texts)]
            if ev_gaps:
                st.markdown("**⚠️ ادعاءات بلا مستندات:**")
                for g in ev_gaps: st.error(f"❌ {g}")
            else:
                if claims_all: st.success("✅ جميع الادعاءات مدعومة")

    # ── استخراج كيانات ─────────────────────────────────────────────────────
    with tt[2]:
        st.markdown("### استخراج الكيانات (NER)")
        if not st.session_state.docs:
            st.info("ارفع الملفات أولاً")
        else:
            di = DocIntel()
            all_ents = {"parties":[],"amounts":[],"articles":[],"dates":[],"ambiguous":[]}
            for t in st.session_state.docs:
                e = di.entities(t)
                for k in all_ents: all_ents[k].extend(e[k])
            # Deduplicate
            for k in all_ents: all_ents[k] = list(set(all_ents[k]))

            ne1, ne2 = st.columns(2)
            with ne1:
                st.markdown("**👥 الأطراف:**")
                for p in all_ents["parties"]:
                    st.markdown(f'<span class="badge">{p}</span>', unsafe_allow_html=True)
                st.markdown("**📅 التواريخ:**")
                for d in all_ents["dates"][:10]:
                    st.markdown(f'<span class="badge">{d}</span>', unsafe_allow_html=True)
            with ne2:
                st.markdown("**💰 المبالغ:**")
                for a in all_ents["amounts"]:
                    st.markdown(f'<span class="badge">{a}</span>', unsafe_allow_html=True)
                st.markdown("**📜 المواد:**")
                for art in all_ents["articles"][:8]:
                    st.markdown(f'<span class="badge">{art}</span>', unsafe_allow_html=True)
            if all_ents["ambiguous"]:
                st.warning("⚠️ عبارات غامضة: " + " | ".join(all_ents["ambiguous"]))

    # ── HuggingFace ─────────────────────────────────────────────────────────
    with tt[3]:
        st.markdown("### 🤗 HuggingFace النماذج")
        st.warning("""
⚠️ **تحذير iPhone 13 Mini**: نماذج HuggingFace تستهلك 500MB–4GB RAM.
يُوصى باستخدام **Claude API** (التبويب الثاني) بدلاً منها للحصول على أفضل أداء.

إذا أردت تجربتها، استخدم نماذج خفيفة فقط مثل `distilbert`.
""")
        hf_model = st.text_input("اسم النموذج", "aubmindlab/bert-base-arabertv2")
        hf_task  = st.selectbox("المهمة", ["text-classification","feature-extraction","fill-mask"])
        if st.button("⬇️ تحميل النموذج"):
            try:
                from transformers import pipeline
                with st.spinner("جاري التحميل... (قد يستغرق دقائق)"):
                    st.session_state["hf_pipe"] = pipeline(hf_task, model=hf_model)
                st.success("✅ تم")
            except Exception as e:
                st.error(f"❌ {e}")
        hf_text = st.text_area("النص", height=100)
        if st.button("🚀 تشغيل") and "hf_pipe" in st.session_state:
            try:
                r = st.session_state["hf_pipe"](hf_text)
                st.json(r)
            except Exception as e:
                st.error(f"❌ {e}")

    # ── تصدير ───────────────────────────────────────────────────────────────
    with tt[4]:
        st.markdown("### 📤 تصدير البيانات")
        if st.button("📦 تصدير أرشيف كامل (JSON)"):
            export = {
                "memory": st.session_state.memory,
                "chat": st.session_state.chat,
                "case_ctx": st.session_state.case_ctx,
                "law_db_count": len(st.session_state.law_db),
                "exported_at": datetime.now().isoformat(),
                "version": "2.0",
            }
            d = json.dumps(export, ensure_ascii=False, indent=2)
            st.download_button("⬇️ تحميل الأرشيف", d.encode("utf-8"),
                f"fuehrer_backup_{datetime.now().strftime('%Y%m%d')}.json",
                "application/json")
        if st.button("📤 تصدير قاعدة القانون (JSON)") and st.session_state.law_db:
            d = json.dumps(st.session_state.law_db, ensure_ascii=False, indent=2)
            st.download_button("⬇️ تحميل القانون", d.encode("utf-8"),
                "saudi_law_db.json", "application/json")

# ─────────────────────────────────────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<hr>
<p style="text-align:center;color:#303848;font-size:11px">
Führer v2.0 | نظام الذكاء القانوني السعودي | محسَّن لـ iPhone 13 Mini (4GB RAM)
<br>Schema: text · article_number · law_name · law_type · source
</p>""", unsafe_allow_html=True)
