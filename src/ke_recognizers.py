from presidio_analyzer import Pattern, PatternRecognizer

KE_ID_CONTEXT = ["id", "identity", "national", "idno", "passport"]


def ke_national_id_recogniser():
    pattern = Pattern(
        name="ke_national_id_7_8_digits",
        regex=r"\b\d{7,8}\b",
        score=0.1,  
    )
    return PatternRecognizer(
        supported_entity="KE_NATIONAL_ID",
        patterns=[pattern],
        context=KE_ID_CONTEXT,
        supported_language="en",
    )
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.context_aware_enhancers import LemmaContextAwareEnhancer

def ke_phone_recogniser():
    pattern = Pattern(
        name="ke_mobile",
        regex=r"(?<!\d)(?:\+?254|0)[\s-]?[17]\d{2}[\s-]?\d{3}[\s-]?\d{3}(?!\d)",
        score=0.6,
    )
    return PatternRecognizer(
        supported_entity="PHONE_NUMBER",
        patterns=[pattern],
        supported_language="en",
    )

def build_ke_analyzer(prefix=3, suffix=2):
    enhancer = LemmaContextAwareEnhancer(
        context_prefix_count=prefix, context_suffix_count=suffix
    )
    analyzer = AnalyzerEngine(context_aware_enhancer=enhancer)
    analyzer.registry.add_recognizer(ke_national_id_recogniser())
    analyzer.registry.add_recognizer(ke_phone_recogniser())
    return analyzer