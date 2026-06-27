@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800;900&display=swap');

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Cairo', sans-serif;
    direction: rtl;
}

html, body, .stApp {
    background: #f0f2f5 !important;
}

[data-testid="stSidebar"],
[data-testid="stSidebarNav"] {
    display: none !important;
}

.hdr {
    background: #2c2c3e;
    border-bottom: 3px solid #rgb(212, 168, 32);
    padding: 28px 32px;
    margin-bottom: 28px;
    text-align: center;
    border-radius: 0 0 16px 16px;
}

.hdr h1 {
    font-size: 52px !important;
    font-weight: 900 !important;
    color: #ffffff !important;
    letter-spacing: 6px;
    margin: 0;
    text-transform: uppercase;
}

.hdr h1::after {
    content: '';
    display: block;
    width: 80px;
    height: 4px;
    background: #rgb(212, 168, 32);
    margin: 12px auto 0;
    border-radius: 2px;
}

.stTabs [data-baseweb="tab-list"] {
    background: #ffffff;
    border-bottom: 2px solid #e0e0e0;
    gap: 8px;
    padding: 10px 16px;
    border-radius: 12px 12px 0 0;
    flex-wrap: wrap;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #555555 !important;
    border: 1.5px solid transparent !important;
    border-radius: 8px !important;
    padding: 10px 22px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    white-space: nowrap;
}

.stTabs [data-baseweb="tab"]:hover {
    background: rgba(212, 168, 32, 0.06) !important;
    color: #rgb(212, 168, 32) !important;
    border-color: #rgb(212, 168, 32) !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: #2c2c3e !important;
    color: #ffffff !important;
    border-color: #rgb(212, 168, 32) !important;
    font-weight: 700 !important;
}

.stTabs [data-baseweb="tab-panel"] {
    background: #ffffff;
    border: 1px solid #e8e8e8;
    border-radius: 0 0 14px 14px;
    padding: 28px 32px;
}

.stButton button {
    background: #2c2c3e !important;
    color: #ffffff !important;
    border: 1.5px solid #rgb(212, 168, 32) !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    padding: 12px 28px !important;
    transition: all 0.3s ease !important;
    font-size: 15px !important;
}

.stButton button:hover {
    background: #rgb(212, 168, 32) !important;
    color: #1a1a2e !important;
    border-color: #rgb(212, 168, 32) !important;
}

.stTextInput input,
.stTextArea textarea,
.stSelectbox select {
    background: #fafafa !important;
    color: #1a1a2e !important;
    border: 1.5px solid #d0d0d0 !important;
    border-radius: 8px !important;
    font-size: 15px !important;
    padding: 14px 18px !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: #rgb(212, 168, 32) !important;
}

[data-testid="stFileUploader"] {
    background: #fafafa !important;
    border: 2px dashed #rgb(212, 168, 32) !important;
    border-radius: 12px !important;
    padding: 32px !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: #c49a1a !important;
}

.chat-user {
    background: #2c2c3e;
    border: 1px solid #rgb(212, 168, 32);
    border-radius: 16px 16px 2px 16px;
    padding: 16px 20px;
    margin: 12px 0;
    max-width: 78%;
    float: right;
    clear: both;
    color: #ffffff !important;
    font-size: 15px;
    line-height: 1.7;
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
    border-right: 4px solid #rgb(212, 168, 32);
    color: #1a1a2e;
    font-size: 15px;
    line-height: 1.7;
}

.result-card {
    background: #f8f9fa;
    border: 1px solid #e8e8e8;
    border-radius: 10px;
    padding: 18px 22px;
    margin: 10px 0;
    border-right: 4px solid #rgb(212, 168, 32);
}

.badge {
    display: inline-block;
    background: #f0f1f3;
    border: 1px solid #rgb(212, 168, 32);
    color: #1a1a2e;
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 700;
    margin: 3px 2px;
}

.metric-card {
    background: #ffffff;
    border: 1px solid #e8e8e8;
    border-radius: 10px;
    padding: 18px 22px;
    text-align: center;
    border-top: 3px solid #rgb(212, 168, 32);
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

@media (max-width: 768px) {
    .hdr h1 {
        font-size: 34px !important;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 13px !important;
        padding: 8px 14px !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding: 18px 16px;
    }
}

@media (max-width: 480px) {
    .hdr h1 {
        font-size: 26px !important;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 11px !important;
        padding: 6px 10px !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding: 14px 12px;
    }
}
