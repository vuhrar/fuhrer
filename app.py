# app.py
"""
Führer — نقطة الدخول الرئيسية.
يجمع كل الوحدات الأخرى (styles, ai_engine, analysis_engine, legal_tools,
file_processing, storage) في واجهة Streamlit واحدة متماسكة.
"""

import streamlit as st
from datetime import datetime

import styles
import ai_engine
import analysis_engine
import legal_tools
import file_processing
import storage


# ══════════════════════════════════════════════
# إعداد الصفحة — اسم التطبيق "Führer" فقط، بلا أي إضافة
# ══════════════════════════════════════════════
st.set_page_config(page_title="Führer", page_icon="⚖️", layout="wide",
                    initial_sidebar_state="expanded")

st.markdown(styles.BASE_CSS, unsafe_allow_html=True)


# ══════════════════════════════════════════════
# تهيئة الحالة
# ══════════════════════════════════════════════
_saved = storage.load_settings()
_defaults = {
    "persona":        "lawyer",
    "active_tool":    None,
    "current_sid":    None,
    "current_msgs":   [],
    "docs_text":      [],
    "preset_name":    _saved.get("preset_name", list(ai_engine.PRESETS.keys())[0]),
    "api_key":        _saved.get("api_key", ""),
    "custom_url":     _saved.get("custom_url", ""),
    "custom_model":   _saved.get("custom_model", ""),
    "custom_fmt":     _saved.get("custom_fmt", "openai"),
    "pending_input":  "",
    "show_panel":     None,   # "dashboard" | "settings" | "connection" | None
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def ai_call(prompt: str, history, system: str) -> str:
    """غلاف يربط ai_engine.call_ai بحالة الجلسة الحالية."""
    return ai_engine.call_ai(
        prompt, history, system,
        preset_name=st.session_state.preset_name,
        api_key=st.session_state.api_key,
        custom_url=st.session_state.custom_url,
        custom_model=st.session_state.custom_model,
        custom_fmt=st.session_state.custom_fmt,
    )


# ══════════════════════════════════════════════
# ─────────────────  SIDEBAR  ──────────────────
# ══════════════════════════════════════════════
with st.sidebar:

    st.markdown("""
    <div style='text-align:center;padding:12px 0 6px;'>
      <span style='font-size:2.4rem;'>⚖️</span>
      <div style='font-size:1.35rem;font-weight:900;color:#c9a84c;'>Führer</div>
    </div>
    """, unsafe_allow_html=True)

    # ── أزرار التحكم الثلاثة المطلوبة صراحة ──
    st.markdown("### لوحة الإدارة")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("لوحة التحكم", key="btn_dash", use_container_width=True):
            st.session_state.show_panel = None if st.session_state.show_panel == "dashboard" else "dashboard"
            st.rerun()
    with c2:
        if st.button("الإعدادات", key="btn_settings", use_container_width=True):
            st.session_state.show_panel = None if st.session_state.show_panel == "settings" else "settings"
            st.rerun()
    with c3:
        if st.button("الاتصال بالخادم", key="btn_conn", use_container_width=True):
            st.session_state.show_panel = None if st.session_state.show_panel == "connection" else "connection"
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── الشخصية ──
    st.markdown("### الشخصية")
    col_l, col_a = st.columns(2)
    with col_l:
        mark = "✅ " if st.session_state.persona == "lawyer" else ""
        if st.button(f"{mark}⚖️ محامي", key="p_lawyer", use_container_width=True):
            st.session_state.persona = "lawyer"
            st.session_state.active_tool = None
            st.rerun()
    with col_a:
        mark = "✅ " if st.session_state.persona == "advisor" else ""
        if st.button(f"{mark}🧑 مستشار", key="p_advisor", use_container_width=True):
            st.session_state.persona = "advisor"
            st.session_state.active_tool = None
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── الأدوات ──
    st.markdown("### الأدوات")
    for icon, label, key in legal_tools.TOOLS[st.session_state.persona]:
        active = st.session_state.active_tool == key
        if st.button(f"{'▶ ' if active else ''}{icon} {label}", key=f"tool_{key}", use_container_width=True):
            st.session_state.active_tool = None if active else key
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── التحليل العميق (18 محوراً) ──
    st.markdown("### التحليل العميق")
    if st.button("🧭 تحليل شامل (18 محوراً)", key="deep_analysis_btn", use_container_width=True):
        st.session_state.active_tool = "deep_analysis"
        st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── الجلسات ──
    st.markdown("### الجلسات")
    if st.button("➕ جلسة جديدة", key="new_sess", use_container_width=True):
        sid = storage.new_session_id()
        st.session_state.current_sid  = sid
        st.session_state.current_msgs = []
        storage.save_session(sid, {"name": "جلسة جديدة", "messages": [], "persona": st.session_state.persona})
        st.rerun()

    for s in storage.list_sessions()[:6]:
        icon = "⚖️" if s.get("persona") == "lawyer" else "🧑"
        cur  = "🟢 " if s["id"] == st.session_state.current_sid else ""
        cc1, cc2 = st.columns([5, 1])
        with cc1:
            if st.button(f"{cur}{icon} {s['name'][:14]} ({s['count']})", key=f"s_{s['id']}", use_container_width=True):
                d = storage.load_session(s["id"])
                st.session_state.current_sid  = s["id"]
                st.session_state.current_msgs = d.get("messages", [])
                st.session_state.persona      = d.get("persona", "lawyer")
                st.rerun()
        with cc2:
            if st.button("🗑", key=f"del_{s['id']}"):
                storage.delete_session(s["id"])
                if st.session_state.current_sid == s["id"]:
                    st.session_state.current_sid  = None
                    st.session_state.current_msgs = []
                st.rerun()


# ══════════════════════════════════════════════
# ─────────────────  HEADER  ───────────────────
# ══════════════════════════════════════════════
persona_color = "#c9a84c" if st.session_state.persona == "lawyer" else "#4a9eff"
persona_label = "المحامي ⚖️" if st.session_state.persona == "lawyer" else "المستشار 🧑"

st.markdown(f"""
<div class='app-header'>
  <h1>Führer</h1>
  <span class='badge' style='border-color:{persona_color};color:{persona_color};'>{persona_label}</span>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# ───────────────  لوحات التحكم  ────────────────
# ══════════════════════════════════════════════
if st.session_state.show_panel == "dashboard":
    st.markdown("## لوحة التحكم")
    sessions = storage.list_sessions()
    st.markdown(f"""
    <div class='stat-grid'>
      <div class='stat-box'><div class='v'>{len(sessions)}</div><div class='l'>الجلسات المحفوظة</div></div>
      <div class='stat-box'><div class='v'>{len(st.session_state.docs_text)}</div><div class='l'>مستندات محمّلة</div></div>
      <div class='stat-box'><div class='v'>{len(st.session_state.current_msgs)}</div><div class='l'>رسائل بالجلسة الحالية</div></div>
      <div class='stat-box'><div class='v'>{'متصل' if st.session_state.api_key else 'غير متصل'}</div><div class='l'>حالة الاتصال</div></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

elif st.session_state.show_panel == "settings":
    st.markdown("## الإعدادات")
    st.caption("تفضيلات الواجهة وسلوك التطبيق.")
    if st.button("🗑 مسح كل الجلسات المحفوظة"):
        for s in storage.list_sessions():
            storage.delete_session(s["id"])
        st.session_state.current_sid = None
        st.session_state.current_msgs = []
        st.success("تم مسح جميع الجلسات.")
        st.rerun()
    st.markdown("---")

elif st.session_state.show_panel == "connection":
    st.markdown("## الاتصال بالخادم")
    new_preset = st.selectbox("النموذج", list(ai_engine.PRESETS.keys()),
                               index=list(ai_engine.PRESETS.keys()).index(st.session_state.preset_name)
                               if st.session_state.preset_name in ai_engine.PRESETS else 0)
    st.session_state.preset_name = new_preset

    if new_preset == "⚙️ مخصص":
        st.session_state.custom_url   = st.text_input("رابط API", value=st.session_state.custom_url)
        st.session_state.custom_model = st.text_input("اسم النموذج", value=st.session_state.custom_model)
        st.session_state.custom_fmt   = st.selectbox("صيغة الاستدعاء", ["openai", "gemini", "anthropic"])

    st.session_state.api_key = st.text_input("مفتاح API", value=st.session_state.api_key,
                                              type="password", placeholder="AIza... أو sk-...")

    key_ok = bool(st.session_state.api_key.strip())
    status_color = "#4ade80" if key_ok else "#ff5a5a"
    status_text  = "✅ متصل — المفتاح مُدخل" if key_ok else "⚠️ غير متصل — أدخل مفتاح API"
    st.markdown(f"<div class='alert' style='border-right-color:{status_color};color:{status_color} !important;'>{status_text}</div>",
                unsafe_allow_html=True)

    if st.button("💾 حفظ إعدادات الاتصال"):
        storage.save_settings({
            "preset_name": st.session_state.preset_name,
            "api_key": st.session_state.api_key,
            "custom_url": st.session_state.custom_url,
            "custom_model": st.session_state.custom_model,
            "custom_fmt": st.session_state.custom_fmt,
        })
        st.success("تم الحفظ.")
    st.markdown("---")


# ══════════════════════════════════════════════
# ───────────────  لوحة الأداة النشطة  ──────────
# ══════════════════════════════════════════════
active_tool = st.session_state.active_tool

if active_tool == "calculator":
    st.markdown("## 🧮 حاسبة المستحقات العمالية")
    c1, c2, c3 = st.columns(3)
    with c1:
        basic = st.number_input("الراتب الأساسي (ريال)", min_value=0.0, step=500.0)
    with c2:
        total = st.number_input("الراتب الإجمالي (ريال)", min_value=0.0, step=500.0)
    with c3:
        years = st.number_input("سنوات الخدمة", min_value=0.0, step=0.5)
    c4, c5 = st.columns(2)
    with c4:
        arbitrary = st.checkbox("فصل تعسفي (م.77)")
    with c5:
        delay_m = st.number_input("أشهر تأخير الراتب", min_value=0, step=1)

    if st.button("احسب المستحقات"):
        if basic > 0 and years > 0:
            res = legal_tools.calculate_eosb(basic, total if total > 0 else basic, years, arbitrary, delay_m)
            st.markdown(f"""
            <div class='stat-grid'>
              <div class='stat-box'><div class='v'>{res['eosb']:,.0f}</div><div class='l'>مكافأة نهاية الخدمة</div></div>
              <div class='stat-box'><div class='v'>{res['arbitrary']:,.0f}</div><div class='l'>تعويض تعسفي</div></div>
              <div class='stat-box'><div class='v'>{res['delay']:,.0f}</div><div class='l'>تعويض التأخير</div></div>
              <div class='stat-box' style='border-color:#c9a84c;'><div class='v' style='font-size:1.5rem;'>{res['grand']:,.0f}</div><div class='l'>الإجمالي (ريال)</div></div>
            </div>
            """, unsafe_allow_html=True)
            for d in res["details"]:
                if d:
                    st.markdown(f"<div class='alert info'>{d}</div>", unsafe_allow_html=True)
        else:
            st.warning("أدخل الراتب الأساسي وسنوات الخدمة على الأقل.")
    st.markdown("---")

elif active_tool == "email_scan":
    st.markdown("## 📧 فحص المراسلات واستخراج الزلات")
    uploaded = st.file_uploader("ارفع ملفات المراسلات", type=["pdf", "txt", "docx"], accept_multiple_files=True)
    manual = st.text_area("أو الصق النص مباشرة", height=140)

    if st.button("فحص المراسلات الآن"):
        combined = manual
        if uploaded:
            for f in uploaded:
                combined += "\n\n" + file_processing.extract_text_from_file(f)
        if combined.strip():
            findings = legal_tools.scan_for_slips(combined)
            if findings:
                st.markdown(f"### تم اكتشاف {len(findings)} نقطة قانونية")
                for f in findings:
                    st.markdown(f"""
                    <div class='alert {f["level"]}'><strong>{f["msg"]}</strong><br>
                    <small style='opacity:0.75;'>النص: «{f["snippet"]}»</small></div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("<div class='alert ok'>لم تُكتشف زلات صريحة بالأنماط الآلية. راجع النص يدوياً أيضاً.</div>", unsafe_allow_html=True)
        else:
            st.warning("ارفع ملفاً أو الصق النص أولاً.")
    st.markdown("---")

elif active_tool == "doc_analysis":
    st.markdown("## 📁 تحليل المستندات المرفوعة")
    uploaded = st.file_uploader("ارفع الملفات", type=["pdf", "docx", "txt"], accept_multiple_files=True)
    if uploaded:
        texts = []
        for f in uploaded:
            with st.expander(f"📄 {f.name}"):
                txt = file_processing.extract_text_from_file(f)
                texts.append(txt)
                st.text_area("معاينة", txt[:600] + ("..." if len(txt) > 600 else ""), height=120, key=f"prev_{f.name}")
                facts = legal_tools.extract_quick_facts(txt)
                if facts["dates"]:    st.markdown(f"📅 **تواريخ:** {' | '.join(facts['dates'])}")
                if facts["amounts"]:  st.markdown(f"💰 **مبالغ:** {' | '.join(facts['amounts'])}")
                if facts["articles"]: st.markdown(f"⚖️ **مواد:** {' | '.join(facts['articles'])}")
        if st.button("📤 إرسال للمحادثة للتحليل"):
            st.session_state.docs_text = texts
            combined = "\n\n---\n\n".join(texts)[:6000]
            st.session_state.pending_input = (
                "حلّل هذه الوثائق قانونياً واستخرج:\n"
                "1. الوقائع الرئيسية\n2. النقاط القوية لصالح الموظف\n"
                "3. النقاط التي يحتج بها صاحب العمل\n4. توصياتك\n\n[الوثائق]:\n" + combined
            )
    st.markdown("---")

elif active_tool == "law_search":
    st.markdown("## 📚 البحث في نظام العمل")
    st.caption("اكتب موضوعاً وسيُجاب عليك مباشرة عبر المحادثة بالمادة ذات الصلة.")
    q = st.text_input("ابحث عن موضوع نظامي", placeholder="مثال: مكافأة نهاية الخدمة")
    if st.button("بحث") and q.strip():
        st.session_state.pending_input = f"ابحث في نظام العمل السعودي عن: {q}\nاذكر رقم المادة ونصها الجوهري بدقة."
    st.markdown("---")

elif active_tool in legal_tools.TOOL_PROMPTS:
    icon, title, auto_prompt = legal_tools.TOOL_PROMPTS[active_tool]
    st.markdown(f"## {icon} {title}")
    context = st.text_area("معطيات القضية (اختياري)", height=120)
    if st.button(f"{icon} تشغيل الأداة"):
        full = auto_prompt
        if context.strip():
            full += f"\n\nمعطيات القضية:\n{context}"
        st.session_state.pending_input = full
    st.markdown("---")

elif active_tool == "deep_analysis":
    st.markdown("## 🧭 التحليل الشامل — 18 محوراً قانونياً")
    st.caption("يحلل قضيتك من 18 زاوية متخصصة بالتسلسل، وينتهي برأي إجماع موحّد.")
    case_text = st.text_area("صف القضية أو الصق وقائعها هنا", height=160,
                              placeholder="مثال: نُقلت تعسفياً بعد تقديمي شكوى رسمية، وتلقيت تقييم أداء سلبياً من مشرف لم يعمل معي فعلياً...")

    if not st.session_state.api_key:
        st.markdown("<div class='alert warn'>⚠️ يلزم إدخال مفتاح API أولاً من زر «الاتصال بالخادم» قبل تشغيل التحليل.</div>", unsafe_allow_html=True)

    if st.button("🧭 ابدأ التحليل الشامل") and case_text.strip():
        if not st.session_state.api_key:
            st.error("أدخل مفتاح API أولاً.")
        else:
            progress = st.progress(0, text="جارٍ بدء التحليل...")
            status = st.empty()

            def _update(i, total, name):
                progress.progress(i / total, text=f"محور {i}/{total}: {name}")

            with st.spinner("جارٍ تحليل القضية من 18 زاوية..."):
                result = analysis_engine.run_full_analysis(case_text, ai_call, progress_callback=_update)

            progress.empty()
            status.empty()

            st.markdown("### ⚖️ رأي الإجماع النهائي")
            st.markdown(f"<div class='card' style='border-right-color:#c9a84c;'>{result['consensus'].replace(chr(10), '<br>')}</div>",
                        unsafe_allow_html=True)

            st.markdown("### تفاصيل المحاور الثمانية عشر")
            for r in result["axes"]:
                with st.expander(f"{r['icon']} {r['name']}"):
                    st.markdown(r["answer"])
    st.markdown("---")


# ══════════════════════════════════════════════
# ───────────────  منطقة الدردشة  ───────────────
# ══════════════════════════════════════════════
if not st.session_state.current_sid:
    st.markdown(f"""
    <div style='text-align:center;padding:50px 16px;'>
      <div style='font-size:3.4rem;margin-bottom:12px;'>{'⚖️' if st.session_state.persona=='lawyer' else '🧑'}</div>
      <h2 style='color:{persona_color};font-size:1.5rem;margin-bottom:8px;'>{persona_label}</h2>
      <p style='color:#8a8ca0;font-size:0.92rem;max-width:440px;margin:0 auto 20px;'>
        {'يصيغ الدعاوى، يكتب المذكرات، ويبني خط الدفاع القانوني.' if st.session_state.persona=='lawyer' else 'يحسب المستحقات، يحلل المخاطر، ويوجّه نحو القرار الأمثل.'}
      </p>
      <p style='color:#55576a;font-size:0.82rem;'>ابدأ بفتح جلسة جديدة من الشريط الجانبي</p>
    </div>
    """, unsafe_allow_html=True)
else:
    sess_data = storage.load_session(st.session_state.current_sid)

    col_name, col_clear = st.columns([5, 1])
    with col_name:
        new_name = st.text_input("اسم الجلسة", value=sess_data.get("name", "جلسة"), label_visibility="collapsed")
        if new_name != sess_data.get("name", ""):
            sess_data["name"] = new_name
            sess_data["messages"] = st.session_state.current_msgs
            storage.save_session(st.session_state.current_sid, sess_data)
    with col_clear:
        if st.button("🗑 مسح"):
            st.session_state.current_msgs = []
            sess_data["messages"] = []
            storage.save_session(st.session_state.current_sid, sess_data)
            st.rerun()

    chat_html = "<div class='chat-box'>"
    ai_cls = "bubble-ai advisor" if st.session_state.persona == "advisor" else "bubble-ai"
    for msg in st.session_state.current_msgs:
        content = msg["content"].replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        ts = msg.get("ts", "")
        if msg["role"] == "user":
            chat_html += f"<div class='bubble-user'>{content}<div class='bubble-meta'>{ts}</div></div>"
        else:
            chat_html += f"<div class='{ai_cls}'>{content}<div class='bubble-meta'>{ts}</div></div>"
    chat_html += "</div>"
    st.markdown(chat_html, unsafe_allow_html=True)

    pending = st.session_state.get("pending_input", "")
    user_input = st.text_area("سؤالك", value=pending, height=100,
                               placeholder="اكتب سؤالك القانوني هنا...", label_visibility="collapsed")
    if pending:
        st.session_state.pending_input = ""

    if st.button("إرسال", key="send_btn") and user_input.strip():
        ts = datetime.now().strftime("%H:%M")
        st.session_state.current_msgs.append({"role": "user", "content": user_input.strip(), "ts": ts})

        system_prompt = legal_tools.PERSONA_PROMPTS[st.session_state.persona]
        if st.session_state.docs_text:
            docs_ctx = "\n\n".join(st.session_state.docs_text[:3])[:3000]
            system_prompt += f"\n\nالوثائق المرفوعة:\n{docs_ctx}"

        history = st.session_state.current_msgs[:-1]

        with st.spinner("جارٍ التحليل..."):
            response = ai_call(user_input.strip(), history, system_prompt)

        st.session_state.current_msgs.append({"role": "assistant", "content": response, "ts": ts})
        sess_data["messages"] = st.session_state.current_msgs
        sess_data["persona"]  = st.session_state.persona
        storage.save_session(st.session_state.current_sid, sess_data)
        st.rerun()
