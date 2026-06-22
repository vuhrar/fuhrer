import streamlit as st
import base64
import re
import tempfile
from datetime import datetime, timedelta
from PIL import Image
import PyPDF2
import pdfplumber
from docx import Document
import pytesseract
import chromadb
from sentence_transformers import SentenceTransformer
import email
from email import policy
from email.parser import BytesParser
from transformers import pipeline
import os
import io
import logging
import traceback
from typing import Any, Dict, List, Optional, Tuple

# =========================
# Logging & App Config
# =========================
logger = logging.getLogger("fuehrer_app")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

st.set_page_config(page_title="Führer", layout="wide")

# =========================
# Safer environment helpers
# =========================
def safe_filename(name: str) -> str:
    # prevent odd characters for IDs/files
    return re.sub(r"[^a-zA-Z0-9._-]", "_", name or "file")

def ensure_bytes(file_like) -> bytes:
    """
    Ensure we can read file-like objects multiple times safely.
    Streamlit UploadedFile supports .getvalue() but we fallback to reading.
    """
    try:
        if hasattr(file_like, "getvalue"):
            return file_like.getvalue()
    except Exception:
        pass
    # Fallback: read entire stream (may consume it once, so we wrap in BytesIO later)
    pos = None
    try:
        pos = file_like.tell()
    except Exception:
        pos = None
    data = file_like.read()
    if pos is not None:
        try:
            file_like.seek(pos)
        except Exception:
            pass
    return data

def normalize_text(text: str) -> str:
    # keep same normalization behavior but more defensive
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# =========================
# Caching resources
# =========================
@st.cache_resource
def load_embedder():
    return SentenceTransformer("all-MiniLM-L6-v2")

@st.cache_resource
def init_chromadb():
    client = chromadb.PersistentClient(path="./legal_db")
    return client.get_or_create_collection("legal_docs")

embedder = load_embedder()
collection = init_chromadb()

# =========================
# Document Intelligence
# =========================
class DocumentIntelligence:
    def _extract_pdf_text(self, file_bytes: bytes) -> str:
        """
        Extract text from PDF with:
        1) pdfplumber primary
        2) PyPDF2 fallback
        """
        # pdfplumber wants a file-like path/stream; BytesIO is safe
        bio = io.BytesIO(file_bytes)
        text_parts: List[str] = []

        # Try pdfplumber first
        try:
            with pdfplumber.open(bio) as pdf:
                for page in pdf.pages:
                    t = page.extract_text() or ""
                    if t.strip():
                        text_parts.append(t)
        except Exception as e:
            logger.warning("pdfplumber failed: %s", e)

        # If empty, fallback to PyPDF2
        candidate = normalize_text("\n".join(text_parts))
        if candidate:
            return candidate

        # fallback
        try:
            bio2 = io.BytesIO(file_bytes)
            reader = PyPDF2.PdfReader(bio2)
            for page in reader.pages:
                t = page.extract_text() or ""
                if t.strip():
                    text_parts.append(t)
        except Exception as e:
            logger.warning("PyPDF2 fallback failed: %s", e)

        return normalize_text("\n".join(text_parts))

    def _extract_docx_text(self, file_bytes: bytes) -> str:
        doc = Document(io.BytesIO(file_bytes))
        parts = []
        for p in doc.paragraphs:
            if p.text:
                parts.append(p.text)
        return normalize_text("\n".join(parts))

    def _extract_txt_text(self, file_bytes: bytes) -> str:
        # Robust encoding handling
        # Default to UTF-8 with fallback
        try:
            return normalize_text(file_bytes.decode("utf-8", errors="ignore"))
        except Exception:
            try:
                return normalize_text(file_bytes.decode("cp1256", errors="ignore"))
            except Exception:
                return ""

    def _extract_image_text(self, file_bytes: bytes) -> str:
        try:
            img = Image.open(io.BytesIO(file_bytes))
        except Exception:
            # Last fallback: try forcing conversion
            img = Image.open(io.BytesIO(file_bytes)).convert("RGB")

        # Keep original behavior: lang='ara'
        # Add safe fallback if tesseract arabic language not installed
        try:
            return normalize_text(pytesseract.image_to_string(img, lang="ara"))
        except Exception as e:
            logger.warning("Tesseract Arabic lang failed, fallback to default. Err=%s", e)
            try:
                return normalize_text(pytesseract.image_to_string(img))
            except Exception:
                return ""

    def _extract_eml_text(self, file_bytes: bytes) -> str:
        # email parser expects bytes stream
        try:
            msg = BytesParser(policy=policy.default).parsebytes(file_bytes)
            body = msg.get_body(preferencelist=("plain", "html"))
            if body:
                content = body.get_content() or ""
                return normalize_text(content)
        except Exception as e:
            logger.warning("EML parsing failed: %s", e)
        return ""

    def extract_text(self, file) -> str:
        """
        Extract text by extension.
        - Adds robust error handling
        - Ensures stream can be read multiple times by using bytes->BytesIO
        - Preserves all original formats and flow.
        """
        ext = (getattr(file, "name", "") or "").split(".")[-1].lower()
        text = ""
        try:
            file_bytes = ensure_bytes(file)

            if ext == "pdf":
                text = self._extract_pdf_text(file_bytes)
            elif ext == "docx":
                text = self._extract_docx_text(file_bytes)
            elif ext == "txt":
                text = self._extract_txt_text(file_bytes)
            elif ext in ["png", "jpg", "jpeg"]:
                text = self._extract_image_text(file_bytes)
            elif ext == "eml":
                text = self._extract_eml_text(file_bytes)
            else:
                return ""
        except Exception as e:
            logger.error("extract_text failed: %s", e)
            return ""

        # Keep original normalization intent
        return normalize_text(text)

    def extract_dates(self, text: str) -> List[str]:
        pattern = r"(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})"
        matches = re.findall(pattern, text or "")
        # Original format: d/m/Y (keep month/day ordering)
        return [f"{m[0]}/{m[1]}/{m[2]}" for m in matches]

    def extract_articles(self, text: str) -> List[str]:
        return re.findall(r"(المادة\s*[\(]?\s*[١٢٣٤٥٦٧٨٩٠]+\s*[\)]?)", text or "")

    def extract_ambiguous(self, text: str) -> List[str]:
        phrases = [
            "يحق للجهة",
            "ما تراه مناسباً",
            "وفق الإجراءات النظامية",
            "حسب المصلحة",
            "تقدير الجهة",
            "لجنة مختصة",
            "سيتم الرد لاحقاً",
            "نحن نؤكد",
            "كما تعلمون",
        ]
        return [p for p in phrases if p and (text or "") .find(p) != -1]

    def extract_claims(self, text: str) -> List[str]:
        claims = []
        patterns = [r"ثبت لدينا", r"نستدل من", r"بناءً على ما ورد", r"نشير إلى", r"نلفت انتباهكم"]
        t = text or ""
        for p in patterns:
            if re.search(p, t):
                claims.append(p)
        return claims

# =========================
# Timeline
# =========================
class TimelineEngine:
    def build_timeline(self, texts: List[str]) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        parser = DocumentIntelligence()

        for idx, txt in enumerate(texts):
            # Make extraction resilient
            try:
                dates = parser.extract_dates(txt)
            except Exception as e:
                logger.warning("extract_dates failed idx=%s err=%s", idx, e)
                continue

            for d in dates:
                try:
                    # Original expects %d/%m/%Y
                    dt = datetime.strptime(d, "%d/%m/%Y")
                    events.append(
                        {"date": dt, "text": (txt or "")[:200], "file_index": idx}
                    )
                except Exception:
                    # Keep original silent behavior for invalid dates
                    pass

        events.sort(key=lambda x: x["date"])
        return events

    def calculate_gaps(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        gaps: List[Dict[str, Any]] = []
        for i in range(len(events) - 1):
            try:
                diff = (events[i + 1]["date"] - events[i]["date"]).days
                if diff > 30:
                    gaps.append(
                        {
                            "from": events[i]["date"].strftime("%d/%m/%Y"),
                            "to": events[i + 1]["date"].strftime("%d/%m/%Y"),
                            "days": diff,
                        }
                    )
            except Exception as e:
                logger.warning("calculate_gaps failed i=%s err=%s", i, e)
                continue
        return gaps

# =========================
# Rule Engine (SAFE replacement for eval)
# =========================
class RuleEngine:
    def __init__(self):
        self.rules = [
            {"cond": "days_abandoned > 30", "out": "⚠️ مدة الانقطاع تجاوزت 30 يوماً (ترك عمل)"},
            {"cond": "days_abandoned > 15 and days_abandoned <= 30", "out": "⚠️ مدة الانقطاع 15-30 يوماً (إنذار)"},
            {"cond": "days_since_firing > 365", "out": "⛔ مضي أكثر من سنة على الفصل (سقوط حق التقاضي)"},
            {"cond": "days_since_firing > 180 and days_since_firing <= 365", "out": "⏳ مضي أكثر من 6 أشهر على الفصل (تقادم جزئي)"},
            {"cond": "reply_delay > 30", "out": "⏳ تأخير إداري من الخصم (أكثر من 30 يوماً)"},
            {"cond": "reply_delay > 15 and reply_delay <= 30", "out": "⏳ تأخير إداري متوسط (15-30 يوماً)"},
            {"cond": "ambiguous_phrases > 3", "out": "🔍 عبارات غامضة في خطابات الخصم (طعن محتمل)"},
            {"cond": "ambiguous_phrases > 5", "out": "🔍 عبارات غامضة كثيرة (تعسف)"},
            {"cond": "contradictions > 1", "out": "⚡ تناقض داخلي في مراسلات الخصم"},
            {"cond": "contradictions > 3", "out": "⚡ تناقضات متعددة (فقدان المصداقية)"},
            {"cond": "force_majeure is False and missed_deadline is True", "out": "📌 فاتك موعد نظامي دون عذر قاهر"},
            {"cond": "settlement_offer is True and risk_score > 60", "out": "🤝 الصلح أفضل من الاستمرار"},
            {"cond": "settlement_offer is True and risk_score <= 40", "out": "⚖️ الصلح ممكن لكن القضية قوية"},
            {"cond": "court_grade == 'Supreme' and similarity > 0.8", "out": "⭐ حكم مشابه من المحكمة العليا (وزن استدلالي عالٍ)"},
            {"cond": "court_grade == 'Appeal' and similarity > 0.7", "out": "📜 حكم من محكمة الاستئناف مشابه"},
            {"cond": "court_grade == 'First' and similarity > 0.6", "out": "📄 حكم من محكمة الدرجة الأولى مشابه"},
            {"cond": "force_majeure is True and days_abandoned > 60", "out": "📌 عذر قاهر يبرر الانقطاع الطويل"},
            {"cond": "service_length < 2", "out": "📌 مدة الخدمة أقل من سنتين (مكافأة نصف شهر)"},
            {"cond": "service_length >= 2 and service_length < 5", "out": "📌 مدة الخدمة 2-5 سنوات (مكافأة شهرين)"},
            {"cond": "service_length >= 5", "out": "📌 مدة الخدمة أكثر من 5 سنوات (مكافأة كاملة)"},
            {"cond": "absence_days > 15 and absence_days <= 20", "out": "⚠️ غياب 15-20 يوماً (إنذار أول)"},
            {"cond": "absence_days > 20 and absence_days <= 30", "out": "⚠️ غياب 20-30 يوماً (إنذار ثانٍ)"},
            {"cond": "absence_days > 30", "out": "⚠️ غياب أكثر من 30 يوماً (فصل)"},
            {"cond": "no_investigation_before_firing", "out": "⚖️ فصل بدون تحقيق (بطلان القرار)"},
            {"cond": "notification_after_7_days", "out": "⚖️ تبليغ بعد 7 أيام (إخلال إجرائي)"},
            {"cond": "not_registered_letter", "out": "⚖️ تبليغ بكتاب غير مسجل (عدم العلم)"},
            {"cond": "violation_date_not_specified", "out": "⚖️ عدم تحديد تاريخ المخالفة (غموض يفسر لصالحك)"},
            {"cond": "penalty_after_1_year", "out": "⛔ مضى سنة على المخالفة دون عقوبة (سقوط الحق)"},
            {"cond": "no_appeal_period_specified", "out": "⚖️ عدم تحديد مدة التظلم (لك الاعتراض في أي وقت)"},
            {"cond": "expert_request_rejected", "out": "⚖️ رفض طلب الخبرة (إخلال بحق الدفاع)"},
            {"cond": "judgment_without_hearing", "out": "⚖️ حكم دون سماع أقوالك (بطلان)"},
            {"cond": "documents_not_submitted_within_5_days", "out": "⚖️ تأخر تقديم المستندات (لا يؤثر على أصل الحق)"},
            {"cond": "no_response_after_90_days", "out": "⚖️ مضى 90 يوماً على طلبك دون رد (اعتبار موافقة ضمنية)"},
            {"cond": "new_evidence_after_deadline", "out": "📌 مستندات جديدة بعد الميعاد (تُقبل لتعلق بالنظام العام)"},
            {"cond": "opponent_refuses_to_produce_document", "out": "⚖️ امتناع الخصم عن تقديم مستند تحت يده (يُحكم ضده)"},
            {"cond": "document_not_signed", "out": "⚖️ مستند غير موقع (لا حجية له)"},
            {"cond": "document_unsigned_copy", "out": "⚖️ صورة غير مصدقة (لا يُعتد بها)"},
            {"cond": "forgery_proven", "out": "⚖️ تزوير ثبت (جريمة)"},
            {"cond": "witness_testimony_accepted", "out": "📌 شهادة شهود مقبولة (إن كانت جائزة)"},
            {"cond": "witnesses_contradictory", "out": "⚖️ تناقض شهادات الشهود (تُرجح أقوال الأكثر عدالة)"},
            {"cond": "witness_relative_of_opponent", "out": "⚖️ شاهد قريب للخصم (شهادته مردودة)"},
            {"cond": "witness_old_event", "out": "⚖️ شهادة عن واقعة قديمة (لا تُقبل للتقادم)"},
            {"cond": "witness_absent_without_excuse", "out": "⚖️ غياب الشاهد دون عذر (يُغرّم)"},
            {"cond": "two_witnesses_vs_one", "out": "📌 شاهدين ضد واحد (تُقبل شهادتهما)"},
            {"cond": "digital_evidence_not_secure", "out": "⚖️ دليل رقمي غير مؤمن (لا حجية له)"},
            {"cond": "non_judicial_acknowledgment", "out": "📌 إقرار غير قضائي (حجة على المقر)"},
            {"cond": "repeated_threats", "out": "⚖️ تكرار التهديد من الخصم (تعسف)"},
            {"cond": "unlimited_deadline_request", "out": "⚖️ طلب مهلة غير محددة (مماطلة)"},
            {"cond": "single_response_to_multiple_requests", "out": "⚖️ رد واحد على عدة طلبات (تغييب للحقائق)"},
            {"cond": "referral_to_another_reference", "out": "⚖️ إحالة لمرجع آخر (دوران إداري)"},
            {"cond": "irrelevant_document_request", "out": "⚖️ طلب مستندات غير ذات صلة (مناورة)"},
            {"cond": "unsigned_meeting_minutes", "out": "⚖️ محضر اجتماع غير موقع (عدم اعتراف)"},
            {"cond": "vague_language_in_letter", "out": "⚖️ لغة غامضة في خطاب الخصم (طعن محتمل)"},
            {"cond": "apology_without_correction", "out": "⚖️ اعتذار دون تصحيح (لا قيمة قانونية له)"},
            {"cond": "study_promise_without_action", "out": "⚖️ وعد بالدراسة دون إجراء (تسويف)"},
            {"cond": "meeting_without_agenda", "out": "⚖️ اجتماع دون جدول أعمال (غير جاد)"},
            {"cond": "representative_without_authority", "out": "⚖️ حضور مندوب دون صفة (عدم صفة)"},
            {"cond": "letter_sent_after_working_hours", "out": "⚖️ إرسال خطاب بعد الدوام (يُحتسب في اليوم التالي)"},
            {"cond": "supreme_court_ruling", "out": "⭐ حكم من المحكمة العليا (أقوى وزن استدلالي)"},
            {"cond": "appeal_court_ruling", "out": "📜 حكم من محكمة الاستئناف (وزن متوسط)"},
            {"cond": "first_instance_ruling", "out": "📄 حكم من محكمة الدرجة الأولى (وزن أقل)"},
            {"cond": "recent_ruling", "out": "📌 حكم حديث (خلال سنة) (وزن أعلى)"},
            {"cond": "old_ruling", "out": "📌 حكم قديم (أكثر من 10 سنوات) (وزن أقل)"},
            {"cond": "high_similarity_ruling", "out": "⭐ سابقة مباشرة (تشابه 90% فما فوق)"},
            {"cond": "medium_similarity_ruling", "out": "📌 مؤشر (تشابه 50-90%)"},
            {"cond": "specialized_circuit_ruling", "out": "⭐ حكم من دائرة متخصصة (وزن خاص)"},
            {"cond": "unanimous_ruling", "out": "⭐ حكم بالإجماع (وزن أقوى)"},
            {"cond": "majority_ruling", "out": "📌 حكم بأغلبية (وزن أقل)"},
            {"cond": "settlement_offered_before_decision", "out": "📌 عرض صلح قبل القرار (مؤشر حسن نية)"},
            {"cond": "rejected_settlement_without_reason", "out": "⚖️ رفض الصلح دون مبرر (تعنت)"},
            {"cond": "offered_settlement_and_refused", "out": "📌 عرضت صلح ورفض (يحق لك التعويض)"},
            {"cond": "government_settlement", "out": "📌 صلح مع جهة حكومية (إجراء شكلي)"},
            {"cond": "both_parties_agree_settlement", "out": "✅ اتفاق صلح نهائي"},
            {"cond": "settlement_partial_right", "out": "📌 تنازل عن جزء من الحق (يُحتسب)"},
            {"cond": "settlement_meeting_absence", "out": "⚖️ غياب الخصم عن جلسة الصلح (إنذار)"},
            {"cond": "settlement_deadline_request", "out": "📌 طلب مهلة للصلح (تُمنح مهلة معقولة)"},
            {"cond": "settlement_out_of_court", "out": "📌 صلح خارج المحكمة (يُصدق عليه)"},
            {"cond": "settlement_broken", "out": "⚖️ نقض الصلح (يُلزم بالتعويض)"},
            {"cond": "arbitrary_dismissal", "out": "⚖️ فصل تعسفي (تستحق تعويضاً)"},
            {"cond": "violation_not_proven", "out": "⚖️ عدم ثبوت المخالفة (يُلغى الفصل)"},
            {"cond": "salary_delay_proven", "out": "⚖️ تأخير الرواتب (تستحق تعويضاً)"},
            {"cond": "end_of_service_benefit_not_paid", "out": "⚖️ عدم صرف المكافأة (تطالب بها)"},
            {"cond": "unlawful_deduction", "out": "⚖️ خصم من الراتب بغير حق (يُرد لك)"},
            {"cond": "disproportionate_fine", "out": "⚖️ غرامة غير متناسبة (تُخفض)"},
            {"cond": "fine_not_specified_in_contract", "out": "⚖️ غرامة غير محددة في العقد (لا تُوقع)"},
            {"cond": "repeated_violation", "out": "⚖️ تكرار المخالفة (يجوز مضاعفة الغرامة)"},
            {"cond": "fine_contrary_to_regulations", "out": "⚖️ غرامة مخالفة للنظام (تُلغى)"},
            {"cond": "undefined_compensation", "out": "⚖️ تعويض غير محدد (يُقدر بقيمة الضرر)"},
            {"cond": "proven_illness", "out": "📌 إعاقة صحية (عذر مقبول)"},
            {"cond": "weather_conditions_prevent_attendance", "out": "📌 ظروف جوية تمنع الحضور (عذر قاهر)"},
            {"cond": "death_of_relative", "out": "📌 وفاة قريب (إجازة رسمية)"},
            {"cond": "emergency_accident", "out": "📌 حادث طارئ (عذر مقبول)"},
            {"cond": "authority_closed", "out": "📌 إغلاق الجهة (عذر قاهر)"},
            {"cond": "service_disruption", "out": "📌 انقطاع الخدمات (عذر قاهر)"},
            {"cond": "lawyer_communication_failure", "out": "📌 تعذر التواصل مع المحامي (عذر مقبول)"},
            {"cond": "strikes", "out": "📌 إضرابات (عذر قاهر)"},
            {"cond": "administrative_order_preventing_attendance", "out": "📌 قرار إداري يمنع الحضور (عذر مقبول)"},
            {"cond": "epidemic", "out": "📌 وباء (عذر قاهر)"},
            {"cond": "electronic_communication_failure", "out": "📌 تعطل الاتصال الإلكتروني (عذر مقبول)"},
            {"cond": "natural_disaster", "out": "📌 كارثة طبيعية (عذر قاهر)"},
            {"cond": "travel_ban", "out": "📌 منع السفر (عذر قاهر)"},
            {"cond": "health_quarantine", "out": "📌 حجر صحي (عذر قاهر)"},
            {"cond": "fire_or_flood", "out": "📌 حريق أو فيضان (عذر قاهر)"},
            {"cond": "political_unrest", "out": "📌 اضطرابات سياسية (عذر قاهر)"},
            {"cond": "absence_of_legal_representative", "out": "📌 غياب الممثل القانوني (عذر مقبول)"},
            {"cond": "court_closure", "out": "📌 إغلاق المحكمة (عذر قاهر)"},
        ]

    def _eval_condition_safe(self, cond: str, ctx: Dict[str, Any]) -> bool:
        """
        Evaluate conditions safely without eval().
        Supported patterns (covering all existing rules):
        - "var", "var is True/False"
        - comparisons: >, >=, <, <=
        - equality: == 'String'
        - boolean combine with 'and'
        """
        try:
            # Split by " and " (rules are simple conjunctions)
            parts = [p.strip() for p in cond.split(" and ")]
            for part in parts:
                if not part:
                    continue

                # Handle "var is True/False"
                m_is = re.match(r"^(\w+)\s+is\s+(True|False)$", part)
                if m_is:
                    key = m_is.group(1)
                    val = m_is.group(2) == "True"
                    if bool(ctx.get(key, False)) != val:
                        return False
                    continue

                # Handle "var" alone (truthy)
                m_bool = re.match(r"^(\w+)$", part)
                if m_bool:
                    key = m_bool.group(1)
                    if not bool(ctx.get(key, False)):
                        return False
                    continue

                # Handle comparisons: var > N, var <= N etc.
                m_cmp = re.match(r"^(\w+)\s*(>=|<=|>|<)\s*([0-9.]+)$", part)
                if m_cmp:
                    key = m_cmp.group(1)
                    op = m_cmp.group(2)
                    raw = m_cmp.group(3)
                    rhs = float(raw)
                    lhs = float(ctx.get(key, 0))
                    ok = {
                        ">": lhs > rhs,
                        ">=": lhs >= rhs,
                        "<": lhs < rhs,
                        "<=": lhs <= rhs,
                    }[op]
                    if not ok:
                        return False
                    continue

                # Handle numeric equality: var == 0.8 (not present but safe)
                m_eq_num = re.match(r"^(\w+)\s*==\s*([0-9.]+)$", part)
                if m_eq_num:
                    key = m_eq_num.group(1)
                    rhs = float(m_eq_num.group(2))
                    lhs = float(ctx.get(key, 0))
                    if lhs != rhs:
                        return False
                    continue

                # Handle string equality: court_grade == 'Supreme'
                m_eq_str = re.match(r"^(\w+)\s*==\s*'([^']*)'$", part)
                if m_eq_str:
                    key = m_eq_str.group(1)
                    rhs = m_eq_str.group(2)
                    if str(ctx.get(key, "")) != rhs:
                        return False
                    continue

                # If unsupported pattern, fail closed (do not trigger)
                return False

            return True
        except Exception as e:
            logger.warning("safe condition eval failed cond=%s err=%s", cond, e)
            return False

    def apply(self, data: Dict[str, Any]) -> List[str]:
        alerts = []
        for r in self.rules:
            try:
                if self._eval_condition_safe(r["cond"], data):
                    alerts.append(r["out"])
            except Exception:
                # Preserve original silent behavior per rule
                continue
        return alerts

# =========================
# Dual Analyzer
# =========================
class DualAnalyzer:
    def analyze(self, timeline: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        strengths, weaknesses = [], []
        for ev in timeline:
            txt = (ev.get("text") or "").lower()

            if "أقر" in txt or "اعترف" in txt:
                weaknesses.append("اعتراف ضمني")
            if "عذر" in txt or "مرض" in txt or "ظروف" in txt:
                strengths.append("أعذار رسمية")
            if "توقيع" not in txt and "ختم" not in txt:
                weaknesses.append("خطاب بدون توقيع")
            if "المادة" in (ev.get("text") or ""):
                strengths.append("استشهاد بمواد نظامية")
            if "تهديد" in txt or "فوراً" in txt:
                weaknesses.append("لغة تهديدية")
            if "نحن نؤكد" in (ev.get("text") or ""):
                weaknesses.append("تأكيد دون مستند")
            if "نحن نعلم" in (ev.get("text") or ""):
                strengths.append("إقرار بالعلم")
            if "نحن نرفض" in (ev.get("text") or ""):
                strengths.append("موقف حازم")

        return {"strengths": list(set(strengths)), "weaknesses": list(set(weaknesses))}

# =========================
# Pleading Engine
# =========================
class PleadingEngine:
    def generate(self, template_type, data):
        templates = {
            "مذكرة دفاع": """
السيد/ رئيس محكمة {court} المحترم،
الموضوع: مذكرة دفاع في الدعوى رقم {case_no}.
نحن {client}، نقدم هذه المذكرة ضد {opponent}، ونبين:
أولاً: الوقائع: {facts}
ثانياً: الدفوع: {defenses}
ثالثاً: الطلبات: {requests}
""",
            "صحيفة دعوى": """
السيد/ رئيس محكمة {court} المحترم،
الموضوع: صحيفة دعوى من {client} ضد {opponent}.
الوقائع: {facts}
الأسباب: {defenses}
الطلبات: {requests}
""",
            "عريضة اعتراض": """
السيد/ رئيس محكمة {court} المحترم،
الموضوع: اعتراض على القرار رقم {case_no}.
أسباب الاعتراض: {defenses}
الطلبات: {requests}
""",
        }
        return (templates.get(template_type, "قالب غير موجود")).format(**data)

# =========================
# Analysis Utilities (same features)
# =========================
def detect_contradictions(texts: List[str]) -> List[str]:
    contradictions = []
    for idx, txt in enumerate(texts):
        t = txt or ""
        dates = re.findall(r"\d{1,2}/\d{1,2}/\d{2,4}", t)
        if len(dates) >= 2 and dates[0] == dates[1]:
            contradictions.append(f"تناقض في التواريخ بالملف {idx+1}")
        # Keep original (though redundant condition in original is a bug logically: "مادة" in txt twice)
        if "مادة" in t and "خطأ" in t and "مادة" in t:
            contradictions.append(f"خطأ في إشارة لمادة بالملف {idx+1}")
        if "توقيع" not in t and "ختم" in t:
            contradictions.append(f"ختم بدون توقيع بالملف {idx+1}")
    return contradictions

def analyze_style(texts: List[str]) -> int:
    score = 0
    for t in texts:
        tt = t or ""
        if "تهديد" in tt or "فوراً" in tt or "يجب" in tt:
            score += 1
        if "نرجو" in tt or "نأمل" in tt:
            score -= 1
        if "عاجل" in tt:
            score += 2
    return max(score, 0)

def calculate_deadlines(events: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    results = []
    for ev in events:
        etext = ev.get("text") or ""
        edate = ev.get("date")
        if not isinstance(edate, datetime):
            continue

        if "فصل" in etext or "إنهاء" in etext or "إيقاف" in etext:
            deadline = edate + timedelta(days=365)
            results.append({"event": etext[:50], "deadline": deadline.strftime("%d/%m/%Y")})
        if "اعتراض" in etext:
            deadline = edate + timedelta(days=30)
            results.append({"event": etext[:50], "deadline": deadline.strftime("%d/%m/%Y")})
        if "استئناف" in etext:
            deadline = edate + timedelta(days=60)
            results.append({"event": etext[:50], "deadline": deadline.strftime("%d/%m/%Y")})
    return results

def calculate_risk(timeline, gaps, contradictions, style_score):
    risk = len(gaps) * 2 + len(contradictions) * 5 + style_score
    if len(timeline) < 2:
        risk += 10
    if len(timeline) > 10:
        risk -= 5
    return min(max(risk, 0), 100)

def credibility_score(texts: List[str]) -> int:
    score = 100
    for t in texts:
        tt = t or ""
        if "نحن نؤكد" in tt:
            score -= 5
        if "مادة" in tt and "خطأ" in tt:
            score -= 10
        if "كما سبق" in tt:
            score -= 3
        if "نحن نعتقد" in tt:
            score -= 2
        if "نحن على يقين" in tt:
            score -= 4
    return max(score, 0)

def extract_fact_summary(timeline: List[Dict[str, Any]]) -> str:
    if not timeline:
        return "لا توجد وقائع كافية."
    summary = "تسلسل الأحداث الرئيسية:\n"
    for ev in timeline[:5]:
        dt = ev.get("date")
        txt = (ev.get("text") or "")
        if isinstance(dt, datetime):
            summary += f"- {dt.strftime('%d/%m/%Y')}: {txt[:100]}...\n"
    return summary

def extract_party_names(texts: List[str]) -> List[str]:
    parties = []
    keywords = [
        "المدعي", "المدعى عليه", "الهيئة", "الشركة", "المؤسسة", "الموظف", "العامل", "الوكيل", "المحامي"
    ]
    for t in texts:
        tt = t or ""
        for p in keywords:
            if p in tt:
                parties.append(p)
    return list(set(parties)) if parties else ["أطراف غير محددة"]

def generate_strategy(timeline, gaps, contradictions, risk):
    strategy = []
    if gaps:
        strategy.append("استغل الفجوات الزمنية كدليل على تعنت الخصم.")
    if contradictions:
        strategy.append("قدم التناقضات المكتشفة كطعن على مصداقية الخصم.")
    if risk > 70:
        strategy.append("الخطر مرتفع، يوصى بالاستعداد للتصعيد القضائي.")
    elif risk > 50:
        strategy.append("خطر متوسط، يوصى بالتفاوض مع الاحتفاظ بالخيارات القضائية.")
    else:
        strategy.append("خطر منخفض، يمكن المضي قدماً في الإجراءات الحالية.")
    if not gaps and not contradictions and risk < 40:
        strategy.append("الوضع مستقر، يمكن الاستمرار بالوتيرة الحالية.")
    if len(gaps) > 3:
        strategy.append("فجوات متعددة، يوصى بتقديم شكوى إدارية ضد تعنت الخصم.")
    return "\n".join(strategy)

def extract_evidence_gaps(texts: List[str], claims: List[str]) -> List[str]:
    gaps = []
    for claim in claims:
        found = False
        for t in texts:
            if claim and claim in (t or ""):
                found = True
                break
        if not found:
            gaps.append(claim)
    return gaps

def procedural_pattern_analyzer(timeline):
    if len(timeline) < 2:
        return "لا توجد بيانات كافية لتحليل النمط."
    try:
        weekdays = [ev["date"].weekday() for ev in timeline if isinstance(ev.get("date"), datetime)]
        if weekdays and all(w in [4, 5] for w in weekdays):
            return "الخصم يرد في نهاية الأسبوع (مماطلة متعمدة)."
        hours = [ev["date"].hour for ev in timeline if isinstance(ev.get("date"), datetime)]
        if hours and all(h > 15 for h in hours):
            return "الخصم يرد في ساعات متأخرة (محاولة لتعطيل الرد)."
    except Exception:
        pass
    return "لا نمط محدد، إجراءات عادية."

def settlement_calculator(risk, credibility, contradictions_count):
    if risk > 70:
        return "فرصة الصلح منخفضة (الخصم متصلب)."
    elif risk < 30 and credibility > 70 and contradictions_count == 0:
        return "فرصة الصلح عالية، يوصى بالتقدم بعرض."
    else:
        return "فرصة الصلح متوسطة، يحتاج تقييم إضافي."

# =========================
# Auto-load law reference (keep feature)
# =========================
law_file_path = "الأنظمة السعودية.pdf"
if os.path.exists(law_file_path):
    try:
        with open(law_file_path, "rb") as f:
            text = DocumentIntelligence().extract_text(f)
            if text:
                chunks = [text[i:i+800] for i in range(0, len(text), 800)]
                # Use ids deterministically to avoid duplicates (best effort)
                for i, chunk in enumerate(chunks):
                    emb = embedder.encode(chunk).tolist()
                    collection.add(
                        documents=[chunk],
                        embeddings=[emb],
                        ids=[f"law_{i}"],
                    )
        st.success("✅ تم تحميل الأنظمة السعودية كمرجع تلقائياً.")
    except Exception as e:
        logger.error("Auto load law failed: %s", e)
        st.warning("⚠️ تعذر تحميل ملف الأنظمة تلقائياً (قد تكون هناك تبعيات أو صلاحيات).")
else:
    st.warning("⚠️ ملف الأنظمة غير موجود، ارفعه يدوياً في التبويب الأول.")

# =========================
# UI Tabs
# =========================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📚 الملفات", "🔎 البحث", "📊 الجدول الزمني", "⚖️ التحليل الثنائي", "📄 التقارير",
    "🧠 الاستراتيجية", "⚙️ الأدوات المتقدمة", "🤖 Hugging Face"
])

# Keep upload list at module level like original intent
uploaded_files: List[Any] = []

# =========================
# Shared computed cache per run
# =========================
def compute_texts_and_timeline(files: List[Any]) -> Tuple[List[str], List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    parser = DocumentIntelligence()
    texts = []
    for f in files:
        try:
            t = parser.extract_text(f)
            texts.append(t)
        except Exception as e:
            logger.warning("File extract failed for %s: %s", getattr(f, "name", "?"), e)
            texts.append("")

    engine = TimelineEngine()
    timeline = engine.build_timeline(texts)
    gaps = engine.calculate_gaps(timeline)
    contradictions = detect_contradictions(texts)
    return texts, timeline, gaps, contradictions

# =========================
# Tab1: Upload & Index
# =========================
with tab1:
    st.subheader("رفع الملفات")
    uploaded = st.file_uploader(
        "اختر الملفات (PDF, DOCX, TXT, صور, EML)",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "eml"],
        accept_multiple_files=True,
    )
    if uploaded:
        uploaded_files = uploaded
        if st.button("فهرسة وتحليل"):
            parser = DocumentIntelligence()
            total = 0
            try:
                for f in uploaded_files:
                    text = parser.extract_text(f)
                    if not text:
                        continue
                    chunks = [text[i:i+800] for i in range(0, len(text), 800)]
                    # Add embeddings per chunk (keep feature)
                    for i, chunk in enumerate(chunks):
                        emb = embedder.encode(chunk).tolist()
                        fid = safe_filename(getattr(f, "name", "file"))
                        collection.add(documents=[chunk], embeddings=[emb], ids=[f"{fid}_{i}"])
                    total += len(chunks)
                st.success(f"تم فهرسة {total} قطعة")
            except Exception as e:
                logger.error("Indexing failed: %s", e)
                st.error("حدث خطأ أثناء الفهرسة. راجع السجلات/الكونسول لمعرفة السبب.")

# =========================
# Tab2: Semantic Search
# =========================
with tab2:
    st.subheader("البحث الدلالي")
    query = st.text_input("اكتب سؤالك القانوني")
    if query:
        try:
            q_emb = embedder.encode(query).tolist()
            results = collection.query(query_embeddings=[q_emb], n_results=5)
            docs = results.get("documents", [])
            if docs and docs[0]:
                for r in docs[0]:
                    st.write(f"- {(r or '')[:500]}...")
            else:
                st.info("لم يتم العثور على نتائج مناسبة.")
        except Exception as e:
            logger.error("Search failed: %s", e)
            st.error("حدث خطأ أثناء البحث. تأكد من إعدادات vector DB أو تبعيات Chroma.")

# =========================
# Tab3: Timeline & gaps
# =========================
with tab3:
    st.subheader("الجدول الزمني والفجوات")
    if uploaded_files:
        try:
            parser = DocumentIntelligence()
            texts = [parser.extract_text(f) for f in uploaded_files]
            engine = TimelineEngine()
            timeline = engine.build_timeline(texts)
            gaps = engine.calculate_gaps(timeline)

            for ev in timeline:
                dt = ev.get("date")
                txt = ev.get("text") or ""
                if isinstance(dt, datetime):
                    st.write(f"- {dt.strftime('%d/%m/%Y')}: {txt[:100]}...")

            if gaps:
                for g in gaps:
                    st.warning(f"فجوة {g['days']} يوم من {g['from']} إلى {g['to']}")
        except Exception as e:
            logger.error("Timeline tab failed: %s", e)
            st.error("حدث خطأ أثناء بناء الجدول الزمني.")

# =========================
# Tab4: Dual analysis & metrics
# =========================
with tab4:
    st.subheader("نقاط القوة والضعف")
    if uploaded_files:
        try:
            parser = DocumentIntelligence()
            texts = [parser.extract_text(f) for f in uploaded_files]
            engine = TimelineEngine()
            timeline = engine.build_timeline(texts)
            gaps = engine.calculate_gaps(timeline)
            contradictions = detect_contradictions(texts)
            style_score = analyze_style(texts)
            risk = calculate_risk(timeline, gaps, contradictions, style_score)
            cred = credibility_score(texts)
            analyzer = DualAnalyzer()
            result = analyzer.analyze(timeline)

            col1, col2 = st.columns(2)
            with col1:
                st.metric("الخطورة", f"{risk}/100")
                st.metric("مصداقية الخصم", f"{cred}/100")
            with col2:
                st.metric("التناقضات", len(contradictions))
                st.metric("التصعيد", style_score)

            for s in result["strengths"]:
                st.success(s)
            for w in result["weaknesses"]:
                st.error(w)

        except Exception as e:
            logger.error("Tab4 failed: %s", e)
            st.error("حدث خطأ أثناء التحليل الثنائي.")

# =========================
# Tab5: Reports & templates
# =========================
with tab5:
    st.subheader("التقارير واللوائح")
    if uploaded_files and st.button("تقرير كامل"):
        try:
            parser = DocumentIntelligence()
            texts = [parser.extract_text(f) for f in uploaded_files]
            engine = TimelineEngine()
            timeline = engine.build_timeline(texts)
            gaps = engine.calculate_gaps(timeline)
            contradictions = detect_contradictions(texts)
            style_score = analyze_style(texts)
            deadlines = calculate_deadlines(timeline)
            risk = calculate_risk(timeline, gaps, contradictions, style_score)
            cred = credibility_score(texts)
            facts = extract_fact_summary(timeline)
            parties = extract_party_names(texts)

            report = (
                f"الخطورة: {risk}\n"
                f"المصداقية: {cred}\n"
                f"التناقضات: {len(contradictions)}\n"
                f"الفجوات: {len(gaps)}\n"
                f"الوقائع: {facts}\n"
                f"المواعيد:\n"
            )
            for d in deadlines:
                report += f"- {d['event']} → {d['deadline']}\n"

            st.download_button("تحميل", data=report, file_name="تقرير.txt")
        except Exception as e:
            logger.error("Full report failed: %s", e)
            st.error("حدث خطأ أثناء إنشاء التقرير الكامل.")

    template = st.selectbox("نوع اللائحة", ["مذكرة دفاع", "صحيفة دعوى", "عريضة اعتراض"])
    if uploaded_files and st.button("أنشئ مسودة"):
        try:
            parser = DocumentIntelligence()
            texts = [parser.extract_text(f) for f in uploaded_files]
            engine_t = TimelineEngine()
            timeline = engine_t.build_timeline(texts)
            facts = extract_fact_summary(timeline)
            parties = extract_party_names(texts)

            analyzer = DualAnalyzer()
            result = analyzer.analyze(timeline)
            defenses = "\n".join(result["strengths"]) if result["strengths"] else "سيتم تحديد الدفوع لاحقاً"

            data = {
                "court": "محكمة العمل",
                "case_no": "قيد التحليل",
                "client": parties[0] if parties else "الطرف الأول",
                "opponent": parties[1] if len(parties) > 1 else "الخصم",
                "facts": facts,
                "defenses": defenses,
                "requests": "إلغاء القرار والتعويض",
            }

            engine_p = PleadingEngine()
            st.text_area("المسودة", engine_p.generate(template, data), height=300)
        except Exception as e:
            logger.error("Draft generation failed: %s", e)
            st.error("حدث خطأ أثناء إنشاء المسودة.")

# =========================
# Tab6: Strategy
# =========================
with tab6:
    st.subheader("الاستراتيجية")
    if uploaded_files:
        try:
            parser = DocumentIntelligence()
            texts = [parser.extract_text(f) for f in uploaded_files]
            engine = TimelineEngine()
            timeline = engine.build_timeline(texts)
            gaps = engine.calculate_gaps(timeline)
            contradictions = detect_contradictions(texts)
            style_score = analyze_style(texts)
            risk = calculate_risk(timeline, gaps, contradictions, style_score)

            st.markdown(generate_strategy(timeline, gaps, contradictions, risk))
        except Exception as e:
            logger.error("Strategy tab failed: %s", e)
            st.error("حدث خطأ أثناء حساب الاستراتيجية.")

# =========================
# Tab7: Advanced Tools
# =========================
with tab7:
    st.subheader("الأدوات المتقدمة")
    if uploaded_files:
        try:
            parser = DocumentIntelligence()
            texts = [parser.extract_text(f) for f in uploaded_files]
            engine = TimelineEngine()
            timeline = engine.build_timeline(texts)
            gaps = engine.calculate_gaps(timeline)
            contradictions = detect_contradictions(texts)
            cred = credibility_score(texts)
            style_score = analyze_style(texts)
            risk = calculate_risk(timeline, gaps, contradictions, style_score)

            for ev in timeline:
                etext = ev.get("text") or ""
                dt = ev.get("date")
                if isinstance(dt, datetime) and ("فصل" in etext or "إيقاف" in etext or "اعتراض" in etext):
                    st.warning(f"- {dt.strftime('%d/%m/%Y')}: {etext[:100]}...")

            st.info(procedural_pattern_analyzer(timeline))
            st.info(settlement_calculator(risk, cred, len(contradictions)))

            claims = []
            for t in texts:
                claims.extend(DocumentIntelligence().extract_claims(t))

            gaps_evidence = extract_evidence_gaps(texts, claims)
            if gaps_evidence:
                for g in gaps_evidence:
                    st.error(f"- {g}")
            else:
                st.success("جميع الادعاءات مدعومة.")

        except Exception as e:
            logger.error("Advanced tools tab failed: %s", e)
            st.error("حدث خطأ في الأدوات المتقدمة.")

# =========================
# Tab8: Hugging Face
# =========================
with tab8:
    st.subheader("Hugging Face")
    model_name = st.text_input("اسم النموذج", value="faisalaljahlan/Labour-Law-SA-QA")

    @st.cache_resource
    def load_hf_model(name):
        # Keep same feature
        return pipeline("text-generation", model=name)

    if st.button("تحميل"):
        try:
            with st.spinner("..."):
                pipe = load_hf_model(model_name)
                st.session_state["hf_pipe"] = pipe
                st.success("تم.")
        except Exception as e:
            logger.error("HF load failed: %s", e)
            st.error("تعذر تحميل النموذج. تأكد من الاتصال/الإعدادات واسم النموذج الصحيح.")

    prompt = st.text_area("النص")
    if st.button("تشغيل") and "hf_pipe" in st.session_state:
        try:
            result = st.session_state["hf_pipe"](prompt, max_new_tokens=200)
            st.write(result[0]["generated_text"])
        except Exception as e:
            logger.error("HF generate failed: %s", e)
            st.error("حدث خطأ أثناء تشغيل النموذج.")

# =========================
# Optional: Keep RuleEngine usage (feature not used before)
# =========================
# NOTE:
# Your original app defined RuleEngine but never used it in any tab.
# We MUST NOT remove it (done), but we also avoid changing UI behavior.
# If you want, we can add a tab/section to show rule alerts without removing anything.