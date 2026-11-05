from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.governance.case_persistence import build_case_document, RISK_ANSWER_KEYS
from src.ui.localization import _translate

ROOT = Path(__file__).resolve().parents[1]


def test_arabic_navigation_and_workflow_keep_case_compatible():
    app = AppTest.from_file(ROOT / "app.py", default_timeout=15).run()
    app.selectbox(key="interface_language").set_value("ar").run()
    assert not app.exception
    assert app.title[0].value == "مختبر حوكمة الذكاء الاصطناعي للقطاع العام السعودي"

    app.switch_page("views/use_case.py").run()
    app.text_input(key="use_case_name").set_value("حالة بلدية افتراضية")
    app.selectbox(key="use_case_ai_role").set_value("Decision support")
    next(b for b in app.button if b.label == "حفظ في الجلسة").click().run()
    assert not app.exception
    assert app.session_state["use_case"]["ai_role"] == "Decision support"
    assert app.session_state["use_case"]["name"] == "حالة بلدية افتراضية"

    app.switch_page("views/risk_assessment.py").run()
    app.checkbox(key="personal_data").check().run()
    assert set(app.session_state["risk_answers"]) == set(RISK_ANSWER_KEYS)
    assert app.session_state["risk_score"] == 2
    next(b for b in app.button if b.label == "حفظ الحالة").click().run()
    assert not app.exception

    pages = {
        "saudi_risk_method": "المنهجية الوطنية السعودية لتقييم المخاطر",
        "risk_register": "سجل المخاطر ومعالجتها",
        "corrective_actions": "الإجراءات التصحيحية",
        "risk_decisions": "قرارات المخاطر المتبقية",
        "deployment_readiness": "جاهزية النشر",
        "raci": "مصفوفة الأدوار والمساءلة RACI",
        "inventory": "سجل أنظمة الذكاء الاصطناعي",
        "controls": "مكتبة ضوابط حوكمة الذكاء الاصطناعي",
        "dashboard": "لوحة الحوكمة التنفيذية",
        "sdaia_alignment": "المواءمة مع مبادئ سدايا",
        "impact_assessment": "تقييم الأثر وفق مبادئ سدايا",
    }
    for page, title in pages.items():
        app.switch_page(f"views/{page}.py").run()
        assert not app.exception, page
        assert app.title[0].value == title, page

    saved = deepcopy(build_case_document(app.session_state, saved_at="2026-11-05T00:00:00Z"))
    app.selectbox(key="interface_language").set_value("en").run()
    assert not app.exception
    assert app.title[0].value == "SDAIA Impact Assessment"
    assert build_case_document(app.session_state, saved_at=saved["saved_at"]) == saved
    app.switch_page("views/use_case.py").run()
    assert app.text_input(key="use_case_name").value == "حالة بلدية افتراضية"
    assert app.selectbox(key="use_case_ai_role").value == "Decision support"


def test_arabic_messages_preserve_identifiers_and_codes():
    assert _translate("Risk 4: likelihood must be an integer from 1 to 4.") == (
        "Risk 4: يجب أن يكون «الاحتمالية» عددًا صحيحًا من 1 إلى 4."
    )
    assert _translate("**Metric 2**") == "**المقياس 2**"
    assert _translate("SDAIA-P145-v1-2026") == "SDAIA-P145-v1-2026"
