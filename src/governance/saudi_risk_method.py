"""SDAIA-P145 v1 arithmetic and labels, verified against the supplied Arabic PDF.

Implements the page-25 matrix, not framework-wide conformity or risk acceptance.
English labels are project translations; Arabic labels follow the source.
"""

METHOD_ID = "SDAIA-P145-v1-2026"
SOURCE_URL = "https://sdaia.gov.sa/ar/MediaCenter/KnowledgeCenter/ResearchLibrary/ExecutiveSummaryAr.pdf"
LIKELIHOOD = {
    1: "Rare — نادر",
    2: "Unlikely — غير مرجح",
    3: "Likely — مرجح",
    4: "Almost certain — شبه مؤكد",
}
IMPACT = {
    1: "Low — منخفض",
    2: "Medium — متوسط",
    3: "High — مرتفع",
    4: "Catastrophic — كارثي",
}
CATEGORIES = (
    "التحيز والتمييز والإساءة",
    "الخصوصية والأمن",
    "المعلومات المضللة",
    "الاستخدام الضار",
    "تفاعل الإنسان والآلة",
    "الآثار الاجتماعية والاقتصادية والبيئية",
    "السلامة والمحدودية",
)
TREATMENTS = ("Avoid — التجنب", "Mitigate — التخفيف", "Transfer — النقل", "Accept — القبول")
STAGES = (
    ("Context and scope — تحديد السياق والنطاق", "17"),
    ("Risk identification — تحديد المخاطر", "18–20"),
    ("Risk assessment — تقييم المخاطر", "22–25"),
    ("Risk treatment — معالجة المخاطر", "26–27"),
    ("Monitoring and review — المتابعة والمراجعة", "28–29"),
)
NATIONAL_FIELDS = (
    "methodology", "category", "assessment_horizon", "likelihood_rationale",
    "impact_rationale", "treatment_strategy", "residual_basis", "residual_rationale",
    "assessment_evidence",
)
RESIDUAL_BASES = ("Planned estimate", "Post-treatment reassessment")


def matrix_result(likelihood, impact):
    if any(type(value) is not int or not 1 <= value <= 4 for value in (likelihood, impact)):
        raise ValueError("Likelihood and impact must be integers from 1 to 4.")
    score = likelihood * impact
    if score <= 2:
        level = "Low — منخفض"
    elif score <= 6:
        level = "Medium — متوسط"
    elif score <= 12:
        level = "High — مرتفع"
    else:
        level = "Catastrophic — كارثي"
    return {"score": score, "level": level}
