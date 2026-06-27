@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800;900&display=swap');

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Cairo', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    direction: rtl;
}

html, body, .stApp {
    background: #f0f2f5 !important;
    min-height: 100%;
}

/* ================================
   خلفية شفافة مع تأثير زجاجي للمحتوى
   ================================ */
.stApp > .main {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: none;
}

/* ================================
   إخفاء الشريط الجانبي
   ================================ */
[data-testid="stSidebar"],
[data-testid="stSidebarNav"] {
    display: none !important;
}

/* ================================
   الهيدر (رأس الصفحة) - رمادي داكن مع اسم كبير
   ================================ */
.hdr {
    background: #2c2c3e;
    border-bottom: 3px solid rgb(212, 168, 32);
    padding: 28px 32px;
    margin-bottom: 28px;
    text-align: center;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    border-radius: 0 0 16px 16px;
    position: relative;
    overflow: hidden;
}

.hdr::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(212, 168, 32, 0.05) 0%, transparent 70%);
    border-radius: 50%;
}

.hdr h1 {
    font-size: 52px !important;
    font-weight: 900 !important;
    color: #ffffff !important;
    letter-spacing: 6px;
    margin: 0;
    text-transform: uppercase;
    text-shadow: 0 2px 12px rgba(0,0,0,0.2);
    position: relative;
    z-index: 1;
}

.hdr h1::after {
    content: '';
    display: block;
    width: 80px;
    height: 4px;
    background: #d4a820;
    margin: 12px auto 0;
    border-radius: 2px;
    box-shadow: 0 0 20px rgba(212, 168, 32, 0.3);
}

/* ================================
   التبويبات (Tabs)
   ================================ */
.stTabs [data-baseweb="tab-list"] {
    background: #ffffff;
    border-bottom: 2px solid #e0e0e0;
    gap: 8px;
    padding: 10px 16px;
    border-radius: 12px 12px 0 0;
    flex-wrap: wrap;
    box-shadow: 0 -2px 12px rgba(0,0,0,0.02);
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #555555 !important;
    border: 1.5px solid transparent !important;
    border-radius: 8px !important;
    padding: 10px 22px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease-in-out !important;
    white-space: nowrap;
}

.stTabs [data-baseweb="tab"]:hover {
    background: rgba(212, 168, 32, 0.06) !important;
    color: #d4a820 !important;
    border-color: #d4a820 !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: #2c2c3e !important;
    color: #ffffff !important;
    border-color: #d4a820 !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    transform: translateY(-2px);
}

.stTabs [data-baseweb="tab-panel"] {
    background: #ffffff;
    border: 1px solid #e8e8e8;
    border-radius: 0 0 14px 14px;
    padding: 28px 32px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.04);
}

/* ================================
   الأزرار - ذهبية مع حواف ديناميكية
   ================================ */
.stButton button {
    background: #2c2c3e !important;
    color: #ffffff !important;
    border: 1.5px solid #d4a820 !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    padding: 12px 28px !important;
    transition: all 0.3s ease !important;
    font-size: 15px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.stButton button:hover {
    background: #d4a820 !important;
    color: #1a1a2e !important;
    border-color: #d4a820 !important;
    box-shadow: 0 4px 20px rgba(212, 168, 32, 0.35);
    transform: translateY(-2px) scale(1.02);
}

.stButton button:active {
    transform: scale(0.98);
}

/* ================================
   المدخلات (Inputs) - حواف ذهبية ديناميكية
   ================================ */
.stTextInput input,
.stTextArea textarea,
.stSelectbox select {
    background: #fafafa !important;
    color: #1a1a2e !important;
    border: 1.5px solid #d0d0d0 !important;
    border-radius: 8px !important;
    font-size: 15px !important;
    padding: 14px 18px !important;
    transition: all 0.3s ease !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: #d4a820 !important;
    box-shadow: 0 0 0 4px rgba(212, 168, 32, 0.12) !important;
    background: #ffffff !important;
}

.stTextArea textarea {
    min-height: 140px;
}

/* ================================
   رفع الملفات - حواف ذهبية ديناميكية
   ================================ */
[data-testid="stFileUploader"] {
    background: rgba(255, 255, 255, 0.3) !important;
    backdrop-filter: blur(8px) !important;
    border: 2px dashed #d4a820 !important;
    border-radius: 12px !important;
    padding: 32px !important;
    transition: all 0.3s ease !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: #c49a1a !important;
    background: rgba(255, 255, 255, 0.5) !important;
    box-shadow: 0 0 40px rgba(212, 168, 32, 0.08);
}

[data-testid="stFileUploader"] div {
    color: #1a1a2e !important;
    font-weight: 600;
}

[data-testid="stFileUploader"] svg {
    stroke: #d4a820 !important;
}

/* ================================
   المحادثة (Chat)
   ================================ */
.chat-wrap {
    overflow: hidden;
    min-height: 80px;
}

.chat-user {
    background: #2c2c3e;
    border: 1px solid #d4a820;
    border-radius: 16px 16px 2px 16px;
    padding: 16px 20px;
    margin: 12px 0;
    max-width: 78%;
    float: right;
    clear: both;
    color: #ffffff !important;
    font-size: 15px;
    line-height: 1.7;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
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
    border-right: 4px solid #d4a820;
    color: #1a1a2e;
    font-size: 15px;
    line-height: 1.7;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}

/* ================================
   البطاقات (Cards)
   ================================ */
.result-card {
    background: #f8f9fa;
    border: 1px solid #e8e8e8;
    border-radius: 10px;
    padding: 18px 22px;
    margin: 10px 0;
    box-shadow: 0 1px 6px rgba(0,0,0,0.02);
    border-right: 4px solid #d4a820;
}

/* ================================
   الشارات (Badges)
   ================================ */
.badge {
    display: inline-block;
    background: #f0f1f3;
    border: 1px solid #d4a820;
    color: #1a1a2e;
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 700;
    margin: 3px 2px;
}

/* ================================
   المقاييس (Metrics)
   ================================ */
.metric-card {
    background: #ffffff;
    border: 1px solid #e8e8e8;
    border-radius: 10px;
    padding: 18px 22px;
    text-align: center;
    box-shadow: 0 1px 6px rgba(0,0,0,0.02);
    border-top: 3px solid #d4a820;
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

.metric-card .sub {
    font-size: 11px;
    color: #999999;
    margin-top: 4px;
}

/* ================================
   مؤشرات التحميل والأيقونات الذهبية
   ================================ */
.stAlert {
    border-radius: 10px !important;
}

.stAlert .stAlert-icon {
    color: #d4a820 !important;
}

/* أيقونات التبويبات */
.stTabs [data-baseweb="tab"] .stIcon {
    color: #d4a820 !important;
}

/* ================================
   شاشات صغيرة
   ================================ */
@media (max-width: 768px) {
    .hdr h1 {
        font-size: 34px !important;
    }
    .hdr {
        padding: 18px 16px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 13px !important;
        padding: 8px 14px !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding: 18px 16px;
    }
    .chat-user, .chat-ai {
        max-width: 92%;
        font-size: 14px;
    }
    .metric-card .value {
        font-size: 24px;
    }
}

@media (max-width: 480px) {
    .hdr h1 {
        font-size: 26px !important;
        letter-spacing: 3px;
    }
    .hdr h1::after {
        width: 50px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 11px !important;
        padding: 6px 10px !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding: 14px 12px;
    }
    .chat-user, .chat-ai {
        font-size: 13px;
        padding: 12px 14px;
    }
    .metric-card .value {
        font-size: 20px;
    }
    .stButton button {
        padding: 10px 18px !important;
        font-size: 13px !important;
    }
}

/* ================================
   خلفية شفافة لمنطقة الملفات
   ================================ */
[data-testid="stFileUploader"] {
    background: rgba(255, 255, 255, 0.2) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
}

/* ================================
   أزرار إضافية (حفظ، تأكيد، إدخال، إدارة)
   ================================ */
.stButton .action-btn {
    background: #2c2c3e !important;
    color: #ffffff !important;
    border: 1.5px solid #d4a820 !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    padding: 12px 24px !important;
    transition: all 0.3s ease !important;
}

.stButton .action-btn:hover {
    background: #d4a820 !important;
    color: #1a1a2e !important;
    box-shadow: 0 4px 20px rgba(212, 168, 32, 0.3);
    transform: translateY(-2px);
}

.stButton .action-btn.save {
    background: #2e7d32 !important;
    border-color: #2e7d32 !important;
}

.stButton .action-btn.save:hover {
    background: #1b5e20 !important;
    box-shadow: 0 4px 20px rgba(46, 125, 50, 0.3);
}

.stButton .action-btn.confirm {
    background: #d4a820 !important;
    border-color: #d4a820 !important;
    color: #1a1a2e !important;
}

.stButton .action-btn.confirm:hover {
    background: #c49a1a !important;
    box-shadow: 0 4px 20px rgba(212, 168, 32, 0.4);
}

.stButton .action-btn.manage {
    background: #1a3a8f !important;
    border-color: #1a3a8f !important;
}

.stButton .action-btn.manage:hover {
    background: #0f2866 !important;
    box-shadow: 0 4px 20px rgba(26, 58, 143, 0.3);
}
