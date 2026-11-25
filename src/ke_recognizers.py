import re
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.context_aware_enhancers import LemmaContextAwareEnhancer

KE_ID_CONTEXT = ["id", "ids", "identity", "national", "idno", "passport"]

PROTECTED = {"ID", "IDS", "SMS", "KES", "DR", "MR", "MRS", "MS", "OPD", "NHIF", "KRA", "PIN"}


def ke_national_id_recogniser(spaced=True):
    patterns = [Pattern(name="ke_national_id_7_8_digits", regex=r"\b\d{7,8}\b", score=0.1)]
    if spaced:
        patterns.append(Pattern(
            name="ke_national_id_spaced",
            regex=r"\b(?:\d{4}\s\d{4}|\d{3}\s\d{4}|\d{4}\s\d{3})\b",
            score=0.1,
        ))
    return PatternRecognizer(
        supported_entity="KE_NATIONAL_ID",
        patterns=patterns,
        context=KE_ID_CONTEXT,
        supported_language="en",
    )


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


def _normalise_caps(text):
    return re.sub(
        r"\b[A-Z]{2,}\b",
        lambda m: m.group(0) if m.group(0) in PROTECTED else m.group(0).capitalize(),
        text,
    )


class KeAnalyzerEngine(AnalyzerEngine):

    def analyze(self, text, language="en", **kwargs):
        results = super().analyze(text=text, language=language, **kwargs)
        entities = kwargs.get("entities")
        normalised = _normalise_caps(text)
        if normalised != text and (entities is None or "PERSON" in entities):
            kw = dict(kwargs)
            kw["entities"] = ["PERSON"]
            names = super().analyze(text=normalised, language=language, **kw)
            results = [r for r in results if r.entity_type != "PERSON"] + names
        return results

class ExactWordContextEnhancer(LemmaContextAwareEnhancer):
    
    @staticmethod
    def _find_supportive_word_in_context(context_list, recognizer_context_list,
                                         matching_mode="substring"):
        return LemmaContextAwareEnhancer._find_supportive_word_in_context(
            context_list, recognizer_context_list, "whole_word"
        )

def build_ke_analyzer(prefix=3, suffix=2, spaced=True, caps=True, exact=True):
    enhancer_cls = ExactWordContextEnhancer if exact else LemmaContextAwareEnhancer
    enhancer = enhancer_cls(context_prefix_count=prefix, context_suffix_count=suffix)
    cls = KeAnalyzerEngine if caps else AnalyzerEngine
    analyzer = cls(context_aware_enhancer=enhancer)
    analyzer.registry.add_recognizer(ke_national_id_recogniser(spaced))
    analyzer.registry.add_recognizer(ke_phone_recogniser())
    return analyzer