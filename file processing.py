# file_processing.py
"""
استخراج النص من الملفات المرفوعة، بمحاولات متدرجة (fallback) لكل نوع
لرفع جودة الاستخراج خصوصاً للنصوص العربية.
"""

import json
import logging

logger = logging.getLogger("file_processing")


def extract_text_from_file(uploaded_file) -> str:
    """يستقبل كائن ملف من st.file_uploader ويعيد النص المستخرج."""
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
        # محاولة 1: PyMuPDF — الأفضل لاستخراج العربية بصورة سليمة
        try:
            import fitz
            doc  = fitz.open(stream=raw, filetype="pdf")
            text = "\n".join(page.get_text("text") for page in doc)
            if len(text.strip()) > 50:
                return text
        except Exception as e:
            logger.warning(f"PyMuPDF failed: {e}")
        # محاولة 2: pypdf كخط رجعة
        try:
            import io
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw))
            text   = "\n".join(p.extract_text() or "" for p in reader.pages)
            if len(text.strip()) > 50:
                return text
        except Exception as e:
            logger.warning(f"pypdf failed: {e}")
        return "⚠️ لم يُمكن استخراج النص من هذا الـ PDF (قد يكون مسحاً ضوئياً يحتاج OCR)."

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
        return "⚠️ تعذّر قراءة الملف. تأكد أنه docx (وليس doc القديم)."

    if name.endswith(".json"):
        try:
            data = json.loads(raw)
            return json.dumps(data, ensure_ascii=False, indent=2)[:8000]
        except Exception:
            return raw.decode("utf-8", errors="replace")[:8000]

    return raw.decode("utf-8", errors="replace")[:5000]
