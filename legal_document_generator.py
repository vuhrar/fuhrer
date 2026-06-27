# legal_document_generator.py
"""
مولد المستندات القانونية الجاهزة (إنذار، صحيفة دعوى، مذكرة قانونية).
"""
from typing import Dict, Any, List, Optional
from datetime import datetime

class LegalDocumentGenerator:
    """مولد المستندات القانونية"""

    def __init__(self, case_data: Dict[str, Any]):
        """
        case_data يجب أن يحتوي على:
        - plaintiff: اسم المدعي
        - defendant: اسم المدعى عليه
        - plaintiff_id: رقم هوية المدعي
        - defendant_id: رقم هوية المدعى عليه (إن وجد)
        - work_location: مكان العمل (لتحديد المحكمة المختصة)
        - claim_amount: مبلغ المطالبة
        - facts: قائمة بالوقائع (نصوص)
        - attachments: قائمة بالمستندات المرفقة (أسماء)
        - laws: قائمة بالمواد القانونية المستندة
        """
        self.data = case_data

    def generate_notice(self, notice_period_days: int = 15) -> str:
        """توليد إنذار رسمي"""
        now = datetime.now().strftime("%d/%m/%Y")
        notice = f"""
        بسم الله الرحمن الرحيم

        إنذار رسمي

        التاريخ: {now}
        المرسل إليه: {self.data.get('defendant', 'صاحب العمل')}
        المرسل: {self.data.get('plaintiff', 'الموظف')}

        موضوع الإنذار: المطالبة بالحقوق العمالية المستحقة

        السيد/ {self.data.get('defendant', 'صاحب العمل المحترم')}،

        السلام عليكم ورحمة الله وبركاته،

        نُعلمكم بأن السيد/ {self.data.get('plaintiff', 'الموظف')} (رقم الهوية: {self.data.get('plaintiff_id', 'غير محدد')}) كان يعمل لديكم في [مكان العمل: {self.data.get('work_location', 'غير محدد')}]، وقد انتهت علاقته العمالية بتاريخ [تاريخ الفصل أو ترك العمل].

        وبعد مراجعة كامل حقوقه العمالية، تبين أن مستحقاته المالية لديكم تبلغ {self.data.get('claim_amount', 0):,} ريال سعودي، وتفصيلها كالتالي:
        {self._format_claim_details()}

        واستناداً إلى أحكام نظام العمل، ولا سيما المواد ({', '.join(self.data.get('laws', ['غير محدد']))})، فإننا نطالبكم بسداد هذه المستحقات خلال {notice_period_days} يوماً من تاريخ استلام هذا الإنذار، وإلا فسنضطر لرفع دعوى قضائية أمام المحكمة العمالية المختصة، مع الاحتفاظ بكامل حقوقنا القانونية في المطالبة بالتعويض عن الأضرار التي لحقت بنا جراء التأخير.

        نأمل سرعة التجاوب، وحفظ الله الجميع لما فيه الخير والصلاح.

        وتفضلوا بقبول فائق الاحترام،

        مقدم الإنذار: {self.data.get('plaintiff', 'الموظف')}
        التوقيع: _______________
        """
        return notice

    def generate_lawsuit(self) -> str:
        """توليد صحيفة دعوى كاملة"""
        now = datetime.now().strftime("%d/%m/%Y")
        facts = "\n".join([f"- {f}" for f in self.data.get('facts', [])])
        attachments = "\n".join([f"- {a}" for a in self.data.get('attachments', [])])
        lawsuit = f"""
        صحيفة دعوى

        التاريخ: {now}

        المحكمة المختصة: المحكمة العمالية في {self._determine_court()}

        المدعي:
        الاسم: {self.data.get('plaintiff', 'غير محدد')}
        رقم الهوية: {self.data.get('plaintiff_id', 'غير محدد')}
        العنوان: {self.data.get('plaintiff_address', 'غير محدد')}

        المدعى عليه:
        الاسم: {self.data.get('defendant', 'غير محدد')}
        رقم الهوية: {self.data.get('defendant_id', 'غير محدد')}
        العنوان: {self.data.get('defendant_address', 'غير محدد')}

        أولاً: الوقائع
        {facts}

        ثانياً: المستندات المؤيدة
        {attachments}

        ثالثاً: المسوغ القانوني
        تستند هذه الدعوى إلى أحكام نظام العمل، ولا سيما المواد التالية: {', '.join(self.data.get('laws', ['غير محدد']))}، والتي تثبت حق المدعي في المطالبة بالمبلغ المذكور.

        رابعاً: الطلبات
        يطلب المدعي الحكم له بما يلي:
        1. إلزام المدعى عليه بدفع مبلغ {self.data.get('claim_amount', 0):,} ريال سعودي، وهو إجمالي المستحقات العمالية للمدعي.
        2. إلزام المدعى عليه بالتعويض عن الأضرار المادية والمعنوية التي لحقت بالمدعي.
        3. إلزام المدعى عليه بالمصاريف القضائية وأتعاب المحاماة.
        4. أي طلبات أخرى يراها القاضي منصفة.

        وللمدعي ما يثبت دعواه من مستندات مرفقة بهذه الصحيفة.

        المدعي: {self.data.get('plaintiff', 'غير محدد')}
        التوقيع: _______________
        """
        return lawsuit

    def generate_legal_memo(self) -> str:
        """توليد مذكرة قانونية (دفاع أو مطالبة)"""
        facts = "\n".join([f"- {f}" for f in self.data.get('facts', [])])
        memo = f"""
        مذكرة قانونية

        الموضوع: {self.data.get('subject', 'خلاف عمالي')}
        التاريخ: {datetime.now().strftime("%d/%m/%Y")}

        أولاً: الوقائع
        {facts}

        ثانياً: التحليل القانوني
        بناءً على الوقائع المذكورة أعلاه، وبالرجوع إلى أحكام نظام العمل، تبين أن المدعي (الموظف) قد تعرض لفصل تعسفي/تأخير رواتب/مخالفة إدارية، مما يُخوّله للمطالبة بحقوقه النظامية كاملة.

        ثالثاً: المواد النظامية المستندة
        {', '.join(self.data.get('laws', ['غير محدد']))}

        رابعاً: الرأي والتوصية
        نوصي بـ [تقديم إنذار رسمي / رفع دعوى قضائية / قبول عرض الصلح]، وذلك وفقاً للمعطيات المتاحة، حيث أن موقف المدعي قوي قانونياً بناءً على الأدلة المتوفرة.

        والله ولي التوفيق،
        المحامي/ المستشار القانوني
        """
        return memo

    def _determine_court(self) -> str:
        """تحديد المحكمة المختصة مكانياً"""
        location = self.data.get('work_location', 'الرياض')
        # في القانون السعودي، المحكمة العمالية المختصة هي التي يقع في دائرتها مكان العمل
        return f"مدينة {location}"

    def _format_claim_details(self) -> str:
        """تنسيق تفاصيل المطالبة"""
        details = ""
        eosb = self.data.get('eosb', 0)
        comp = self.data.get('arbitrary_compensation', 0)
        delay = self.data.get('salary_delay', 0)
        if eosb:
            details += f"- مكافأة نهاية الخدمة: {eosb:,} ريال\n"
        if comp:
            details += f"- تعويض الفصل التعسفي: {comp:,} ريال\n"
        if delay:
            details += f"- تعويض تأخير الراتب: {delay:,} ريال\n"
        return details
