# fuhrer.py - النسخة النهائية (بدون أي وصف إضافي)

import streamlit as st
import re, os, json, logging, hashlib, base64, io
from datetime import datetime
from typing import Dict, List, Any, Optional

# ========== الاستيرادات الأساسية ==========
from utils import _bytes, _norm, new_sid
from storage import (
    load_json, save_json, list_sessions, load_session, save_session, delete_session,
    load_settings, save_settings, DATA_DIR, SESSIONS_DIR, MEMORY_FILE, LAW_FILE, BG_FILE
)
from doc_processing import DocIntel, extract_laws_from_pdf, extract_laws_from_docx, extract_laws_from_text
from rules_engine import RULES, apply_rules
from ai_client import AIClient
import config

# ========== RAG المتقدم ==========
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from sentence_transformers import SentenceTransformer
    import chromadb
    from chromadb.utils import embedding_functions
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

# ========== المحللات المتقدمة ==========
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
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ========== CSS ==========
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Zain:wght@300;400;600;700;800;900&display=swap');

@font-face {
    font-family: 'Waltograph';
    src: url('https://cdn.jsdelivr.net/npm/font-waltograph@1.0.0/Waltograph.woff2') format('woff2');
    font-weight: 400;
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

# ========== الهيدر ==========
st.markdown("""
<div class="hdr">
<h1>Führer</h1>
</div>
""", unsafe_allow_html=True)

# ========== التهيئة ==========
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

# ========== RAG Engine ==========
if RAG_AVAILABLE:
    @st.cache_resource
    def load_embedder
