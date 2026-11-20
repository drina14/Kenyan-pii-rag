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