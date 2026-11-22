import re
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.context_aware_enhancers import LemmaContextAwareEnhancer

# Words that, when they appear near a number, suggest it is a national ID.
KE_ID_CONTEXT = ["id", "identity", "national", "idno", "passport"]

# All-caps words that are not names; left alone by the case normalisation.
PROTECTED = {"ID", "IDS", "SMS", "KES", "DR", "MR", "MRS", "MS", "OPD", "NHIF", "KRA", "PIN"}


def ke_national_id_recogniser(spaced=True):
    """Kenyan national ID: 7 or 8 digits (optionally one space inside), low base score,
    boosted by nearby context words."""
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
    """Kenyan mobile numbers: +254 / 254 / 0 prefix, then 7xx or 1xx, optional spaces or hyphens."""
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
    """Title-case all-caps words (same length, so character offsets stay valid)."""
    return re.sub(
        r"\b[A-Z]{2,}\b",
        lambda m: m.group(0) if m.group(0) in PROTECTED else m.group(0).capitalize(),
        text,
    )


class KeAnalyzerEngine(AnalyzerEngine):
    """PERSON is detected on a case-normalised copy; everything else on the original text."""

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


def build_ke_analyzer(prefix=3, suffix=2, spaced=True, caps=True):
    """Presidio analyser with the Kenyan recognisers and a narrowed context window."""
    enhancer = LemmaContextAwareEnhancer(
        context_prefix_count=prefix, context_suffix_count=suffix
    )
    cls = KeAnalyzerEngine if caps else AnalyzerEngine
    analyzer = cls(context_aware_enhancer=enhancer)
    analyzer.registry.add_recognizer(ke_national_id_recogniser(spaced))
    analyzer.registry.add_recognizer(ke_phone_recogniser())
    return analyzer