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


def build_ke_analyzer(prefix=3, suffix=0):
    """Presidio analyser with the Kenyan ID recogniser and a narrowed context window."""
    enhancer = LemmaContextAwareEnhancer(
        context_prefix_count=prefix, context_suffix_count=suffix
    )
    analyzer = AnalyzerEngine(context_aware_enhancer=enhancer)
    analyzer.registry.add_recognizer(ke_national_id_recogniser())
    return analyzer