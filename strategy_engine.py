# strategy_engine.py
"""
محرر استراتيجية التقاضي.
يحدد نقاط القوة والضعف في القضية، ويُصدر توصيات استراتيجية.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime

class StrategyEngine:
    """
    تحليل استراتيجي للقضية لتحديد أفضل مسار قانوني.
    """

    def __init__(self):
        self.case_strengths = []
        self.case_weaknesses = []
        self.recommendations = []

    def analyze(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        تحليل شامل للقضية وإصدار استراتيجية مقترحة.
        case_data يجب أن يحتوي على:
        - facts: قائمة بالوقائع
        - evidence: قائمة بالأدلة المتوفرة
        - laws: قائمة بالمواد القانونية المستندة
        - financial_claim: المبلغ المطلوب
        - opponent: معلومات عن الخصم (اختياري)
        - timeline: جدول زمني للأحداث (اختياري)
        """
        self.case_strengths = []
        self.case_weaknesses = []
        self.recommendations = []

        # 1. تحليل نقاط القوة
        self._analyze_strengths(case_data)

        # 2. تحليل نقاط الضعف
        self._analyze_weaknesses(case_data)

        # 3. تحليل الجدوى الاقتصادية
        economic_feasibility = self._analyze_economic_feasibility(case_data)

        # 4. تحديد الاستراتيجية الموصى بها
        recommended_strategy = self._determine_strategy(case_data)

        return {
            "strengths": self.case_strengths,
            "weaknesses": self.case_weaknesses,
            "recommendations": self.recommendations,
            "economic_feasibility": economic_feasibility,
            "recommended_strategy": recommended_strategy,
            "summary": self._generate_summary(case_data),
        }

    def _analyze_strengths(self, case_data: Dict):
        """
        تحديد نقاط القوة في القضية.
        """
        facts = case_data.get("facts", [])
        evidence = case_data.get("evidence", [])
        laws = case_data.get("laws", [])

        # قوة الأدلة
        if evidence:
            self.case_strengths.append(f"✅ تتوفر {len(evidence)} دليل(ة) كتابي(ة) تدعم موقفك.")
            if len(evidence) >= 3:
                self.case_strengths.append("✅ وجود أدلة متعددة يعزز موقفك بشكل كبير.")

        # قوة المواد القانونية
        if laws:
            self.case_strengths.append(f"✅ تستند إلى {len(laws)} مادة نظامية واضحة.")

        # وجود إقرارات من الخصم
        for fact in facts:
            if "أقر" in fact or "اعترف" in fact:
                self.case_strengths.append("✅ يوجد إقرار كتابي من الخصم يُثبت صحة موقفك.")
                break

        # مدة الخدمة الطويلة تزيد من المكافأة
        if "years" in case_data and case_data["years"] >= 5:
            self.case_strengths.append("✅ مدة الخدمة الطويلة تزيد من قيمة المكافأة المستحقة.")

        # فصل تعسفي واضح
        if case_data.get("is_arbitrary"):
            self.case_strengths.append("✅ الفصل التعسفي يمنحك الحق في تعويض إضافي.")

    def _analyze_weaknesses(self, case_data: Dict):
        """
        تحديد نقاط الضعف في القضية.
        """
        facts = case_data.get("facts", [])
        evidence = case_data.get("evidence", [])
        timeline = case_data.get("timeline", [])

        # ضعف الأدلة
        if not evidence:
            self.case_weaknesses.append("❌ لا توجد أدلة كتابية واضحة تدعم موقفك.")
        elif len(evidence) < 2:
            self.case_weaknesses.append("⚠️ الأدلة محدودة، قد تحتاج إلى تعزيزها بشهادات أو مستندات إضافية.")

        # عدم وجود إشعار أو إنذار سابق
        for fact in facts:
            if "فصل" in fact and "إنذار" not in fact and "تحقيق" not in fact:
                self.case_weaknesses.append("⚠️ تم الفصل دون إجراءات سابقة (تحقيق/إنذار) مما قد يُضعف موقف الخصم لكن يحتاج إلى إثبات.")

        # مرور وقت طويل على الفصل (تقادم)
        if timeline:
            try:
                # محاولة حساب الوقت المنقضي
                last_event = timeline[-1]
                last_date = last_event.get("date")
                if last_date:
                    days_ago = (datetime.now() - last_date).days
                    if days_ago > 365:
                        self.case_weaknesses.append(f"⛔ مضى {days_ago} يوماً على آخر حدث، قد يكون الحق قد سقط بالتقادم (سنة واحدة).")
                    elif days_ago > 180:
                        self.case_weaknesses.append(f"⚠️ مضى {days_ago} يوماً، يُنصح بالإسراع قبل سقوط الحق بالتقادم.")
            except:
                pass

        # ضعف الموقف المالي
        claim = case_data.get("financial_claim", 0)
        if claim > 50000:
            self.case_weaknesses.append("⚠️ المبلغ المطلوب كبير نسبياً، قد يدفع الخصم للتقاضي الطويل.")

    def _analyze_economic_feasibility(self, case_data: Dict) -> Dict[str, Any]:
        """
        تحليل الجدوى الاقتصادية للتقاضي.
        """
        claim = case_data.get("financial_claim", 0)
        legal_fees = 0.05 * claim  # تقدير 5% رسوم تقاضي
        lawyer_fees = 0.10 * claim  # تقدير 10% أتعاب محاماة (إن وجد)
        total_cost = legal_fees + lawyer_fees

        net_gain = claim - total_cost

        if claim <= 0:
            return {"feasible": False, "reason": "المبلغ المطلوب غير محدد", "net_gain": 0}

        if net_gain > claim * 0.5:
            feasibility = "مرتفعة (العائد أكبر من 50% من المبلغ)"
            recommendation = "يُنصح بالمضي قدماً في التقاضي"
        elif net_gain > claim * 0.2:
            feasibility = "متوسطة (العائد بين 20% و 50% من المبلغ)"
            recommendation = "يُنصح بتقييم الخيارات البديلة (صلح، وساطة) قبل التقاضي"
        else:
            feasibility = "منخفضة (العائد أقل من 20% من المبلغ)"
            recommendation = "يُنصح بالتفاوض للصلح بدلاً من التقاضي"

        return {
            "claim_amount": claim,
            "estimated_legal_fees": legal_fees,
            "estimated_lawyer_fees": lawyer_fees,
            "total_cost": total_cost,
            "net_gain": net_gain,
            "feasibility": feasibility,
            "recommendation": recommendation,
        }

    def _determine_strategy(self, case_data: Dict) -> Dict[str, Any]:
        """
        تحديد الاستراتيجية الموصى بها.
        """
        strengths = len(self.case_strengths)
        weaknesses = len(self.case_weaknesses)
        claim = case_data.get("financial_claim", 0)

        if strengths >= 3 and weaknesses <= 1 and claim > 10000:
            strategy = "تقاضي"
            description = "قضيتك قوية جداً، يُنصح برفع دعوى فورية."
        elif strengths >= 2 and weaknesses <= 2 and claim > 5000:
            strategy = "تقاضي مع خيار الصلح"
            description = "قضيتك جيدة، لكن يُنصح بفتح باب الصلح مع الاستعداد للتقاضي."
        elif strengths >= 1 and claim > 3000:
            strategy = "صلح مع إنذار"
            description = "قضيتك مقبولة، يُنصح بإرسال إنذار رسمي ومحاولة الصلح أولاً."
        else:
            strategy = "تقييم إضافي"
            description = "قضيتك تحتاج إلى مزيد من الأدلة أو استشارة قانونية متخصصة قبل اتخاذ القرار."

        return {
            "strategy": strategy,
            "description": description,
            "strengths_count": strengths,
            "weaknesses_count": weaknesses,
            "next_steps": self._generate_next_steps(strategy),
        }

    def _generate_next_steps(self, strategy: str) -> List[str]:
        """
        توليد الخطوات التالية بناءً على الاستراتيجية المختارة.
        """
        if strategy == "تقاضي":
            return [
                "1. جمع جميع الأدلة والمستندات المؤيدة",
                "2. صياغة صحيفة الدعوى (متوفر في التطبيق)",
                "3. تقديم الدعوى لدى المحكمة العمالية المختصة",
                "4. متابعة الجلسات والرد على دفوع الخصم"
            ]
        elif strategy == "تقاضي مع خيار الصلح":
            return [
                "1. إرسال إنذار رسمي للخصم (متوفر في التطبيق)",
                "2. انتظار رد الخصم لمدة 15 يوماً",
                "3. إذا لم يتم الصلح، رفع دعوى فورية"
            ]
        elif strategy == "صلح مع إنذار":
            return [
                "1. إرسال إنذار رسمي للخصم",
                "2. التفاوض على تسوية ودية",
                "3. في حال الرفض، تقييم خيارات التقاضي"
            ]
        else:
            return [
                "1. مراجعة المستندات والأدلة المتوفرة",
                "2. استشارة محامٍ متخصص في القانون العمالي",
                "3. جمع أدلة إضافية (شهادات، مراسلات جديدة)"
            ]

    def _generate_summary(self, case_data: Dict) -> str:
        """
        توليد ملخص استراتيجي للقضية.
        """
        return f"""
        📊 **الملخص الاستراتيجي**

        نقاط القوة: {len(self.case_strengths)}
        نقاط الضعف: {len(self.case_weaknesses)}
        المبلغ المطلوب: {case_data.get('financial_claim', 0):,.2f} ريال

        التوصية النهائية: {self._determine_strategy(case_data)['strategy']}
        """
