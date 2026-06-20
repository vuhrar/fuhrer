import streamlit as st
import PyPDF2
import pdfplumber
from docx import Document
import chromadb
from sentence_transformers import SentenceTransformer
import re
from datetime import datetime
from PIL import Image
import pytesseract
import email
from email import policy
from email.parser import BytesParser
import io
import os

st.set_page_config(page_title="Führer", layout="wide")

# عرض الشعار
try:
    from PIL import Image as PILImage
    logo = PILImage.open("IMG_5029.png")
    st.image(logo, width=100)
except:
    pass

st.title("⚖️ Führer")
st.markdown("")  # تم إزالة العبارة السابقة

# نموذج التضمينات
@st.cache_resource
def load_embedder():
    return SentenceTransformer('all-MiniLM-L6-v2')

embedder = load_embedder()

# قاعدة البيانات المتجهية
@st.cache_resource
def init_db():
    client = chromadb.PersistentClient(path="./legal_vector_db")
    collection = client.get_or_create_collection("saudi_laws")
    return collection

collection = init_db()

# === دوال قراءة الملفات الموسعة ===
def extract_text_from_pdf(file):
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t: text += t + "\n"
        if not text.strip():
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        st.error(f"خطأ في قراءة PDF: {e}")
    return text

def extract_text_from_docx(file):
    text = ""
    try:
        doc = Document(file)
        for p in doc.paragraphs:
            text += p.text + "\n"
    except Exception as e:
        st.error(f"خطأ في قراءة DOCX: {e}")
    return text

def extract_text_from_image(file):
    text = ""
    try:
        image = Image.open(file)
        # استخدام OCR للغة العربية
        text = pytesseract.image_to_string(image, lang='ara')
    except Exception as e:
        st.error(f"خطأ في قراءة الصورة: {e}")
    return text

def extract_text_from_eml(file):
    text = ""
    try:
        msg = BytesParser(policy=policy.default).parse(file)
        # النص الأساسي
        if msg.get_body(preferencelist=('plain', 'html')):
            body = msg.get_body(preferencelist=('plain', 'html'))
            text += body.get_content() + "\n"
        # المرفقات النصية
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get_content_type() in ['text/plain', 'text/html']:
                continue
            # محاولة قراءة المرفقات النصية (PDF, DOCX, TXT)
            filename = part.get_filename()
            if filename:
                ext = filename.split('.')[-1].lower()
                if ext in ['pdf', 'docx', 'txt']:
                    payload = part.get_payload(decode=True)
                    if payload:
                        temp_file = io.BytesIO(payload)
                        temp_file.name = filename
                        if ext == 'pdf':
                            text += extract_text_from_pdf(temp_file) + "\n"
                        elif ext == 'docx':
                            text += extract_text_from_docx(temp_file) + "\n"
                        elif ext == 'txt':
                            text += payload.decode('utf-8', errors='ignore') + "\n"
    except Exception as e:
        st.error(f"خطأ في قراءة البريد الإلكتروني: {e}")
    return text

def extract_text(file):
    ext = file.name.split('.')[-1].lower()
    text = ""
    try:
        if ext == "pdf":
            text = extract_text_from_pdf(file)
        elif ext == "docx":
            text = extract_text_from_docx(file)
        elif ext == "txt":
            text = file.read().decode("utf-8")
        elif ext in ["png", "jpg", "jpeg"]:
            text = extract_text_from_image(file)
        elif ext == "eml":
            text = extract_text_from_eml(file)
        else:
            st.warning(f"نوع الملف {ext} غير مدعوم حالياً")
            return ""
    except Exception as e:
        st.error(f"خطأ في قراءة الملف: {e}")
        return ""
    return re.sub(r'\s+', ' ', text).strip()

# دالة فهرسة ملف واحد
def ingest_law(file):
    text = extract_text(file)
    if not text:
        st.warning(f"الملف {file.name} لا يحتوي على نص قابل للقراءة.")
        return 0
    chunks = [text[i:i+800] for i in range(0, len(text), 800)]
    for i, chunk in enumerate(chunks):
        if chunk.strip():
            emb = embedder.encode(chunk).tolist()
            collection.add(
                documents=[chunk],
                embeddings=[emb],
                ids=[f"law_{file.name}_{i}_{datetime.now().timestamp()}"]
            )
    return len(chunks)

# دالة البحث
def search_law(query):
    q_emb = embedder.encode(query).tolist()
    results = collection.query(query_embeddings=[q_emb], n_results=5)
    return results['documents'][0] if results['documents'] else []

# === واجهة المستخدم ===
tab1, tab2 = st.tabs(["📚 1. رفع وتحليل الملفات", "🔎 2. الاستشارة الذكية"])

with tab1:
    st.subheader("ارفع جميع ملفاتك (PDF, DOCX, TXT, صور, EML)")
    uploaded_files = st.file_uploader(
        "اختر الملفات (يمكنك رفع عدة ملفات مرة واحدة)",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "eml"],
        accept_multiple_files=True
    )
    
    if uploaded_files and st.button("🚀 تحميل وتحليل جميع الملفات"):
        total_chunks = 0
        progress_bar = st.progress(0)
        for idx, file in enumerate(uploaded_files):
            with st.spinner(f"جاري معالجة {file.name}..."):
                chunks = ingest_law(file)
                if chunks > 0:
                    total_chunks += chunks
                    st.success(f"✅ تم تخزين {chunks} قطعة من {file.name}")
                else:
                    st.warning(f"⚠️ الملف {file.name} لم يُقرأ (قد يكون فارغاً أو تالفاً).")
            progress_bar.progress((idx + 1) / len(uploaded_files))
        if total_chunks > 0:
            st.success(f"🎉 تم بنجاح تخزين {total_chunks} قطعة قانونية في الذاكرة!")

with tab2:
    st.subheader("اسأل عن حكم أو مادة قانونية")
    query = st.text_input("اكتب سؤالك (مثل: مدة التقادم في قضايا العمل، عقوبة الرشوة)")
    if query:
        with st.spinner("جارٍ البحث في جميع الملفات التي رفعتها..."):
            results = search_law(query)
            if results:
                st.subheader("📜 النتائج المستخلصة:")
                for r in results:
                    st.write(f"- {r[:500]}...")
            else:
                st.info("💡 لم يتم العثور على نتيجة. تأكد من رفع ملفات الأنظمة في التبويب الأول.")