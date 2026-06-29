import streamlit as st
import re
import os
import json
import logging
import hashlib
import base64
from datetime import datetime
from typing import Dict, List, Any, Optional

from utils import _bytes, _norm, new_sid
from storage import (
    load_json, save_json, list_sessions, load_session, save_session, delete_session,
    load_settings, save_settings, DATA_DIR, SESSIONS_DIR, MEMORY_FILE, LAW_FILE, BG_FILE
)
from doc_processing import DocIntel, extract_laws_from_pdf, extract_laws_from_docx, extract_laws_from_text
from rules_engine import RULES, apply_rules
from ai_client import AIClient
import config
from labor_law_rag import LaborLawRAG

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from sentence_transformers import SentenceTransformer
    import chromadb
    from chromadb.utils import embedding_functions
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

try:
    from procedural_analyzer import ProceduralAnalyzer
    from discrepancy_analyzer import DiscrepancyAnalyzer
    from sentiment_analyzer import SentimentAnalyzer
    from legal_document_generator import LegalDocumentGenerator
    from forensics import DigitalForensicsAnalyzer
    ANALYZERS_AVAILABLE = True
except ImportError:
    ANALYZERS_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fuehrer")

st.set_page_config(
    page_title="Führer",
    page_icon="🦾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Zain:wght@300;400;600;700;800;900&display=swap');

@font-face {
    font-family: 'Waltograph';
    src: url('https://cdn.jsdelivr.net/npm/font-waltograph@1.0.0/Waltograph.woff2') format('woff2');
    font-weight: 900;
    font-style: normal;
}

@font-face {
    font-family: 'WaltographFallback';
    src: local('Pacifico'), local('Cookie'), local('Brush Script MT');
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Waltograph', 'WaltographFallback', 'Zain', sans-serif;
    direction: rtl;
}

html, body, .stApp {
    background: #e8eaed !important;
    min-height: 100vh;
    width: 100%;
}

.stApp::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: url('https://i.ibb.co/pjW2kJjW/IMG-5118.jpeg');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    background-repeat: no-repeat;
    opacity: 0.15;
    z-index: 0;
    pointer-events: none;
}

.stApp > .main {
    position: relative;
    z-index: 1;
}

[data-testid="stSidebar"],
[data-testid="stSidebarNav"] {
    display: none !important;
}

.hdr {
    background: rgba(44, 44, 62, 0.85);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 4px solid rgb(212, 168, 32);
    padding: 32px 40px;
    margin-bottom: 32px;
    text-align: center;
    border-radius: 0 0 24px 24px;
    box-shadow: 0 8px 40px rgba(0,0,0,0.15);
    position: relative;
    overflow: hidden;
}

.hdr::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle at 30% 50%, rgba(212, 168, 32, 0.05) 0%, transparent 60%);
    animation: goldShine 6s ease-in-out infinite alternate;
    z-index: 0;
}

@keyframes goldShine {
    0% { transform: translateX(-10%) scale(1); opacity: 0.4; }
    100% { transform: translateX(10%) scale(1.2); opacity: 0.8; }
}

.hdr h1 {
    font-family: 'Waltograph', 'WaltographFallback', cursive !important;
    font-size: clamp(3.5rem, 10vw, 8rem) !important;
    font-weight: 900 !important;
    color: #ffffff !important;
    letter-spacing: 0.08em;
    margin: 0;
    text-shadow:
        0 0 20px rgba(212, 168, 32, 0.3),
        0 0 60px rgba(212, 168, 32, 0.1),
        0 4px 12px rgba(0,0,0,0.3);
    position: relative;
    z-index: 1;
    text-transform: uppercase;
}

.hdr h1::after {
    content: '';
    display: block;
    width: 120px;
    height: 4px;
    background: linear-gradient(90deg, transparent, rgb(212, 168, 32), rgb(255, 215, 0), rgb(212, 168, 32), transparent);
    margin: 16px auto 0;
    border-radius: 2px;
    animation: goldLinePulse 3s ease-in-out infinite;
    box-shadow: 0 0 30px rgba(212, 168, 32, 0.3);
}

@keyframes goldLinePulse {
    0% { transform: scaleX(0.7); opacity: 0.6; }
    50% { transform: scaleX(1); opacity: 1; }
    100% { transform: scaleX(0.7); opacity: 0.6; }
}

.stTabs [data-baseweb="tab-list"] {
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-bottom: 2px solid rgba(212, 168, 32, 0.3);
    gap: 6px;
    padding: 10px 18px;
    border-radius: 16px 16px 0 0;
    flex-wrap: wrap;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #444444 !important;
    border: 1.5px solid transparent !important;
    border-radius: 10px !important;
    padding: 12px 24px !important;
    font-family: 'Zain', 'Times New Roman', sans-serif !important;
    font-size: 17px !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em;
    transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94) !important;
    white-space: nowrap;
    position: relative;
}

.stTabs [data-baseweb="tab"]::after {
    content: '';
    position: absolute;
    bottom: -2px;
    left: 50%;
    width: 0;
    height: 3px;
    background: linear-gradient(90deg, rgb(212, 168, 32), rgb(255, 215, 0));
    transition: all 0.3s ease;
    transform: translateX(-50%);
    border-radius: 2px;
}

.stTabs [data-baseweb="tab"]:hover::after {
    width: 60%;
}

.stTabs [data-baseweb="tab"]:hover {
    background: rgba(212, 168, 32, 0.06) !important;
    color: rgb(44, 44, 62) !important;
    border-color: rgba(212, 168, 32, 0.2) !important;
    transform: translateY(-2px);
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: #2c2c3e !important;
    color: #ffffff !important;
    border-color: rgb(212, 168, 32) !important;
    font-weight: 700 !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.12);
}

.stTabs [data-baseweb="tab"][aria-selected="true"]::after {
    width: 80%;
    background: linear-gradient(90deg, rgb(255, 215, 0), rgb(212, 168, 32));
}

.stTabs [data-baseweb="tab-panel"] {
    background: rgba(255, 255, 255, 0.92);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(212, 168, 32, 0.15);
    border-radius: 0 0 18px 18px;
    padding: 32px 36px;
    box-shadow: 0 8px 48px rgba(0,0,0,0.04);
}

.stButton button {
    background: linear-gradient(135deg, #2c2c3e 0%, #1a1a2e 100%) !important;
    color: #ffffff !important;
    border: 1.5px solid rgb(212, 168, 32) !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-family: 'Zain', 'Times New Roman', sans-serif !important;
    padding: 14px 32px !important;
    font-size: 16px !important;
    letter-spacing: 0.03em;
    transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94) !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    position: relative;
    overflow: hidden;
}

.stButton button::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(212, 168, 32, 0.1) 0%, transparent 60%);
    opacity: 0;
    transition: opacity 0.4s ease;
}

.stButton button:hover {
    background: linear-gradient(135deg, #d4a820 0%, #f0c040 100%) !important;
    color: #1a1a2e !important;
    border-color: #d4a820 !important;
    transform: translateY(-3px) scale(1.02);
    box-shadow: 0 8px 32px rgba(212, 168, 32, 0.35);
}

.stButton button:hover::before {
    opacity: 1;
}

.stButton button:active {
    transform: scale(0.97);
}

.stTextInput input,
.stTextArea textarea,
.stSelectbox select {
    background: rgba(255, 255, 255, 0.9) !important;
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    color: #1a1a2e !important;
    border: 1.5px solid rgba(212, 168, 32, 0.3) !important;
    border-radius: 10px !important;
    font-family: 'Zain', 'Times New Roman', sans-serif !important;
    font-size: 16px !important;
    padding: 16px 20px !important;
    transition: all 0.3s ease !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: rgb(212, 168, 32) !important;
    box-shadow: 0 0 0 4px rgba(212, 168, 32, 0.12) !important;
    background: #ffffff !important;
}

[data-testid="stFileUploader"] {
    background: rgba(255, 255, 255, 0.3) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 2.5px dashed rgb(212, 168, 32) !important;
    border-radius: 16px !important;
    padding: 40px !important;
    transition: all 0.3s ease !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: rgb(196, 154, 26) !important;
    background: rgba(255, 255, 255, 0.5) !important;
    box-shadow: 0 0 60px rgba(212, 168, 32, 0.06);
}

[data-testid="stFileUploader"] div {
    color: #1a1a2e !important;
    font-weight: 600;
    font-size: 15px !important;
}

.chat-user {
    background: rgba(44, 44, 62, 0.92);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1.5px solid rgb(212, 168, 32);
    border-radius: 18px 18px 4px 18px;
    padding: 18px 24px;
    margin: 14px 0;
    max-width: 78%;
    float: right;
    clear: both;
    color: #ffffff !important;
    font-family: 'Zain', 'Times New Roman', sans-serif !important;
    font-size: 16px;
    line-height: 1.8;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}

.chat-ai {
    background: rgba(255, 255, 255, 0.92);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1.5px solid rgba(212, 168, 32, 0.2);
    border-radius: 18px 18px 18px 4px;
    padding: 18px 24px;
    margin: 14px 0;
    max-width: 84%;
    float: left;
    clear: both;
    border-right: 5px solid rgb(212, 168, 32);
    color: #1a1a2e;
    font-family: 'Zain', 'Times New Roman', sans-serif !important;
    font-size: 16px;
    line-height: 1.8;
    box-shadow: 0 4px 20px rgba(0,0,0,0.04);
}

.result-card {
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(212, 168, 32, 0.15);
    border-radius: 12px;
    padding: 20px 24px;
    margin: 12px 0;
    border-right: 5px solid rgb(212, 168, 32);
    box-shadow: 0 4px 24px rgba(0,0,0,0.03);
}

.badge {
    display: inline-block;
    background: rgba(44, 44, 62, 0.08);
    border: 1px solid rgb(212, 168, 32);
    color: #1a1a2e;
    border-radius: 8px;
    padding: 5px 14px;
    font-size: 13px;
    font-weight: 700;
    margin: 4px 3px;
    font-family: 'Zain', 'Times New Roman', sans-serif;
}

.metric-card {
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(212, 168, 32, 0.15);
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    border-top: 4px solid rgb(212, 168, 32);
    box-shadow: 0 4px 24px rgba(0,0,0,0.03);
}

.metric-card .label {
    font-size: 14px;
    color: #666666;
    font-weight: 600;
    letter-spacing: 0.03em;
}

.metric-card .value {
    font-size: clamp(2rem, 4vw, 3.2rem);
    font-weight: 800;
    color: #2c2c3e;
    margin-top: 6px;
}

@media (max-width: 1920px) {
    .hdr { padding: 40px 60px; }
    .hdr h1 { font-size: clamp(4rem, 8vw, 8rem) !important; }
    .stTabs [data-baseweb="tab"] { font-size: 18px !important; padding: 14px 28px !important; }
}

@media (max-width: 1440px) {
    .hdr h1 { font-size: clamp(3.5rem, 7vw, 6rem) !important; }
    .stTabs [data-baseweb="tab"] { font-size: 16px !important; padding: 12px 24px !important; }
}

@media (max-width: 1024px) {
    .hdr { padding: 24px 28px; }
    .hdr h1 { font-size: clamp(2.8rem, 6vw, 4.5rem) !important; }
    .stTabs [data-baseweb="tab"] { font-size: 15px !important; padding: 10px 18px !important; }
    .stTabs [data-baseweb="tab-panel"] { padding: 24px 20px; }
    .chat-user, .chat-ai { max-width: 92%; font-size: 15px; }
}

@media (max-width: 768px) {
    .hdr { padding: 18px 16px; }
    .hdr h1 { font-size: clamp(2.2rem, 5vw, 3.2rem) !important; }
    .hdr h1::after { width: 60px; }
    .stTabs [data-baseweb="tab"] { font-size: 13px !important; padding: 8px 14px !important; }
    .stTabs [data-baseweb="tab-panel"] { padding: 18px 16px; }
    .stButton button { padding: 10px 18px !important; font-size: 14px !important; }
    .chat-user, .chat-ai { font-size: 14px; padding: 14px 18px; }
    .metric-card .value { font-size: clamp(1.6rem, 4vw, 2.4rem); }
}

@media (max-width: 480px) {
    .hdr h1 { font-size: clamp(1.6rem, 4vw, 2.4rem) !important; letter-spacing: 0.04em; }
    .hdr h1::after { width: 40px; height: 3px; }
    .stTabs [data-baseweb="tab"] { font-size: 11px !important; padding: 6px 10px !important; }
    .stTabs [data-baseweb="tab-panel"] { padding: 14px 12px; }
    .stButton button { padding: 8px 14px !important; font-size: 12px !important; }
    .chat-user, .chat-ai { font-size: 13px; padding: 12px 14px; }
    .metric-card .value { font-size: clamp(1.2rem, 3vw, 1.8rem); }
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hdr">
<h1>Führer</h1>
</div>
""", unsafe_allow_html=True)

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
        "rag_indexed": False,
    }
    for k, v in defs.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if not st.session_state.bg_b64 and os.path.exists(BG_FILE):
        with open(BG_FILE, "r") as f:
            st.session_state.bg_b64 = f.read().strip()
_init()
if "rag_engine" not in st.session_state:
    st.session_state.rag_engine = LaborLawRAG()
try:
    from labor_law_rag import LaborLawRAG
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("⚠️ ملفات RAG غير موجودة. تأكد من وجود labor_law_rag.py ")

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
        background: rgba(232,234,237,0.92);
        z-index: 0;
        pointer-events: none;
    }}
    </style>
    """, unsafe_allow_html=True)

if RAG_AVAILABLE:
    @st.cache_resource
    def load_embedder():
        return SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

    @st.cache_resource
    def get_chroma_client():
        return chromadb.PersistentClient(path="./fuehrer_data/chroma_db")

    def get_collection():
        client = get_chroma_client()
        return client.get_or_create_collection(
            name="law_collection",
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="paraphrase-multilingual-MiniLM-L12-v2"
            )
        )

    def index_law_db():
        if not st.session_state.law_db:
            return 0
        collection = get_collection()
        try:
            collection.delete(collection.get()['ids'])
        except:
            pass
        texts = []
        metadatas = []
        ids = []
        for i, item in enumerate(st.session_state.law_db):
            text = item.get("text", "").strip()
            if text:
                texts.append(text)
                metadatas.append({
                    "law_name": item.get("law_name", ""),
                    "article": item.get("article", ""),
                    "source": item.get("source", "")
                })
                ids.append(f"law_{i}")
        if texts:
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            all_chunks = []
            all_metadatas = []
            all_ids = []
            for idx, (text, meta) in enumerate(zip(texts, metadatas)):
                chunks = splitter.split_text(text)
                for j, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    all_metadatas.append(meta)
                    all_ids.append(f"law_{idx}_{j}")
            collection.add(documents=all_chunks, metadatas=all_metadatas, ids=all_ids)
        st.session_state.rag_indexed = True
        return len(all_chunks)

    def search_law(query: str, top_k: int = 5):
        if not st.session_state.rag_indexed:
            return []
        collection = get_collection()
        results = collection.query(query_texts=[query], n_results=top_k)
        documents = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
        return list(zip(documents, metadatas))
else:
    def index_law_db():
        return 0
    def search_law(query, top_k=5):
        return []

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
    context = ""
    if RAG_AVAILABLE and st.session_state.rag_indexed:
        results = search_law(prompt, top_k=3)
        if results:
            context = "\n\nالمواد القانونية ذات الصلة:\n"
            for doc, meta in results:
                context += f"• {meta.get('law_name', '')} - {meta.get('article', '')}: {doc[:200]}...\n"
    full_prompt = f"{system}{context}\n\nسؤال المستخدم: {prompt}"
    try:
        client = AIClient(endpoint, model, fmt, key)
        return client.generate(system, msgs + [{"role": "user", "content": full_prompt}])
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

tabs = st.tabs(["المحادثة", "الملفات", "التدقيق", "الدعوى", "القانون", "الذاكرة", "الإعدادات"])
t_ai, t_files, t_audit, t_docs, t_law, t_mem, t_settings = tabs

with t_ai:
    st.subheader("المحادثة")
    st.caption("اطرح سؤالك القانوني، سيبحث النظام في قاعدة القوانين ويستجيب بدقة.")

    if not st.session_state.current_sid:
        st.info("📌 ابدأ جلسة جديدة من الإعدادات.")
    else:
        sess = load_session(st.session_state.current_sid)
        new_name = st.text_input("اسم الجلسة", value=sess.get("name", "جلسة"), key="sess_name_inp")
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
user_inp = st.text_area("اكتب سؤالك هنا", value=st.session_state.pending_q, height=100, placeholder="مثال: ما هي مكافأة نهاية الخدمة？")
col1, col2 = st.columns([3, 1])

with col1:
    if st.button("إرسال", use_container_width=True) and user_inp.strip():
        st.session_state.pending_q = ""
        ts = datetime.now().strftime("%H:%M")
        st.session_state.current_msgs.append({"role": "user", "content": user_inp, "ts": ts})
        
        # البحث الدلالي في نظام العمل
        results = st.session_state.rag_engine.search(user_inp, top_k=3)
        context = "\n".join([doc for doc, meta in results])
        context_en = context
        
        # توليد الإجابة مع السياق
        if context_en:
            full_prompt = f"السياق القانوني:\n{context_en}\n\nالسؤال: {user_inp}\n\nالإجابة:"
        else:
            full_prompt = user_inp
        
        with st.spinner("⚖️ يبحث في القوانين..."):
            resp = call_ai(full_prompt)
        
        st.session_state.current_msgs.append({"role": "assistant", "content": resp, "ts": ts})
        sess["messages"] = st.session_state.current_msgs
        save_session(st.session_state.current_sid, sess)
        
        if len(resp) > 80 and "❌" not in resp:
            mem_add(f"س: {user_inp[:80]} | ج: {resp[:150]}...", tags=["محادثة", st.session_state.case_type], cat="محادثة")
        
        st.rerun()

with col2:
    if st.button("مسح", use_container_width=True):
        st.session_state.current_msgs = []
        sess["messages"] = []
        save_session(st.session_state.current_sid, sess)
        st.rerun()
    
    # البحث الدلالي في نظام العمل
    results = st.session_state.rag_engine.search(user_inp, top_k=3)
    context = "\n".join([doc for doc, meta in results])
    
    # ترجمة السياق إلى الإنجليزية (
    context_en = context
    
    # توليد الإجابة مع السياق
    if context_en:
        full_prompt = f"السياق القانوني:\n{context_en}\n\nالسؤال: {user_inp}\n\nالإجابة:"
    else:
        full_prompt = user_inp
    
with st.spinner("⚖️ يبحث في القوانين..."):
    resp = call_ai(full_prompt)
st.session_state.current_msgs.append({"role": "assistant", "content": resp, "ts": ts})
sess["messages"] = st.session_state.current_msgs
save_session(st.session_state.current_sid, sess)
if len(resp) > 80 and "❌" not in resp:
        mem_add(f"س: {user_inp[:80]} | ج: {resp[:150]}...", tags=["محادثة", st.session_state.case_type], cat="محادثة")
st.rerun()
with col2:
 if st.button("مسح", use_container_width=True):
        st.session_state.current_msgs = []
        sess["messages"] = []
save_session(st.session_state.current_sid, sess)
st.rerun()
with t_files:
 st.subheader("الملفات")
 uploaded = st.file_uploader("اختر الملفات (PDF, DOCX, TXT, JSON)", type=["pdf", "docx", "txt", "json"], accept_multiple_files=True, label_visibility="collapsed")
if uploaded:
 st.info(f"تم رفع {len(uploaded)} ملف")
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
 st.warning("⚠️ لم يُستخرج نص من هذا الملف")
if texts:
 st.session_state.docs = texts
col1, col2, col3 = st.columns(3)
 with col1:
if st.button("تحليل شامل",
use_container_width=True):
 with st.spinner("جاري التحليل..."):
combined = "\n\n".join(texts)
analysis = generate_analysis(combined)
st.session_state.analysis_result = analysis
st.session_state.uploaded_texts = texts
st.success("✅ تم التحليل، انتقل إلى 'المحادثة' لطرح الأسئلة")
with col2:
 if st.button("استخراج القوانين", use_container_width=True):
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
                    st.success(f"✅ تم استخراج {total} مادة قانونية")
                    if RAG_AVAILABLE and total > 0:
                        with st.spinner("جاري فهرسة القوانين في RAG..."):
                            count = index_law_db()
                            st.success(f"✅ تم فهرسة {count} جزء في قاعدة المتجهات")


    if st.button("فهرسة PDF كنظام عمل", use_container_width=True):
        for f in uploaded:
            if f.name.endswith('.pdf'):
                articles = st.session_state.rag_engine.parse_pdf(_bytes(f))
                count = st.session_state.rag_engine.index_articles(articles)
                st.success(f"تم فهرسة {count} مادة من {f.name}")# 
            with col3:
                if RAG_AVAILABLE and st.session_state.law_db:
                    if st.button("🧠 فهرسة RAG", use_container_width=True):
                        with st.spinner("جاري فهرسة القوانين..."):
                            count = index_law_db()
                            st.success(f"✅ تم فهرسة {count} جزء")

with t_audit:
    st.subheader("التدقيق الإداري والقانوني")
    text_input = st.text_area("الصق النص هنا", height=200, placeholder="مثال: تم فصل الموظف محمد بدون تحقيق...")
    if st.button("تدقيق", use_container_width=True) and text_input.strip():
        with st.spinner("جاري التحليل..."):
            if ANALYZERS_AVAILABLE:
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
                    st.markdown("**الإجراءات الإدارية**")
                    if proc_result.get("is_arbitrary"):
                        st.error("❌ فصل تعسفي (المادة 81)")
                    if not proc_result.get("has_investigation"):
                        st.warning("⚠️ لا يوجد تحقيق مسبق (المادة 80)")
                    if not proc_result.get("has_warning"):
                        st.warning("⚠️ لا يوجد إنذار سابق (المادة 75)")
                    if proc_result.get("has_termination_letter") and proc_result.get("has_investigation"):
                        st.success("✅ الإجراءات سليمة شكلاً")
                with col2:
                    st.markdown("**المواد المخالفة**")
                    if alerts:
                        for alert in alerts:
                            st.error(f"⚠️ {alert['text']}")
                    else:
                        st.success("✅ لا توجد مخالفات نظامية واضحة")
                st.markdown("---")
                st.markdown("**التوصيات**")
                for rec in proc_result.get("recommendations", []):
                    st.markdown(f"- {rec}")
                if disc_result.get("discrepancies"):
                    st.markdown("---")
                    st.markdown("**التناقضات المكتشفة**")
                    for d in disc_result["discrepancies"][:5]:
                        st.warning(f"• {d.get('message', '')}")
                if proc_result.get("legal_references"):
                    st.markdown("---")
                    st.markdown("**المراجع القانونية**")
                    for ref in proc_result["legal_references"]:
                        st.markdown(f"- {ref}")
            else:
                st.error("المحللات المتقدمة غير مثبتة. تأكد من وجود الملفات: procedural_analyzer.py, discrepancy_analyzer.py")

with t_docs:
    st.subheader("توليد المستندات القانونية")
    with st.form("doc_form"):
        col1, col2 = st.columns(2)
        with col1:
            plaintiff = st.text_input("اسم المدعي")
            plaintiff_id = st.text_input("رقم الهوية")
            work_location = st.text_input("مكان العمل", value="الرياض")
        with col2:
            defendant = st.text_input("اسم المدعى عليه")
            defendant_id = st.text_input("رقم المنشأة")
            claim_amount = st.number_input("المبلغ المطلوب", min_value=0.0, value=0.0, step=1000.0)
        facts = st.text_area("الوقائع", height=100)
        laws = st.text_input("المواد", value="المادة 84, المادة 77")
        if st.form_submit_button("توليد"):
            if ANALYZERS_AVAILABLE:
                generator = LegalDocumentGenerator({
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
                })
                docs = {
                    "إنذار رسمي": generator.generate_notice(),
                    "صحيفة دعوى": generator.generate_lawsuit(),
                    "مذكرة قانونية": generator.generate_legal_memo()
                }
                for title, content in docs.items():
                    with st.expander(f"📄 {title}"):
                        st.text_area(f"نص {title}", content, height=200, key=f"doc_{title}")
                        st.download_button(f"⬇️ تحميل {title}", data=content.encode("utf-8"), file_name=f"{title}.txt", mime="text/plain")
            else:
                st.error("مولد المستندات غير مثبت. تأكد من وجود legal_document_generator.py")

with t_law:
    st.subheader("قاعدة الأنظمة السعودية")
    st.caption(f"إجمالي المواد: {len(st.session_state.law_db):,}")
    if st.session_state.law_db:
        st.success(f"✅ القاعدة تحتوي على {len(st.session_state.law_db)} مادة قانونية")
        if RAG_AVAILABLE:
            if st.session_state.rag_indexed:
                st.success("✅ القاعدة مفهرسة في RAG")
            else:
                st.warning("⚠️ القاعدة غير مفهرسة في RAG. استخدم زر 'فهرسة RAG' في تبويب الملفات.")
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

with t_mem:
    st.subheader("الذاكرة الدائمة")
    with st.expander("✏️ إضافة ملاحظة"):
        mt = st.text_area("النص", height=100)
        mcat = st.selectbox("الفئة", ["قضية", "موكل", "حكم", "ملاحظة", "استراتيجية", "قانون", "عام"])
        mtags = st.text_input("وسوم")
        if st.button("حفظ") and mt.strip():
            tags = [x.strip() for x in mtags.split(",") if x.strip()]
            mem_add(mt, tags, mcat)
            st.rerun()
    for m in reversed(st.session_state.memory[-15:]):
        st.markdown(f'<div class="result-card"><small>{m.get("ts", "")} · {m.get("category", "")}</small><br>{m["text"][:200]}</div>', unsafe_allow_html=True)

with t_settings:
    st.subheader("الإعدادات والجلسات")
    st.markdown("**النموذج**")
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

    st.markdown("**مفتاح API**")
    new_key = st.text_input("", value=st.session_state.ai_key, type="password",
                            placeholder="AIza... أو sk-...", label_visibility="collapsed")
    if new_key != st.session_state.ai_key:
        st.session_state.ai_key = new_key

    if preset_name == "⚙️ مخصص":
        st.session_state.ai_endpoint = st.text_input("رابط API", value=st.session_state.ai_endpoint)
        st.session_state.ai_model = st.text_input("اسم النموذج", value=st.session_state.ai_model)
        st.session_state.ai_format = st.selectbox("الصيغة", ["openai", "gemini", "anthropic"], index=0)

    st.markdown("---")
    st.markdown("**الجلسات**")
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
    st.markdown("**نوع القضية**")
    st.session_state.case_type = st.selectbox("", ["قضية عمالية", "نزاع تجاري", "قضية عقارية", "نزاع إداري", "قضية جنائية", "إفلاس وتصفية"], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("**صورة الخلفية**")
    bg_file = st.file_uploader("ارفع صورة (PNG, JPG)", type=["png", "jpg", "jpeg"])
    if bg_file:
        b64 = base64.b64encode(_bytes(bg_file)).decode()
        st.session_state.bg_b64 = b64
        with open(BG_FILE, "w") as f:
            f.write(b64)
        st.rerun()
    if st.session_state.bg_b64 and st.button("إزالة الخلفية"):
        st.session_state.bg_b64 = ""
        if os.path.exists(BG_FILE):
            os.remove(BG_FILE)
        st.rerun()

    st.markdown("---")
    st.markdown("تصدير البيانات")
    if st.button("تصدير النسخة الاحتياطية", use_container_width=True):
        export = {"memory": st.session_state.memory, "law_db": st.session_state.law_db, "exported_at": datetime.now().isoformat()}
        st.download_button("⬇️ تحميل", json.dumps(export, ensure_ascii=False, indent=2).encode("utf-8"), "backup.json", "application/json")
