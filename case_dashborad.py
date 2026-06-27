# case_dashboard.py
"""
لوحة التحكم الرئيسية - تعرض جميع المخرجات في واجهة واحدة.
"""
import streamlit as st
from typing import Dict, Any

class CaseDashboard:
    @staticmethod
    def render(analysis_result: Dict[str, Any]):
        """
        يعرض لوحة التحكم مع جميع المخرجات.
        """
        extracted = analysis_result.get("extracted_data", {})
        strategic = analysis_result.get("strategic_recommendations", {})
        alerts = analysis_result.get("rules_alerts", [])
        procedural = analysis_result.get("procedural_result", {})
        deep = analysis_result.get("deep_result", {})
        counter_args = analysis_result.get("counter_arguments", [])

        # ============================
        # 1. الملخص التنفيذي
        # ============================
        st.markdown("### الملخص التنفيذي")
        st.markdown(f"""
        <div style="background:#f8f9fa;padding:15px;border-radius:8px;border-right:4px solid #1a1a1a;">
        <strong>الأطراف:</strong> {extracted.get('personal', {}).get('employee_name', 'غير محدد')} ضد {extracted.get('personal', {}).get('employer_name', 'غير محدد')}<br>
        <strong>المبلغ التقديري:</strong> {extracted.get('financial', {}).get('total_salary', 0) * 6:,.2f} ريال<br>
        <strong>قوة الموقف القانوني:</strong> {strategic.get('strength_score', 0)}%<br>
        <strong>المخاطر:</strong> {strategic.get('risk_level', 'غير محدد')}<br>
        <strong>التوصية:</strong> {strategic.get('legal_path', 'صلح')}
        </div>
        """, unsafe_allow_html=True)

        # ============================
        # 2. مصفوفة الحجج
        # ============================
        st.markdown("---")
        st.markdown("### مصفوفة الحجج")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**نقاط القوة**")
            strengths = []
            if procedural.get("is_arbitrary"):
                strengths.append("✅ فصل تعسفي (المادة 81)")
            if not procedural.get("has_investigation") and procedural.get("has_termination_letter"):
                strengths.append("✅ فصل دون تحقيق (المادة 80 - بطلان)")
            if deep.get("tone_analysis", {}).get("acknowledgments_detected", False):
                strengths.append("✅ إقرارات من الخصم")
            if strengths:
                for s in strengths[:5]:
                    st.markdown(f"- {s}")
            else:
                st.info("لم يتم اكتشاف نقاط قوة واضحة")

        with col2:
            st.markdown("**نقاط الضعف**")
            weaknesses = []
            if not extracted.get("evidence"):
                weaknesses.append("❌ ضعف الأدلة")
            if deep.get("tone_analysis", {}).get("threats_detected", False):
                weaknesses.append("❌ لغة تهديدية من الخصم")
            if extracted.get("employment", {}).get("service_years", 0) < 2:
                weaknesses.append("❌ مدة خدمة قصيرة")
            if weaknesses:
                for w in weaknesses[:5]:
                    st.markdown(f"- {w}")
            else:
                st.success("لا توجد نقاط ضعف واضحة")

        # ============================
        # 3. التنبيهات والتوصيات
        # ============================
        st.markdown("---")
        st.markdown("### التنبيهات والتوصيات")
        if alerts:
            for alert in alerts[:5]:
                st.warning(f"⚠️ {alert['text']}")
        for rec in strategic.get("immediate_actions", []):
            st.info(f"💡 {rec}")

        # ============================
        # 4. الحجج المضادة (إن وجدت)
        # ============================
        if counter_args:
            st.markdown("---")
            st.markdown("### الحجج المضادة المقترحة")
            for arg in counter_args[:2]:
                st.markdown(f"<div style='background:#f0f0f0;padding:10px;border-radius:6px;margin:5px 0;'>{arg}</div>", unsafe_allow_html=True)
