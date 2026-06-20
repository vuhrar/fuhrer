import streamlit as st
import PyPDF2
import pdfplumber
from docx import Document
import chromadb
from sentence_transformers import SentenceTransformer
import re
from datetime import datetime

st.set_page_config(page_title="Führer", layout="wide")
from PIL import Image
logo = Image.open("logo.png")
st.image(logo, width=120)
st.title("⚖️ Führer")
st.markdown("🦾")

# نموذج التضمينات (للبحث الدلالي)
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

# دوال قراءة الملفات
def extract_text(file):
    ext = file.name.split('.')[-1].lower()
    text = ""
    try:
        if ext == "pdf":
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t: text += t + "\n"
            if not text.strip():
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        elif ext == "docx":
            doc = Document(file)
            for p in doc.paragraphs:
                text += p.text + "\n"
        elif ext == "txt":
            text = file.read().decode("utf-8")
        else:
            return ""
    except Exception as e:
        st.error(f"خطأ في القراءة: {e}")
        return ""
    return re.sub(r'\s+', ' ', text).strip()

# دالة الفهرسة
def ingest_law(file):
    text = extract_text(file)
    if not text: return
    chunks = [text[i:i+800] for i in range(0, len(text), 800)]
    for i, chunk in enumerate(chunks):
        emb = embedder.encode(chunk).tolist()
        collection.add(
            documents=[chunk],
            embeddings=[emb],
            ids=[f"law_{i}_{file.name}"]
        )
    st.success(f"✅ تم تخزين {len(chunks)} قطعة من {file.name}")

# دالة البحث
def search_law(query):
    q_emb = embedder.encode(query).tolist()
    results = collection.query(query_embeddings=[q_emb], n_results=5)
    return results['documents'][0] if results['documents'] else []

# واجهة المستخدم
tab1, tab2 = st.tabs(["📚 1. تحميل الأنظمة", "🔎 2. الاستشارة الذكية"])

with tab1:
    st.subheader("ارفع ملف الأنظمة السعودية (PDF)")
    law_file = st.file_uploader("اختر ملف PDF", type=["pdf"])
    if st.button("🚀 تحميل في الذاكرة"):
        if law_file:
            with st.spinner("جاري المعالجة..."):
                ingest_law(law_file)
        else:
            st.warning("يرجى اختيار ملف أولاً")

with tab2:
    st.subheader("اسأل عن حكم أو مادة قانونية")
    query = st.text_input("اكتب سؤالك (مثل: مدة التقادم في قضايا العمل)")
    if query:
        with st.spinner("جارٍ البحث..."):
            results = search_law(query)
            if results:
                st.subheader("📜 النتائج:")
                for r in results:
                    st.write(f"- {r[:500]}...")
            else:
                st.info("لم يتم العثور على نتيجة. تأكد من تحميل الأنظمة في التبويب الأول.")