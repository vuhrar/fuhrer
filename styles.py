# styles.py
"""
كل التنسيقات البصرية للتطبيق في مكان واحد.
القواعد الصارمة المتبعة:
  1. شاشة داكنة كاملة من الجذر (html/body/stApp)، بدون استثناءات بيضاء.
  2. خط أبيض/رمادي فاتح على كل العناصر.
  3. كل عنصر تفاعلي (أزرار الشريط الجانبي) له width صريح بالبكسل + overflow محكوم،
     لمنع انهيار النص العمودي تحت عرض ضيق (مشكلة كانت موجودة سابقاً وتم إصلاحها هنا).
  4. لا توجد عناصر position:absolute/fixed عشوائية يمكن أن "تطفو" فوق المحتوى.
"""

BASE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;900&display=swap');

* , *::before, *::after {
  box-sizing: border-box !important;
  font-family: 'Tajawal', 'Segoe UI', sans-serif !important;
}

/* ───────────────────────────────────────────
   الخلفية الداكنة الكاملة — لا استثناءات
   ─────────────────────────────────────────── */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
  background-color: #0d0e14 !important;
  color: #e4e4e8 !important;
  direction: rtl !important;
}

[data-testid="stHeader"] { background: transparent !important; height: 0 !important; }
#MainMenu, footer { visibility: hidden !important; }

/* منع أي عرض أفقي زائد يسبب انضغاط العناصر */
.main .block-container {
  max-width: 100% !important;
  padding: 0.75rem 1rem 2rem !important;
  overflow-x: hidden !important;
}

/* ───────────────────────────────────────────
   الشريط العلوي — اسم التطبيق فقط، بدون إضافات
   ─────────────────────────────────────────── */
.app-header {
  background: linear-gradient(135deg, #14151f 0%, #1a1c2b 100%);
  border-bottom: 2px solid #c9a84c;
  border-radius: 14px;
  padding: 16px 20px;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}
.app-header h1 {
  font-size: 1.7rem !important;
  font-weight: 900 !important;
  color: #c9a84c !important;
  margin: 0 !important;
  letter-spacing: 0.03em;
  white-space: nowrap;
}
.app-header .badge {
  background: rgba(201,168,76,0.12);
  border: 1px solid #c9a84c;
  border-radius: 18px;
  padding: 5px 14px;
  font-size: 0.82rem;
  font-weight: 700;
  color: #c9a84c;
  white-space: nowrap;
}

/* ───────────────────────────────────────────
   الشريط الجانبي
   ─────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background-color: #0a0b11 !important;
  border-left: 1px solid #232434 !important;
  min-width: 280px !important;
  max-width: 320px !important;
}
[data-testid="stSidebar"] * { color: #d6d6dc !important; }
[data-testid="stSidebar"] h3 {
  color: #c9a84c !important;
  font-size: 0.78rem !important;
  font-weight: 800 !important;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin: 18px 0 8px !important;
  border-bottom: 1px solid #232434;
  padding-bottom: 6px;
}

/* ───────────────────────────────────────────
   إصلاح جذري لمشكلة انهيار النص العمودي:
   كل زر بالشريط الجانبي يُجبر على عرض كامل
   وارتفاع ثابت ونص بسطر واحد لا يلتف عمودياً
   ─────────────────────────────────────────── */
[data-testid="stSidebar"] .stButton {
  width: 100% !important;
}
[data-testid="stSidebar"] .stButton > button {
  width: 100% !important;
  min-height: 42px !important;
  max-height: 56px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  white-space: normal !important;
  word-break: break-word !important;
  line-height: 1.3 !important;
  text-align: right !important;
  background-color: #161725 !important;
  border: 1px solid #262838 !important;
  border-radius: 10px !important;
  color: #d6d6dc !important;
  font-size: 0.85rem !important;
  font-weight: 600 !important;
  padding: 8px 14px !important;
  margin-bottom: 6px !important;
  transition: border-color 0.15s ease, background-color 0.15s ease !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  border-color: #c9a84c !important;
  background-color: #1d1f30 !important;
  color: #c9a84c !important;
}
[data-testid="stSidebar"] .stButton > button:focus {
  box-shadow: 0 0 0 2px rgba(201,168,76,0.25) !important;
}

/* أزرار التحكم الرئيسية الثلاثة (لوحة التحكم / الإعدادات / الاتصال بالخادم) */
.control-row { display: flex; gap: 8px; margin: 6px 0 4px; }
.control-row .stButton > button {
  font-size: 0.78rem !important;
  min-height: 40px !important;
}

/* ───────────────────────────────────────────
   بطاقات اختيار الشخصية
   ─────────────────────────────────────────── */
.persona-strip { display: flex; gap: 8px; margin-bottom: 6px; }

/* ───────────────────────────────────────────
   منطقة الدردشة
   ─────────────────────────────────────────── */
.chat-box {
  max-height: 58vh;
  overflow-y: auto;
  padding: 6px 4px;
}
.bubble-user {
  background: #18223a;
  border: 1px solid #28365c;
  border-radius: 16px 16px 4px 16px;
  padding: 12px 16px;
  margin: 8px 0 8px 12%;
  color: #dce8ff !important;
  font-size: 0.92rem;
  line-height: 1.75;
  word-wrap: break-word;
}
.bubble-ai {
  background: #15161f;
  border: 1px solid #25263a;
  border-right: 3px solid #c9a84c;
  border-radius: 16px 16px 16px 4px;
  padding: 12px 16px;
  margin: 8px 12% 8px 0;
  color: #e4e4e0 !important;
  font-size: 0.92rem;
  line-height: 1.8;
  word-wrap: break-word;
}
.bubble-ai.advisor { border-right-color: #4a9eff; }
.bubble-meta {
  font-size: 0.7rem;
  color: #55576a !important;
  margin-top: 5px;
}

/* ───────────────────────────────────────────
   عناصر الإدخال
   ─────────────────────────────────────────── */
.stTextArea textarea, .stTextInput input {
  background-color: #14151f !important;
  color: #e4e4e8 !important;
  border: 1.5px solid #262838 !important;
  border-radius: 10px !important;
  direction: rtl !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
  border-color: #c9a84c !important;
  box-shadow: 0 0 0 2px rgba(201,168,76,0.15) !important;
}
.stSelectbox > div > div, .stNumberInput input {
  background-color: #14151f !important;
  color: #e4e4e8 !important;
  border: 1.5px solid #262838 !important;
  border-radius: 10px !important;
}

/* الزر الرئيسي (إرسال / تنفيذ) */
.stButton > button {
  background: linear-gradient(135deg, #c9a84c, #b08f3a) !important;
  color: #0d0e14 !important;
  border: none !important;
  border-radius: 10px !important;
  font-weight: 800 !important;
  font-size: 0.92rem !important;
}
.stButton > button:hover {
  filter: brightness(1.08);
}

/* ───────────────────────────────────────────
   بطاقات النتائج والتنبيهات
   ─────────────────────────────────────────── */
.card {
  background: #14151f;
  border: 1px solid #25263a;
  border-right: 4px solid #c9a84c;
  border-radius: 12px;
  padding: 14px 18px;
  margin: 8px 0;
  color: #e4e4e8 !important;
}
.card.blue   { border-right-color: #4a9eff; }
.card.danger { border-right-color: #ff5a5a; }
.card.ok     { border-right-color: #4ade80; }

.alert { border-radius: 10px; padding: 10px 14px; margin: 6px 0; font-size: 0.85rem; line-height: 1.65; }
.alert.warn   { background: rgba(255,180,0,0.07);  border-right: 3px solid #ffb400; color: #ffd060 !important; }
.alert.danger { background: rgba(255,90,90,0.07);  border-right: 3px solid #ff5a5a; color: #ff9090 !important; }
.alert.ok     { background: rgba(74,222,128,0.07); border-right: 3px solid #4ade80; color: #86f0b0 !important; }
.alert.info   { background: rgba(74,158,255,0.07); border-right: 3px solid #4a9eff; color: #95cbff !important; }

.stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px,1fr)); gap: 10px; margin: 12px 0; }
.stat-box  { background: #161725; border: 1px solid #25263a; border-radius: 10px; padding: 12px; text-align: center; }
.stat-box .v { font-size: 1.3rem; font-weight: 800; color: #c9a84c; }
.stat-box .l { font-size: 0.7rem; color: #8a8ca0 !important; margin-top: 3px; }

/* ───────────────────────────────────────────
   تبويبات ومحددات Streamlit
   ─────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] { background: #14151f !important; border-radius: 10px 10px 0 0 !important; gap: 4px; padding: 6px 10px; }
.stTabs [data-baseweb="tab"] { color: #8a8ca0 !important; font-weight: 700 !important; font-size: 0.82rem !important; border-radius: 8px !important; }
.stTabs [data-baseweb="tab"][aria-selected="true"] { background: #c9a84c !important; color: #0d0e14 !important; }
.stTabs [data-baseweb="tab-panel"] { background: #14151f !important; border: 1px solid #25263a !important; border-radius: 0 0 10px 10px !important; padding: 16px !important; }

.streamlit-expanderHeader { background: #14151f !important; color: #c9a84c !important; border-radius: 8px !important; }
.streamlit-expanderContent { background: #101119 !important; border: 1px solid #232434 !important; }

[data-testid="stFileUploader"] {
  background: #14151f !important;
  border: 2px dashed #262838 !important;
  border-radius: 12px !important;
}
[data-testid="stFileUploader"] section { color: #d6d6dc !important; }

hr { border-color: #232434 !important; }

/* ───────────────────────────────────────────
   استجابة فعلية لعرض الموبايل الضيق (≤480px)
   هذا القسم تحديداً هو ما كان ناقصاً وتسبب
   بانهيار الواجهة سابقاً.
   ─────────────────────────────────────────── */
@media (max-width: 480px) {
  .app-header h1 { font-size: 1.3rem !important; }
  .app-header .badge { font-size: 0.72rem !important; padding: 4px 10px; }
  .bubble-user, .bubble-ai { margin-left: 4%; margin-right: 4%; font-size: 0.88rem; }
  [data-testid="stSidebar"] { min-width: 250px !important; }
  [data-testid="stSidebar"] .stButton > button { font-size: 0.8rem !important; }
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
"""
